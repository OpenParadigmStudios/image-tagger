#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Main server application with FastAPI

import json
import logging
import sys
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Import core modules
sys.path.append(str(Path(__file__).parent.parent))
from core.config import AppConfig
from core.filesystem import (
    setup_directories,
    scan_image_files,
    setup_output_directory,
    setup_tags_file,
    get_processed_images,
    save_session_state,
    SessionState
)


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

    async def send_message(self, websocket: WebSocket, message: str) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logging.error(f"Error sending message to client: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str) -> None:
        """Send a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


def initialize_application_state(config: AppConfig) -> Dict:
    """
    Initialize the application state and resources.

    Args:
        config: Application configuration

    Returns:
        Dictionary with application state
    """
    # Set up output directory
    output_dir = setup_output_directory(config.input_directory, config.output_dir)

    # Define paths for session and tags files
    session_file_path = output_dir / "session.json"
    tags_file_path = output_dir / "tags.txt"

    # Scan for image files
    image_files = scan_image_files(config.input_directory)

    # Initialize or load session state
    if config.resume and session_file_path.exists():
        session_state = get_processed_images(session_file_path)
        logging.info(f"Resuming session: {len(session_state.processed_images)} images already processed.")
    else:
        session_state = SessionState()
        session_state.stats["total_images"] = len(image_files)
        logging.info(f"Starting new session with {len(image_files)} images.")

    # Load or initialize tags
    tags = setup_tags_file(tags_file_path)
    if tags and not session_state.tags:
        session_state.tags = tags

    # Save initial session state
    save_session_state(session_file_path, session_state)

    # Create WebSocket connection manager
    connection_manager = ConnectionManager()

    # Return complete application state
    return {
        "config": config,
        "session_state": session_state,
        "image_files": image_files,
        "output_dir": output_dir,
        "session_file_path": session_file_path,
        "tags_file_path": tags_file_path,
        "connection_manager": connection_manager
    }


def create_app(config: AppConfig) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        config: Application configuration

    Returns:
        FastAPI: Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="CivitAI Flux Dev LoRA Tagging Assistant",
        description="Web interface for tagging images for CivitAI Flux Dev LoRA model training",
        version="1.0.0"
    )

    # Initialize application state
    state = initialize_application_state(config)

    # Store the state in the app
    app.state.app_state = state

    # Serve static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Basic routes
    @app.get("/")
    async def get_index():
        """Serve the main HTML page."""
        return FileResponse("static/index.html")

    @app.get("/api/status")
    async def get_status():
        """Get the current application status."""
        session_state = app.state.app_state["session_state"]
        return {
            "status": "running",
            "total_images": session_state.stats["total_images"],
            "processed_images": len(session_state.processed_images),
            "current_position": session_state.current_position,
            "last_updated": session_state.last_updated
        }

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Handle WebSocket connections for real-time updates."""
        connection_manager = app.state.app_state["connection_manager"]
        await connection_manager.connect(websocket)

        try:
            # Send initial session state
            session_state = app.state.app_state["session_state"]
            await connection_manager.send_message(
                websocket,
                json.dumps({
                    "type": "session_state",
                    "data": {
                        "total_images": session_state.stats["total_images"],
                        "processed_images": len(session_state.processed_images),
                        "current_position": session_state.current_position,
                        "tags": session_state.tags
                    }
                })
            )

            # Process messages from this client
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Process different message types
                if message["type"] == "ping":
                    await connection_manager.send_message(
                        websocket,
                        json.dumps({"type": "pong"})
                    )

                # Add other message handlers here

        except WebSocketDisconnect:
            connection_manager.disconnect(websocket)
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
            connection_manager.disconnect(websocket)

    # Import and include API routers here
    # from server.routers import images, tags
    # app.include_router(images.router, prefix="/api")
    # app.include_router(tags.router, prefix="/api")

    return app


def start_server(config: AppConfig) -> None:
    """
    Start the FastAPI server with the given configuration.

    Args:
        config: Application configuration
    """
    app = create_app(config)

    # Open browser to the application
    webbrowser.open(f"http://{config.host}:{config.port}")

    # Start the server
    uvicorn.run(app, host=config.host, port=config.port)


def graceful_shutdown(app: FastAPI) -> None:
    """
    Perform a graceful shutdown, saving state and releasing resources.

    Args:
        app: FastAPI application
    """
    logging.info("Performing graceful shutdown")

    # Get application state
    state = app.state.app_state

    # Save final session state
    save_session_state(state["session_file_path"], state["session_state"])

    # Notify connected clients (in a production app, this would be properly handled)
    # state["connection_manager"].broadcast(json.dumps({"type": "shutdown", "data": {"message": "Server shutting down"}}))

    logging.info("Application shutdown complete.")
