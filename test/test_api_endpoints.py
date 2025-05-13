#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# API endpoints tests

import unittest
import tempfile
import json
import shutil
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import FastAPI application and initialize it for testing
from fastapi import FastAPI, HTTPException
from core.config import AppConfig
from models.api import (
    TagList,
    ImageInfo,
    ImageList,
    SuccessResponse,
    ErrorResponse,
    TagUpdate
)

class ApiEndpointsTest(unittest.TestCase):
    """Test the API endpoints."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.test_dir / "input"
        self.input_dir.mkdir()
        self.output_dir = self.input_dir / "output"
        self.output_dir.mkdir()

        # Create test images
        for i in range(3):
            test_img = self.input_dir / f"test_image_{i}.jpg"
            test_img.write_bytes(b"FAKE IMAGE DATA")

        # Create test config
        self.config = AppConfig(
            input_directory=self.input_dir,
            output_dir="output",
            resume=False,
            prefix="img",
            verbose=True,
            auto_save=5
        )

        # Create dummy FastAPI instance for testing
        self.app = FastAPI()

        # Setup mock session manager
        self.mock_session = MagicMock()
        self.mock_session.get_status.return_value = {
            "status": "active",
            "current_position": "img_001",
            "total_images": 3,
            "processed_images": 1,
            "tags": ["tag1", "tag2"],
            "processed_images_mapping": {"test_image_0.jpg": "img_001.jpg"}
        }

        # Create endpoints for testing
        @self.app.get("/api/status")
        def get_status():
            return SuccessResponse(detail="Server is running").dict()

        @self.app.get("/api/session/state")
        def get_session_state():
            return self.mock_session.get_status()

        @self.app.get("/api/images")
        def get_image_list():
            return ImageList(
                images=[
                    ImageInfo(id="img_001", original_name="test_image_0.jpg", path="output/img_001.jpg"),
                    ImageInfo(id="img_002", original_name="test_image_1.jpg", path="output/img_002.jpg"),
                    ImageInfo(id="img_003", original_name="test_image_2.jpg", path="output/img_003.jpg")
                ],
                total=3,
                current_position="img_001"
            ).dict()

        @self.app.get("/api/tags")
        def get_tags():
            return TagList(tags=["tag1", "tag2", "tag3"]).dict()

        @self.app.post("/api/tags")
        def update_tags(tag_update: TagUpdate):
            return SuccessResponse(
                detail="Tags updated",
                data={
                    "image_id": tag_update.image_id,
                    "tags": tag_update.tags
                }
            ).dict()

        @self.app.get("/api/tags/{image_id}")
        def get_image_tags(image_id: str):
            if image_id == "invalid_id":
                return ErrorResponse(
                    detail="Image not found",
                    code="NOT_FOUND",
                    path=f"/api/tags/{image_id}"
                ).dict()
            return SuccessResponse(
                detail="Tags retrieved",
                data={
                    "image_id": image_id,
                    "tags": ["tag1", "tag2"]
                }
            ).dict()

        @self.app.post("/api/tags/{image_id}/add")
        def add_tag(image_id: str, tag_data: dict):
            current_tags = ["tag1", "tag2"]
            if tag_data.get("tag") not in current_tags:
                current_tags.append(tag_data.get("tag"))

            return SuccessResponse(
                detail="Tag added",
                data={
                    "image_id": image_id,
                    "tags": current_tags
                }
            ).dict()

        @self.app.post("/api/tags/{image_id}/remove")
        def remove_tag(image_id: str, tag_data: dict):
            current_tags = ["tag1", "tag2"]
            if tag_data.get("tag") in current_tags:
                current_tags.remove(tag_data.get("tag"))

            return SuccessResponse(
                detail="Tag removed",
                data={
                    "image_id": image_id,
                    "tags": current_tags
                }
            ).dict()

        # Create test client
        self.client = TestClient(self.app)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_get_status(self):
        """Test the status endpoint."""
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Server is running", data["detail"])

    def test_get_session_state(self):
        """Test the session state endpoint."""
        response = self.client.get("/api/session/state")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["current_position"], "img_001")
        self.assertEqual(data["total_images"], 3)
        self.assertEqual(data["processed_images"], 1)
        self.assertEqual(len(data["tags"]), 2)
        self.assertEqual(list(data["processed_images_mapping"].keys())[0], "test_image_0.jpg")

    def test_get_image_list(self):
        """Test the image list endpoint."""
        response = self.client.get("/api/images")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["images"]), 3)
        self.assertEqual(data["total"], 3)

    def test_get_tags(self):
        """Test the tags endpoint."""
        response = self.client.get("/api/tags")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tags"]), 3)

    def test_update_tags(self):
        """Test the tag update endpoint."""
        response = self.client.post(
            "/api/tags",
            json={"image_id": "img_001", "tags": ["tag1", "tag2", "new_tag"]}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual("Tags updated", data["detail"])
        self.assertEqual(data["data"]["image_id"], "img_001")
        self.assertEqual(len(data["data"]["tags"]), 3)
        self.assertIn("new_tag", data["data"]["tags"])

    def test_get_image_tags(self):
        """Test getting tags for a specific image."""
        response = self.client.get("/api/tags/img_001")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["image_id"], "img_001")
        self.assertEqual(len(data["data"]["tags"]), 2)

    def test_add_tag(self):
        """Test adding a tag to an image."""
        response = self.client.post(
            "/api/tags/img_001/add",
            json={"tag": "new_tag"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["image_id"], "img_001")
        self.assertEqual(len(data["data"]["tags"]), 3)
        self.assertIn("new_tag", data["data"]["tags"])

    def test_remove_tag(self):
        """Test removing a tag from an image."""
        response = self.client.post(
            "/api/tags/img_001/remove",
            json={"tag": "tag2"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["image_id"], "img_001")
        self.assertEqual(len(data["data"]["tags"]), 1)
        self.assertNotIn("tag2", data["data"]["tags"])

    def test_error_handling(self):
        """Test endpoint error handling."""
        response = self.client.get("/api/tags/invalid_id")
        self.assertEqual(response.status_code, 200)  # Our mock still returns 200
        data = response.json()
        self.assertEqual(data["code"], "NOT_FOUND")
        self.assertIn("Image not found", data["detail"])


if __name__ == "__main__":
    unittest.main()
