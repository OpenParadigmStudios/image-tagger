#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Router package initialization

from server.routers import images
from server.routers import tags
from server.routers import websocket
from server.routers import status

# Export router instances for easy access
from server.routers.websocket import connection_manager

"""API routers for the FastAPI application."""
