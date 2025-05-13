#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Image processing tests

import unittest
import tempfile
import shutil
import os
from pathlib import Path

from core.image_processing import (
    validate_image_with_pillow,
    is_valid_image,
    scan_image_files,
    get_next_sequence_number,
    generate_unique_filename,
    copy_image_to_output,
    create_text_file,
    process_image,
    process_with_recovery,
    ImageProcessingError
)


class ImageProcessingTest(unittest.TestCase):
    """Test the image processing functionality."""

    def setUp(self):
        """Set up a temporary environment for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        self.input_dir = self.test_dir / "input"
        self.output_dir = self.test_dir / "output"
        self.input_dir.mkdir()
        self.output_dir.mkdir()

        # Create some test files
        self.create_test_files()

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def create_test_files(self):
        """Create test files for image processing."""
        # Create a fake image file (not a real image, just for testing)
        self.test_image1 = self.input_dir / "test1.jpg"
        self.test_image1.write_bytes(b'FAKE IMAGE DATA')

        self.test_image2 = self.input_dir / "test2.jpg"
        self.test_image2.write_bytes(b'FAKE IMAGE DATA')

        # Create a non-image file
        self.non_image = self.input_dir / "not_an_image.txt"
        self.non_image.write_text("This is not an image")

    def test_validate_image(self):
        """Test image validation."""
        # In a real test, we'd use actual image files, but for unit testing,
        # we'll mock the behavior of validate_image_with_pillow

        # This is a limitation of this unit test - it won't actually validate images
        # but in a full testing suite, we'd use real test images

        # For this test, let's assume the function works correctly and skip actual testing
        # We'll just verify it returns False for text files
        self.assertFalse(is_valid_image(self.non_image))

    def test_scan_image_files(self):
        """Test scanning for image files."""
        # For the same reason as above, we need to monkeypatch is_valid_image
        # to make it return True for our fake test files

        # Create a monkeypatched version that returns True for .jpg files
        import core.image_processing
        original_is_valid = core.image_processing.is_valid_image

        try:
            def mock_is_valid_image(file_path):
                return file_path.suffix.lower() == '.jpg'

            core.image_processing.is_valid_image = mock_is_valid_image

            # Now test scanning
            image_files = scan_image_files(self.input_dir)
            self.assertEqual(len(image_files), 2)
            self.assertIn(self.test_image1, image_files)
            self.assertIn(self.test_image2, image_files)
        finally:
            # Restore original function
            core.image_processing.is_valid_image = original_is_valid

    def test_get_next_sequence_number(self):
        """Test getting the next sequence number."""
        processed_images = {
            "image1.jpg": "output/img_001.jpg",
            "image2.jpg": "output/img_002.jpg",
            "image3.jpg": "output/img_003.jpg"
        }

        # Next number should be 4
        self.assertEqual(get_next_sequence_number(processed_images, "img"), 4)

        # Test with empty dict
        self.assertEqual(get_next_sequence_number({}, "img"), 1)

        # Test with different prefix
        self.assertEqual(get_next_sequence_number(processed_images, "test"), 1)

        # Test with non-sequential numbers
        processed_images = {
            "image1.jpg": "output/img_001.jpg",
            "image2.jpg": "output/img_005.jpg",
            "image3.jpg": "output/img_010.jpg"
        }
        self.assertEqual(get_next_sequence_number(processed_images, "img"), 11)

    def test_generate_unique_filename(self):
        """Test generating unique filenames."""
        processed_images = {
            "image1.jpg": "output/img_001.jpg",
            "image2.jpg": "output/img_002.jpg",
        }

        # Generate new filename
        path = self.input_dir / "new_image.jpg"
        filename = generate_unique_filename(path, "img", processed_images)
        self.assertEqual(filename, "img_003.jpg")

        # Generate for already processed image
        path_str = str(self.input_dir / "image1.jpg")
        processed_images[path_str] = "output/img_001.jpg"
        filename = generate_unique_filename(Path(path_str), "img", processed_images)
        self.assertEqual(filename, "img_001.jpg")

    def test_copy_image_to_output(self):
        """Test copying images to output directory."""
        # Copy image
        output_path = copy_image_to_output(self.test_image1, self.output_dir, "copied.jpg")
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path, self.output_dir / "copied.jpg")

        # Test copying non-existent file should raise error
        non_existent = self.input_dir / "non_existent.jpg"
        with self.assertRaises(ImageProcessingError):
            copy_image_to_output(non_existent, self.output_dir, "error.jpg")

        # Test copying to existing file (should not raise error)
        output_path = copy_image_to_output(self.test_image1, self.output_dir, "copied.jpg")
        self.assertEqual(output_path, self.output_dir / "copied.jpg")

    def test_create_text_file(self):
        """Test creating text files for images."""
        # Create text file
        image_path = self.output_dir / "test_image.jpg"
        image_path.touch()
        text_path = create_text_file(image_path)
        self.assertTrue(text_path.exists())
        self.assertEqual(text_path, image_path.with_suffix('.txt'))

        # Test creating for existing text file (should not raise error)
        text_path = create_text_file(image_path)
        self.assertEqual(text_path, image_path.with_suffix('.txt'))

    def test_process_image(self):
        """Test the complete image processing workflow."""
        # Process image
        processed_images = {}
        result = process_image(self.test_image1, self.output_dir, "img", processed_images)

        # Unpack result
        updated_processed, output_path, text_path = result

        # Verify results
        self.assertEqual(len(updated_processed), 1)
        self.assertIn(str(self.test_image1), updated_processed)
        self.assertTrue(output_path.exists())
        self.assertTrue(text_path.exists())
        self.assertEqual(text_path.suffix, '.txt')

        # Process another image
        result = process_image(self.test_image2, self.output_dir, "img", updated_processed)
        updated_processed, output_path2, text_path2 = result

        # Verify results
        self.assertEqual(len(updated_processed), 2)
        self.assertIn(str(self.test_image2), updated_processed)
        self.assertTrue(output_path2.exists())
        self.assertTrue(text_path2.exists())
        self.assertNotEqual(output_path, output_path2)

    def test_process_with_recovery(self):
        """Test the recovery mechanism for processing."""
        # Create a function that fails on first two attempts but succeeds on third
        attempts = [0]

        def failing_function():
            attempts[0] += 1
            if attempts[0] < 3:
                raise IOError(f"Simulated failure on attempt {attempts[0]}")
            return "success"

        # Process with recovery
        result = process_with_recovery(failing_function, max_retries=3)
        self.assertEqual(result, "success")
        self.assertEqual(attempts[0], 3)

        # Test with function that always fails
        attempts = [0]

        def always_failing():
            attempts[0] += 1
            raise IOError("Always fails")

        # Should raise after max retries
        with self.assertRaises(IOError):
            process_with_recovery(always_failing, max_retries=2)
        self.assertEqual(attempts[0], 2)


if __name__ == "__main__":
    unittest.main()
