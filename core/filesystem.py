#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# File system operations

import json
import logging
import shutil
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Set, Any, Optional

# List of supported image extensions
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}


@dataclass
class SessionState:
    """Store session state information."""
    processed_images: Dict[str, str] = field(default_factory=dict)
    current_position: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    version: str = "1.0"
    stats: Dict[str, int] = field(default_factory=lambda: {"total_images": 0, "processed_images": 0})


def validate_directory(path: Path) -> bool:
    """
    Verify that the directory exists and is a directory.

    Args:
        path: Path to validate

    Returns:
        bool: True if path exists and is a directory
    """
    if not path.exists():
        logging.error(f"Directory does not exist: {path}")
        return False

    if not path.is_dir():
        logging.error(f"Path exists but is not a directory: {path}")
        return False

    # Basic check if directory contains anything
    if not any(path.iterdir()):
        logging.warning(f"Directory appears to be empty: {path}")

    return True


def setup_output_directory(input_dir: Path, output_name: str) -> Path:
    """
    Create the output directory if it doesn't exist.

    Args:
        input_dir: The input directory path
        output_name: Name of the output directory

    Returns:
        Path: Path to the output directory
    """
    output_dir = input_dir / output_name
    try:
        output_dir.mkdir(exist_ok=True)
        logging.info(f"Output directory ready: {output_dir}")
        return output_dir
    except PermissionError:
        logging.error(f"Permission denied when creating output directory: {output_dir}")
        raise
    except Exception as e:
        logging.error(f"Error creating output directory: {e}")
        raise


def validate_image_with_pillow(file_path: Path) -> bool:
    """
    Check if a file is a valid image using Pillow.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if the file is a valid image
    """
    # Fast check - extension
    if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        return False

    # Thorough check - file content
    try:
        from PIL import Image
        img = Image.open(file_path)
        img.verify()  # Verify it's an image
        return True
    except Exception as e:
        logging.debug(f"Error validating image {file_path}: {e}")
        return False


def scan_image_files(input_dir: Path) -> List[Path]:
    """
    Scan the input directory for valid image files.

    Args:
        input_dir: Directory path to scan

    Returns:
        List[Path]: List of valid image file paths
    """
    logging.info(f"Scanning for images in {input_dir}")
    image_files = []
    skipped_files = 0

    for file_path in input_dir.iterdir():
        if file_path.is_file() and validate_image_with_pillow(file_path):
            image_files.append(file_path)
        elif file_path.is_file():
            skipped_files += 1

    logging.info(f"Found {len(image_files)} valid image files")
    if skipped_files > 0:
        logging.info(f"Skipped {skipped_files} non-image files")

    if not image_files:
        logging.warning("No valid image files found in directory")

    return sorted(image_files)


def create_backup(file_path: Path) -> bool:
    """
    Create a backup of a file before modification.

    Args:
        file_path: Path to the file to back up

    Returns:
        bool: True if backup was successful
    """
    if not file_path.exists():
        return False

    backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
    try:
        shutil.copy2(file_path, backup_path)
        logging.debug(f"Created backup of {file_path} at {backup_path}")
        return True
    except Exception as e:
        logging.warning(f"Failed to create backup of {file_path}: {e}")
        return False


