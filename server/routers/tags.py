#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Tags management router

import logging
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from models.api import TagsList, TagsUpdate
from server.utils import validate_and_load_tags

# Create router
router = APIRouter(
    prefix="/api/tags",
    tags=["tags"],
    responses={404: {"description": "Not found"}},
)


def get_app_state():
    """Dependency to get application state."""
    from server.main import app
    return app.state.app_state


@router.get("/", response_model=TagsList)
async def list_tags(
    state: Dict = Depends(get_app_state),
    search: Optional[str] = None
):
    """
    List all tags in the master tag list.

    Args:
        state: Application state
        search: Optional search term for filtering tags

    Returns:
        TagsList: List of tags
    """
    try:
        tags_file_path = state["tags_file_path"]
        tags = await run_in_threadpool(validate_and_load_tags, tags_file_path)

        # Filter tags if search is provided
        if search:
            search_lower = search.lower()
            tags = [tag for tag in tags if search_lower in tag.lower()]

        return TagsList(tags=tags)
    except Exception as e:
        logging.error(f"Error listing tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing tags: {str(e)}")


@router.post("/", response_model=TagsList)
async def add_tags(
    tags_update: TagsUpdate,
    state: Dict = Depends(get_app_state)
):
    """
    Add new tags to the master tag list.

    Args:
        tags_update: Tags to add
        state: Application state

    Returns:
        TagsList: Updated list of tags
    """
    try:
        tags_file_path = state["tags_file_path"]

        # Load existing tags
        existing_tags = await run_in_threadpool(validate_and_load_tags, tags_file_path)

        # Add new tags
        updated = False
        for tag in tags_update.tags:
            if tag and tag not in existing_tags:
                existing_tags.append(tag)
                updated = True

        # Save if there were changes
        if updated:
            async def write_tags():
                with tags_file_path.open('w', encoding='utf-8') as f:
                    f.write('\n'.join(existing_tags))

            await run_in_threadpool(write_tags)

            # Broadcast update to clients
            if state["connection_manager"]:
                state["connection_manager"].broadcast_json({
                    "type": "tags_updated",
                    "data": {"tags": existing_tags}
                })

        return TagsList(tags=existing_tags)
    except Exception as e:
        logging.error(f"Error adding tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding tags: {str(e)}")


@router.delete("/", response_model=TagsList)
async def delete_tags(
    tags_update: TagsUpdate,
    state: Dict = Depends(get_app_state)
):
    """
    Delete tags from the master tag list.

    Args:
        tags_update: Tags to delete
        state: Application state

    Returns:
        TagsList: Updated list of tags
    """
    try:
        tags_file_path = state["tags_file_path"]

        # Load existing tags
        existing_tags = await run_in_threadpool(validate_and_load_tags, tags_file_path)

        # Remove tags
        updated = False
        for tag in tags_update.tags:
            if tag in existing_tags:
                existing_tags.remove(tag)
                updated = True

        # Save if there were changes
        if updated:
            async def write_tags():
                with tags_file_path.open('w', encoding='utf-8') as f:
                    f.write('\n'.join(existing_tags))

            await run_in_threadpool(write_tags)

            # Broadcast update to clients
            if state["connection_manager"]:
                state["connection_manager"].broadcast_json({
                    "type": "tags_updated",
                    "data": {"tags": existing_tags}
                })

        return TagsList(tags=existing_tags)
    except Exception as e:
        logging.error(f"Error deleting tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting tags: {str(e)}")


@router.put("/", response_model=TagsList)
async def replace_tags(
    tags_update: TagsUpdate,
    state: Dict = Depends(get_app_state)
):
    """
    Replace the entire master tag list.

    Args:
        tags_update: New list of tags
        state: Application state

    Returns:
        TagsList: Updated list of tags
    """
    try:
        tags_file_path = state["tags_file_path"]

        # Replace tags
        async def write_tags():
            with tags_file_path.open('w', encoding='utf-8') as f:
                f.write('\n'.join(tags_update.tags))

        await run_in_threadpool(write_tags)

        # Broadcast update to clients
        if state["connection_manager"]:
            state["connection_manager"].broadcast_json({
                "type": "tags_replaced",
                "data": {"tags": tags_update.tags}
            })

        return TagsList(tags=tags_update.tags)
    except Exception as e:
        logging.error(f"Error replacing tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error replacing tags: {str(e)}")


@router.get("/session", response_model=TagsList)
async def get_session_tags(
    state: Dict = Depends(get_app_state)
):
    """
    Get tags from the current session.

    Args:
        state: Application state

    Returns:
        TagsList: Session tags
    """
    try:
        session_manager = state["session_manager"]
        return TagsList(tags=session_manager.state.tags)
    except Exception as e:
        logging.error(f"Error getting session tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session tags: {str(e)}")


@router.post("/session", response_model=TagsList)
async def update_session_tags(
    tags_update: TagsUpdate,
    state: Dict = Depends(get_app_state)
):
    """
    Update tags in the current session.

    Args:
        tags_update: Tags to update
        state: Application state

    Returns:
        TagsList: Updated session tags
    """
    try:
        session_manager = state["session_manager"]

        # Update tags
        session_manager.update_tags(tags_update.tags)

        # Save session
        await run_in_threadpool(session_manager.save)

        # Broadcast update
        if state["connection_manager"]:
            state["connection_manager"].broadcast_json({
                "type": "session_tags_updated",
                "data": {"tags": tags_update.tags}
            })

        return TagsList(tags=session_manager.state.tags)
    except Exception as e:
        logging.error(f"Error updating session tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating session tags: {str(e)}")
