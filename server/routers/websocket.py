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
from fastapi.concurrency import run_in_threadpool

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
            message: The message to broadcast (JSON string)
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

    async def broadcast_json(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients directly from a Python dict.

        Args:
            message: Python dictionary containing the message
        """
        try:
            # Validate message format
            message_obj = WebSocketMessage(type=message.get("type"), data=message.get("data", {}))

            # Convert to JSON string
            message_json = json.dumps(message_obj.dict())

            # Use existing broadcast method
            await self.broadcast(message_json)
        except ValidationError as e:
            logging.error(f"Invalid broadcast_json message format: {e}")
        except Exception as e:
            logging.error(f"Error during broadcast_json: {e}")

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
        request: The FastAPI request object
    """
    state = request.state.app_state
    connection_manager = state["connection_manager"]

    try:
        # Parse the message
        message_data = json.loads(message_text)
        message = WebSocketMessage(**message_data)

        # Update heartbeat timestamp
        await connection_manager.update_heartbeat(websocket)

        # Handle message based on type
        if message.type == "heartbeat":
            # Simple heartbeat response
            await connection_manager.send_message(websocket, {
                "type": "heartbeat",
                "data": {"timestamp": time.time()}
            })

        elif message.type == "tags_request":
            # Request for tags list
            async def get_tags():
                tags_file_path = state["tags_file_path"]
                if tags_file_path.exists():
                    return [line.strip() for line in tags_file_path.read_text(encoding='utf-8').splitlines() if line.strip()]
                return []

            tags = await run_in_threadpool(lambda: get_tags())

            await connection_manager.send_message(websocket, {
                "type": "tags_update",
                "data": {"tags": tags}
            })

        elif message.type == "session_request":
            # Request for session info
            session_manager = state["session_manager"]

            session_info = {
                "current_position": session_manager.state.current_position,
                "last_updated": session_manager.state.last_updated,
                "stats": {
                    "total_images": session_manager.state.stats.get("total_images", 0),
                    "processed_images": session_manager.state.stats.get("processed_images", 0)
                },
                "version": session_manager.state.version
            }

            await connection_manager.send_message(websocket, {
                "type": "session_update",
                "data": session_info
            })

        else:
            # Unknown message type - log it
            logging.warning(f"Unknown WebSocket message type: {message.type}")

    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in WebSocket message: {message_text}")
        await connection_manager.send_message(websocket, {
            "type": "error",
            "data": {"message": "Invalid JSON format"}
        })

    except ValidationError as e:
        logging.error(f"Validation error in WebSocket message: {e}")
        await connection_manager.send_message(websocket, {
            "type": "error",
            "data": {"message": "Invalid message format"}
        })

    except Exception as e:
        logging.error(f"Error handling WebSocket message: {e}")
        try:
            await connection_manager.send_message(websocket, {
                "type": "error",
                "data": {"message": "Server error processing message"}
            })
        except Exception:
            # If sending the error message fails, just log it
            logging.error("Failed to send error message to WebSocket client")


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
