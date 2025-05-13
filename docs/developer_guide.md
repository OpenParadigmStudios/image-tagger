# CivitAI Flux Dev LoRA Tagging Assistant - Developer Guide

## Architecture Overview

The CivitAI Tagger application follows a client-server architecture with a Python FastAPI backend and JavaScript front-end. This document provides detailed information about the application architecture, code organization, and development workflow.

### Component Diagram

```
┌────────────────┐           ┌──────────────────────────────────────┐
│                │           │              Server                   │
│   Web Client   │◄─────────►│  (FastAPI + WebSockets + Uvicorn)    │
│                │           │                                      │
└────────────────┘           └──────────────┬───────────────────────┘
                                           │
                                           ▼
                             ┌─────────────────────────────────────┐
                             │            Core Modules             │
                             │                                     │
                             │  ┌───────────┐     ┌────────────┐   │
                             │  │  Session  │     │ Filesystem │   │
                             │  │ Management│     │ Operations │   │
                             │  └───────────┘     └────────────┘   │
                             │                                     │
                             │  ┌───────────┐     ┌────────────┐   │
                             │  │   Image   │     │    Tag     │   │
                             │  │ Processing│     │ Management │   │
                             │  └───────────┘     └────────────┘   │
                             │                                     │
                             └─────────────────────────────────────┘
                                           │
                                           ▼
                             ┌─────────────────────────────────────┐
                             │          Data Storage               │
                             │                                     │
                             │  ┌───────────┐     ┌────────────┐   │
                             │  │  Images   │     │Session State│   │
                             │  │           │     │             │   │
                             │  └───────────┘     └────────────┘   │
                             │                                     │
                             │  ┌───────────┐                      │
                             │  │ Tag Files │                      │
                             │  │           │                      │
                             │  └───────────┘                      │
                             │                                     │
                             └─────────────────────────────────────┘
```

### Data Flow

1. User starts the application with a directory path
2. Server initializes and scans the directory for images
3. Client connects to the server via WebSocket and HTTP
4. User browses images and adds/removes tags
5. Tags are sent to the server and saved to corresponding text files
6. Session state is maintained on the server and persisted to disk

## Project Structure

The project follows a modular structure with clear separation of concerns:

```
civitai_tagger/
├── main.py                  # Entry point
├── core/                    # Core functionality
│   ├── config.py            # Configuration handling
│   ├── filesystem.py        # File system operations
│   ├── image_processing.py  # Image handling
│   ├── session.py           # Session management
│   └── tagging.py           # Tag management
├── server/                  # Server implementation
│   ├── main.py              # FastAPI server setup
│   ├── state.py             # Application state
│   └── routers/             # API endpoints
│       ├── images.py        # Image endpoints
│       ├── tags.py          # Tag endpoints
│       └── websocket.py     # WebSocket handling
├── models/                  # Data models
│   ├── config.py            # Configuration models
│   ├── session.py           # Session state models
│   └── api.py               # API models
├── static/                  # Web client
│   ├── index.html           # Main HTML page
│   ├── css/                 # CSS styles
│   └── js/                  # JavaScript modules
│       ├── api.js           # API client
│       ├── websocket.js     # WebSocket client
│       ├── imageViewer.js   # Image viewing
│       ├── tagManager.js    # Tag management
│       ├── sessionManager.js # Session control
│       └── app.js           # Main application
└── test/                    # Test files
    ├── test_filesystem.py   # Filesystem tests
    ├── test_api_models.py   # API model tests
    └── ...                  # Other test files
```

## Development Environment Setup

### Prerequisites

- Python 3.8+
- UV package manager (recommended)
- Git for version control
- A modern IDE with Python support (VS Code, Cursor IDE, PyCharm)

### Setting Up the Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/username/civitai-tagger.git
   cd civitai-tagger
   ```

2. Create a virtual environment using UV:
   ```bash
   uv venv
   ```

3. Activate the virtual environment:
   ```bash
   # On Unix/macOS
   source .venv/bin/activate

   # On Windows
   .venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

5. Install in development mode:
   ```bash
   pip install -e .
   ```

### Editor Configuration

The project includes VS Code settings in `.vscode/settings.json`:
- Python interpreter path points to the virtual environment
- Editor uses 4 spaces for indentation
- Trailing whitespace is trimmed automatically
- Final newline is added to files

## Core Modules

### Configuration (core/config.py)

Handles command-line arguments and application configuration:
- Uses `argparse` to parse command-line arguments
- Validates input parameters
- Creates `AppConfig` dataclass with application settings
- Sets up logging with appropriate verbosity

```python
# Example usage
from core.config import parse_arguments

config = parse_arguments()
print(f"Input directory: {config.input_directory}")
```

### Filesystem (core/filesystem.py)

