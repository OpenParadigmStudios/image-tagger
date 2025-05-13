#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# API data models

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import re


class Tag(BaseModel):
    """Tag model for API requests and responses."""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None

    @validator('name')
    def name_must_be_valid(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_\-., ]+$', v):
            raise ValueError('Tag name contains invalid characters')
        return v


class TagList(BaseModel):
    """List of tags model for API requests and responses."""
    tags: List[str] = Field(..., min_items=0)

    @validator('tags', each_item=True)
    def tag_must_be_valid(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_\-., ]+$', v):
            raise ValueError('Tag contains invalid characters')
        return v


class ImageInfo(BaseModel):
    """Image information model for API responses."""
    id: str = Field(..., min_length=1)
    original_name: str
    new_name: Optional[str] = None
    path: str
    processed: bool = False
    tags: Optional[List[str]] = None

    @validator('id', 'original_name', 'path')
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
    tags: List[str] = Field(..., min_items=0)


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


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: Dict[str, Any]

    @validator('type')
    def type_must_be_valid(cls, v):
        valid_types = {
            'connect', 'disconnect', 'error', 'session_update',
            'image_update', 'tag_update', 'tags_request', 'tag_add',
            'tag_remove', 'image_tags_update', 'shutdown'
        }
        if v not in valid_types:
            raise ValueError(f'Invalid message type: {v}')
        return v


class ImageRequest(BaseModel):
    """Image request model for API requests."""
    image_id: Optional[str] = None
    position: Optional[int] = None

    @validator('position')
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

    @validator('path')
    def path_must_be_valid(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_\-./\\]+$', v):
            raise ValueError('Path contains invalid characters')
        return v


class BatchTagUpdate(BaseModel):
    """Batch tag update model for API requests."""
    updates: Dict[str, List[str]] = Field(..., min_items=1)

    @validator('updates')
    def updates_must_be_valid(cls, v):
        for path, tags in v.items():
            if not re.match(r'^[a-zA-Z0-9_\-./\\]+$', path):
                raise ValueError(f'Path contains invalid characters: {path}')
            for tag in tags:
                if not re.match(r'^[a-zA-Z0-9_\-., ]+$', tag):
                    raise ValueError(f'Tag contains invalid characters: {tag}')
        return v
