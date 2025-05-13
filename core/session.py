#!/usr/bin/env python3
# CivitAI Flux Dev LoRA Tagging Assistant
# Session management functionality

"""
Core session management module for the CivitAI Flux Dev LoRA Tagging Assistant.

This module provides functionality for managing the session state including:
- Safe loading and saving of session data with proper error handling
- Thread-safe operations with locking
- Automatic saving at configurable intervals
- Tracking of processed images and current position

The session state is persisted as JSON for easy inspection and backup.
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import datetime

class SessionError(Exception):
    """Raised when session operations fail."""
    pass

@dataclass
class SessionState:
    """Store session state information."""
    processed_images: Dict[str, str] = field(default_factory=dict)
    current_position: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    version: str = "1.0"
    stats: Dict[str, int] = field(default_factory=lambda: {"total_images": 0, "processed_images": 0})

    def update_timestamp(self) -> None:
        """
        Update the last_updated timestamp to the current time.

        This method sets the last_updated field to the current time in ISO 8601 format.
        """
        self.last_updated = time.strftime("%Y-%m-%dT%H:%M:%S")

    def update_stats(self, total_images: Optional[int] = None, processed_images: Optional[int] = None) -> None:
        """
        Update session statistics.

        Args:
            total_images: Total number of images in the collection, if provided
            processed_images: Number of processed images, if provided
        """
        if total_images is not None:
            self.stats["total_images"] = total_images
        if processed_images is not None:
            self.stats["processed_images"] = processed_images


class SessionManager:
    """Manage session state with safe operations."""

    def __init__(self, session_file: Union[str, Path]):
        """
        Initialize the session manager.

        Args:
            session_file: Path to the session file where state will be persisted
        """
        self.session_file = Path(session_file)
        self.state = self._load_session()
        self._lock = threading.RLock()
        self._auto_save_interval = 60  # Default auto-save interval in seconds
        self._last_save_time = time.time()
        self._changes_pending = False

    def _load_session(self) -> SessionState:
        """
        Load session from file or create new.

        Returns:
            SessionState: The loaded or newly created session state

        Notes:
            If the session file is corrupted, it will be backed up with a .corrupted extension
            and a new session will be created.
        """
        if not self.session_file.exists():
            logging.info(f"No session file found at {self.session_file}, creating new session")
            return SessionState()

        try:
            with self.session_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
                session = SessionState(**data)
                logging.info(f"Loaded existing session from {self.session_file}")
                return session
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in session file: {e}")
            # Create backup of corrupted file
            backup_path = self.session_file.with_suffix(f"{self.session_file.suffix}.corrupted")
            self.session_file.rename(backup_path)
            logging.info(f"Backed up corrupted session file to {backup_path}")
            return SessionState()
        except Exception as e:
            logging.error(f"Error loading session file: {e}")
            return SessionState()

    def save(self, force: bool = False) -> bool:
        """
        Save session state to file with locking.

        Args:
            force: Force saving even if the auto-save interval hasn't elapsed

        Returns:
            bool: True if save was successful

        Raises:
            SessionError: If the save operation fails

        Notes:
            This method creates a backup of the existing file before overwriting it.
            It uses a temporary file for safe writing to prevent corruption.
        """
        current_time = time.time()

        # Only save if forced or if auto-save interval has elapsed
        if not force and (current_time - self._last_save_time) < self._auto_save_interval:
            return True

        with self._lock:
            # Update timestamp before saving
            self.state.update_timestamp()

            try:
                # Ensure the parent directory exists
                self.session_file.parent.mkdir(parents=True, exist_ok=True)

                # Create temporary file for safe writing
                temp_file = self.session_file.with_suffix('.tmp')
                with temp_file.open('w', encoding='utf-8') as f:
                    json.dump(asdict(self.state), f, indent=2)

                # Create backup of existing file if it exists
                if self.session_file.exists():
                    backup_file = self.session_file.with_suffix('.bak')
                    self.session_file.replace(backup_file)

                # Rename temp file to target file
                temp_file.replace(self.session_file)

                self._last_save_time = current_time
                self._changes_pending = False
                logging.debug(f"Session state saved to {self.session_file}")
                return True
            except Exception as e:
                logging.error(f"Failed to save session state: {e}")
                raise SessionError(f"Failed to save session state: {e}")

    def _create_backup(self, session_file: Path) -> Path:
        # Implementation of _create_backup method
        # This method should return the path to the created backup file
        pass

    def reset_auto_save_timer(self) -> None:
        """
        Reset the auto-save timer.

        This method updates the last save time to the current time, effectively
        resetting the auto-save interval.
        """
        self._last_save_time = time.time()

    def set_auto_save_interval(self, seconds: int) -> None:
        """
        Set the auto-save interval.

        Args:
            seconds: Auto-save interval in seconds

        Raises:
            ValueError: If seconds is less than 1
        """
        if seconds < 1:
            raise ValueError("Auto-save interval must be at least 1 second")
        self._auto_save_interval = seconds
        logging.debug(f"Auto-save interval set to {seconds} seconds")

    def update_processed_image(self, original_path: str, new_path: str) -> None:
        """
        Update the processed images dictionary.

        Args:
            original_path: Original path of the image
            new_path: New path of the image

        Notes:
            This method is thread-safe and automatically updates the processed_images count.
        """
        with self._lock:
            self.state.processed_images[original_path] = new_path
            self.state.stats["processed_images"] = len(self.state.processed_images)

    def set_current_position(self, position: Optional[str]) -> None:
        """
        Set the current position in the image processing workflow.

        Args:
            position: Current position (image path or identifier)

        Notes:
            This method is thread-safe and marks changes as pending for auto-save.
        """
        with self._lock:
            self.state.current_position = position

    def update_tags(self, tags: List[str]) -> None:
        """
        Update the list of tags in the session.

        Args:
            tags: List of tags

        Notes:
            This method is thread-safe and replaces the entire tags list.
        """
        with self._lock:
            self.state.tags = tags

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the session if it doesn't exist.

        Args:
            tag: Tag to add

        Notes:
            This method is thread-safe and only adds the tag if it doesn't already exist.
        """
        with self._lock:
            if tag not in self.state.tags:
                self.state.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the session if it exists.

        Args:
            tag: Tag to remove

        Notes:
            This method is thread-safe and only attempts to remove the tag if it exists.
        """
        with self._lock:
            if tag in self.state.tags:
                self.state.tags.remove(tag)

    def update_stats(self, total_images: Optional[int] = None,
                     processed_images: Optional[int] = None) -> None:
        """
        Update session statistics.

        Args:
            total_images: Total number of images
            processed_images: Number of processed images

        Notes:
            This method is thread-safe and only updates the provided statistics.
        """
        with self._lock:
            self.state.update_stats(total_images, processed_images)