Manages file system operations:
- Validates and creates directories
- Scans for image files
- Handles file naming and copying
- Manages tag files
- Provides safe file operations with atomic writes

```python
# Example usage
from core.filesystem import scan_image_files

images = scan_image_files("/path/to/images")
print(f"Found {len(images)} images")
```

### Session Management (core/session.py)

Handles session state and persistence:
- Tracks processing progress
- Persists state to JSON files
- Provides thread-safe state access
- Implements session recovery

```python
# Example usage
from core.session import SessionState, save_session

session = SessionState(images=images, current_index=0)
save_session(session, "/path/to/output/session.json")
```

### Image Processing (core/image_processing.py)

Handles image-related operations:
- Validates image files using Pillow
- Generates unique filenames
- Copies images with new names
- Extracts image metadata

```python
# Example usage
from core.image_processing import process_image

new_path = process_image(image_path, output_dir, "img_")
```

### Tag Management (core/tagging.py)

Manages tag collection and operations:
- Loads and saves tag files
- Adds/removes tags
- Normalizes tag format
- Maintains master tag list

```python
# Example usage
from core.tagging import add_tags_to_image

add_tags_to_image("path/to/image.txt", ["tag1", "tag2"])
```

## Server Implementation

### FastAPI Server (server/main.py)

Sets up the FastAPI application:
- Configures CORS and middleware
- Mounts static files
- Registers API routers
- Initializes application state
- Starts Uvicorn server

```python
# Example usage
from server.main import start_server

start_server(config)
```

### API Routers

#### Images Router (server/routers/images.py)

Handles image-related API endpoints:
- GET /api/images - List all images
- GET /api/images/{id} - Get image info
- GET /api/images/{id}/file - Serve image file
- POST /api/images/{id}/tags - Add tags to image

#### Tags Router (server/routers/tags.py)

Manages tag-related API endpoints:
- GET /api/tags - List all tags
- POST /api/tags - Add new tags
- DELETE /api/tags/{tag} - Remove a tag
- GET /api/tags/recent - Get recently used tags

#### WebSocket Router (server/routers/websocket.py)

Handles WebSocket connections:
- Establishes WebSocket connection
- Sends real-time updates
- Processes client messages
- Maintains active connections list

## Client Implementation

### Main Application (static/js/app.js)

Coordinates the client-side application:
- Initializes all components
- Handles global events
- Manages component communication
- Implements keyboard shortcuts

### API Client (static/js/api.js)

Handles HTTP communication with the server:
- Uses fetch API for HTTP requests
- Implements REST API client methods
- Handles errors and retries
- Provides promise-based interface

```javascript
// Example usage
api.getTags().then(tags => {
  console.log(`Found ${tags.length} tags`);
});
```

### WebSocket Client (static/js/websocket.js)

Manages WebSocket communication:
- Establishes WebSocket connection
- Handles reconnection
- Processes incoming messages
- Sends messages to server
- Implements event-based interface

```javascript
// Example usage
websocket.onMessage("tags_updated", (data) => {
  console.log("Tags updated:", data);
});
```

### Image Viewer (static/js/imageViewer.js)

Handles image display and navigation:
- Loads and displays images
- Provides navigation controls
- Handles keyboard shortcuts
- Sends image change events

### Tag Manager (static/js/tagManager.js)

Manages tag UI and operations:
- Displays available tags
- Allows tag selection
- Provides tag filtering
- Manages recently used tags
- Sends tag update events

### Session Manager (static/js/sessionManager.js)

Controls session-related UI and operations:
- Displays session progress
- Provides session controls
- Handles session state updates
- Manages session exit

## Data Models

### API Models (models/api.py)

Defines Pydantic models for API requests and responses:
- ImageInfo - Image metadata
- TagList - List of tags
- SessionInfo - Session state information
- ErrorResponse - Error details

### Configuration Models (models/config.py)

Defines configuration-related models:
- AppConfig - Application configuration
- ServerConfig - Server-specific settings

### Session Models (models/session.py)

Defines session state models:
- SessionState - Current processing state
- ImageState - Per-image processing state

## Testing

### Testing Strategy

The project uses a comprehensive testing approach:
- Unit tests for individual functions
- Integration tests for component interactions
- API tests for endpoints
- WebSocket tests for real-time communication
- Edge case tests for error handling

### Running Tests

Use the test runner script:
```bash
# Run all tests
python -m test.run_tests

# Run specific test modules
python -m test.run_tests -p api

# Run with verbose output
python -m test.run_tests -v
```

### Writing Tests

Follow these guidelines for new tests:
- Create test classes that inherit from `unittest.TestCase`
- Use descriptive test method names with `test_` prefix
- Set up and tear down test fixtures properly
- Test both normal and error cases
- Use mocks for external dependencies
- Follow the AAA pattern (Arrange, Act, Assert)

