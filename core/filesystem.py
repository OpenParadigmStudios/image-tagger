#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# File system operations

"""
Core filesystem operations module for the CivitAI Flux Dev LoRA Tagging Assistant.

This module provides file system utility functions including:
- Directory validation and creation
- File backup and recovery
- Path validation and sanitization
- Safe file operations
- Default path management

The module focuses on safe operations with proper error handling to prevent data loss.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

# Import from specialized modules
from core.session import SessionState


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

    Raises:
        PermissionError: If the user doesn't have write permission
        Exception: For other errors during directory creation
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


def create_backup(file_path: Path, suffix: str = ".bak") -> Optional[Path]:
    """
    Create a backup of a file before modification.

    Args:
        file_path: Path to the file to back up
        suffix: Suffix to use for the backup file (default: .bak)

    Returns:
        Optional[Path]: Path to the backup file if successful, None otherwise
    """
    if not file_path.exists():
        return None

    backup_path = file_path.with_suffix(f"{file_path.suffix}{suffix}")
    try:
        shutil.copy2(file_path, backup_path)
        logging.debug(f"Created backup of {file_path} at {backup_path}")
        return backup_path
    except Exception as e:
        logging.warning(f"Failed to create backup of {file_path}: {e}")
        return None


def setup_directories(config) -> bool:
    """
    Setup and validate directories for the application.

    Args:
        config: Application configuration

    Returns:
        bool: True if setup was successful
    """
    # Validate input directory
    if not validate_directory(config.input_directory):
        return False

    # Setup output directory
    try:
        output_dir = setup_output_directory(config.input_directory, config.output_dir)

        # Create session and tags files if they don't exist
        session_file = output_dir / "session.json"
        tags_file = output_dir / "tags.txt"

        # Setup tags file
        from core.tagging import setup_tags_file
        setup_tags_file(tags_file)

        logging.info("Directory setup complete")
        return True
    except Exception as e:
        logging.error(f"Failed to setup directories: {e}")
        return False


def ensure_path_exists(path: Path, is_directory: bool = False) -> bool:
    """
    Ensure a path exists, creating it if necessary.

    Args:
        path: Path to ensure exists
        is_directory: Whether the path is a directory

    Returns:
        bool: True if the path exists or was created successfully
    """
    try:
        if is_directory:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.touch()
        return True
    except Exception as e:
        logging.error(f"Failed to ensure path exists ({path}): {e}")
        return False


def safe_delete(path: Path) -> bool:
    """
    Safely delete a file or directory with backup.

    Args:
        path: Path to delete

    Returns:
        bool: True if deletion was successful
    """
    if not path.exists():
        return True

    try:
        if path.is_file():
            # Create backup before deletion
            backup_path = create_backup(path)
            if backup_path:
                path.unlink()
        elif path.is_dir():
            # Backup directory by renaming it
            backup_path = path.with_suffix(f"{path.suffix}.bak")
            if backup_path.exists() and backup_path.is_dir():
                shutil.rmtree(backup_path)
            path.rename(backup_path)
            path.mkdir()
        return True
    except Exception as e:
        logging.error(f"Failed to safely delete {path}: {e}")
        return False


def get_default_paths(config) -> dict:
    """
    Get default paths for application files.

    Args:
        config: Application configuration

    Returns:
        dict: Dictionary of default paths containing output_dir, session_file, and tags_file
    """
    output_dir = config.input_directory / config.output_dir

    return {
        "output_dir": output_dir,
        "session_file": output_dir / "session.json",
        "tags_file": output_dir / "tags.txt",
    }


def sanitize_path(path_str: str, base_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Sanitize a path string to prevent path traversal attacks.

    Args:
        path_str: Path string to sanitize
        base_dir: Optional base directory to restrict paths to

    Returns:
        Optional[Path]: Sanitized path or None if invalid

    Raises:
        ValueError: If path_str is empty or None
        OSError: If there's an operating system error when resolving the path
    """
    if not path_str:
        raise ValueError("Path cannot be empty")

    # Check for null character, which causes issues in file operations
    if "\0" in path_str:
        raise ValueError("Path contains null character")

    try:
        # Convert to absolute path and normalize
        path = Path(path_str).absolute().resolve()

        # Check for path traversal
        if ".." in path_str:
            logging.warning(f"Path contains potential traversal: {path_str}")
            return None

        # If base_dir is provided, ensure the path is within it
        if base_dir is not None:
            base_dir = base_dir.absolute().resolve()
            if not str(path).startswith(str(base_dir)):
                logging.warning(f"Path is outside allowed directory: {path}")
                return None

        return path
    except OSError as e:
        logging.error(f"Invalid path: {path_str} - {e}")
        raise
    except Exception as e:
        logging.error(f"Error validating path: {path_str} - {e}")
        return None
