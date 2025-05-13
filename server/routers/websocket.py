#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# WebSocket router for real-time communication

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Set, Optional, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from pydantic import ValidationError

from models.api import ImageTags, WebSocketMessage

# Create router
router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)

class ConnectionManager:
    """
    Manage WebSocket connections with clients.
    """
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: List[WebSocket] = []
        self.client_info: Dict[WebSocket, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str = None) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            client_id: Optional client identifier
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            self.client_info[websocket] = {
                "id": client_id or str(id(websocket)),
                "connected_at": asyncio.get_event_loop().time(),
                "last_heartbeat": asyncio.get_event_loop().time(),
                "message_count": 0
            }
        logging.info(f"Client connected: {self.client_info[websocket]['id']}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        async with self._lock:
            if websocket in self.active_connections:
                client_id = self.client_info.get(websocket, {}).get("id", "unknown")
                self.active_connections.remove(websocket)
                if websocket in self.client_info:
                    del self.client_info[websocket]
                logging.info(f"Client disconnected: {client_id}")

    def disconnect_all(self) -> None:
        """Disconnect all WebSocket connections."""
        self.active_connections = []
        self.client_info = {}
        logging.info("All WebSocket connections closed")

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific client.

        Args:
            websocket: The WebSocket connection
            message: The message to send

        Returns:
            bool: True if message was sent successfully
        """
        if websocket not in self.active_connections:
            return False

        try:
            # Validate message format
            message_obj = WebSocketMessage(type=message.get("type"), data=message.get("data", {}))

            # Send message
            await websocket.send_text(json.dumps(message_obj.dict()))

            # Update stats
            if websocket in self.client_info:
                self.client_info[websocket]["message_count"] += 1

            return True
        except ValidationError as e:
            logging.error(f"Invalid message format: {e}")
            return False
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            await self.disconnect(websocket)
            return False

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        try:
            # Parse the message to validate it
            message_dict = json.loads(message)
            message_obj = WebSocketMessage(type=message_dict.get("type"), data=message_dict.get("data", {}))

            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                    if connection in self.client_info:
                        self.client_info[connection]["message_count"] += 1
                except Exception as e:
                    logging.warning(f"Error broadcasting to client: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                await self.disconnect(connection)

            if len(self.active_connections) > 0:
                logging.debug(f"Broadcast message to {len(self.active_connections)} clients")
        except ValidationError as e:
            logging.error(f"Invalid broadcast message format: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in broadcast message: {e}")
        except Exception as e:
            logging.error(f"Error during broadcast: {e}")

    async def update_heartbeat(self, websocket: WebSocket) -> None:
        """
        Update the heartbeat timestamp for a connection.

        Args:
            websocket: The WebSocket connection
        """
        if websocket in self.client_info:
            self.client_info[websocket]["last_heartbeat"] = asyncio.get_event_loop().time()

    async def cleanup_stale_connections(self, max_idle_time: float = 300) -> None:
        """
        Remove connections that haven't sent a heartbeat in a while.

        Args:
            max_idle_time: Maximum idle time in seconds
        """
        current_time = asyncio.get_event_loop().time()
        disconnected = []

        for websocket, info in self.client_info.items():
            if current_time - info["last_heartbeat"] > max_idle_time:
                disconnected.append(websocket)

        for websocket in disconnected:
            logging.info(f"Removing stale connection: {self.client_info[websocket]['id']}")
            await self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """
        Get the number of active connections.

        Returns:
            int: Number of active connections
        """
        return len(self.active_connections)

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active connections.

        Returns:
            Dict: Connection statistics
        """
        return {
            "active_connections": len(self.active_connections),
            "clients": [info for info in self.client_info.values()]
        }


# Create a connection manager instance
connection_manager = ConnectionManager()


async def handle_websocket_message(websocket: WebSocket, message_text: str, request: Request) -> None:
    """
    Handle incoming WebSocket messages.

    Args:
        websocket: The WebSocket connection
        message_text: The message text
        request: The HTTP request
    """
    try:
        # Parse message JSON
        message = json.loads(message_text)

        # Validate message format
        message_obj = WebSocketMessage(type=message.get("type"), data=message.get("data", {}))

        # Handle different message types
        message_type = message_obj.type
        data = message_obj.data
        app_state = request.state.app_state

        if message_type == "heartbeat":
            # Update heartbeat timestamp
            await connection_manager.update_heartbeat(websocket)

            # Send heartbeat response
            await connection_manager.send_message(
                websocket,
                {"type": "heartbeat", "data": {"timestamp": asyncio.get_event_loop().time()}}
            )

        elif message_type == "session_request":
            # Client is requesting session state
            session_state = app_state["session_manager"].state

            # Send session state
            await connection_manager.send_message(
                websocket,
                {
                    "type": "session_update",
                    "data": {
                        "status": "active",
                        "total_images": session_state.stats.get("total_images", 0),
                        "processed_images": session_state.stats.get("processed_images", 0),
                        "current_position": session_state.current_position,
                        "last_updated": session_state.last_updated
                    }
                }
            )

        elif message_type == "tags_request":
            # Client is requesting all tags
            tags_file = app_state["paths"]["tags_file"]
            from core.tagging import load_tags
            all_tags = load_tags(tags_file)

            # Send all tags
            await connection_manager.send_message(
                websocket,
                {"type": "tag_update", "data": {"tags": all_tags}}
            )

        elif message_type == "tag_add":
            # Client is adding a tag
            if "tag" not in data or not data["tag"]:
                raise ValueError("Tag is required")

            new_tag = data["tag"]

            # Add tag to master list
            tags_file = app_state["paths"]["tags_file"]
            from core.tagging import load_tags, save_tags, add_tag
            all_tags = load_tags(tags_file)
            all_tags = add_tag(all_tags, new_tag)
            save_tags(tags_file, all_tags)

            # Add tag to session state
            app_state["session_manager"].add_tag(new_tag)
            app_state["session_manager"].save()

            # Broadcast tag update to all clients
            await connection_manager.broadcast(
                json.dumps({"type": "tag_update", "data": {"tags": all_tags}})
            )

        elif message_type == "tag_remove":
            # Client is removing a tag
            if "tag" not in data or not data["tag"]:
                raise ValueError("Tag is required")

            tag_to_remove = data["tag"]

            # Remove tag from master list
            tags_file = app_state["paths"]["tags_file"]
            from core.tagging import load_tags, save_tags, remove_tag
            all_tags = load_tags(tags_file)
            all_tags = remove_tag(all_tags, tag_to_remove)
            save_tags(tags_file, all_tags)

            # Remove tag from session state
            app_state["session_manager"].remove_tag(tag_to_remove)
            app_state["session_manager"].save()

            # Broadcast tag update to all clients
            await connection_manager.broadcast(
                json.dumps({"type": "tag_update", "data": {"tags": all_tags}})
            )

        elif message_type == "image_tags_update":
            # Client is updating tags for an image
            if "image_id" not in data or not data["image_id"]:
                raise ValueError("Image ID is required")
            if "tags" not in data:
                raise ValueError("Tags array is required")

            image_id = data["image_id"]
            tags = data["tags"]

            # Find the image path
            session_state = app_state["session_manager"].state
            image_path = None
            for orig_path, new_path in session_state.processed_images.items():
                if Path(new_path).stem == image_id:
                    image_path = new_path
                    break

            if not image_path:
                raise ValueError(f"Image not found: {image_id}")

            # Update image tags
            from core.tagging import save_image_tags
            text_file_path = Path(image_path).with_suffix('.txt')
            save_image_tags(text_file_path, tags)

            # Update session state
            app_state["session_manager"].set_current_position(image_id)
            app_state["session_manager"].save()

            # Broadcast update to all clients
            await connection_manager.broadcast(
                json.dumps({
                    "type": "image_tags_update",
                    "data": {
                        "image_id": image_id,
                        "tags": tags
                    }
                })
            )

        else:
            # Unknown message type
            logging.warning(f"Unknown WebSocket message type: {message_type}")

    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in WebSocket message: {e}")

    except ValidationError as e:
        logging.error(f"Invalid WebSocket message format: {e}")

    except Exception as e:
        logging.error(f"Error handling WebSocket message: {e}")

        # Send error to client
        try:
            await connection_manager.send_message(
                websocket,
                {"type": "error", "data": {"message": str(e)}}
            )
        except:
            pass


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, request: Request):
    """
    WebSocket endpoint for real-time communication.

    Args:
        websocket: The WebSocket connection
        request: The HTTP request
    """
    client_id = None

    try:
        # Accept connection
        await connection_manager.connect(websocket, client_id)

        # Send initial connection confirmation
        await connection_manager.send_message(
            websocket,
            {"type": "connect", "data": {"message": "Connected to server"}}
        )

        # Receive and process messages
        while True:
            message = await websocket.receive_text()
            await handle_websocket_message(websocket, message, request)

    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")

    except Exception as e:
        logging.error(f"WebSocket error: {e}")

    finally:
        # Clean up connection
        await connection_manager.disconnect(websocket)


@router.on_event("startup")
async def start_connection_cleanup():
    """Start periodic cleanup of stale connections."""
    asyncio.create_task(periodic_connection_cleanup())


async def periodic_connection_cleanup():
    """Periodically clean up stale connections."""
    while True:
        try:
            await connection_manager.cleanup_stale_connections()
        except Exception as e:
            logging.error(f"Error during connection cleanup: {e}")

        await asyncio.sleep(60)  # Run every minute
