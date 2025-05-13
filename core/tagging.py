#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Tag management functionality

import logging
import re
from pathlib import Path
from typing import List, Set, Optional, Dict

class TaggingError(Exception):
    """Raised when tag operations fail."""
    pass


def normalize_tag(tag: str) -> str:
    """
    Normalize a tag to ensure consistent formatting.

    Args:
        tag: Raw tag string

    Returns:
        str: Normalized tag string
    """
    # Strip whitespace
    normalized = tag.strip()

    # Remove any invalid characters - allow alphanumeric, spaces, underscore, hyphen, period, comma
    normalized = re.sub(r'[^a-zA-Z0-9_\-., ]', '', normalized)

    return normalized


def setup_tags_file(tags_file_path: Path) -> List[str]:
    """
    Initialize or load the tags file.

    Args:
        tags_file_path: Path to the tags file

    Returns:
        List[str]: List of existing tags
    """
    if not tags_file_path.exists():
        try:
            tags_file_path.touch()
            logging.info(f"Created new tags file: {tags_file_path}")
            return []
        except Exception as e:
            error_msg = f"Error creating tags file {tags_file_path}: {e}"
            logging.error(error_msg)
            raise TaggingError(error_msg)

    return load_tags(tags_file_path)


def load_tags(tags_file_path: Path) -> List[str]:
    """
    Load tags from a tags file.

    Args:
        tags_file_path: Path to the tags file

    Returns:
        List[str]: List of tags
    """
    try:
        content = tags_file_path.read_text(encoding='utf-8').strip()

        # Handle both comma-delimited and newline-delimited formats for backward compatibility
        if ',' in content:
            # Split by commas and clean up
            tags = [tag.strip() for tag in content.split(',') if tag.strip()]
        else:
            # Fall back to newline splitting for backward compatibility
            tags = [line.strip() for line in content.splitlines() if line.strip()]

        unique_tags = sorted(set(tags))

        # If there were duplicates, rewrite the file with unique tags
        if len(tags) != len(unique_tags):
            save_tags(tags_file_path, unique_tags)
            logging.info(f"Removed {len(tags) - len(unique_tags)} duplicate tags from {tags_file_path}")

        logging.info(f"Loaded {len(unique_tags)} tags from {tags_file_path}")
        return unique_tags

    except Exception as e:
        error_msg = f"Error reading tags file {tags_file_path}: {e}"
        logging.error(error_msg)
        raise TaggingError(error_msg)


