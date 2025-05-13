#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# API data models

from typing import List, Optional, Dict, Any, ClassVar
from pydantic import BaseModel, Field, field_validator, model_validator
import re
from datetime import datetime
from enum import Enum


class Tag(BaseModel):
    """Tag model for API requests and responses.

    Represents a single tag with optional description.
    """
    name: str = Field(
        ...,
        min_length=1,
        description="The tag name, must contain only alphanumeric characters, underscore, dash, dot, comma or space"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description for the tag"
    )

    # Regular expression for validating tag names
    TAG_NAME_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z0-9_\-., ]+$')

    @field_validator('name')
    @classmethod
    def name_must_be_valid(cls, v):
        if not v or not cls.TAG_NAME_PATTERN.match(v):
            raise ValueError('Tag name contains invalid characters')
        return v.strip()  # Strip whitespace from tag names


class TagList(BaseModel):
    """List of tags model for API requests and responses.

    Used for bulk operations on multiple tags.
    """
    tags: List[str] = Field(
        ...,
        min_length=0,
        description="List of tag names"
    )

    @field_validator('tags')
    @classmethod
    def tags_must_be_valid(cls, v):
        for tag in v:
            if not tag or not re.match(r'^[a-zA-Z0-9_\-., ]+$', tag):
                raise ValueError(f'Tag contains invalid characters: {tag}')
        # Remove duplicates and strip whitespace
        return [tag.strip() for tag in dict.fromkeys(v)]


class ImageInfo(BaseModel):
    """Image information model for API responses.

    Contains details about an image file, including its processing status and tags.
    """
    id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the image"
    )
    original_name: str = Field(
        ...,
        description="Original filename of the image"
    )
    new_name: Optional[str] = Field(
        None,
        description="New filename assigned during processing"
    )
    path: str = Field(
        ...,
        description="Path to the image file"
    )
    processed: bool = Field(
        False,
        description="Whether the image has been processed"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="List of tags associated with the image"
    )

    # Regular expression for validating paths
    PATH_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z0-9_\-./\\]+$')

    @field_validator('id', 'original_name', 'path')
    @classmethod
    def path_must_be_valid(cls, v):
        if not v or not cls.PATH_PATTERN.match(v):
            raise ValueError('Path contains invalid characters')
        return v


class ImageList(BaseModel):
    """List of images model for API responses.

    Used for paginated responses of image collections.
    """
    images: List[ImageInfo] = Field(
        ...,
        description="List of image information objects"
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of images in the collection"
    )
    current_position: Optional[str] = Field(
        None,
        description="ID of the current image in the session"
    )


class ImageTags(BaseModel):
    """Image tags model for API requests and responses.

    Associates tags with a specific image.
    """
    image_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the image"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="List of tags associated with the image"
    )

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        # Remove duplicates and validate tag format
        unique_tags = []
        for tag in v:
            if not tag or not re.match(r'^[a-zA-Z0-9_\-., ]+$', tag):
                raise ValueError(f'Tag contains invalid characters: {tag}')
            tag = tag.strip()
            if tag not in unique_tags:
                unique_tags.append(tag)
        return unique_tags


class TagUpdate(BaseModel):
    """Model for tag update operations.

    Used when updating tags for a specific image.
    """
    image_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the image"
    )
    tags: List[str] = Field(
        ...,
        min_length=0,
        description="New list of tags for the image"
    )

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        # Remove duplicates and validate tag format
        return [tag.strip() for tag in dict.fromkeys(v) if tag and re.match(r'^[a-zA-Z0-9_\-., ]+$', tag)]


class SessionStatus(BaseModel):
    """Session status model for API responses.

    Provides information about the current processing session.
    """
    status: str = Field(
        ...,
        description="Current status of the session (e.g., 'active', 'paused', 'completed')"
    )
    total_images: int = Field(
        ...,
        ge=0,
        description="Total number of images in the session"
    )
    processed_images: int = Field(
        ...,
        ge=0,
        description="Number of images processed so far"
    )
    current_position: Optional[str] = Field(
        None,
        description="ID of the current image in the session"
    )
    last_updated: str = Field(
        ...,
        description="Timestamp of when the session was last updated"
    )

    @model_validator(mode='after')
    def validate_counts(self):
        if self.processed_images > self.total_images:
            raise ValueError('Processed images count cannot exceed total images count')
        return self


class ErrorResponse(BaseModel):
    """Error response model.

    Used for API error responses.
    """
    detail: str = Field(
        ...,
        description="Detailed error message"
    )
    code: Optional[str] = Field(
        None,
        description="Error code for programmatic handling"
    )
    path: Optional[str] = Field(
        None,
        description="Path related to the error"
    )


