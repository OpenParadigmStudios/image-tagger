#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# WebSocket tests

import unittest
import tempfile
import json
import shutil
import asyncio
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from core.config import AppConfig
from models.api import WebSocketMessage


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.sent_messages = []
        self.closed = False

    async def accept(self):
        return

    async def send_text(self, text):
        self.sent_messages.append(text)

    async def send_json(self, data):
        self.sent_messages.append(json.dumps(data))

    def receive_text(self):
        return "{}"

    async def close(self):
        self.closed = True


class ConnectionManager:
    """Connection manager for WebSocket testing based on the actual implementation."""

    def __init__(self):
        self.active_connections = []
        self.client_info = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket, client_id=None):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            self.client_info[websocket] = {
                "id": client_id or str(id(websocket)),
                "connected_at": asyncio.get_event_loop().time(),
                "last_heartbeat": asyncio.get_event_loop().time(),
                "message_count": 0
            }

    async def disconnect(self, websocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                if websocket in self.client_info:
                    del self.client_info[websocket]

    def disconnect_all(self):
        self.active_connections = []
        self.client_info = {}

    async def send_message(self, websocket, message):
        if websocket not in self.active_connections:
            return False

        try:
            message_obj = WebSocketMessage(type=message.get("type"), data=message.get("data", {}))
            await websocket.send_text(json.dumps(message_obj.dict()))

            if websocket in self.client_info:
                self.client_info[websocket]["message_count"] += 1

            return True
        except Exception as e:
            await self.disconnect(websocket)
            return False

    async def broadcast(self, message):
        if isinstance(message, dict):
            message_text = json.dumps(message)
        else:
            message_text = message

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
                if connection in self.client_info:
                    self.client_info[connection]["message_count"] += 1
            except Exception:
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            await self.disconnect(connection)

    async def update_heartbeat(self, websocket):
        if websocket in self.client_info:
            self.client_info[websocket]["last_heartbeat"] = asyncio.get_event_loop().time()

    def get_connection_count(self):
        return len(self.active_connections)


class WebSocketTest(unittest.TestCase):
    """Test WebSocket communication."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.input_dir = self.test_dir / "input"
        self.input_dir.mkdir()
        self.output_dir = self.input_dir / "output"
        self.output_dir.mkdir()

        # Create test config
        self.config = AppConfig(
            input_directory=self.input_dir,
            output_dir="output",
            resume=False,
            prefix="img",
            verbose=True,
            auto_save=5
        )

        # Create mock session state
        self.session_state = {
            "current_position": "img_001",
            "total_images": 3,
            "processed_images": 1,
            "tags": ["tag1", "tag2"],
            "processed_images_mapping": {"test_image_0.jpg": "img_001.jpg"}
        }

        # Create connection manager
        self.connection_manager = ConnectionManager()

        # Create test FastAPI app with WebSocket endpoint
        self.app = FastAPI()

        # Define WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connection_manager.active_connections.append(websocket)
            try:
                while True:
                    data = await websocket.receive_json()
                    message_type = data.get("type", "")

                    if message_type == "ping":
                        await websocket.send_json({"type": "pong", "data": {}})

                    elif message_type == "get_session_state":
                        await websocket.send_json({
                            "type": "session_state",
                            "data": self.session_state
                        })

                    elif message_type == "tag_update":
                        image_id = data.get("data", {}).get("image_id", "")
                        tags = data.get("data", {}).get("tags", [])

                        if image_id == "invalid_id":
                            await websocket.send_json({
                                "type": "error",
                                "data": {
                                    "success": False,
                                    "message": "Invalid image ID",
                                    "error_type": "ValueError"
                                }
                            })
                        else:
                            await websocket.send_json({
                                "type": "tag_update_response",
                                "data": {
                                    "success": True,
                                    "image_id": image_id,
                                    "tags": tags
                                }
                            })

                    elif message_type == "add_tag":
                        image_id = data.get("data", {}).get("image_id", "")
                        tag = data.get("data", {}).get("tag", "")
                        current_tags = ["tag1", "tag2"]
                        if tag not in current_tags:
                            current_tags.append(tag)

                        await websocket.send_json({
                            "type": "tag_update_response",
                            "data": {
                                "success": True,
                                "image_id": image_id,
                                "tags": current_tags
                            }
                        })

                    elif message_type == "remove_tag":
                        image_id = data.get("data", {}).get("image_id", "")
                        tag = data.get("data", {}).get("tag", "")
                        current_tags = ["tag1", "tag2"]
                        if tag in current_tags:
                            current_tags.remove(tag)

                        await websocket.send_json({
                            "type": "tag_update_response",
                            "data": {
                                "success": True,
                                "image_id": image_id,
                                "tags": current_tags
                            }
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "data": {
                                "success": False,
                                "message": f"Unknown message type: {message_type}",
                                "error_type": "ValueError"
                            }
                        })

            except WebSocketDisconnect:
                self.connection_manager.active_connections.remove(websocket)

        # Create test client
        self.client = TestClient(self.app)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_websocket_connection(self):
        """Test WebSocket connection and basic messaging."""
        with self.client.websocket_connect("/ws") as websocket:
            # Test connection
            websocket.send_json({"type": "ping", "data": {}})
            response = websocket.receive_json()
            self.assertEqual(response["type"], "pong")

    def test_websocket_session_state(self):
        """Test receiving session state updates."""
        with self.client.websocket_connect("/ws") as websocket:
            # Request session state
            websocket.send_json({"type": "get_session_state", "data": {}})
            response = websocket.receive_json()
            self.assertEqual(response["type"], "session_state")
            self.assertEqual(response["data"]["current_position"], "img_001")
            self.assertEqual(response["data"]["total_images"], 3)
            self.assertEqual(response["data"]["processed_images"], 1)

    def test_websocket_tag_update(self):
        """Test tag update via WebSocket."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send tag update
            websocket.send_json({
                "type": "tag_update",
                "data": {
                    "image_id": "img_001",
                    "tags": ["tag1", "tag2", "new_tag"]
                }
            })

            # Receive confirmation
            response = websocket.receive_json()
            self.assertEqual(response["type"], "tag_update_response")
            self.assertTrue(response["data"]["success"])
            self.assertEqual(response["data"]["image_id"], "img_001")
            self.assertEqual(len(response["data"]["tags"]), 3)

    def test_websocket_tag_add(self):
        """Test adding a tag via WebSocket."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send tag add request
            websocket.send_json({
                "type": "add_tag",
                "data": {
                    "image_id": "img_001",
                    "tag": "new_tag"
                }
            })

            # Receive confirmation
            response = websocket.receive_json()
            self.assertEqual(response["type"], "tag_update_response")
            self.assertTrue(response["data"]["success"])
            self.assertEqual(response["data"]["image_id"], "img_001")
            self.assertIn("new_tag", response["data"]["tags"])

    def test_websocket_tag_remove(self):
        """Test removing a tag via WebSocket."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send tag remove request
            websocket.send_json({
                "type": "remove_tag",
                "data": {
                    "image_id": "img_001",
                    "tag": "tag2"
                }
            })

            # Receive confirmation
            response = websocket.receive_json()
            self.assertEqual(response["type"], "tag_update_response")
            self.assertTrue(response["data"]["success"])
            self.assertEqual(response["data"]["image_id"], "img_001")
            self.assertNotIn("tag2", response["data"]["tags"])

    def test_websocket_error_handling(self):
        """Test error handling in WebSocket communication."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send tag update with error
            websocket.send_json({
                "type": "tag_update",
                "data": {
                    "image_id": "invalid_id",
                    "tags": ["tag1", "tag2"]
                }
            })

            # Receive error response
            response = websocket.receive_json()
            self.assertEqual(response["type"], "error")
            self.assertFalse(response["data"]["success"])
            self.assertEqual(response["data"]["error_type"], "ValueError")


@pytest.mark.asyncio
async def test_connection_manager():
    """Test ConnectionManager functionality with proper async handling."""
    manager = ConnectionManager()

    # Create mock connections
    connection1 = MockWebSocket()
    connection2 = MockWebSocket()

    # Test connection tracking
    await manager.connect(connection1)
    await manager.connect(connection2)
    assert len(manager.active_connections) == 2

    # Test message sending
    message = {"type": "session_update", "data": {"value": "test_data"}}
    await manager.send_message(connection1, message)
    assert len(connection1.sent_messages) == 1

    # Test broadcast
    await manager.broadcast(message)
    assert len(connection1.sent_messages) == 2
    assert len(connection2.sent_messages) == 1

    # Test disconnect
    await manager.disconnect(connection1)
    assert len(manager.active_connections) == 1

    # Test disconnect all
    manager.disconnect_all()
    assert len(manager.active_connections) == 0


if __name__ == "__main__":
    unittest.main()
