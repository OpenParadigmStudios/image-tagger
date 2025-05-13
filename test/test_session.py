#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Session management tests

import unittest
import os
import tempfile
import json
import time
from pathlib import Path

from core.session import SessionManager, SessionState, SessionError


class SessionManagerTest(unittest.TestCase):
    """Test the session management functionality."""

    def setUp(self):
        """Set up a temporary environment for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_file = Path(self.temp_dir.name) / "session.json"

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_session_creation(self):
        """Test creating a new session manager."""
        manager = SessionManager(self.session_file)
        self.assertIsInstance(manager.state, SessionState)
        self.assertEqual(len(manager.state.processed_images), 0)
        self.assertEqual(len(manager.state.tags), 0)
        self.assertIsNone(manager.state.current_position)

    def test_session_save_load(self):
        """Test saving and loading session state."""
        # Create and populate session
        manager = SessionManager(self.session_file)
        manager.state.processed_images["test_image.jpg"] = "output/img_001.jpg"
        manager.state.tags = ["tag1", "tag2"]
        manager.state.current_position = "img_001"
        manager.state.stats["total_images"] = 10
        manager.state.stats["processed_images"] = 1

        # Save session
        manager.save(force=True)
        self.assertTrue(self.session_file.exists())

        # Load session in new manager
        new_manager = SessionManager(self.session_file)
        self.assertEqual(len(new_manager.state.processed_images), 1)
        self.assertEqual(len(new_manager.state.tags), 2)
        self.assertEqual(new_manager.state.current_position, "img_001")
        self.assertEqual(new_manager.state.stats["total_images"], 10)
        self.assertEqual(new_manager.state.stats["processed_images"], 1)

    def test_auto_save_interval(self):
        """Test auto-save interval functionality."""
        manager = SessionManager(self.session_file)
        # Set a very short interval for testing
        manager.set_auto_save_interval(1)

        # First save with force=True should always create the file
        manager.save(force=True)
        self.assertTrue(self.session_file.exists())

        # Remove file to test if it gets recreated
        os.unlink(self.session_file)
        self.assertFalse(self.session_file.exists())

        # Immediate save should be skipped due to interval
        manager.save()  # No force parameter, so should respect interval
        self.assertFalse(self.session_file.exists())

        # Wait for interval to pass
        time.sleep(1.1)

        # Now save should happen
        manager.save()
        self.assertTrue(self.session_file.exists())

    def test_session_update_methods(self):
        """Test the various update methods."""
        manager = SessionManager(self.session_file)

        # Test update_processed_image
        manager.update_processed_image("orig.jpg", "new.jpg")
        self.assertEqual(len(manager.state.processed_images), 1)
        self.assertEqual(manager.state.processed_images["orig.jpg"], "new.jpg")
        self.assertEqual(manager.state.stats["processed_images"], 1)

        # Test set_current_position
        manager.set_current_position("position1")
        self.assertEqual(manager.state.current_position, "position1")

        # Test update_tags
        manager.update_tags(["tag1", "tag2"])
        self.assertEqual(manager.state.tags, ["tag1", "tag2"])

        # Test add_tag
        manager.add_tag("tag3")
        self.assertEqual(len(manager.state.tags), 3)
        self.assertIn("tag3", manager.state.tags)

        # Test adding duplicate tag
        manager.add_tag("tag3")
        self.assertEqual(len(manager.state.tags), 3)

        # Test remove_tag
        manager.remove_tag("tag2")
        self.assertEqual(len(manager.state.tags), 2)
        self.assertNotIn("tag2", manager.state.tags)

        # Test update_stats
        manager.update_stats(total_images=100, processed_images=50)
        self.assertEqual(manager.state.stats["total_images"], 100)
        self.assertEqual(manager.state.stats["processed_images"], 50)

    def test_corrupt_session_file(self):
        """Test handling of corrupted session files."""
        # Create a corrupted session file
        with open(self.session_file, 'w') as f:
            f.write("{This is not valid JSON}")

        # Session manager should handle this gracefully
        manager = SessionManager(self.session_file)
        self.assertIsInstance(manager.state, SessionState)

        # Backup file should have been created
        corrupted_backup = self.session_file.with_suffix(f"{self.session_file.suffix}.corrupted")
        self.assertTrue(corrupted_backup.exists())


if __name__ == "__main__":
    unittest.main()
