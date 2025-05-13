#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# API models tests

import unittest
from pydantic import ValidationError
import pytest
from models.api import (
    Tag,
    TagList,
    ImageInfo,
    ImageList,
    ImageTags,
    TagUpdate,
    SessionStatus,
    ErrorResponse,
    SuccessResponse,
    WebSocketMessage,
    ImageRequest,
    TagSearchRequest,
    PathRequest,
    BatchTagUpdate
)

class ApiModelsTest(unittest.TestCase):
    """Test validation and behavior of API models."""

    def test_tag_model(self):
        """Test Tag model validation."""
        # Valid case
        valid_tag = Tag(name="test_tag")
        self.assertEqual(valid_tag.name, "test_tag")

        # Test with invalid tag name
        with self.assertRaises(ValidationError):
            Tag(name="<script>alert('xss')</script>")

    def test_tag_update_validation(self):
        """Test TagUpdate model validation."""
        # Valid case
        valid_update = TagUpdate(image_id="test_image", tags=["tag1", "tag2"])
        self.assertEqual(valid_update.image_id, "test_image")
        self.assertEqual(valid_update.tags, ["tag1", "tag2"])

        # Test with invalid image_id (empty)
        with self.assertRaises(ValidationError):
            TagUpdate(image_id="", tags=["tag1", "tag2"])

    def test_image_identifier_validation(self):
        """Test ImageInfo model validation."""
        # Valid case
        valid_id = ImageInfo(id="test_image_123", original_name="test.jpg", path="images/test.jpg")
        self.assertEqual(valid_id.id, "test_image_123")

        # Test with invalid ID (empty)
        with self.assertRaises(ValidationError):
            ImageInfo(id="", original_name="test.jpg", path="images/test.jpg")

        # Test with invalid path containing special characters
        with self.assertRaises(ValidationError):
            ImageInfo(id="test_image", original_name="test.jpg", path="<script>alert('xss')</script>")

    def test_status_response(self):
        """Test SuccessResponse model."""
        status = SuccessResponse(detail="Operation completed")
        self.assertEqual(status.detail, "Operation completed")
        self.assertIsNone(status.data)

    def test_error_response(self):
        """Test ErrorResponse model."""
        error = ErrorResponse(
            detail="Operation failed",
            code="VALIDATION_ERROR",
            path="tags"
        )
        self.assertEqual(error.detail, "Operation failed")
        self.assertEqual(error.code, "VALIDATION_ERROR")
        self.assertEqual(error.path, "tags")

    def test_image_list_response(self):
        """Test ImageList model."""
        images = [
            ImageInfo(id="img_001", original_name="image1.jpg", path="images/image1.jpg"),
            ImageInfo(id="img_002", original_name="image2.jpg", path="images/image2.jpg"),
            ImageInfo(id="img_003", original_name="image3.jpg", path="images/image3.jpg")
        ]
        response = ImageList(images=images, total=len(images), current_position="img_001")
        self.assertEqual(response.total, 3)
        self.assertEqual(len(response.images), 3)
        self.assertEqual(response.current_position, "img_001")

    def test_tag_operation_response(self):
        """Test TagList model."""
        response = TagList(tags=["tag1", "tag2"])
        self.assertEqual(len(response.tags), 2)
        self.assertIn("tag1", response.tags)
        self.assertIn("tag2", response.tags)

    def test_session_status_response(self):
        """Test SessionStatus model."""
        response = SessionStatus(
            status="active",
            total_images=10,
            processed_images=3,
            current_position="img_003",
            last_updated="2023-05-13T12:34:56"
        )
        self.assertEqual(response.status, "active")
        self.assertEqual(response.total_images, 10)
        self.assertEqual(response.processed_images, 3)
        self.assertEqual(response.current_position, "img_003")

    def test_websocket_message(self):
        """Test WebSocketMessage model validation."""
        # Valid message
        valid_msg = WebSocketMessage(
            type="image_update",
            data={"image_id": "test_image", "tags": ["tag1", "tag2"]}
        )
        self.assertEqual(valid_msg.type, "image_update")
        self.assertEqual(valid_msg.data["image_id"], "test_image")

        # Invalid message type
        with self.assertRaises(ValidationError):
            WebSocketMessage(type="invalid_type", data={})

    def test_image_request(self):
        """Test ImageRequest model."""
        # Valid requests
        req1 = ImageRequest(image_id="img_001")
        self.assertEqual(req1.image_id, "img_001")
        self.assertIsNone(req1.position)

        req2 = ImageRequest(position=5)
        self.assertEqual(req2.position, 5)
        self.assertIsNone(req2.image_id)

        # Test with invalid position
        with self.assertRaises(ValidationError):
            ImageRequest(position=-1)

    def test_tag_search_request(self):
        """Test TagSearchRequest model."""
        req = TagSearchRequest(query="nature")
        self.assertEqual(req.query, "nature")
        self.assertFalse(req.case_sensitive)

        req_case = TagSearchRequest(query="Nature", case_sensitive=True)
        self.assertEqual(req_case.query, "Nature")
        self.assertTrue(req_case.case_sensitive)

    def test_path_request(self):
        """Test PathRequest model."""
        # Valid path
        req = PathRequest(path="images/test")
        self.assertEqual(req.path, "images/test")

        # Invalid path
        with self.assertRaises(ValidationError):
            PathRequest(path="")

        with self.assertRaises(ValidationError):
            PathRequest(path="<script>alert('xss')</script>")

    def test_batch_tag_update(self):
        """Test BatchTagUpdate model."""
        # Valid update
        updates = {
            "img_001": ["tag1", "tag2"],
            "img_002": ["tag3", "tag4"]
        }
        batch = BatchTagUpdate(updates=updates)
        self.assertEqual(batch.updates["img_001"], ["tag1", "tag2"])
        self.assertEqual(batch.updates["img_002"], ["tag3", "tag4"])

        # Invalid update (invalid path with special characters)
        with self.assertRaises(ValidationError):
            BatchTagUpdate(updates={"path<with>invalid*chars": ["tag1"]})

        # Invalid update (invalid tag)
        with self.assertRaises(ValidationError):
            BatchTagUpdate(updates={"img_001": ["<script>alert('xss')</script>"]})


if __name__ == "__main__":
    unittest.main()
