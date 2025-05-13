#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Status API router

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends

from models.api import SessionStatus

# Create router
router = APIRouter(
    prefix="/api/status",
    tags=["status"],
)


def get_app_state():
    """Dependency to get application state."""
    from server.main import app_state
    return app_state


@router.get("/", response_model=SessionStatus)
async def get_status(state: Dict[str, Any] = Depends(get_app_state)):
    """
    Get application status.

    Returns:
        SessionStatus: Current application status
    """
    try:
        session_manager = state["session_manager"]

        return SessionStatus(
            status="active",
            total_images=session_manager.state.stats.get("total_images", 0),
            processed_images=session_manager.state.stats.get("processed_images", 0),
            current_position=session_manager.state.current_position,
            last_updated=session_manager.state.last_updated
        )
    except Exception as e:
        logging.error(f"Error getting application status: {e}")
        return SessionStatus(
            status="error",
            total_images=0,
            processed_images=0,
            current_position=None,
            last_updated=""
        )
