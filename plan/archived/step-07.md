# Step 7: Code Refactoring and Integration

## Overview
This step focuses on code quality, reducing technical debt, and creating a cohesive integrated application. We'll consolidate duplicate code, improve error handling, and ensure all components work together seamlessly.

## Objectives
1. Resolve code duplication between `civitai_tagger.py` and modular components
2. Improve error handling across component boundaries
3. Implement graceful shutdown and cleanup
4. Complete the end-to-end workflow
5. Optimize performance in critical sections
6. Enhance security throughout the application

## Code Restructuring Tasks

### 1. Move Functionality from civitai_tagger.py to Modules
Currently, much of the core functionality is in `civitai_tagger.py` while newer components are properly modularized. This leads to duplication and potential inconsistencies.

#### Action Plan:
- Move remaining file operations from `civitai_tagger.py` to `core/filesystem.py`
- Ensure consistency in function signatures and behavior
- Update imports across the codebase
- Add proper type hints and docstrings to all functions
- Remove duplicated code after successful migration

```python
# Example refactoring approach - moving functionality
# From civitai_tagger.py to core/filesystem.py

# In core/filesystem.py
def process_image(
    original_path: Path,
    output_dir: Path,
    prefix: str,
    processed_images: Dict[str, str]
) -> Tuple[Dict[str, str], Path, Path]:
    """Process a single image file.

    Args:
        original_path: Path to the original image
        output_dir: Path to the output directory
        prefix: Filename prefix for renamed images
        processed_images: Dictionary of already processed images

    Returns:
        Tuple containing:
        - Updated processed_images dictionary
        - Path to the copied image file
        - Path to the created text file
    """
    # Implementation moved from civitai_tagger.py
    ...

```

### 2. Improve SessionState Management
The current SessionState handling is scattered across multiple modules and needs consolidation.

#### Action Plan:
- Create a dedicated module for session management
- Implement atomic updates with proper locking
- Add session validation
- Enhance session recovery for interrupted processes

```python
# In core/session.py
class SessionManager:
    """Manage session state with safe operations."""

    def __init__(self, session_file: Path):
        self.session_file = session_file
        self.state = self._load_session()
        self._lock = threading.Lock()

    def _load_session(self) -> SessionState:
        """Load session from file or create new."""
        ...

    def save(self) -> bool:
        """Save session state to file with locking."""
        with self._lock:
            # Safe file writing logic
            ...
```

### 3. Improve Error Handling

#### Action Plan:
- Implement consistent error handling patterns
- Add proper exception types for different error conditions
- Create error recovery strategies for critical operations
- Ensure proper error propagation to UI

```python
# Custom exception types
class ImageProcessingError(Exception):
    """Raised when image processing fails."""
    pass

class SessionError(Exception):
    """Raised when session operations fail."""
    pass

# Example error handling pattern
def process_with_recovery(func, *args, max_retries=3, **kwargs):
    """Execute a function with automatic retry on failure."""
    retries = 0
    while retries < max_retries:
        try:
            return func(*args, **kwargs)
        except (IOError, OSError) as e:
            retries += 1
            if retries >= max_retries:
                raise
            time.sleep(0.5)  # Back off before retry
    raise RuntimeError(f"Failed after {max_retries} retries")
```

### 4. Enhance WebSocket Communication

#### Action Plan:
- Implement proper connection management with reconnection logic
- Add message validation and error handling
- Create a more consistent message format for all operations
- Implement proper message queuing for reliable delivery

```javascript
// In websocket.js
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.socket = null;
        this.messageQueue = [];
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectTimeoutId = null;
        this.eventHandlers = {};
    }

    connect() {
        // Connection logic with reconnection
        ...
    }

    send(message) {
        // Send with queueing for reliability
        if (this.connected) {
            this.socket.send(JSON.stringify(message));
        } else {
            this.messageQueue.push(message);
        }
    }

    // Other methods...
}
```

### 5. Consolidate API Models
The current API models are spread across different files, which makes them hard to maintain.

#### Action Plan:
- Centralize all API models in `models/api.py`
- Ensure consistency in model design
- Add proper validation for all fields
- Create documentation for API models

```python
# In models/api.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional
import re

class ImageInfo(BaseModel):
    """Information about an image file."""
    original_path: str
    output_path: str
    tag_file_path: str

    @validator('original_path', 'output_path', 'tag_file_path')
    def paths_must_be_valid(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_\-./\\]+$', v):
            raise ValueError('Path contains invalid characters')
        return v

class TagUpdate(BaseModel):
    """Model for tag update operations."""
    image_id: str = Field(..., min_length=1)
    tags: List[str] = Field(..., min_items=0)

    @validator('tags', each_item=True)
    def tag_must_be_valid(cls, v):
        if not v or not re.match(r'^[a-zA-Z0-9_\-., ]+$', v):
            raise ValueError('Tag contains invalid characters')
        return v
```

### 6. Implement Graceful Shutdown

#### Action Plan:
- Add proper signal handlers for SIGINT and SIGTERM
- Implement resource cleanup on shutdown
- Ensure all data is saved before shutdown
- Notify connected clients of shutdown

```python
# In server/main.py
def setup_signal_handlers(app_state):
    """Set up signal handlers for graceful shutdown."""
    def handle_shutdown(sig, frame):
        logging.info(f"Received signal {sig}, shutting down...")
        # Save session state
        save_session_state(
            app_state["session_file_path"],
            app_state["session_state"]
        )

        # Notify clients
        shutdown_message = {
            "type": "shutdown",
            "data": {"message": "Server shutting down"}
        }
        app_state["connection_manager"].broadcast(
            json.dumps(shutdown_message)
        )

        # Stop the server
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
```

## Integration Tasks

### 1. Complete End-to-End Workflow Testing
Test the complete application workflow from start to finish to ensure all components work together properly.

#### Action Plan:
- Create integration tests covering the entire workflow
- Implement test fixtures for reproducible testing
- Test image processing, tag management, and session handling
- Verify client-server communication

### 2. Security Enhancements

#### Action Plan:
- Implement input validation for all user inputs
- Add path traversal protection for file operations
- Use secure HTTP headers for FastAPI responses
- Sanitize file paths to prevent injection attacks

### 3. Performance Optimization

#### Action Plan:
- Profile code to identify bottlenecks
- Optimize image handling for better performance
- Improve WebSocket performance for large tag sets
- Optimize session state handling for faster operations

## Testing Strategy

1. Unit Tests:
   - Create or update tests for all refactored functions
   - Ensure high coverage for core functionality
   - Test error handling paths

2. Integration Tests:
   - Test complete workflow from end to end
   - Test client-server communication
   - Test session persistence and recovery

3. Stress/Performance Tests:
   - Test with large tag sets
   - Test with large image directories
   - Test with multiple concurrent connections

## Completion Criteria
- Code duplication resolved
- All functionality properly modularized
- End-to-end workflow tested and working
- Error handling improved across all components
- Graceful shutdown implemented
- Performance optimized for key operations
- Documentation updated to reflect changes
