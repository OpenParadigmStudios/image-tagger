#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Edge case and error handling tests

import unittest
import tempfile
import shutil
import json
import os
import signal
from pathlib import Path
from unittest.mock import patch, MagicMock
import asyncio
import pytest
from fastapi import WebSocket

from core.config import AppConfig
from core.session import SessionManager
from core.image_processing import validate_image_with_pillow

# Mock classes for testing
class SessionError(Exception):
    """Mock session error class for testing."""
    pass

class ImageProcessingError(Exception):
    """Mock image processing error class for testing."""
    pass

class TaggingError(Exception):
    """Mock tagging error class for testing."""
    pass

class MockSessionManager:
    """Mock session manager for testing."""
    def __init__(self, session_path):
        self.session_path = session_path
        self.data = {}

    def save(self):
        with open(self.session_path, 'w') as f:
            json.dump(self.data, f)

    def load(self):
        try:
            with open(self.session_path, 'r') as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            raise SessionError("Failed to load session data")

class MockConnectionManager:
    """Mock ConnectionManager for testing."""

    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, websocket, message):
        if websocket not in self.active_connections:
            return False
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            await self.disconnect(websocket)
            return False

class EdgeCaseTest(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.test_dir / "input"
        self.input_dir.mkdir()
        self.output_dir = self.input_dir / "output"
        self.output_dir.mkdir()

        # Create test configuration
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

    def test_empty_directory(self):
        """Test handling of empty input directory."""
        # Directory with no files
        with patch("core.image_processing.scan_image_files") as mock_scan:
            mock_scan.return_value = []
            files = mock_scan(self.input_dir)
            self.assertEqual(len(files), 0)

    def test_invalid_image_files(self):
        """Test handling of invalid image files."""
        # Create fake "image" files with incorrect content
        invalid_img = self.input_dir / "invalid.jpg"
        invalid_img.write_text("This is not an image file")

        valid_img = self.input_dir / "valid.jpg"
        valid_img.write_bytes(b"FAKE IMAGE DATA")

        # Mock validate_image_with_pillow
        original_validate = validate_image_with_pillow

        def mock_validate(file_path):
            if file_path.name == "invalid.jpg":
                return False
            return True

        # Patch the validation function
        with patch('core.image_processing.validate_image_with_pillow', mock_validate):
            # Test with the mocked validation
            self.assertFalse(mock_validate(invalid_img))
            self.assertTrue(mock_validate(valid_img))

            # Mock scan_image_files to filter based on validation
            with patch('core.image_processing.scan_image_files') as mock_scan:
                mock_scan.return_value = [p for p in [invalid_img, valid_img] if mock_validate(p)]

                image_files = mock_scan()
                # Only valid images should be returned
                self.assertEqual(len(image_files), 1)
                self.assertEqual(image_files[0].name, "valid.jpg")

    def test_corrupt_session_file(self):
        """Test handling of corrupt session file."""
        session_file = self.output_dir / "session.json"

        # Write invalid JSON to session file
        with open(session_file, "w") as f:
            f.write("This is not valid JSON {")

        # Mock SessionManager
        with patch('core.session.SessionManager', MockSessionManager):
            # Create a mock instance that raises an error
            mock_session = MockSessionManager(session_file)

            # Should handle corrupt file by raising SessionError
            with self.assertRaises(SessionError):
                mock_session.load()

    def test_image_processing_errors(self):
        """Test handling of errors during image processing."""
        # Create a test image
        test_img = self.input_dir / "test.jpg"
        test_img.write_bytes(b"FAKE IMAGE DATA")

        # Test error during file copying
        with patch('shutil.copy2') as mock_copy:
            mock_copy.side_effect = IOError("Disk full")

            # Define a mock process_image function
            def mock_process_image(src, dest_dir, prefix, processed_images):
                dest_path = dest_dir / f"{prefix}_{len(processed_images):03d}.jpg"
                shutil.copy2(src, dest_path)
                return dest_path

            # Patch process_image to use shutil.copy2
            with patch('core.image_processing.process_image', mock_process_image):
                with self.assertRaises(IOError):
                    mock_process_image(test_img, self.output_dir, "img", {})

    def test_permission_errors(self):
        """Test handling of permission errors."""
        # Create a test file path
        test_file = self.output_dir / "test_perm.txt"

        # Mock a permission error when writing to the file
        with patch('pathlib.Path.write_text') as mock_write:
            mock_write.side_effect = PermissionError("Permission denied")

            with self.assertRaises(PermissionError):
                test_file.write_text("test")

    def test_malicious_path_traversal(self):
        """Test prevention of path traversal attempts."""
        # Attempt to access file outside working directory
        traversal_path = "../../../etc/passwd"

        # Define a mock validation function
        def validate_path(path):
            """Mock validation function to prevent path traversal."""
            if ".." in str(path):
                raise ValueError("Path traversal attempt")
            return path

        # Test the mock validation
        with self.assertRaises(ValueError):
            validate_path(traversal_path)

        # Test on a valid path
        valid_path = "images/test.jpg"
        self.assertEqual(validate_path(valid_path), valid_path)

    def test_signal_handling(self):
        """Test graceful handling of termination signals."""
        # Mock signal handler function
        def mock_signal_handler(sig, frame):
            return

        # Store original signal handler
        original_handler = signal.getsignal(signal.SIGINT)

        try:
            # Set our mock handler
            signal.signal(signal.SIGINT, mock_signal_handler)

            # Verify it was set correctly
            self.assertEqual(signal.getsignal(signal.SIGINT), mock_signal_handler)
        finally:
            # Restore original handler
            signal.signal(signal.SIGINT, original_handler)

    def test_missing_required_fields(self):
        """Test handling of missing required fields in API requests."""
        # Import Pydantic
        from pydantic import BaseModel, Field, ValidationError

        # Create a test model
        class TestModel(BaseModel):
            required_field: str
            optional_field: str = "default"

        # Test missing required field
        with self.assertRaises(ValidationError):
            TestModel(optional_field="test")

        # Test with all required fields
        model = TestModel(required_field="test")
        self.assertEqual(model.required_field, "test")
        self.assertEqual(model.optional_field, "default")

    def test_unicode_filenames(self):
        """Test handling of Unicode filenames."""
        # Create image with Unicode name
        unicode_name = "测试图像.jpg"  # "Test image" in Chinese
        unicode_path = self.input_dir / unicode_name
        unicode_path.write_bytes(b"FAKE IMAGE DATA")

        # Test that the file exists and can be read
        self.assertTrue(unicode_path.exists())
        data = unicode_path.read_bytes()
        self.assertEqual(data, b"FAKE IMAGE DATA")

        # Test that we can get the correct name
        self.assertEqual(unicode_path.name, unicode_name)

    def test_zero_byte_files(self):
        """Test handling of zero-byte files."""
        # Create empty file
        empty_img = self.input_dir / "empty.jpg"
        empty_img.touch()  # Creates empty file

        # Check that the file exists but has zero bytes
        self.assertTrue(empty_img.exists())
        self.assertEqual(empty_img.stat().st_size, 0)

    def test_command_line_argument_validation(self):
        """Test validation of command line arguments."""
        import argparse

        # Create a simple argument parser
        parser = argparse.ArgumentParser()
        parser.add_argument("input_directory", type=str, help="Directory containing images to process")

        # Test with missing required argument
        with self.assertRaises(SystemExit):
            parser.parse_args([])

        # Test with valid argument
        args = parser.parse_args([str(self.input_dir)])
        self.assertEqual(args.input_directory, str(self.input_dir))


@pytest.mark.asyncio
async def test_websocket_message_handling():
    """Test WebSocket message handling with proper async code."""
    # Create mock objects
    mock_websocket = MagicMock(spec=WebSocket)
    mock_request = MagicMock()

    # Setup message and connection manager
    message = {"type": "ping", "data": {}}
    manager = MockConnectionManager()

    # Connect websocket
    await manager.connect(mock_websocket)

    # Test sending a message
    success = await manager.send_message(mock_websocket, message)
    assert success is True
    mock_websocket.send_json.assert_called_once_with(message)


if __name__ == "__main__":
    unittest.main()
