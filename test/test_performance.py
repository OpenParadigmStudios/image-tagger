#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Performance tests

import unittest
import tempfile
import shutil
import time
import logging
from pathlib import Path
from PIL import Image
from unittest.mock import patch

from core.filesystem import setup_directories
from core.session import SessionManager
from core.image_processing import process_image, scan_image_files
from core.tagging import setup_tags_file, save_image_tags
from core.config import AppConfig


class PerformanceTest(unittest.TestCase):
    """Test application performance with large data sets."""

    def setUp(self):
        """Set up test environment."""
        # Disable logging for performance tests
        logging.disable(logging.CRITICAL)

        # Create temporary test directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.test_dir / "input"
        self.input_dir.mkdir()
        self.output_dir = self.input_dir / "output"
        self.output_dir.mkdir()

        # Set up test configuration
        self.config = AppConfig(
            input_directory=self.input_dir,
            output_dir="output",
            resume=False,
            prefix="img",
            verbose=False,
            auto_save=10
        )

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
        logging.disable(logging.NOTSET)  # Re-enable logging

    def create_test_images(self, count=100, size=(100, 100)):
        """Create a specified number of test images."""
        for i in range(count):
            # Create a simple color image
            img = Image.new('RGB', size, color=(i % 255, (i * 2) % 255, (i * 3) % 255))
            img_path = self.input_dir / f"test_image_{i:04d}.jpg"
            img.save(img_path)
        return count

    def test_directory_scanning_performance(self):
        """Test performance of directory scanning with large number of files."""
        # Create 1000 test images
        num_images = 500
        self.create_test_images(num_images)

        # Measure time for scanning
        start_time = time.time()
        image_files = scan_image_files(self.input_dir)
        duration = time.time() - start_time

        # Verify results
        self.assertEqual(len(image_files), num_images)

        # Check performance (should scan 500 images in less than 2 seconds)
        self.assertLess(duration, 2.0, f"Directory scanning took {duration:.2f}s, exceeding 2s limit")

        # Log performance metrics
        print(f"\nScanned {num_images} images in {duration:.2f}s ({num_images/duration:.2f} images/s)")

    @patch('core.image_processing.validate_image_with_pillow')
    def test_image_processing_performance(self, mock_validate):
        """Test performance of image processing with many images."""
        # Mock image validation to skip actual validation
        mock_validate.return_value = True

        # Create 100 test images
        num_images = 100
        self.create_test_images(num_images)

        # Set up session
        session_file = self.output_dir / "session.json"
        session_manager = SessionManager(session_file)

        # Set up directories and scan for images
        setup_directories(self.config)
        image_files = scan_image_files(self.input_dir)

        # Measure processing time
        start_time = time.time()
        processed = {}

        for i, img_path in enumerate(image_files):
            processed, output_path, text_path = process_image(
                img_path, self.output_dir, self.config.prefix, processed
            )
            # Update session state (simulating real workflow)
            session_manager.update_processed_image(str(img_path), str(output_path))

            # Every 10 images, save session
            if i % 10 == 0:
                session_manager.save(force=True)

        # Force final save
        session_manager.save(force=True)

        duration = time.time() - start_time

        # Check performance (processing 100 images should take less than 10 seconds)
        self.assertLess(duration, 10.0, f"Processing {num_images} images took {duration:.2f}s, exceeding 10s limit")

        # Log performance metrics
        print(f"\nProcessed {num_images} images in {duration:.2f}s ({num_images/duration:.2f} images/s)")

    def test_tag_management_performance(self):
        """Test tag management performance with a large number of tags."""
        # Create a list of many tags
        num_tags = 1000
        tags = [f"test_tag_{i}" for i in range(num_tags)]

        # Set up tags file
        tags_file = self.output_dir / "tags.txt"
        setup_tags_file(tags_file)

        # Create a sample image and its tag file
        self.create_test_images(1)
        image_files = scan_image_files(self.input_dir)

        with patch('core.image_processing.validate_image_with_pillow', return_value=True):
            processed, output_path, text_path = process_image(
                image_files[0], self.output_dir, self.config.prefix, {}
            )

        # Measure time to save many tags
        start_time = time.time()
        save_image_tags(text_path, tags)
        duration_save = time.time() - start_time

        # Check performance (saving 1000 tags should take less than 1 second)
        self.assertLess(duration_save, 1.0, f"Saving {num_tags} tags took {duration_save:.2f}s, exceeding 1s limit")

        # Log performance metrics
        print(f"\nSaved {num_tags} tags in {duration_save:.2f}s ({num_tags/duration_save:.2f} tags/s)")

    def test_session_management_performance(self):
        """Test session management performance with large state."""
        # Create session manager
        session_file = self.output_dir / "session.json"
        session_manager = SessionManager(session_file)

        # Add many processed images to session
        num_images = 1000
        start_time = time.time()

        for i in range(num_images):
            orig_path = f"test_image_{i:04d}.jpg"
            new_path = f"img_{i:04d}.jpg"
            session_manager.update_processed_image(orig_path, new_path)

            # Add some tags
            for j in range(5):  # 5 tags per image
                tag = f"tag_{i%100}_{j}"  # Reuse tags to simulate real usage
                session_manager.add_tag(tag)

            # Update current position
            session_manager.set_current_position(f"img_{i:04d}")

            # Update stats
            session_manager.update_stats(total_images=num_images, processed_images=i+1)

            # Save every 100 images
            if (i+1) % 100 == 0:
                session_manager.save(force=True)

        # Force final save
        session_manager.save(force=True)
        duration = time.time() - start_time

        # Check performance (processing 1000 session updates should take less than 10 seconds)
        self.assertLess(duration, 10.0, f"Session management for {num_images} images took {duration:.2f}s, exceeding 10s limit")

        # Log performance metrics
        print(f"\nManaged session for {num_images} images in {duration:.2f}s ({num_images/duration:.2f} images/s)")

        # Test loading time
        start_time = time.time()
        new_session_manager = SessionManager(session_file)
        load_duration = time.time() - start_time

        # Check loading performance
        self.assertLess(load_duration, 1.0, f"Loading large session took {load_duration:.2f}s, exceeding 1s limit")
        print(f"Loaded large session in {load_duration:.2f}s")


if __name__ == "__main__":
    unittest.main()
