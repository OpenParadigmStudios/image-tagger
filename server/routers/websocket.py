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

                elif message_type == "get_tags":
                    await handle_get_tags(websocket, connection_manager, state)

                elif message_type == "add_tag":
                    tag = message.get("data", {}).get("tag")
                    if tag:
                        await handle_add_tag(websocket, connection_manager, state, tag)

                elif message_type == "delete_tag":
                    tag = message.get("data", {}).get("tag")
                    if tag:
                        await handle_delete_tag(websocket, connection_manager, state, tag)

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
        tags: List of tags for the image
    """
    try:
        image_files = state["image_files"]
        img_index = int(image_id)

        if img_index < 0 or img_index >= len(image_files):
            raise ValueError(f"Invalid image index: {img_index}")

        img_path = image_files[img_index]
        output_dir = state["output_dir"]

        # Check if the image has been processed
        processed = str(img_path) in state["session_state"].processed_images

        if not processed:
            await connection_manager.send_message(
                websocket,
                {
                    "type": "error",
                    "data": {"message": f"Image {image_id} has not been processed yet"}
                }
            )
            return

        relative_path = state["session_state"].processed_images.get(str(img_path))
        if not relative_path:
            await connection_manager.send_message(
                websocket,
                {
                    "type": "error",
                    "data": {"message": f"Cannot find processed path for image {image_id}"}
                }
            )
            return

        # Get processed file path
        processed_path = output_dir / Path(relative_path).name
        txt_path = processed_path.with_suffix(".txt")

        # Import here to avoid circular imports
        from core.filesystem import save_image_tags, normalize_tag, load_tags, save_tags, add_tag

        # Normalize tags
        normalized_tags = [normalize_tag(tag) for tag in tags if normalize_tag(tag)]

        # Save tags to image file
        if save_image_tags(txt_path, normalized_tags):
            # Update master tags list with any new tags
            all_tags = load_tags(state["tags_file_path"])
            updated = False

            for tag in normalized_tags:
                if tag not in all_tags:
                    all_tags = add_tag(all_tags, tag)
                    updated = True

            if updated:
                save_tags(state["tags_file_path"], all_tags)
                state["session_state"].tags = sorted(all_tags)

                # Broadcast master tag list update
                await connection_manager.broadcast({
                    "type": "master_tags_update",
                    "data": {"tags": sorted(all_tags)}
                })

            # Update session state
            state["session_state"].last_updated = time.strftime("%Y-%m-%dT%H:%M:%S")

            # Send confirmation message
            await connection_manager.send_message(
                websocket,
                {
                    "type": "tags_updated",
                    "data": {
                        "image_id": image_id,
                        "tags": normalized_tags
                    }
                }
            )

            # Broadcast image tags update to other clients
            for conn in connection_manager.active_connections:
                if conn != websocket:
                    await connection_manager.send_message(
                        conn,
                        {
                            "type": "image_tags_update",
                            "data": {
                                "image_id": image_id,
                                "tags": normalized_tags
                            }
                        }
                    )

            logging.info(f"Updated tags for image {image_id}: {len(normalized_tags)} tags")

        else:
            await connection_manager.send_message(
                websocket,
                {
                    "type": "error",
                    "data": {"message": f"Failed to save tags for image {image_id}"}
                }
            )

    except ValueError:
        await connection_manager.send_message(
            websocket,
            {
                "type": "error",
                "data": {"message": f"Invalid image ID: {image_id}"}
            }
        )
    except Exception as e:
        logging.error(f"Error updating image tags: {e}")
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


async def handle_get_tags(
    websocket: WebSocket,
    connection_manager: ConnectionManager,
    state: Dict
) -> None:
    """
    Handle get_tags message type.

    Args:
        websocket: WebSocket connection
        connection_manager: Connection manager
        state: Application state
    """
    try:
        # Import here to avoid circular imports
        from core.filesystem import load_tags

        # Get tags from file
        tags = load_tags(state["tags_file_path"])

        # Send tags to client
        await connection_manager.send_message(
            websocket,
            {
                "type": "tags_list",
                "data": {"tags": sorted(tags)}
            }
        )

    except Exception as e:
        logging.error(f"Error getting tags: {e}")
        await connection_manager.send_message(
            websocket,
            {
                "type": "error",
                "data": {"message": str(e)}
            }
        )


async def handle_add_tag(
    websocket: WebSocket,
    connection_manager: ConnectionManager,
    state: Dict,
    tag: str
) -> None:
    """
    Handle add_tag message type.

    Args:
        websocket: WebSocket connection
        connection_manager: Connection manager
        state: Application state
        tag: Tag to add
    """
    try:
        # Import here to avoid circular imports
        from core.filesystem import load_tags, save_tags, add_tag, normalize_tag

        normalized_tag = normalize_tag(tag)
        if not normalized_tag:
            await connection_manager.send_message(
                websocket,
                {
                    "type": "error",
                    "data": {"message": "Tag cannot be empty"}
                }
            )
            return

        # Get existing tags
        existing_tags = load_tags(state["tags_file_path"])

        # Add new tag
        updated_tags = add_tag(existing_tags, normalized_tag)

        # Save if changed
        if len(updated_tags) > len(existing_tags):
            save_tags(state["tags_file_path"], updated_tags)

            # Update session state
            state["session_state"].tags = sorted(updated_tags)

            # Send confirmation to this client
            await connection_manager.send_message(
                websocket,
                {
                    "type": "tag_added",
                    "data": {
                        "tag": normalized_tag,
                        "tags": sorted(updated_tags)
                    }
                }
            )

            # Broadcast update to other clients
            for conn in connection_manager.active_connections:
                if conn != websocket:
                    await connection_manager.send_message(
                        conn,
                        {
                            "type": "tag_update",
                            "data": {
                                "action": "add",
                                "tag": normalized_tag,
                                "tags": sorted(updated_tags)
                            }
                        }
                    )

            logging.info(f"Added tag via WebSocket: {normalized_tag}")
        else:
            # Tag already exists
            await connection_manager.send_message(
                websocket,
                {
                    "type": "tag_exists",
                    "data": {
                        "tag": normalized_tag,
                        "tags": sorted(updated_tags)
                    }
                }
            )

    except Exception as e:
        logging.error(f"Error adding tag: {e}")
        await connection_manager.send_message(
            websocket,
            {
                "type": "error",
                "data": {"message": str(e)}
            }
        )


async def handle_delete_tag(
    websocket: WebSocket,
    connection_manager: ConnectionManager,
    state: Dict,
    tag: str
) -> None:
    """
    Handle delete_tag message type.

    Args:
        websocket: WebSocket connection
        connection_manager: Connection manager
        state: Application state
        tag: Tag to delete
    """
    try:
        # Import here to avoid circular imports
        from core.filesystem import load_tags, save_tags, remove_tag

        # Get existing tags
        existing_tags = load_tags(state["tags_file_path"])

        # Get count before removal
        before_count = len(existing_tags)

        # Remove tag
        updated_tags = remove_tag(existing_tags, tag)

        # Save if changed
        if len(updated_tags) < before_count:
            save_tags(state["tags_file_path"], updated_tags)

            # Update session state
            state["session_state"].tags = sorted(updated_tags)

            # Send confirmation to this client
            await connection_manager.send_message(
                websocket,
                {
                    "type": "tag_deleted",
                    "data": {
                        "tag": tag,
                        "tags": sorted(updated_tags)
                    }
                }
            )

            # Broadcast update to other clients
            for conn in connection_manager.active_connections:
                if conn != websocket:
                    await connection_manager.send_message(
                        conn,
                        {
                            "type": "tag_update",
                            "data": {
                                "action": "delete",
                                "tag": tag,
                                "tags": sorted(updated_tags)
                            }
                        }
                    )

            logging.info(f"Deleted tag via WebSocket: {tag}")
        else:
            # Tag not found
            await connection_manager.send_message(
                websocket,
                {
                    "type": "tag_not_found",
                    "data": {
                        "tag": tag,
                        "tags": sorted(updated_tags)
                    }
                }
            )

    except Exception as e:
        logging.error(f"Error deleting tag: {e}")
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
