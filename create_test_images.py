#!/usr/bin/env python3
"""Create sample test images for testing the CivitAI tagger."""

from pathlib import Path
from PIL import Image
import os

# Ensure test directory exists
test_dir = Path("test_images")
test_dir.mkdir(exist_ok=True)

# Remove any existing files
for file in test_dir.glob("*"):
    if file.is_file():
        file.unlink()

# Create sample images with different formats
formats = [
    ("test1.jpg", "JPEG"),
    ("test2.png", "PNG"),
    ("test3.webp", "WEBP")
]

# Create a small 100x100 image of different colors
for filename, format_name in formats:
    img = Image.new('RGB', (100, 100), color=(
        formats.index((filename, format_name)) * 80,
        100,
        200
    ))
    img.save(test_dir / filename, format=format_name)
    print(f"Created: {test_dir / filename}")

print(f"Created {len(formats)} test images in {test_dir}")
