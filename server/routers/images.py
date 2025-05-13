#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Image handling router

import logging
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse

from models.api import ImageInfo, ImageList, ImageTags
from core.image_processing import validate_image_with_pillow
from server.utils import get_image_by_id, ensure_image_processed, validate_and_load_tags

# Create router
router = APIRouter(
    prefix="/api/images",
    tags=["images"],
    responses={404: {"description": "Not found"}},
)


def get_app_state():
    """Dependency to get application state."""
    from server.main import app_state
    return app_state


@router.get("/", response_model=ImageList)
async def list_images(
    state: Dict = Depends(get_app_state),
    limit: int = 100,
    offset: int = 0
):
    """
    List all images in the input directory.

    Args:
        state: Application state
        limit: Maximum number of images to return
        offset: Number of images to skip

    Returns:
        ImageList: List of images with pagination info
    """
    image_files = state["image_files"]
    total = len(image_files)

    # Apply pagination
    paginated_images = image_files[offset:offset + limit]

    # Prepare response
    images = []
    for i, img_path in enumerate(paginated_images):
        img_id = str(offset + i)
        original_name = img_path.name
        processed = str(img_path) in state["session_state"].processed_images

        # Get new name if processed
        new_name = None
        if processed:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            if relative_path:
                new_name = Path(relative_path).name

        images.append(
            ImageInfo(
                id=img_id,
                original_name=original_name,
                new_name=new_name,
                path=str(img_path),
                processed=processed
            )
        )

    return ImageList(images=images, total=total)


@router.get("/{image_id}", response_model=ImageInfo)
async def get_image_info(
    image_id: str,
    state: Dict = Depends(get_app_state)
):
    """
    Get information about a specific image.

    Args:
        image_id: Image ID (index in the list)
        state: Application state

    Returns:
        ImageInfo: Image information
    """
    try:
        img_path, img_index = get_image_by_id(image_id, state)
        original_name = img_path.name
        processed = str(img_path) in state["session_state"].processed_images

        # Get new name if processed
        new_name = None
        if processed:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            if relative_path:
                new_name = Path(relative_path).name

        return ImageInfo(
            id=image_id,
            original_name=original_name,
            new_name=new_name,
            path=str(img_path),
            processed=processed
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting image info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting image info: {str(e)}")


@router.get("/{image_id}/file")
async def get_image_file(
    image_id: str,
    state: Dict = Depends(get_app_state)
):
    """
    Get the image file.

    Args:
        image_id: Image ID (index in the list)
        state: Application state

    Returns:
        FileResponse: Image file
    """
    try:
        img_path, _ = get_image_by_id(image_id, state)

        # Determine correct serving path
        serving_path = None

        # Check if it's been processed (should serve from output dir)
        if str(img_path) in state["session_state"].processed_images:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            if relative_path:
                processed_path = state["config"].input_directory / relative_path
                if processed_path.exists():
                    serving_path = processed_path

        # If not found in processed images, serve the original
        if serving_path is None:
            if img_path.exists() and validate_image_with_pillow(img_path):
                serving_path = img_path
            else:
                raise HTTPException(status_code=404, detail="Image file not found")

        # Ensure image can be loaded
        if not validate_image_with_pillow(serving_path):
            logging.error(f"Invalid image file: {serving_path}")
            raise HTTPException(status_code=415, detail="Invalid image file")

        # Get content type based on extension
        content_type = None
        suffix = serving_path.suffix.lower()
        if suffix in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif suffix == '.png':
            content_type = 'image/png'
        elif suffix == '.gif':
            content_type = 'image/gif'
        elif suffix == '.webp':
            content_type = 'image/webp'
        elif suffix in ['.tif', '.tiff']:
            content_type = 'image/tiff'
        elif suffix == '.bmp':
            content_type = 'image/bmp'

        # Log the image being served
        logging.debug(f"Serving image {serving_path} with content type {content_type}")

        # Return file response with appropriate headers
        return FileResponse(
            path=serving_path,
            media_type=content_type,
            filename=serving_path.name
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error serving image file: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving image file: {str(e)}")


@router.get("/{image_id}/tags", response_model=ImageTags)
async def get_image_tags(
    image_id: str,
    state: Dict = Depends(get_app_state)
):
    """
    Get tags for a specific image.

    Args:
        image_id: Image ID
        state: Application state

    Returns:
        ImageTags: Image tags information
    """
    try:
        img_path, _ = get_image_by_id(image_id, state)

        # Check if it's been processed
        if str(img_path) in state["session_state"].processed_images:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            if relative_path:
                processed_path = state["config"].input_directory / relative_path
                txt_path = processed_path.with_suffix(".txt")

                if txt_path.exists():
                    tags = validate_and_load_tags(txt_path, create_if_missing=False)
                    return ImageTags(image_id=image_id, tags=tags)

        # No tags yet
        return ImageTags(image_id=image_id, tags=[])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting image tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting image tags: {str(e)}")


@router.put("/{image_id}/tags", response_model=ImageTags)
async def update_image_tags(
    image_id: str,
    tags_data: ImageTags,
    state: Dict = Depends(get_app_state)
):
    """
    Update tags for a specific image.

    Args:
        image_id: Image ID
        tags_data: Image tags data
        state: Application state

    Returns:
        ImageTags: Updated image tags information
    """
    try:
        img_path, _ = get_image_by_id(image_id, state)

        # Process the image if not already processed
        processed_path, txt_path = ensure_image_processed(img_path, state)

        # Update tags in text file
        with txt_path.open('w', encoding='utf-8') as f:
            f.write('\n'.join(tags_data.tags))

        # Update master tags list
        update_master_tags_list(tags_data.tags, state["tags_file_path"])

        # Broadcast update to connected clients
        if state["connection_manager"]:
            state["connection_manager"].broadcast_json({
                "type": "tags_updated",
                "data": {
                    "image_id": image_id,
                    "tags": tags_data.tags
                }
            })

        return ImageTags(image_id=image_id, tags=tags_data.tags)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating image tags: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating image tags: {str(e)}")


def update_master_tags_list(new_tags: List[str], tags_file_path: Path) -> None:
    """
    Update the master tags list with new tags.

    Args:
        new_tags: List of new tags
        tags_file_path: Path to the tags file
    """
    try:
        # Load existing tags
        existing_tags = validate_and_load_tags(tags_file_path)

        # Add new tags that don't exist yet
        updated = False
        for tag in new_tags:
            if tag and tag not in existing_tags:
                existing_tags.append(tag)
                updated = True

        # Only write if there were changes
        if updated:
            with tags_file_path.open('w', encoding='utf-8') as f:
                f.write('\n'.join(existing_tags))
            logging.debug(f"Updated master tags list with {len(new_tags)} tags")
    except Exception as e:
        logging.error(f"Error updating master tags list: {e}")
        # Don't raise - non-critical operation
