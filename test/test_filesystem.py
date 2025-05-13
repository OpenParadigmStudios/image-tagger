#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Filesystem tests

import unittest
import tempfile
import shutil
import os
from pathlib import Path

from core.filesystem import (
    validate_directory,
    setup_output_directory,
    create_backup,
    safe_delete,
    get_default_paths,
    sanitize_path,
    ensure_path_exists
)
from core.config import AppConfig


class FilesystemTest(unittest.TestCase):
    """Test the filesystem operations functionality."""

    def setUp(self):
        """Set up a temporary environment for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.input_dir = self.test_dir / "input"
        self.output_dir = self.test_dir / "output"
        self.input_dir.mkdir()

        # Create some test files
        self.test_file = self.input_dir / "test.txt"
        self.test_file.write_text("Test content")

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_validate_directory(self):
        """Test directory validation."""
        # Test valid directory
        self.assertTrue(validate_directory(self.input_dir))

        # Test non-existent directory
        non_existent = self.test_dir / "non_existent"
        self.assertFalse(validate_directory(non_existent))

        # Test file as directory (should fail)
        self.assertFalse(validate_directory(self.test_file))

        # Test empty directory (should pass but with warning)
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()
        self.assertTrue(validate_directory(empty_dir))

    def test_setup_output_directory(self):
        """Test output directory setup."""
        # Test creating new directory
        output_dir = setup_output_directory(self.input_dir, "output")
        self.assertTrue(output_dir.exists())
        self.assertTrue(output_dir.is_dir())
        self.assertEqual(output_dir, self.input_dir / "output")

        # Test with existing directory (should not raise error)
        output_dir = setup_output_directory(self.input_dir, "output")
        self.assertTrue(output_dir.exists())

        # Test with permission denied - can be challenging to test properly in unit tests
        # We'll skip this test case as it requires modifying file permissions

    def test_create_backup(self):
        """Test file backup creation."""
        # Test backup of existing file
        self.assertTrue(create_backup(self.test_file))
        backup_path = self.test_file.with_suffix(f"{self.test_file.suffix}.bak")
        self.assertTrue(backup_path.exists())
        self.assertEqual(backup_path.read_text(), "Test content")

        # Test backup of non-existent file (should return False)
        non_existent = self.input_dir / "non_existent.txt"
        self.assertFalse(create_backup(non_existent))

    def test_safe_delete(self):
        """Test safe file deletion."""
        # Test deleting a file
        self.assertTrue(safe_delete(self.test_file))
        self.assertFalse(self.test_file.exists())
        backup_path = self.test_file.with_suffix(f"{self.test_file.suffix}.bak")
        self.assertTrue(backup_path.exists())

        # Test deleting a directory
        dir_to_delete = self.test_dir / "to_delete"
        dir_to_delete.mkdir()
        test_file_in_dir = dir_to_delete / "test.txt"
        test_file_in_dir.write_text("Test content")

        self.assertTrue(safe_delete(dir_to_delete))
        self.assertFalse(test_file_in_dir.exists())
        self.assertTrue(dir_to_delete.exists())  # Directory is renamed and recreated
        self.assertTrue(dir_to_delete.is_dir())

        # Test deleting non-existent file (should return True)
        non_existent = self.input_dir / "non_existent.txt"
        self.assertTrue(safe_delete(non_existent))

    def test_ensure_path_exists(self):
        """Test ensuring paths exist."""
        # Test creating file path
        file_path = self.test_dir / "new_dir" / "test.txt"
        self.assertTrue(ensure_path_exists(file_path))
        self.assertTrue(file_path.parent.exists())
        self.assertTrue(file_path.exists())

        # Test creating directory path
        dir_path = self.test_dir / "new_dir2" / "subdir"
        self.assertTrue(ensure_path_exists(dir_path, is_directory=True))
        self.assertTrue(dir_path.exists())
        self.assertTrue(dir_path.is_dir())

        # Test with existing path (should return True)
        self.assertTrue(ensure_path_exists(file_path))
        self.assertTrue(ensure_path_exists(dir_path, is_directory=True))

    def test_get_default_paths(self):
        """Test getting default paths."""
        # Create a test config
        config = AppConfig(
            input_directory=self.input_dir,
            output_dir="output"
        )

        # Get default paths
        paths = get_default_paths(config)

        # Verify paths
        expected_output_dir = self.input_dir / "output"
        self.assertEqual(paths["output_dir"], expected_output_dir)
        self.assertEqual(paths["session_file"], expected_output_dir / "session.json")
        self.assertEqual(paths["tags_file"], expected_output_dir / "tags.txt")

    def test_sanitize_path(self):
        """Test path sanitization."""
        # Test valid path
        valid_path = self.test_dir / "valid" / "path.txt"
        sanitized = sanitize_path(str(valid_path))
        self.assertIsNotNone(sanitized)
        self.assertEqual(sanitized, valid_path.absolute().resolve())

        # Test path with traversal (should return None)
        traversal_path = str(self.test_dir / "valid" / ".." / "path.txt")
        sanitized = sanitize_path(traversal_path)
        self.assertIsNone(sanitized)

        # Test with base directory restriction
        base_dir = self.test_dir
        inside_path = str(self.test_dir / "inside.txt")
        outside_path = str(Path(self.test_dir).parent / "outside.txt")

        # Path inside base_dir should be allowed
        sanitized = sanitize_path(inside_path, base_dir)
        self.assertIsNotNone(sanitized)

        # Path outside base_dir should be rejected
        sanitized = sanitize_path(outside_path, base_dir)
        self.assertIsNone(sanitized)

        # Test empty path (should raise ValueError)
        with self.assertRaises(ValueError):
            sanitize_path("")

        # Test path with null character (should raise ValueError)
        invalid_path = "not a valid path:\0character"
        with self.assertRaises(ValueError):
            sanitize_path(invalid_path)


if __name__ == "__main__":
    unittest.main()
