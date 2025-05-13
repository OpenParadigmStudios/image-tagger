#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Tag management tests

import unittest
import tempfile
import shutil
from pathlib import Path

from core.tagging import (
    normalize_tag,
    setup_tags_file,
    load_tags,
    save_tags,
    add_tag,
    remove_tag,
    get_image_tags,
    save_image_tags,
    find_tags_by_prefix,
    search_tags,
    TaggingError
)


class TaggingTest(unittest.TestCase):
    """Test the tag management functionality."""

    def setUp(self):
        """Set up a temporary environment for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tags_file = Path(self.temp_dir.name) / "tags.txt"
        self.image_text_file = Path(self.temp_dir.name) / "image.txt"

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_normalize_tag(self):
        """Test tag normalization."""
        # Test basic normalization
        self.assertEqual(normalize_tag("  test  "), "test")

        # Test invalid characters removal
        self.assertEqual(normalize_tag("test!@#$%^&*()"), "test")

        # Test allowed characters
        self.assertEqual(normalize_tag("test-tag_123.with, spaces"), "test-tag_123.with, spaces")

        # Test empty string
        self.assertEqual(normalize_tag(""), "")

        # Test only invalid characters
        self.assertEqual(normalize_tag("!@#$%^&*()"), "")

    def test_setup_tags_file(self):
        """Test setting up the tags file."""
        # Test creating new file
        tags = setup_tags_file(self.tags_file)
        self.assertTrue(self.tags_file.exists())
        self.assertEqual(tags, [])

        # Test with existing file
        with open(self.tags_file, 'w') as f:
            f.write("tag1\ntag2\ntag3")

        tags = setup_tags_file(self.tags_file)
        self.assertEqual(set(tags), {"tag1", "tag2", "tag3"})

    def test_load_save_tags(self):
        """Test loading and saving tags."""
        # Test saving tags
        test_tags = ["tag1", "tag2", "tag3"]
        self.assertTrue(save_tags(self.tags_file, test_tags))

        # Test loading tags
        loaded_tags = load_tags(self.tags_file)
        self.assertEqual(set(loaded_tags), set(test_tags))

        # Test loading with duplicates
        with open(self.tags_file, 'w') as f:
            f.write("tag1\ntag2\ntag2\ntag3\ntag1")

        loaded_tags = load_tags(self.tags_file)
        self.assertEqual(set(loaded_tags), set(test_tags))

        # Test loading from non-existent file should raise TaggingError
        non_existent = Path(self.temp_dir.name) / "nonexistent.txt"
        with self.assertRaises(TaggingError):
            load_tags(non_existent)

    def test_add_remove_tag(self):
        """Test adding and removing tags."""
        # Start with empty list
        tags = []

        # Add tags
        tags = add_tag(tags, "tag1")
        self.assertEqual(tags, ["tag1"])

        tags = add_tag(tags, "tag2")
        self.assertEqual(set(tags), {"tag1", "tag2"})

        # Add duplicate tag should not change list
        tags = add_tag(tags, "tag1")
        self.assertEqual(set(tags), {"tag1", "tag2"})

        # Add tag with normalization
        tags = add_tag(tags, "  tag3!@#  ")
        self.assertEqual(set(tags), {"tag1", "tag2", "tag3"})

        # Remove tag
        tags = remove_tag(tags, "tag2")
        self.assertEqual(set(tags), {"tag1", "tag3"})

        # Remove non-existent tag should not change list
        tags = remove_tag(tags, "tag4")
        self.assertEqual(set(tags), {"tag1", "tag3"})

        # Remove tag with normalization
        tags = remove_tag(tags, "  tag1!@#  ")
        self.assertEqual(tags, ["tag3"])

    def test_image_tags(self):
        """Test getting and saving image tags."""
        # Create test tags
        test_tags = ["tag1", "tag2", "tag3"]

        # Save tags to image file
        self.assertTrue(save_image_tags(self.image_text_file, test_tags))

        # Get tags from image file
        loaded_tags = get_image_tags(self.image_text_file)
        self.assertEqual(set(loaded_tags), set(test_tags))

        # Test with non-existent file
        self.assertEqual(get_image_tags(Path(self.temp_dir.name) / "nonexistent.txt"), [])

    def test_tag_search(self):
        """Test tag search functionality."""
        tags = ["apple", "banana", "cherry", "date", "Apple Pie", "Cherry Jam"]

        # Test prefix search case sensitive
        results = find_tags_by_prefix(tags, "app", case_sensitive=True)
        self.assertEqual(results, ["apple"])

        # Test prefix search case insensitive
        results = find_tags_by_prefix(tags, "App", case_sensitive=False)
        self.assertEqual(set(results), {"apple", "Apple Pie"})

        # Test full search case sensitive
        results = search_tags(tags, "erry", case_sensitive=True)
        self.assertEqual(set(results), {"cherry", "Cherry Jam"})

        # Test full search case insensitive
        results = search_tags(tags, "APPLE", case_sensitive=False)
        self.assertEqual(set(results), {"apple", "Apple Pie"})

        # Test no results
        results = search_tags(tags, "xyz")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
