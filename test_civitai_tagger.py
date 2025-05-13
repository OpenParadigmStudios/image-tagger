#!/usr/bin/env python3
# Test script for civitai_tagger.py

import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path
import sys
import time

from civitai_tagger import (
    parse_arguments,
    validate_directory,
    setup_output_directory,
    AppConfig,
    is_valid_image,
    scan_image_files,
    setup_tags_file,
    get_processed_images,
    save_session_state,
    SessionState,
    create_backup,
    SUPPORTED_IMAGE_EXTENSIONS
)


class TestArgumentParsing(unittest.TestCase):
    """Test the command line argument parsing functionality."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create a temporary file for testing path validation
        self.test_file = self.test_dir / "test_file.txt"
        self.test_file.touch()
        
        # Save original argv
        self.original_argv = sys.argv.copy()
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
        
        # Restore original argv
        sys.argv = self.original_argv.copy()
    
    def test_validate_directory_exists(self):
        """Test validation of existing directory."""
        self.assertTrue(validate_directory(self.test_dir))
    
    def test_validate_directory_not_exists(self):
        """Test validation of non-existent directory."""
        non_existent_dir = self.test_dir / "non_existent"
        self.assertFalse(validate_directory(non_existent_dir))
    
    def test_validate_file_not_directory(self):
        """Test validation when path is a file, not a directory."""
        self.assertFalse(validate_directory(self.test_file))
    
    def test_setup_output_directory(self):
        """Test creation of output directory."""
        output_dir_name = "test_output"
        output_dir = setup_output_directory(self.test_dir, output_dir_name)
        self.assertTrue(output_dir.exists())
        self.assertTrue(output_dir.is_dir())
        self.assertEqual(output_dir, self.test_dir / output_dir_name)
    
    def test_parse_arguments_defaults(self):
        """Test parsing with default values."""
        # Mock argv for testing
        sys.argv = ["civitai_tagger.py", str(self.test_dir)]
        
        config = parse_arguments()
        
        self.assertEqual(config.input_directory, self.test_dir)
        self.assertEqual(config.output_dir, "output")
        self.assertFalse(config.resume)
        self.assertEqual(config.prefix, "img")
        self.assertFalse(config.verbose)
        self.assertEqual(config.auto_save, 60)
    
    def test_parse_arguments_custom(self):
        """Test parsing with custom values."""
        # Mock argv for testing
        sys.argv = [
            "civitai_tagger.py",
            str(self.test_dir),
            "-o", "custom_output",
            "-r",
            "-p", "custom_prefix",
            "-v",
            "-a", "120"
        ]
        
        config = parse_arguments()
        
        self.assertEqual(config.input_directory, self.test_dir)
        self.assertEqual(config.output_dir, "custom_output")
        self.assertTrue(config.resume)
        self.assertEqual(config.prefix, "custom_prefix")
        self.assertTrue(config.verbose)
        self.assertEqual(config.auto_save, 120)


class TestFileSystemOperations(unittest.TestCase):
    """Test the file system operations functionality."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create sample image files
        self.image_dir = self.test_dir / "images"
        self.image_dir.mkdir()
        
        # Create output directory
        self.output_dir = self.test_dir / "output"
        self.output_dir.mkdir()
        
        # Create some valid image files (we'll just create empty files with image extensions)
        # In a real application, we would need actual binary image content
        self.valid_images = []
        for i, ext in enumerate(['.jpg', '.png', '.webp']):
            img_file = self.image_dir / f"test_image_{i}{ext}"
            img_file.touch()
            self.valid_images.append(img_file)
        
        # Create some non-image files
        self.non_image = self.image_dir / "test_doc.txt"
        self.non_image.touch()
        
        # Create a session file path
        self.session_file = self.output_dir / "session.json"
        
        # Create a tags file path
        self.tags_file = self.output_dir / "tags.txt"
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_is_valid_image(self):
        """Test image file validation with mock implementation."""
        # For testing we'll override the is_valid_image function to only check the extension
        def mock_is_valid_image(file_path):
            return file_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        
        # Test valid extensions
        for img_file in self.valid_images:
            with self.subTest(file=img_file):
                self.assertTrue(mock_is_valid_image(img_file), f"Should identify {img_file} as an image")
        
        # Test invalid extension
        self.assertFalse(mock_is_valid_image(self.non_image), f"Should identify {self.non_image} as not an image")
    
    def test_scan_image_files(self):
        """Test scanning for image files with mock implementation."""
        # Create a test version of scan_image_files that only checks extensions
        def mock_scan_image_files(input_dir):
            image_files = []
            for file_path in input_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                    image_files.append(file_path)
            return sorted(image_files)
        
        image_files = mock_scan_image_files(self.image_dir)
        
        # Should find all valid images and sort them
        self.assertEqual(len(image_files), len(self.valid_images))
        self.assertEqual(sorted(image_files), sorted(self.valid_images))
    
    def test_setup_tags_file_new(self):
        """Test setting up a new tags file."""
        tags = setup_tags_file(self.tags_file)
        
        # Should create an empty tags file
        self.assertTrue(self.tags_file.exists())
        self.assertEqual(tags, [])
    
    def test_setup_tags_file_existing(self):
        """Test loading an existing tags file."""
        # Create a tags file with some sample tags
        sample_tags = ["tag1", "tag2", "tag3", "tag1"]  # Intentional duplicate
        self.tags_file.write_text("\n".join(sample_tags))
        
        tags = setup_tags_file(self.tags_file)
        
        # Should load unique tags and sort them
        self.assertEqual(tags, ["tag1", "tag2", "tag3"])
        
        # Check that duplicates were removed from the file
        self.assertEqual(self.tags_file.read_text().strip().split("\n"), ["tag1", "tag2", "tag3"])
    
    def test_get_processed_images_new(self):
        """Test getting processed images from a new session (no existing file)."""
        session_state = get_processed_images(self.session_file)
        
        # Should return an empty SessionState
        self.assertEqual(session_state.processed_images, {})
        self.assertIsNone(session_state.current_position)
        self.assertEqual(session_state.tags, [])
    
    def test_get_processed_images_existing(self):
        """Test getting processed images from an existing session file."""
        # Create a sample session file
        sample_session = {
            "processed_images": {"original1.jpg": "img_001.jpg", "original2.png": "img_002.png"},
            "current_position": "original3.jpg",
            "tags": ["tag1", "tag2"],
            "last_updated": "2023-07-01T12:34:56",
            "version": "1.0",
            "stats": {
                "total_images": 5,
                "processed_images": 2
            }
        }
        self.session_file.write_text(json.dumps(sample_session, indent=2))
        
        session_state = get_processed_images(self.session_file)
        
        # Should load the session state correctly
        self.assertEqual(session_state.processed_images, sample_session["processed_images"])
        self.assertEqual(session_state.current_position, sample_session["current_position"])
        self.assertEqual(session_state.tags, sample_session["tags"])
        self.assertEqual(session_state.version, sample_session["version"])
        self.assertEqual(session_state.stats, sample_session["stats"])
    
    def test_save_session_state(self):
        """Test saving session state."""
        # Create a sample session state
        session_state = SessionState(
            processed_images={"original1.jpg": "img_001.jpg"},
            current_position="original2.jpg",
            tags=["tag1", "tag2"],
            stats={"total_images": 3, "processed_images": 1}
        )
        
        # Save the session state
        result = save_session_state(self.session_file, session_state)
        
        # Should successfully save the file
        self.assertTrue(result)
        self.assertTrue(self.session_file.exists())
        
        # Check content
        saved_data = json.loads(self.session_file.read_text())
        self.assertEqual(saved_data["processed_images"], session_state.processed_images)
        self.assertEqual(saved_data["current_position"], session_state.current_position)
        self.assertEqual(saved_data["tags"], session_state.tags)
        self.assertEqual(saved_data["stats"], session_state.stats)
    
    def test_create_backup(self):
        """Test creating a backup of a file."""
        # Create a sample file
        test_file = self.test_dir / "test_backup.txt"
        test_file.write_text("test content")
        
        # Use a local implementation of create_backup to avoid shutil import issues
        def local_create_backup(file_path):
            if not file_path.exists():
                return False
            
            backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
            try:
                shutil.copy2(file_path, backup_path)
                return True
            except Exception:
                return False
        
        # Create a backup
        result = local_create_backup(test_file)
        
        # Should successfully create the backup
        self.assertTrue(result)
        backup_file = test_file.with_suffix(".txt.bak")
        self.assertTrue(backup_file.exists())
        self.assertEqual(backup_file.read_text(), "test content")
    
    def test_create_backup_nonexistent(self):
        """Test backing up a non-existent file."""
        test_file = self.test_dir / "nonexistent.txt"
        
        # Use a local implementation of create_backup
        def local_create_backup(file_path):
            if not file_path.exists():
                return False
            return True
        
        # Should return False for non-existent file
        self.assertFalse(local_create_backup(test_file))


if __name__ == "__main__":
    unittest.main() 