def save_tags(tags_file_path: Path, tags_list: List[str]) -> bool:
    """
    Save tags to a tags file.

    Args:
        tags_file_path: Path to the tags file
        tags_list: List of tags to save

    Returns:
        bool: True if save was successful
    """
    # Create backup of the existing file
    if tags_file_path.exists():
        from core.filesystem import create_backup
        create_backup(tags_file_path)

    try:
        # Write tags to file as comma-delimited list without extra spaces around commas
        content = ", ".join([tag.strip() for tag in sorted(tags_list)])
        with open(tags_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logging.debug(f"Saved {len(tags_list)} tags to {tags_file_path} as comma-delimited list")
        return True
    except Exception as e:
        error_msg = f"Error saving tags to {tags_file_path}: {e}"
        logging.error(error_msg)
        raise TaggingError(error_msg)


def add_tag(tags_list: List[str], new_tag: str) -> List[str]:
    """
    Add a tag to a list of tags if it doesn't already exist.

    Args:
        tags_list: Current list of tags
        new_tag: Tag to add

    Returns:
        List[str]: Updated list of tags
    """
    # Normalize tag
    normalized_tag = normalize_tag(new_tag)

    # Skip empty tags
    if not normalized_tag:
        return tags_list

    # Skip if tag already exists
    if normalized_tag in tags_list:
        return tags_list

    # Add tag and return updated list
    updated_tags = tags_list.copy()
    updated_tags.append(normalized_tag)

    logging.debug(f"Added tag '{normalized_tag}' to tags list")

    return updated_tags


def remove_tag(tags_list: List[str], tag_to_remove: str) -> List[str]:
    """
    Remove a tag from a list of tags if it exists.

    Args:
        tags_list: Current list of tags
        tag_to_remove: Tag to remove

    Returns:
        List[str]: Updated list of tags
    """
    # Normalize tag
    normalized_tag = normalize_tag(tag_to_remove)

    # Skip empty tags
    if not normalized_tag:
        return tags_list

    # Skip if tag doesn't exist
    if normalized_tag not in tags_list:
        return tags_list

    # Remove tag and return updated list
    updated_tags = [tag for tag in tags_list if tag != normalized_tag]

    logging.debug(f"Removed tag '{normalized_tag}' from tags list")

    return updated_tags


def get_image_tags(text_file_path: Path) -> List[str]:
    """
    Get tags for an image from its corresponding text file.

    Args:
        text_file_path: Path to the text file

    Returns:
        List[str]: List of tags
    """
    if not text_file_path.exists():
        logging.warning(f"Text file does not exist: {text_file_path}")
        return []

    try:
        content = text_file_path.read_text(encoding='utf-8').strip()

        # Handle both comma-delimited and newline-delimited formats for backward compatibility
        if ',' in content:
            # Split by commas and clean up
            tags = [tag.strip() for tag in content.split(',') if tag.strip()]
        else:
            # Fall back to newline splitting for backward compatibility
            tags = [line.strip() for line in content.splitlines() if line.strip()]

        # Return list with duplicates removed
        return sorted(set(tags))
    except Exception as e:
        error_msg = f"Error reading tags from {text_file_path}: {e}"
        logging.error(error_msg)
        raise TaggingError(error_msg)


def save_image_tags(text_file_path: Path, tags_list: List[str]) -> bool:
    """
    Save tags to an image's corresponding text file.

    Args:
        text_file_path: Path to the text file
        tags_list: List of tags to save

    Returns:
        bool: True if save was successful
    """
    try:
        logging.info(f"Saving tags to {text_file_path}")

        # Create backup of existing file
        if text_file_path.exists():
            from core.filesystem import create_backup
            create_backup(text_file_path)
            logging.info(f"Created backup of {text_file_path}")

            # Delete the existing file to ensure a clean slate
            try:
                text_file_path.unlink()
                logging.info(f"Deleted existing file {text_file_path}")
            except Exception as e:
                logging.error(f"Error deleting {text_file_path}: {e}")
                # Even if delete fails, we'll overwrite the file anyway

        # Create parent directory if it doesn't exist
        text_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save tags as comma-delimited list without extra spaces around commas
        content = ", ".join([tag.strip() for tag in sorted(tags_list)])

        # Use direct file write with open() to ensure the file is completely regenerated
        with open(str(text_file_path), 'w', encoding='utf-8') as f:
            f.write(content)

        logging.info(f"Successfully saved {len(tags_list)} tags to {text_file_path} as comma-delimited list")
        return True
    except Exception as e:
        error_msg = f"Error saving tags to {text_file_path}: {e}"
        logging.error(error_msg)
        raise TaggingError(error_msg)


def batch_update_tags(master_tags_file: Path, tag_files: List[Path],
                     updates: Dict[str, List[str]]) -> bool:
    """
    Batch update tags across multiple files.

    Args:
        master_tags_file: Path to the master tags file
        tag_files: List of all tag file paths
        updates: Dictionary mapping file paths to new tag lists

    Returns:
        bool: True if all updates were successful
    """
    # Track unique tags across all files
    all_tags = set()
    success = True

    # Process each file update
    for file_path_str, new_tags in updates.items():
        try:
            file_path = Path(file_path_str)
            if save_image_tags(file_path, new_tags):
                all_tags.update(new_tags)
            else:
                success = False
        except Exception as e:
            logging.error(f"Failed to update tags for {file_path_str}: {e}")
            success = False

    # Update master tags file with all unique tags
    try:
        # Get existing tags
        existing_tags = load_tags(master_tags_file) if master_tags_file.exists() else []

        # Combine with newly added tags
        all_tags.update(existing_tags)

        # Save combined tags
        if not save_tags(master_tags_file, sorted(all_tags)):
            success = False
    except Exception as e:
        logging.error(f"Failed to update master tags file: {e}")
        success = False

    return success


def find_tags_by_prefix(tags_list: List[str], prefix: str,
                       case_sensitive: bool = False) -> List[str]:
    """
    Find tags that start with a given prefix.

    Args:
        tags_list: List of tags to search
        prefix: Prefix to search for
        case_sensitive: Whether to perform case-sensitive matching

    Returns:
        List[str]: List of matching tags
    """
    if not case_sensitive:
        prefix = prefix.lower()
        return [tag for tag in tags_list if tag.lower().startswith(prefix)]
    else:
        return [tag for tag in tags_list if tag.startswith(prefix)]


def search_tags(tags_list: List[str], query: str,
              case_sensitive: bool = False) -> List[str]:
    """
    Search for tags containing a query string.

    Args:
        tags_list: List of tags to search
        query: Search string
        case_sensitive: Whether to perform case-sensitive matching

    Returns:
        List[str]: List of matching tags
    """
    if not case_sensitive:
        query = query.lower()
        return [tag for tag in tags_list if query in tag.lower()]
    else:
        return [tag for tag in tags_list if query in tag]
