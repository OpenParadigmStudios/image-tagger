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

# Import routers
from server.routers import images, tags, websocket

# Import core modules
from core.config import AppConfig
from core.filesystem import get_default_paths
from core.session import SessionManager, SessionState
from core.image_processing import scan_image_files
from core.tagging import setup_tags_file


# Global state to store application context
app_state: Dict[str, Any] = {
    "config": None,
    "session_manager": None,
    "paths": None,
    "connection_manager": None,
    "image_files": None,
    "shutdown_event": None
}


def setup_signal_handlers(app_state: Dict[str, Any]) -> None:
    """
    Set up signal handlers for graceful shutdown.

    Args:
        app_state: Global application state
    """
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
                app_state["connection_manager"].broadcast(json.dumps(shutdown_message))
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


def init_app() -> FastAPI:
    """
    Initialize the FastAPI application.

    Returns:
        FastAPI: The initialized application
    """
    app = FastAPI(
        title="CivitAI Flux Dev LoRA Tagging Assistant",
        description="Web-based image tagging for CivitAI Flux Dev LoRA model training",
        version="1.0.0"
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )

    # Include routers
    app.include_router(images.router)
    app.include_router(tags.router)
    app.include_router(websocket.router)

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

    # Provide access to app_state throughout the application
    @app.middleware("http")
    async def add_app_state(request: Request, call_next):
        request.state.app_state = app_state
        response = await call_next(request)
        return response

    return app


async def startup_event(app: FastAPI) -> None:
    """
    Initialize application state on startup.

    Args:
        app: FastAPI application instance
    """
    config = app_state["config"]

    # Set up paths
    paths = get_default_paths(config)
    app_state["paths"] = paths

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


async def shutdown_event(app: FastAPI) -> None:
    """
    Clean up resources during shutdown.

    Args:
        app: FastAPI application instance
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

    # Create FastAPI application
    app = init_app()

    # Setup signal handlers
    setup_signal_handlers(app_state)

    # Add startup and shutdown event handlers
    app.add_event_handler("startup", lambda: startup_event(app))
    app.add_event_handler("shutdown", lambda: shutdown_event(app))

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