```python
# Example test
class TestImageProcessing(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_image(self):
        # Arrange
        image_path = "test_images/test.jpg"

        # Act
        result = process_image(image_path, self.temp_dir.name, "img_")

        # Assert
        self.assertTrue(os.path.exists(result))
        self.assertTrue(result.startswith(self.temp_dir.name))
```

## API Documentation

### REST API Endpoints

#### Images API

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| /api/images | GET | List all images | JSON array of ImageInfo |
| /api/images/{id} | GET | Get image details | ImageInfo object |
| /api/images/{id}/file | GET | Get image file | Image file |
| /api/images/{id}/tags | GET | Get image tags | TagList object |
| /api/images/{id}/tags | POST | Update image tags | Updated TagList |

#### Tags API

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| /api/tags | GET | Get all tags | TagList object |
| /api/tags | POST | Add new tags | Updated TagList |
| /api/tags/{tag} | DELETE | Remove a tag | Success message |
| /api/tags/recent | GET | Get recent tags | TagList object |

#### Session API

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| /api/session | GET | Get session info | SessionInfo object |
| /api/session/save | POST | Save session | Success message |
| /api/session/next | POST | Move to next image | ImageInfo object |
| /api/session/prev | POST | Move to prev image | ImageInfo object |

### WebSocket Messages

#### Server to Client

| Message Type | Description | Payload |
|--------------|-------------|---------|
| session_update | Session state update | SessionInfo object |
| tags_updated | Tag list updated | TagList object |
| image_changed | Current image changed | ImageInfo object |
| error | Error occurred | ErrorInfo object |

#### Client to Server

| Message Type | Description | Payload |
|--------------|-------------|---------|
| add_tags | Add tags to current image | Array of tag strings |
| remove_tags | Remove tags from current image | Array of tag strings |
| next_image | Request next image | None |
| prev_image | Request previous image | None |
| save_session | Request session save | None |

## Contribution Guidelines

### Code Style

Follow these style guidelines:
- Use 4 spaces for indentation
- Follow PEP 8 for Python code
- Use type hints for Python functions
- Write comprehensive docstrings
- Follow ES6+ standards for JavaScript
- Use camelCase for JavaScript variables and functions

### Development Workflow

1. Create a new branch for your feature/fix
2. Make your changes
3. Run the test suite
4. Submit a pull request with a clear description

### Git Workflow

- Use descriptive commit messages
- Reference issue numbers in commits when applicable
- Keep commits focused on single changes
- Squash related commits before merging

### Code Review Process

All contributions undergo code review:
- Code must pass all tests
- Code must follow style guidelines
- Documentation must be updated
- New features must include tests

## Packaging and Distribution

### Creating a Distribution Package

```bash
# Install build tools
pip install build

# Build distribution packages
python -m build
```

This creates:
- A source distribution (.tar.gz)
- A wheel distribution (.whl)

### Publishing to PyPI

```bash
# Install Twine
pip install twine

# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

### Creating a Release

1. Update version in setup.py
2. Update CHANGELOG.md
3. Create a Git tag for the version
4. Build distribution packages
5. Create a GitHub release
6. Upload packages to PyPI

## Performance Considerations

### Optimizing for Large Directories

- Use batched processing for large image collections
- Implement pagination for image and tag listings
- Use lazy loading for image display
- Optimize tag searching with indexing
- Implement caching for frequently accessed data

### Memory Management

- Avoid loading all images into memory
- Process images sequentially
- Use context managers for file handling
- Release resources after use
- Implement proper cleanup in shutdown handlers

## Security Considerations

### Input Validation

- Validate all user input
- Sanitize file paths
- Use Pydantic models for data validation
- Implement proper error handling

### File System Security

- Restrict file operations to designated directories
- Validate file types before processing
- Use secure file operations with proper permissions
- Implement path traversal protection

### API Security

- Implement rate limiting
- Validate request parameters
- Use proper HTTP methods
- Return appropriate status codes
- Handle errors securely

## Troubleshooting Development Issues

### Common Development Problems

#### Server won't start

- Check port availability
- Verify virtual environment is active
- Check for syntax errors in code
- Ensure all dependencies are installed

#### WebSocket connection issues

- Check CORS configuration
- Verify network connectivity
- Check for proxy interference
- Use browser developer tools to inspect WebSocket traffic

#### Package installation problems

- Use correct Python version
- Check for conflicting dependencies
- Try recreating the virtual environment
- Verify pip/uv is up to date

### Debugging Tips

- Use logging with increased verbosity
- Check server logs for errors
- Use browser developer tools for client-side debugging
- Add debug print statements when needed
- Use a debugger for step-through debugging
