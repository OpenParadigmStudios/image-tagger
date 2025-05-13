#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# API data models

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re
from datetime import datetime
from enum import Enum


class Tag(BaseModel):
    """Tag model for API requests and responses."""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def name_must_be_valid(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_\-., ]+$', v):
            raise ValueError('Tag name contains invalid characters')
        return v


class TagList(BaseModel):
    """List of tags model for API requests and responses."""
    tags: List[str] = Field(..., min_length=0)

    @field_validator('tags')
    @classmethod
    def tags_must_be_valid(cls, v):
        for tag in v:
            if not tag or not re.match(r'^[a-zA-Z0-9_\-., ]+$', tag):
                raise ValueError(f'Tag contains invalid characters: {tag}')
        return v


class ImageInfo(BaseModel):
    """Image information model for API responses."""
    id: str = Field(..., min_length=1)
    original_name: str
    new_name: Optional[str] = None
    path: str
    processed: bool = False
    tags: Optional[List[str]] = None

    @field_validator('id', 'original_name', 'path')
    @classmethod
    def path_must_be_valid(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_\-./\\]+$', v):
            raise ValueError('Path contains invalid characters')
        return v


class ImageList(BaseModel):
    """List of images model for API responses."""
    images: List[ImageInfo]
    total: int
    current_position: Optional[str] = None


class ImageTags(BaseModel):
    """Image tags model for API requests and responses."""
    image_id: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)


class TagUpdate(BaseModel):
    """Model for tag update operations."""
    image_id: str = Field(..., min_length=1)
    tags: List[str] = Field(..., min_length=0)


class SessionStatus(BaseModel):
    """Session status model for API responses."""
    status: str
    total_images: int
    processed_images: int
    current_position: Optional[str] = None
    last_updated: str


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    code: Optional[str] = None
    path: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response model."""
    detail: str
    data: Optional[Dict[str, Any]] = None


class WebSocketMessageType(str, Enum):
    """Types of WebSocket messages."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    HEARTBEAT = "heartbeat"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    IMAGE_UPDATE = "image_update"
    IMAGE_DATA = "image_data"
    GET_IMAGE = "get_image"
    TAGS_UPDATE = "tags_update"
    TAGS_REPLACED = "tags_replaced"
    GET_TAGS = "get_tags"
    SESSION_TAGS_UPDATED = "session_tags_updated"
    STATS_UPDATE = "stats_update"
    SESSION_UPDATE = "session_update"
    SESSION_REQUEST = "session_request"
    SAVE_SESSION = "save_session"
    SESSION_SAVED = "session_saved"
    NOTIFICATION = "notification"
    SHUTDOWN = "shutdown"
    UPDATE_TAGS = "update_tags"
    TAG_UPDATE = "tag_update"
    TAGS_SAVED = "tags_saved"


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: Dict[str, Any]

    @field_validator('type')
    @classmethod
    def type_must_be_valid(cls, v):
        # Validate message type against enum values
        if v not in [e.value for e in WebSocketMessageType]:
            raise ValueError(f'Invalid message type: {v}')
        return v


class ImageRequest(BaseModel):
    """Image request model for API requests."""
    image_id: Optional[str] = None
    position: Optional[int] = None

    @field_validator('position')
    @classmethod
    def position_must_be_valid(cls, v):
        if v is not None and v < 0:
            raise ValueError('Position must be a non-negative integer')
        return v


class TagSearchRequest(BaseModel):
    """Tag search request model for API requests."""
    query: str = Field(..., min_length=1)
    case_sensitive: bool = False


class PathRequest(BaseModel):
    """Path request model for API requests."""
    path: str = Field(..., min_length=1)

    @field_validator('path')
    @classmethod
    def path_must_be_valid(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_\-./\\]+$', v):
            raise ValueError('Path contains invalid characters')
        return v


class BatchTagUpdate(BaseModel):
    """Batch tag update model for API requests."""
    updates: Dict[str, List[str]] = Field(..., min_length=1)

    @field_validator('updates')
    @classmethod
    def updates_must_be_valid(cls, v):
        for path, tags in v.items():
            if not re.match(r'^[a-zA-Z0-9_\-./\\]+$', path):
                raise ValueError(f'Path contains invalid characters: {path}')
            for tag in tags:
                if not re.match(r'^[a-zA-Z0-9_\-., ]+$', tag):
                    raise ValueError(f'Tag contains invalid characters: {tag}')
        return v


class TagsList(BaseModel):
    """List of tags."""
    tags: List[str] = []


class TagsUpdate(BaseModel):
    """Tags update data."""
    tags: List[str] = []


class SessionStats(BaseModel):
    """Statistics about the current session."""
    total_images: int = 0
    processed_images: int = 0
    remaining_images: int = 0
    percent_complete: float = 0.0

    @field_validator("percent_complete", mode="before")
    @classmethod
    def calculate_percent(cls, v, info):
        """Calculate the percentage of completion."""
        values = info.data
        total = values.get("total_images", 0)
        processed = values.get("processed_images", 0)
        if total > 0:
            return round((processed / total) * 100, 2)
        return 0.0

    @field_validator("remaining_images", mode="before")
    @classmethod
    def calculate_remaining(cls, v, info):
        """Calculate the number of remaining images."""
        values = info.data
        total = values.get("total_images", 0)
        processed = values.get("processed_images", 0)
        return max(0, total - processed)


class SessionInfo(BaseModel):
    """Information about the current session."""
    current_position: Optional[str] = None
    last_updated: Optional[str] = None
    stats: SessionStats = Field(default_factory=SessionStats)
    version: str = "1.0"
