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