def setup_tags_file(tags_file_path: Path) -> List[str]:
    """
    Initialize or load the tags file.

    Args:
        tags_file_path: Path to the tags file

    Returns:
        List[str]: List of existing tags
    """
    if not tags_file_path.exists():
        tags_file_path.touch()
        logging.info(f"Created new tags file: {tags_file_path}")
        return []

    try:
        tags = [line.strip() for line in tags_file_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        unique_tags = sorted(set(tags))

        # If there were duplicates, rewrite the file with unique tags
        if len(tags) != len(unique_tags):
            tags_file_path.write_text('\n'.join(unique_tags), encoding='utf-8')
            logging.info(f"Removed {len(tags) - len(unique_tags)} duplicate tags from {tags_file_path}")

        logging.info(f"Loaded {len(unique_tags)} tags from {tags_file_path}")
        return unique_tags

    except Exception as e:
        logging.error(f"Error reading tags file {tags_file_path}: {e}")
        return []


def normalize_tag(tag: str) -> str:
    """
    Normalize a tag to ensure consistent formatting.

    Args:
        tag: Raw tag string

    Returns:
        str: Normalized tag string
    """
    # Strip whitespace and convert to lowercase
    normalized = tag.strip()

    # Remove any invalid characters - keep only alphanumeric, underscore, and hyphen
    # This can be customized based on specific tag format requirements

    # Return non-empty normalized tag
    return normalized if normalized else ""


def load_tags(tags_file_path: Path) -> List[str]:
    """
    Load the existing tags from the tags file.

    Args:
        tags_file_path: Path to the tags file

    Returns:
        List[str]: List of existing tags
    """
    if not tags_file_path.exists():
        return []

    try:
        return [line.strip() for line in tags_file_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    except Exception as e:
        logging.error(f"Error loading tags from {tags_file_path}: {e}")
        return []


def save_tags(tags_file_path: Path, tags_list: List[str]) -> bool:
    """
    Save the current tags list to the tags file.

    Args:
        tags_file_path: Path to the tags file
        tags_list: List of tags to save

    Returns:
        bool: True if successful
    """
    try:
        # Sort tags alphabetically for consistency
        sorted_tags = sorted(set(tags_list))

        # Create backup before writing
        create_backup(tags_file_path)

        # Write tags to file
        tags_file_path.write_text('\n'.join(sorted_tags), encoding='utf-8')
        logging.info(f"Saved {len(sorted_tags)} tags to {tags_file_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving tags to {tags_file_path}: {e}")
        return False


def add_tag(tags_list: List[str], new_tag: str) -> List[str]:
    """
    Add a new tag to the tags list if it doesn't exist.

    Args:
        tags_list: Current list of tags
        new_tag: New tag to add

    Returns:
        List[str]: Updated list of tags
    """
    # Normalize the tag
    normalized_tag = normalize_tag(new_tag)

    if not normalized_tag:
        return tags_list

    # Check if tag already exists (case-insensitive)
    if normalized_tag not in {tag.lower() for tag in tags_list}:
        tags_list.append(normalized_tag)

    return tags_list


def remove_tag(tags_list: List[str], tag_to_remove: str) -> List[str]:
    """
    Remove a tag from the tags list.

    Args:
        tags_list: Current list of tags
        tag_to_remove: Tag to remove

    Returns:
        List[str]: Updated list of tags
    """
    # First try exact match
    if tag_to_remove in tags_list:
        tags_list.remove(tag_to_remove)
        return tags_list

    # If not found, try case-insensitive
    tag_lower = tag_to_remove.lower()
    for tag in list(tags_list):  # Create a copy to avoid modification during iteration
        if tag.lower() == tag_lower:
            tags_list.remove(tag)

    return tags_list


def get_image_tags(text_file_path: Path) -> List[str]:
    """
    Get the tags associated with a specific image.

    Args:
        text_file_path: Path to the text file for the image

    Returns:
        List[str]: List of tags for the image
    """
    if not text_file_path.exists():
        return []

    try:
        content = text_file_path.read_text(encoding='utf-8').strip()

        # Handle both comma-separated and newline-separated formats
        if ',' in content:
            tags = [tag.strip() for tag in content.split(',') if tag.strip()]
        else:
            tags = [line.strip() for line in content.splitlines() if line.strip()]

        return tags
    except Exception as e:
        logging.error(f"Error reading tags from {text_file_path}: {e}")
        return []


def save_image_tags(text_file_path: Path, tags_list: List[str]) -> bool:
    """
    Save tags for a specific image to its text file.

    Args:
        text_file_path: Path to the text file
        tags_list: List of tags to save

    Returns:
        bool: True if successful
    """
    try:
        # Create parent directory if it doesn't exist
        text_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists
        if text_file_path.exists():
            create_backup(text_file_path)

        # Join tags as comma-separated list
        content = ", ".join(tags_list)

        # Write to file
        text_file_path.write_text(content, encoding='utf-8')
        logging.info(f"Saved {len(tags_list)} tags to {text_file_path}")
        return True
    except Exception as e:
        logging.error(f"Error saving tags to {text_file_path}: {e}")
        return False


def get_processed_images(session_file_path: Path) -> SessionState:
    """
    Retrieve session state from session file.

    Args:
        session_file_path: Path to session state file

    Returns:
        SessionState: Session state object
    """
    if not session_file_path.exists():
        logging.info(f"No session file found at {session_file_path}")
        return SessionState()

    try:
        session_data = json.loads(session_file_path.read_text(encoding='utf-8'))

        # Create SessionState object from JSON data
        state = SessionState(
            processed_images=session_data.get('processed_images', {}),
            current_position=session_data.get('current_position'),
            tags=session_data.get('tags', []),
            last_updated=session_data.get('last_updated', time.strftime("%Y-%m-%dT%H:%M:%S")),
            version=session_data.get('version', "1.0"),
            stats=session_data.get('stats', {"total_images": 0, "processed_images": 0})
        )

        logging.info(f"Loaded session state: {len(state.processed_images)} processed images, "
                   f"{len(state.tags)} tags")

        return state

    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in session file {session_file_path}: {e}")
        # Create backup of corrupted file
        create_backup(session_file_path)
        return SessionState()

    except Exception as e:
        logging.error(f"Error reading session file {session_file_path}: {e}")
        return SessionState()


def save_session_state(session_file_path: Path, session_state: SessionState) -> bool:
    """
    Save current processing state for later resumption.

    Args:
        session_file_path: Path to session state file
        session_state: Session state object

    Returns:
        bool: True if save was successful
    """
    # Update timestamp
    session_state.last_updated = time.strftime("%Y-%m-%dT%H:%M:%S")

    # Convert to dictionary for JSON serialization
    session_data = asdict(session_state)

    # Create temporary file for atomic write
    temp_file = session_file_path.with_suffix('.tmp')

    try:
        # Backup existing file if it exists
        if session_file_path.exists():
            create_backup(session_file_path)

        # Write to temporary file
        temp_file.write_text(json.dumps(session_data, indent=2), encoding='utf-8')

        # Rename temporary file to target file (atomic operation)
        temp_file.replace(session_file_path)

        logging.debug(f"Session state saved to {session_file_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to save session state to {session_file_path}: {e}")
        if temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass
        return False


def setup_directories(config) -> bool:
    """
    Set up and validate all required directories.

    Args:
        config: Application configuration

    Returns:
        bool: True if all directories are valid and ready
    """
    # Validate input directory
    if not validate_directory(config.input_directory):
        return False

    # Setup output directory
    try:
        setup_output_directory(config.input_directory, config.output_dir)
        return True
    except Exception as e:
        logging.error(f"Failed to set up directories: {e}")
        return False
