#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Tags handling router

import logging
from pathlib import Path
from typing import List, Dict, Set

from fastapi import APIRouter, Depends, HTTPException

from models.api import Tag, TagList

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


@router.get("/", response_model=TagList)
async def get_all_tags(state: Dict = Depends(get_app_state)):
    """
    Get all tags from the master tags list.

    Args:
        state: Application state

    Returns:
        TagList: List of all tags
    """
    tags_file_path = state["tags_file_path"]

    try:
        if tags_file_path.exists():
            tags = [line.strip() for line in tags_file_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        else:
            tags = []

        return TagList(tags=sorted(tags))
    except Exception as e:
        logging.error(f"Error reading tags file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=TagList)
async def add_new_tag(
    tag_data: Tag,
    state: Dict = Depends(get_app_state)
):
    """
    Add a new tag to the master tags list.

    Args:
        tag_data: Tag to add
        state: Application state

    Returns:
        TagList: Updated list of all tags
    """
    if not tag_data.name or tag_data.name.isspace():
        raise HTTPException(status_code=400, detail="Tag name cannot be empty")

    tags_file_path = state["tags_file_path"]

    try:
        # Load existing tags
        if tags_file_path.exists():
            existing_tags = [line.strip() for line in tags_file_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        else:
            existing_tags = []

        # Add new tag if it doesn't exist
        if tag_data.name not in existing_tags:
            existing_tags.append(tag_data.name)

            # Sort and write back
            sorted_tags = sorted(existing_tags)
            tags_file_path.write_text("\n".join(sorted_tags), encoding='utf-8')

            # Update session state
            state["session_state"].tags = sorted_tags

            logging.info(f"Added new tag: {tag_data.name}")

        return TagList(tags=sorted(existing_tags))
    except Exception as e:
        logging.error(f"Error adding new tag: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tag_name}", response_model=TagList)
async def delete_tag(
    tag_name: str,
    state: Dict = Depends(get_app_state)
):
    """
    Delete a tag from the master tags list.

    Args:
        tag_name: Tag to delete
        state: Application state

    Returns:
        TagList: Updated list of all tags
    """
    tags_file_path = state["tags_file_path"]

    try:
        # Load existing tags
        if tags_file_path.exists():
            existing_tags = [line.strip() for line in tags_file_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        else:
            existing_tags = []

        # Remove tag if it exists
        if tag_name in existing_tags:
            existing_tags.remove(tag_name)

            # Write back
            tags_file_path.write_text("\n".join(sorted(existing_tags)), encoding='utf-8')

            # Update session state
            state["session_state"].tags = sorted(existing_tags)

            logging.info(f"Deleted tag: {tag_name}")

        return TagList(tags=sorted(existing_tags))
    except Exception as e:
        logging.error(f"Error deleting tag: {e}")
        raise HTTPException(status_code=500, detail=str(e))
