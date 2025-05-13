#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Integration tests

import unittest
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch

# Import modules to test
from core.config import AppConfig
from core.session import SessionManager, SessionState
from core.filesystem import setup_output_directory, setup_directories
from core.image_processing import process_image, scan_image_files
from core.tagging import setup_tags_file, add_tag, save_image_tags


class IntegrationTest(unittest.TestCase):
    """Test integration between the core modules."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directories
        self.test_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.test_dir / "input"
        self.input_dir.mkdir()

        # Create test images
        self.create_test_images()

        # Set up test configuration
        self.config = AppConfig(
            input_directory=self.input_dir,
            output_dir="output",
            resume=False,
            prefix="img",
            verbose=True,
            auto_save=5
        )

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def create_test_images(self):
        """Create test image files."""
        # Create placeholder "images" (not real images but files for testing)
        for i in range(3):
            img_path = self.input_dir / f"test_image_{i}.jpg"
            img_path.write_bytes(b'FAKE IMAGE DATA')  # Just write some bytes for testing

    @patch('core.image_processing.validate_image_with_pillow')
    def test_end_to_end_workflow(self, mock_validate):
        """Test the complete workflow from directories to session management."""
        # Mock image validation to always return True for our test files
        mock_validate.return_value = True

        # Step 1: Setup directories
        self.assertTrue(setup_directories(self.config))

        # Step 2: Check output directory structure
        output_dir = self.input_dir / self.config.output_dir
        self.assertTrue(output_dir.exists())
        self.assertTrue(output_dir.is_dir())

        # Step 3: Verify tags file creation
        tags_file = output_dir / "tags.txt"
        self.assertTrue(tags_file.exists())

        # Step 4: Scan for images
        images = scan_image_files(self.input_dir)
        self.assertEqual(len(images), 3)

        # Step 5: Create session manager
        session_file = output_dir / "session.json"
        session_manager = SessionManager(session_file)

        # Step 6: Process one image
        processed = {}
        for img_path in images[:1]:  # Process only the first image
            processed, output_path, text_path = process_image(
                img_path, output_dir, self.config.prefix, processed
            )
            # Update session state
            session_manager.update_processed_image(str(img_path), str(output_path))
            session_manager.set_current_position(str(output_path.stem))

            # Add some tags to the image
            tags = ["test_tag_1", "test_tag_2"]
            save_image_tags(text_path, tags)

            # Add tags to the master list
            for tag in tags:
                session_manager.add_tag(tag)

        # Force save the session
        session_manager.save(force=True)

        # Step 7: Verify session state
        self.assertTrue(session_file.exists())
        with open(session_file, "r") as f:
            session_data = json.load(f)
            self.assertEqual(len(session_data.get("processed_images", {})), 1)
            self.assertEqual(len(session_data.get("tags", [])), 2)

        # Step 8: Load session state again and verify
        new_session_manager = SessionManager(session_file)
        self.assertEqual(len(new_session_manager.state.processed_images), 1)
        self.assertEqual(len(new_session_manager.state.tags), 2)

        # Step 9: Update stats
        new_session_manager.update_stats(total_images=len(images), processed_images=1)
        new_session_manager.save(force=True)

        # Step 10: Verify stats
        with open(session_file, "r") as f:
            session_data = json.load(f)
            stats = session_data.get("stats", {})
            self.assertEqual(stats.get("total_images"), 3)
            self.assertEqual(stats.get("processed_images"), 1)


if __name__ == "__main__":
    unittest.main()