class SuccessResponse(BaseModel):
    """Success response model.

    Used for API success responses.
    """
    detail: str = Field(
        ...,
        description="Success message"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional data returned with the success response"
    )


class WebSocketMessageType(str, Enum):
    """Types of WebSocket messages.

    Defines all possible message types for WebSocket communication.
    """
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
    """WebSocket message model.

    Base model for all WebSocket messages.
    """
    type: str = Field(
        ...,
        description="Type of the WebSocket message"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Data payload of the WebSocket message"
    )

    @field_validator('type')
    @classmethod
    def type_must_be_valid(cls, v):
        # Validate message type against enum values
        if v not in [e.value for e in WebSocketMessageType]:
            raise ValueError(f'Invalid message type: {v}')
        return v


class ImageRequest(BaseModel):
    """Image request model for API requests.

    Used for requesting a specific image.
    """
    image_id: Optional[str] = Field(
        None,
        description="Unique identifier of the image"
    )
    position: Optional[int] = Field(
        None,
        description="Position index of the image in the collection"
    )

    @field_validator('position')
    @classmethod
    def position_must_be_valid(cls, v):
        if v is not None and v < 0:
            raise ValueError('Position must be a non-negative integer')
        return v

    @model_validator(mode='after')
    def validate_request(self):
        # Either image_id or position must be provided
        if self.image_id is None and self.position is None:
            raise ValueError('Either image_id or position must be provided')
        return self


class TagSearchRequest(BaseModel):
    """Tag search request model for API requests.

    Used for searching tags with a query string.
    """
    query: str = Field(
        ...,
        min_length=1,
        description="Search query string"
    )
    case_sensitive: bool = Field(
        False,
        description="Whether the search should be case-sensitive"
    )


class PathRequest(BaseModel):
    """Path request model for API requests.

    Used for operations that require a file system path.
    """
    path: str = Field(
        ...,
        min_length=1,
        description="File system path"
    )

    # Regular expression for validating paths
    PATH_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z0-9_\-./\\]+$')

    @field_validator('path')
    @classmethod
    def path_must_be_valid(cls, v):
        if not v or not cls.PATH_PATTERN.match(v):
            raise ValueError('Path contains invalid characters')
        return v


class BatchTagUpdate(BaseModel):
    """Batch tag update model for API requests.

    Used for updating tags for multiple images at once.
    """
    updates: Dict[str, List[str]] = Field(
        ...,
        min_length=1,
        description="Dictionary mapping image IDs to lists of tags"
    )

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
    """List of tags.

    Simple model containing just a list of tag strings.
    """
    tags: List[str] = Field(
        default_factory=list,
        description="List of tag names"
    )

    def add(self, tag: str) -> bool:
        """Add a tag to the list if it doesn't already exist.

        Args:
            tag: The tag to add

        Returns:
            bool: True if the tag was added, False if it already existed
        """
        if tag not in self.tags:
            self.tags.append(tag)
            return True
        return False

    def remove(self, tag: str) -> bool:
        """Remove a tag from the list if it exists.

        Args:
            tag: The tag to remove

        Returns:
            bool: True if the tag was removed, False if it didn't exist
        """
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False


class TagsUpdate(BaseModel):
    """Tags update data.

    Used for updating the list of tags.
    """
    tags: List[str] = Field(
        default_factory=list,
        description="List of tag names"
    )


class SessionStats(BaseModel):
    """Statistics about the current session.

    Provides numerical metrics about the session progress.
    """
    total_images: int = Field(
        0,
        ge=0,
        description="Total number of images in the session"
    )
    processed_images: int = Field(
        0,
        ge=0,
        description="Number of images processed so far"
    )
    remaining_images: int = Field(
        0,
        ge=0,
        description="Number of images remaining to be processed"
    )
    percent_complete: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of completion (0-100)"
    )

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
    """Information about the current session.

    Comprehensive model with session status and statistics.
    """
    current_position: Optional[str] = Field(
        None,
        description="ID of the current image in the session"
    )
    last_updated: Optional[str] = Field(
        None,
        description="Timestamp of when the session was last updated"
    )
    stats: SessionStats = Field(
        default_factory=SessionStats,
        description="Statistics about the session progress"
    )
    version: str = Field(
        "1.0",
        description="Version of the session format"
    )

    def is_complete(self) -> bool:
        """Check if the session is complete.

        Returns:
            bool: True if all images have been processed, False otherwise
        """
        return (self.stats.processed_images >= self.stats.total_images and
                self.stats.total_images > 0)

    def update_timestamp(self) -> None:
        """Update the last_updated timestamp to the current time."""
        self.last_updated = datetime.now().isoformat()
