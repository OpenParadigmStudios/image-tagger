#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Image processing functionality

import logging
import re
import shutil
from pathlib import Path
from typing import Dict, Tuple, List, Optional

# Import Pillow for image validation
try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    logging.error("Pillow (PIL) is required but not installed. Please install it with 'pip install Pillow'")
    raise ImportError("Pillow (PIL) is required but not installed")

# List of supported image extensions
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}


class ImageProcessingError(Exception):
    """Raised when image processing fails."""
    pass


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

    # Thorough check - file content with Pillow
    try:
        with Image.open(file_path) as img:
            # Try to verify the image by loading it
            img.verify()
        return True
    except (UnidentifiedImageError, IOError, SyntaxError) as e:
        logging.debug(f"Error validating image {file_path}: {e}")
        return False
    except Exception as e:
        logging.debug(f"Unexpected error validating image {file_path}: {e}")
        return False


def is_valid_image(file_path: Path) -> bool:
    """
    Check if a file is a valid image.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if the file is a valid image
    """
    return validate_image_with_pillow(file_path)


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
        if file_path.is_file() and is_valid_image(file_path):
            image_files.append(file_path)
        elif file_path.is_file():
            skipped_files += 1

    logging.info(f"Found {len(image_files)} valid image files")
    if skipped_files > 0:
        logging.info(f"Skipped {skipped_files} non-image files")

    if not image_files:
        logging.warning("No valid image files found in directory")

    return sorted(image_files)


def get_next_sequence_number(processed_images: Dict[str, str], prefix: str) -> int:
    """
    Find the next sequence number for image file naming.

    Args:
        processed_images: Dictionary of already processed images
        prefix: Prefix used for filename generation

    Returns:
        int: Next sequence number
    """
    sequence_numbers = []
    pattern = re.compile(f"^{re.escape(prefix)}_([0-9]+)\\.")

    # Extract sequence numbers from processed image filenames
    for original_path, new_path in processed_images.items():
        new_filename = Path(new_path).name
        match = pattern.match(new_filename)
        if match:
            try:
                sequence_numbers.append(int(match.group(1)))
            except ValueError:
                continue

    return max(sequence_numbers, default=0) + 1


def generate_unique_filename(original_path: Path, prefix: str,
                       processed_images: Dict[str, str], padding: int = 3) -> str:
    """
    Generate a unique filename for an image.

    Args:
        original_path: Path to the original image
        prefix: Filename prefix
        processed_images: Dictionary of already processed images
        padding: Zero padding for sequence numbers

    Returns:
        str: New unique filename
    """
    # Check if image has already been processed
    orig_path_str = str(original_path)
    if orig_path_str in processed_images:
        # Return just the filename part, not the full path
        return Path(processed_images[orig_path_str]).name

    # Get the next sequence number
    seq_num = get_next_sequence_number(processed_images, prefix)

    # Create new filename with prefix, sequence number, and original extension
    new_filename = f"{prefix}_{seq_num:0{padding}d}{original_path.suffix.lower()}"

    logging.debug(f"Generated unique filename '{new_filename}' for {original_path}")

    return new_filename


def copy_image_to_output(original_path: Path, output_dir: Path, new_filename: str) -> Path:
    """
    Copy image to output directory with new filename.

    Args:
        original_path: Path to the original image
        output_dir: Output directory path
        new_filename: New filename to use

    Returns:
        Path: Path to the copied image file
    """
    output_path = output_dir / new_filename

    # Skip if the file already exists in the output directory
    if output_path.exists():
        logging.debug(f"Output file already exists: {output_path}")
        return output_path

    try:
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy the file with metadata preservation
        shutil.copy2(original_path, output_path)
        logging.debug(f"Copied {original_path} to {output_path}")

        return output_path
    except Exception as e:
        error_msg = f"Error copying image {original_path} to {output_path}: {e}"
        logging.error(error_msg)
        raise ImageProcessingError(error_msg)


def create_text_file(image_path: Path) -> Path:
    """
    Create a corresponding text file for an image.

    Args:
        image_path: Path to the image file

    Returns:
        Path: Path to the created text file
    """
    text_path = image_path.with_suffix('.txt')

    # Skip if text file already exists
    if text_path.exists():
        logging.debug(f"Text file already exists: {text_path}")
        return text_path

    try:
        # Create empty text file
        text_path.touch()
        logging.debug(f"Created text file: {text_path}")

        return text_path
    except Exception as e:
        error_msg = f"Error creating text file for {image_path}: {e}"
        logging.error(error_msg)
        raise ImageProcessingError(error_msg)


def process_image(original_path: Path, output_dir: Path, prefix: str,
             processed_images: Dict[str, str]) -> Tuple[Dict[str, str], Path, Path]:
    """
    Process a single image file.

    Args:
        original_path: Path to the original image
        output_dir: Path to the output directory
        prefix: Filename prefix for renamed images
        processed_images: Dictionary of already processed images

    Returns:
        Tuple containing:
        - Updated processed_images dictionary
        - Path to the copied image file
        - Path to the created text file
    """
    try:
        # Generate unique filename
        new_filename = generate_unique_filename(
            original_path, prefix, processed_images
        )

        # Copy image to output directory
        output_path = copy_image_to_output(
            original_path, output_dir, new_filename
        )

        # Create corresponding text file
        text_path = create_text_file(output_path)

        # Update processed images dictionary
        processed_images[str(original_path)] = str(output_path)

        return processed_images, output_path, text_path

    except Exception as e:
        error_msg = f"Failed to process image {original_path}: {e}"
        logging.error(error_msg)
        raise ImageProcessingError(error_msg)


def process_with_recovery(func, *args, max_retries=3, **kwargs):
    """
    Execute a function with automatic retry on failure.

    Args:
        func: Function to execute
        *args: Positional arguments for func
        max_retries: Maximum number of retries
        **kwargs: Keyword arguments for func

    Returns:
        The return value of the function

    Raises:
        Exception: If all retries fail
    """
    retries = 0
    last_error = None

    while retries < max_retries:
        try:
            return func(*args, **kwargs)
        except (IOError, OSError) as e:
            last_error = e
            retries += 1
            if retries < max_retries:
                logging.warning(f"Operation failed, retrying ({retries}/{max_retries}): {e}")
            import time
            time.sleep(0.5)  # Back off before retry

    if last_error:
        logging.error(f"Operation failed after {max_retries} retries: {last_error}")
        raise last_error
    else:
        raise Exception(f"Operation failed after {max_retries} retries")
