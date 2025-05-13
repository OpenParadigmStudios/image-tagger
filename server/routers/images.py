#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Image handling router

import logging
from pathlib import Path
from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse

from models.api import ImageInfo, ImageList, ImageTags
from core.filesystem import validate_image_with_pillow

# Create router
router = APIRouter(
    prefix="/api/images",
    tags=["images"],
    responses={404: {"description": "Not found"}},
)


def get_app_state():
    """Dependency to get application state."""
    from server.main import app
    return app.state.app_state


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
    image_files = state["image_files"]

    try:
        img_index = int(image_id)
        if img_index < 0 or img_index >= len(image_files):
            raise HTTPException(status_code=404, detail="Image not found")

        img_path = image_files[img_index]
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
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID")


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
    image_files = state["image_files"]

    try:
        img_index = int(image_id)
        if img_index < 0 or img_index >= len(image_files):
            raise HTTPException(status_code=404, detail="Image not found")

        img_path = image_files[img_index]

        # Check if it's been processed (should serve from output dir)
        if str(img_path) in state["session_state"].processed_images:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            if relative_path:
                processed_path = state["config"].input_directory / relative_path
                if processed_path.exists():
                    return FileResponse(processed_path)

        # Otherwise serve original
        if img_path.exists() and validate_image_with_pillow(img_path):
            return FileResponse(img_path)
        else:
            raise HTTPException(status_code=404, detail="Image file not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID")


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
    image_files = state["image_files"]

    try:
        img_index = int(image_id)
        if img_index < 0 or img_index >= len(image_files):
            raise HTTPException(status_code=404, detail="Image not found")

        img_path = image_files[img_index]

        # Check if it's been processed
        if str(img_path) in state["session_state"].processed_images:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            if relative_path:
                processed_path = state["config"].input_directory / relative_path
                txt_path = processed_path.with_suffix(".txt")

                if txt_path.exists():
                    tags = [line.strip() for line in txt_path.read_text(encoding='utf-8').splitlines() if line.strip()]
                    return ImageTags(image_id=image_id, tags=tags)

        # No tags yet
        return ImageTags(image_id=image_id, tags=[])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID")


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
        tags_data: Tags data
        state: Application state

    Returns:
        ImageTags: Updated image tags
    """
    if image_id != tags_data.image_id:
        raise HTTPException(status_code=400, detail="Image ID mismatch")

    image_files = state["image_files"]

    try:
        img_index = int(image_id)
        if img_index < 0 or img_index >= len(image_files):
            raise HTTPException(status_code=404, detail="Image not found")

        img_path = image_files[img_index]

        # Process the image if not already processed
        from core.filesystem import process_image

        if str(img_path) not in state["session_state"].processed_images:
            state["session_state"].processed_images, new_img_path, txt_file_path = process_image(
                img_path,
                state["output_dir"],
                state["config"].prefix,
                state["session_state"].processed_images
            )
        else:
            relative_path = state["session_state"].processed_images.get(str(img_path))
            new_img_path = state["config"].input_directory / relative_path
            txt_file_path = new_img_path.with_suffix(".txt")

        # Write tags to text file
        txt_file_path.write_text("\n".join(tags_data.tags), encoding='utf-8')

        # Update master tags list with any new tags
        update_master_tags_list(tags_data.tags, state["tags_file_path"])

        # Save session state
        from core.filesystem import save_session_state
        state["session_state"].current_position = image_id
        save_session_state(state["session_file_path"], state["session_state"])

        return tags_data
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID")
    except Exception as e:
        logging.error(f"Error updating tags: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def update_master_tags_list(new_tags: List[str], tags_file_path: Path) -> None:
    """
    Update the master tags list with new tags.

    Args:
        new_tags: List of new tags
        tags_file_path: Path to the tags file
    """
    try:
        # Read existing tags
        if tags_file_path.exists():
            existing_tags = [line.strip() for line in tags_file_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        else:
            existing_tags = []

        # Merge and deduplicate tags
        all_tags = sorted(set(existing_tags + new_tags))

        # Write updated tags
        tags_file_path.write_text("\n".join(all_tags), encoding='utf-8')

        logging.info(f"Updated master tags list: {len(all_tags)} total tags")
    except Exception as e:
        logging.error(f"Error updating master tags list: {e}")
        raise
