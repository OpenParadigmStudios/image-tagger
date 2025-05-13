#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Server implementation

import asyncio
import json
import logging
import os
import signal
import sys
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from fastapi import WebSocket

# Import routers
from server.routers import images, tags, websocket, status

# Import core modules
from core.config import AppConfig
from core.filesystem import get_default_paths
from core.session import SessionManager, SessionState
from core.image_processing import scan_image_files
from core.tagging import setup_tags_file

# Create global app instance and global state
app = FastAPI(
    title="CivitAI Flux Dev LoRA Tagging Assistant",
    description="Web-based image tagging for CivitAI Flux Dev LoRA model training",
    version="1.0.0"
)

# Global state to store application context
app_state: Dict[str, Any] = {
    "config": None,
    "session_manager": None,
    "paths": None,
    "connection_manager": None,
    "image_files": None,
    "shutdown_event": None
}


def setup_signal_handlers() -> None:
    """
    Set up signal handlers for graceful shutdown.
    """
    def sync_broadcast(message):
        """Helper to send sync broadcast message."""
        if "connection_manager" in app_state and app_state["connection_manager"]:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # The message will be sent by server shutdown handlers
                    logging.info("Skipping broadcast during shutdown in running loop")
                    return
                else:
                    # Create a new event loop if needed
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        app_state["connection_manager"].broadcast_json(message)
                    )
                    loop.close()
            except Exception as e:
                logging.error(f"Error in sync broadcast: {e}")

    def handle_shutdown(sig, frame):
        logging.info(f"Received signal {sig}, initiating graceful shutdown...")

        # Save session state
        if app_state["session_manager"] is not None:
            try:
                app_state["session_manager"].save(force=True)
                logging.info("Session state saved")
            except Exception as e:
                logging.error(f"Error saving session state during shutdown: {e}")

        # Notify connected clients
        if app_state["connection_manager"] is not None:
            try:
                shutdown_message = {
                    "type": "shutdown",
                    "data": {"message": "Server shutting down"}
                }
                sync_broadcast(shutdown_message)
                logging.info("Shutdown notification sent to clients")
            except Exception as e:
                logging.error(f"Error notifying clients during shutdown: {e}")

        # Set shutdown event
        if app_state["shutdown_event"] is not None:
            app_state["shutdown_event"].set()

        # Exit with success code
        logging.info("Shutdown complete")
        sys.exit(0)

    # Register handlers for SIGINT and SIGTERM
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    logging.info("Signal handlers registered for graceful shutdown")


def setup_middleware():
    """Set up middlewares for the FastAPI application."""
    # Set up CORS with more specific settings
    origins = [
        f"http://{os.environ.get('HOST', '127.0.0.1')}:{os.environ.get('PORT', '8000')}",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Provide access to app_state throughout the application
    @app.middleware("http")
    async def add_app_state(request: Request, call_next):
        request.state.app_state = app_state
        response = await call_next(request)
        return response


def setup_routes():
    """Set up routes and endpoints for the FastAPI application."""
    # Include routers
    app.include_router(images.router)
    app.include_router(tags.router)
    app.include_router(status.router)

    # Direct WebSocket endpoint (not using the router)
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        from server.routers.websocket import handle_websocket_message

        client_id = None

        try:
            # Accept connection immediately
            await websocket.accept()

            # Register with connection manager
            await app_state["connection_manager"].connect(websocket, client_id)

            # Send initial connection confirmation
            await app_state["connection_manager"].send_message(
                websocket,
                {"type": "connect", "data": {"message": "Connected to server"}}
            )

            # Handle messages
            while True:
                message = await websocket.receive_text()
                await handle_websocket_message(websocket, message, None)

        except Exception as e:
            logging.error(f"WebSocket error: {e}")

        finally:
            # Clean up connection
            if websocket in app_state["connection_manager"].active_connections:
                await app_state["connection_manager"].disconnect(websocket)

    # Serve static files
    static_dir = Path(__file__).parent.parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Root endpoint for the web UI
    @app.get("/")
    async def get_index():
        index_path = static_dir / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="Web UI not found")
        return FileResponse(index_path)


@app.on_event("startup")
async def startup_event():
    """
    Initialize application state on startup.
    """
    config = app_state["config"]

    # Set up paths
    paths = get_default_paths(config)
    app_state["paths"] = paths

    # Standardize direct access to key paths
    app_state["output_dir"] = paths["output_dir"]
    app_state["session_file_path"] = paths["session_file"]
    app_state["tags_file_path"] = paths["tags_file"]

    # Create shutdown event
    app_state["shutdown_event"] = asyncio.Event()

    # Scan for images
    try:
        image_files = scan_image_files(config.input_directory)
        app_state["image_files"] = image_files
    except Exception as e:
        logging.error(f"Error scanning images: {e}")
        app_state["image_files"] = []

    # Set up session manager
    session_file = paths["session_file"]
    session_manager = SessionManager(session_file)
    session_manager.set_auto_save_interval(config.auto_save)
    app_state["session_manager"] = session_manager

    # Make session state directly accessible
    app_state["session_state"] = session_manager.state

    # Get WebSocket connection manager from websocket router
    app_state["connection_manager"] = websocket.connection_manager

    # Setup tags file
    tags_file = paths["tags_file"]
    setup_tags_file(tags_file)

    # Update session stats
    session_manager.update_stats(
        total_images=len(image_files) if image_files else 0,
        processed_images=len(session_manager.state.processed_images)
    )

    logging.info("Application state initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up resources during shutdown.
    """
    # Save session state
    if app_state["session_manager"] is not None:
        try:
            app_state["session_manager"].save(force=True)
            logging.info("Session state saved during shutdown")
        except Exception as e:
            logging.error(f"Error saving session state during shutdown: {e}")

    # Close WebSocket connections
    if app_state["connection_manager"] is not None:
        app_state["connection_manager"].disconnect_all()
        logging.info("All WebSocket connections closed")

    logging.info("Shutdown complete")


def start_server(config: AppConfig) -> None:
    """
    Start the FastAPI server.

    Args:
        config: Application configuration
    """
    # Store configuration in app_state
    app_state["config"] = config

    # Setup signal handlers
    setup_signal_handlers()

    # Setup app middleware
    setup_middleware()

    # Setup routes and endpoints
    setup_routes()

    # Open browser if not in test mode
    if not os.environ.get("TAGGER_TEST_MODE"):
        url = f"http://{config.host}:{config.port}"
        webbrowser.open(url)
        logging.info(f"Opening browser at {url}")

    # Start the server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info"
    )
