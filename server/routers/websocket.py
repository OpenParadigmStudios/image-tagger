#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# WebSocket handling router

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from core.filesystem import save_session_state
from models.api import ImageTags, WebSocketMessage


class ConnectionManager:
    """Manage active WebSocket connections."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"New WebSocket connection established. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info(f"WebSocket connection closed. Remaining connections: {len(self.active_connections)}")

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logging.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Send a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logging.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Create router
router = APIRouter(tags=["websocket"])


def get_app_state():
    """Dependency to get application state."""
    from server.main import app
    return app.state.app_state


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, state: Dict = Depends(get_app_state)):
    """
    Handle WebSocket connections for real-time updates.

    Args:
        websocket: WebSocket connection
        state: Application state
    """
    connection_manager = state["connection_manager"]
    await connection_manager.connect(websocket)

    try:
        # Send initial session state
        session_state = state["session_state"]
        await connection_manager.send_message(
            websocket,
            {
                "type": "session_state",
                "data": {
                    "total_images": session_state.stats["total_images"],
                    "processed_images": len(session_state.processed_images),
                    "current_position": session_state.current_position,
                    "tags": session_state.tags
                }
            }
        )

        # Process messages from this client
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type", "")

                # Handle different message types
                if message_type == "ping":
                    await connection_manager.send_message(
                        websocket,
                        {"type": "pong"}
                    )

                elif message_type == "get_image":
                    image_id = message.get("data", {}).get("image_id")
                    if image_id is not None:
                        await handle_get_image(websocket, connection_manager, state, image_id)

                elif message_type == "update_tags":
                    image_id = message.get("data", {}).get("image_id")
                    tags = message.get("data", {}).get("tags", [])
                    if image_id is not None:
                        await handle_update_tags(websocket, connection_manager, state, image_id, tags)

                elif message_type == "save_session":
                    await handle_save_session(websocket, connection_manager, state)

                else:
                    logging.warning(f"Unknown message type: {message_type}")
                    await connection_manager.send_message(
                        websocket,
                        {
                            "type": "error",
                            "data": {"message": f"Unknown message type: {message_type}"}
                        }
                    )

            except json.JSONDecodeError:
                logging.error("Invalid JSON received from client")
                await connection_manager.send_message(
                    websocket,
                    {
                        "type": "error",
                        "data": {"message": "Invalid JSON format"}
                    }
                )

            except Exception as e:
                logging.error(f"Error processing message: {e}")
                await connection_manager.send_message(
                    websocket,
                    {
                        "type": "error",
                        "data": {"message": str(e)}
                    }
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logging.info("WebSocket disconnected")

    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


async def handle_get_image(
    websocket: WebSocket,
    connection_manager: ConnectionManager,
    state: Dict,
    image_id: str
) -> None:
    """
    Handle get_image message type.

    Args:
        websocket: WebSocket connection
        connection_manager: Connection manager
        state: Application state
        image_id: Image ID to get
    """
    try:
        image_files = state["image_files"]
        img_index = int(image_id)

        if img_index < 0 or img_index >= len(image_files):
            raise ValueError(f"Invalid image index: {img_index}")

        img_path = image_files[img_index]
        original_name = img_path.name

        # Check if this image has been processed
        processed = str(img_path) in state["session_state"].processed_images
        new_name = None
        relative_path = None

        if processed:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            if relative_path:
                new_name = Path(relative_path).name

        # Get tags if processed
        tags = []
        if processed and relative_path:
            processed_path = state["config"].input_directory / relative_path
            txt_path = processed_path.with_suffix(".txt")

            if txt_path.exists():
                tags = [line.strip() for line in txt_path.read_text(encoding='utf-8').splitlines() if line.strip()]

        # Prepare response
        image_url = f"/api/images/{image_id}/file"

        await connection_manager.send_message(
            websocket,
            {
                "type": "image_data",
                "data": {
                    "id": image_id,
                    "original_name": original_name,
                    "new_name": new_name,
                    "url": image_url,
                    "processed": processed,
                    "tags": tags
                }
            }
        )

        # Update current position in session state
        state["session_state"].current_position = image_id

    except ValueError as e:
        logging.error(f"Invalid image ID: {e}")
        await connection_manager.send_message(
            websocket,
            {
                "type": "error",
                "data": {"message": f"Invalid image ID: {image_id}"}
            }
        )
    except Exception as e:
        logging.error(f"Error handling get_image: {e}")
        await connection_manager.send_message(
            websocket,
            {
                "type": "error",
                "data": {"message": str(e)}
            }
        )


async def handle_update_tags(
    websocket: WebSocket,
    connection_manager: ConnectionManager,
    state: Dict,
    image_id: str,
    tags: List[str]
) -> None:
    """
    Handle update_tags message type.

    Args:
        websocket: WebSocket connection
        connection_manager: Connection manager
        state: Application state
        image_id: Image ID to update
        tags: New tags for the image
    """
    try:
        from server.routers.images import update_master_tags_list
        from core.filesystem import process_image

        image_files = state["image_files"]
        img_index = int(image_id)

        if img_index < 0 or img_index >= len(image_files):
            raise ValueError(f"Invalid image index: {img_index}")

        img_path = image_files[img_index]

        # Process the image if not already processed
        if str(img_path) not in state["session_state"].processed_images:
            state["session_state"].processed_images, new_img_path, txt_file_path = process_image(
                img_path,
                state["output_dir"],
                state["config"].prefix,
                state["session_state"].processed_images
            )
        else:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            new_img_path = state["config"].input_directory / relative_path
            txt_file_path = new_img_path.with_suffix(".txt")

        # Write tags to text file
        txt_file_path.write_text("\n".join(tags), encoding='utf-8')

        # Update master tags list
        update_master_tags_list(tags, state["tags_file_path"])

        # Update session state
        state["session_state"].current_position = image_id
        save_session_state(state["session_file_path"], state["session_state"])

        # Send success response
        await connection_manager.send_message(
            websocket,
            {
                "type": "tags_updated",
                "data": {
                    "image_id": image_id,
                    "tags": tags
                }
            }
        )

        # Broadcast session update to all clients
        await connection_manager.broadcast(
            {
                "type": "session_update",
                "data": {
                    "total_images": state["session_state"].stats["total_images"],
                    "processed_images": len(state["session_state"].processed_images),
                    "current_position": state["session_state"].current_position
                }
            }
        )

    except Exception as e:
        logging.error(f"Error handling update_tags: {e}")
        await connection_manager.send_message(
            websocket,
            {
                "type": "error",
                "data": {"message": str(e)}
            }
        )


async def handle_save_session(
    websocket: WebSocket,
    connection_manager: ConnectionManager,
    state: Dict
) -> None:
    """
    Handle save_session message type.

    Args:
        websocket: WebSocket connection
        connection_manager: Connection manager
        state: Application state
    """
    try:
        # Save session state
        success = save_session_state(state["session_file_path"], state["session_state"])

        # Send response
        await connection_manager.send_message(
            websocket,
            {
                "type": "session_saved",
                "data": {
                    "success": success,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
            }
        )

    except Exception as e:
        logging.error(f"Error handling save_session: {e}")
        await connection_manager.send_message(
            websocket,
            {
                "type": "error",
                "data": {"message": str(e)}
            }
        )


async def handle_websocket_connection(websocket: WebSocket, app_state: Dict) -> None:
    """
    Handle a WebSocket connection.

    Args:
        websocket: WebSocket connection
        app_state: Application state
    """
    await websocket_endpoint(websocket, app_state)
