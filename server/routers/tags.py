#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Tags handling router

import logging
from pathlib import Path
from typing import List, Dict, Set

from fastapi import APIRouter, Depends, HTTPException

from models.api import Tag, TagList, ImageTags, WebSocketMessage
from core.filesystem import (
    load_tags,
    save_tags,
    add_tag,
    remove_tag,
    get_image_tags,
    save_image_tags,
    normalize_tag
)

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
        tags = load_tags(tags_file_path)
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
    connection_manager = state["connection_manager"]

    try:
        # Load existing tags
        existing_tags = load_tags(tags_file_path)

        # Add new tag if it doesn't exist
        normalized_tag = normalize_tag(tag_data.name)
        updated_tags = add_tag(existing_tags, normalized_tag)

        # Save tags if changed
        if len(updated_tags) > len(existing_tags):
            save_tags(tags_file_path, updated_tags)

            # Update session state
            state["session_state"].tags = sorted(updated_tags)

            # Broadcast tag update to connected clients
            await connection_manager.broadcast({
                "type": "tag_update",
                "data": {"action": "add", "tag": normalized_tag, "tags": sorted(updated_tags)}
            })

            logging.info(f"Added new tag: {normalized_tag}")

        return TagList(tags=sorted(updated_tags))
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
    connection_manager = state["connection_manager"]

    try:
        # Load existing tags
        existing_tags = load_tags(tags_file_path)

        # Get tag count before removal
        before_count = len(existing_tags)

        # Remove tag if it exists
        updated_tags = remove_tag(existing_tags, tag_name)

        # Save tags if changed
        if len(updated_tags) < before_count:
            save_tags(tags_file_path, updated_tags)

            # Update session state
            state["session_state"].tags = sorted(updated_tags)

            # Broadcast tag update to connected clients
            await connection_manager.broadcast({
                "type": "tag_update",
                "data": {"action": "delete", "tag": tag_name, "tags": sorted(updated_tags)}
            })

            logging.info(f"Deleted tag: {tag_name}")

        return TagList(tags=sorted(updated_tags))
    except Exception as e:
        logging.error(f"Error deleting tag: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{image_id}", response_model=ImageTags)
async def get_image_tags_endpoint(
    image_id: str,
    state: Dict = Depends(get_app_state)
):
    """
    Get tags associated with a specific image.

    Args:
        image_id: Image ID
        state: Application state

    Returns:
        ImageTags: Object containing image ID and its tags
    """
    try:
        image_files = state["image_files"]
        img_index = int(image_id)

        if img_index < 0 or img_index >= len(image_files):
            raise ValueError(f"Invalid image index: {img_index}")

        img_path = image_files[img_index]

        # Check if this image has been processed
        processed = str(img_path) in state["session_state"].processed_images
        tags = []

        if processed:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            if relative_path:
                processed_path = state["output_dir"] / Path(relative_path).name
                txt_path = processed_path.with_suffix(".txt")
                tags = get_image_tags(txt_path)

        return ImageTags(image_id=image_id, tags=tags)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid image ID: {image_id}")
    except Exception as e:
        logging.error(f"Error retrieving image tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/images/{image_id}", response_model=ImageTags)
async def update_image_tags(
    image_id: str,
    tag_data: TagList,
    state: Dict = Depends(get_app_state)
):
    """
    Update tags for a specific image.

    Args:
        image_id: Image ID
        tag_data: New tags for the image
        state: Application state

    Returns:
        ImageTags: Updated image tags object
    """
    try:
        image_files = state["image_files"]
        connection_manager = state["connection_manager"]
        img_index = int(image_id)

        if img_index < 0 or img_index >= len(image_files):
            raise ValueError(f"Invalid image index: {img_index}")

        img_path = image_files[img_index]
        output_dir = state["output_dir"]

        # Check if the image has been processed
        processed = str(img_path) in state["session_state"].processed_images

        if not processed:
            raise HTTPException(status_code=400, detail=f"Image {image_id} has not been processed yet")

        relative_path = state["session_state"].processed_images.get(str(img_path))
        if not relative_path:
            raise HTTPException(status_code=400, detail=f"Cannot find processed path for image {image_id}")

        processed_path = output_dir / Path(relative_path).name
        txt_path = processed_path.with_suffix(".txt")

        # Normalize tags
        normalized_tags = [normalize_tag(tag) for tag in tag_data.tags if normalize_tag(tag)]

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

            # Broadcast image tags update
            await connection_manager.broadcast({
                "type": "image_tags_update",
                "data": {"image_id": image_id, "tags": normalized_tags}
            })

            logging.info(f"Updated tags for image {image_id}: {len(normalized_tags)} tags")

            return ImageTags(image_id=image_id, tags=normalized_tags)
        else:
            raise HTTPException(status_code=500, detail=f"Failed to save tags for image {image_id}")

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid image ID: {image_id}")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating image tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))
