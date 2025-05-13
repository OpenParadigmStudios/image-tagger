#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# API data models

from typing import List, Optional, Dict
from pydantic import BaseModel


class Tag(BaseModel):
    """Tag model for API requests and responses."""
    name: str
    description: Optional[str] = None


class TagList(BaseModel):
    """List of tags model for API requests and responses."""
    tags: List[str]


class ImageInfo(BaseModel):
    """Image information model for API responses."""
    id: str
    original_name: str
    new_name: Optional[str] = None
    path: str
    processed: bool = False


class ImageList(BaseModel):
    """List of images model for API responses."""
    images: List[ImageInfo]
    total: int


class ImageTags(BaseModel):
    """Image tags model for API requests and responses."""
    image_id: str
    tags: List[str]


class SessionStatus(BaseModel):
    """Session status model for API responses."""
    status: str
    total_images: int
    processed_images: int
    current_position: Optional[str] = None
    last_updated: str


class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: Dict
