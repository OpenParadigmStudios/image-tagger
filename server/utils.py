#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Server utility functions for reuse across routers

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from fastapi import HTTPException

from core.image_processing import validate_image_with_pillow, process_image


def get_image_by_id(image_id: str, app_state: Dict[str, Any]) -> Tuple[Path, int]:
    """
    Get image path by ID from app_state.

    Args:
        image_id: Image ID (index in the list)
        app_state: Application state dictionary

    Returns:
        Tuple[Path, int]: Tuple containing image path and image index

    Raises:
        HTTPException: If image ID is invalid or image not found
    """
    image_files = app_state["image_files"]

    try:
        img_index = int(image_id)
        if img_index < 0 or img_index >= len(image_files):
            raise HTTPException(status_code=404, detail="Image not found")

        img_path = image_files[img_index]
        if not img_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found")

        return img_path, img_index
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image ID")


def ensure_image_processed(
    image_path: Path,
    app_state: Dict[str, Any]
) -> Tuple[Path, Path]:
    """
    Ensure an image is processed, processing it if needed.

    Args:
        image_path: Path to the image
        app_state: Application state dictionary

    Returns:
        Tuple[Path, Path]: Tuple containing processed image path and text file path

    Raises:
        HTTPException: If image processing fails
    """
    session_manager = app_state["session_manager"]
    output_dir = app_state["output_dir"]
    config = app_state["config"]

    # Check if image has already been processed
    if str(image_path) in session_manager.state.processed_images:
        relative_path = session_manager.state.processed_images.get(str(image_path))
        processed_path = config.input_directory / relative_path
        txt_path = processed_path.with_suffix(".txt")

        return processed_path, txt_path

    # Process the image
    try:
        updated_dict, output_image_path, txt_file_path = process_image(
            image_path,
            output_dir,
            config.prefix,
            session_manager.state.processed_images
        )

        # Update session state with newly processed image
        for orig_path, new_path in updated_dict.items():
            session_manager.update_processed_image(orig_path, new_path)

        # Save session state
        session_manager.save()

        # Update stats and broadcast to clients
        new_stats = {
            "total_images": len(app_state["image_files"]),
            "processed_images": len(session_manager.state.processed_images)
        }
        session_manager.update_stats(**new_stats)

        # Broadcast update if connection manager exists
        if app_state["connection_manager"]:
            app_state["connection_manager"].broadcast_json({
                "type": "stats_update",
                "data": new_stats
            })

        return output_image_path, txt_file_path
    except Exception as e:
        logging.error(f"Failed to process image {image_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")


def validate_and_load_tags(
    tags_file_path: Path,
    create_if_missing: bool = True
) -> List[str]:
    """
    Validate and load tags from a tags file.

    Args:
        tags_file_path: Path to tags file
        create_if_missing: Whether to create the file if it doesn't exist

    Returns:
        List[str]: List of tags

    Raises:
        HTTPException: If tags file cannot be loaded
    """
    try:
        if not tags_file_path.exists():
            if create_if_missing:
                tags_file_path.parent.mkdir(parents=True, exist_ok=True)
                tags_file_path.touch()
                return []
            else:
                raise HTTPException(status_code=404, detail="Tags file not found")

        # Load tags from file
        tags = [line.strip() for line in tags_file_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        return tags
    except Exception as e:
        logging.error(f"Failed to load tags from {tags_file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load tags: {str(e)}")
