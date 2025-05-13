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
from server.routers.websocket import ConnectionManager

# Create global FastAPI app instance
app = FastAPI(
    title="CivitAI Flux Dev LoRA Tagging Assistant",
    description="Web interface for tagging images for CivitAI Flux Dev LoRA model training",
    version="1.0.0"
)


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
    # Initialize application state
    state = initialize_application_state(config)

    # Store the state in the app
    app.state.app_state = state

    # Serve static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Import routers
    from server.routers.images import router as images_router
    from server.routers.tags import router as tags_router
    from server.routers.websocket import router as websocket_router

    # Include routers
    app.include_router(images_router)
    app.include_router(tags_router)
    app.include_router(websocket_router)

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

    return app


def start_server(config: AppConfig) -> None:
    """
    Start the FastAPI server.

    Args:
        config: Application configuration
    """
    # Create FastAPI app
    app = create_app(config)

    # Attempt to open a web browser
    url = f"http://{config.host}:{config.port}"
    try:
        webbrowser.open(url)
        logging.info(f"Opened web browser to {url}")
    except Exception as e:
        logging.warning(f"Failed to open web browser: {e}")
        logging.info(f"Please manually open {url} in your web browser")

    # Start Uvicorn server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info"
    )


def graceful_shutdown(app: FastAPI) -> None:
    """
    Perform graceful shutdown tasks.

    Args:
        app: FastAPI application instance
    """
    # Save session state
    if hasattr(app, "state") and hasattr(app.state, "app_state"):
        session_file_path = app.state.app_state.get("session_file_path")
        session_state = app.state.app_state.get("session_state")

        if session_file_path and session_state:
            logging.info("Saving session state before shutdown...")
            save_session_state(session_file_path, session_state)

    logging.info("Server shutdown complete.")
