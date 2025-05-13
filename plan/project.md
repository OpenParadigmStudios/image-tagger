# CivitAI Flux Dev LoRA Tagging Assistant

## Project Overview
This Python application assists in creating tag files for CivitAI Flux Dev LoRA model training. The tool:
1. Processes directories of images
2. Creates corresponding text files for each image with the same name but `.txt` extension
3. Provides interactive tagging through a web-based interface
4. Maintains a collection of previously used tags for easy reuse
5. Supports interrupting and resuming the tagging process

## Requirements

### Core Features
1. Accept a directory path as input argument
2. Create an output subdirectory within the given directory
3. Process image files:
   - Rename each image to a unique identifier
   - Move renamed images to the output directory
   - Create corresponding `.txt` files for each image
4. Web User Interface:
   - Display a preview of the current image
   - Show a list of all tags created so far as interactive elements
   - Allow adding new tags not previously used
   - Save selected tags to the corresponding `.txt` file
   - Access via web browser on localhost
5. Maintain a master tags list in `tags.txt` within the output directory
6. Session Persistence:
   - Track progress through the image set
   - Allow exiting at any point
   - Support resuming from the last processed image
   - Save session state information

### Implementation Notes
- **Platform**: macOS (Macbook Pro M3), with compatibility for Windows and Linux
- **Language**: Python 3.8+
- **Backend**: FastAPI with WebSocket support
- **Frontend**: HTML/CSS/JavaScript with component-based architecture
- **File Naming**: Sequential numbering with configurable prefix for organized, predictable naming
- **Session State**: Store progress in a JSON file in the output directory with regular auto-saving

## Technical Approach

### Current Architecture
- **Client-Server Architecture**:
  - Server: FastAPI-based backend handling file operations and session management
  - Client: Web-based frontend for image viewing and tag management
  - WebSocket: For real-time communication between client and server
- **Command-line interface** for starting the server with directory input and configuration
- **Modular design** with properly separated concerns:
  - Core functionality in `core/` directory
  - Server implementation in `server/` directory
  - API models in `models/` directory
  - Client-side code in `static/` directory

### Libraries Used
- **Backend Framework**: FastAPI for high-performance API endpoints and WebSocket support
- **Server**: Uvicorn as the ASGI server
- **Image Processing**: Pillow (PIL fork) for wide format support and efficient image operations
- **File Management**: pathlib for path operations
- **State Management**: json for human-readable session persistence
- **Validation**: Pydantic models for robust data structures
- **Frontend**: HTML, CSS, JavaScript with component-based architecture
- **Testing**: unittest and pytest frameworks for automated testing

### Data Flow
1. User starts the application with a directory path
2. Server launches and opens a web browser to the interface URL
3. Server checks for existing session in the output directory
   - If found, offers to resume from last point
   - If not found, starts new session
4. Server scans for image files (or loads from session)
5. Creates output directory, tags.txt, and session file if not present
6. Client establishes WebSocket connection with server
7. For each image:
   - Server generates unique name (or retrieves from session)
   - Server copies to output directory with new name (if not already done)
   - Client displays image preview loaded from server
   - Client shows tagging interface with existing tags
   - Client sends selected tags to server via WebSocket
   - Server saves tags to corresponding text file
   - Server updates master tags list if new tags added
   - Server updates session state file
8. When user exits, server saves current position and state

### User Experience
- Clean, responsive web interface with scalable image preview
- Tag organization with search/filter capabilities
- Recently used tags section for quick access
- Keyboard shortcuts for common actions (next image, save)
- Clear progress indicators and status messages
- Automatic backup of session data to prevent loss
- Accessible from any web browser on the local machine

## Implementation Plan Status

### Completed
1. ✅ Set up basic command-line argument parsing and server initialization
2. ✅ Implement file system operations (scanning, creating directories)
3. ✅ Build image renaming and copying functionality
4. ✅ Develop tag management system with API endpoints
5. ✅ Create session state tracking and persistence
6. ✅ Implement WebSocket communication and API endpoints
7. ✅ Create web-based UI for image preview and tag selection
8. ✅ Step 8: Testing and Refinement
   - Comprehensive testing with automated test suite
   - Bug fixes and edge cases
   - UI improvements
   - Performance optimization
9. ✅ Step 9: Documentation and Distribution
   - User documentation in docs/user_guide.md
   - Developer documentation in docs/developer_guide.md
   - Packaging with setup.py and MANIFEST.in
   - Docker support with Dockerfile and docker-compose.yml
   - Multiple installation methods documented

## Project Structure

Current project structure:
```
civitai_tagger/
├── main.py                  # Entry point and main application
├── core/                    # Core functionality
│   ├── config.py            # Configuration and arguments
│   ├── filesystem.py        # File system operations
│   ├── image_processing.py  # Image handling functions
│   ├── session.py           # Session management
│   └── tagging.py           # Tag management functions
├── server/                  # Server implementation
│   ├── main.py              # FastAPI server setup
│   ├── utils.py             # Utility functions for the server
│   └── routers/             # API route handlers
│       ├── images.py        # Image processing endpoints
│       ├── tags.py          # Tag management endpoints
│       ├── status.py        # Server status endpoints
│       └── websocket.py     # WebSocket implementation
├── models/                  # Data models
│   ├── config.py            # Configuration data models
│   ├── session.py           # Session state models
│   └── api.py               # API request/response models
├── static/                  # Web client files
│   ├── index.html           # Main HTML page
│   ├── css/                 # CSS style files
│   └── js/                  # JavaScript client code
│       ├── api.js           # API client
│       ├── websocket.js     # WebSocket client
│       ├── imageViewer.js   # Image viewing component
│       ├── tagManager.js    # Tag management component
│       ├── sessionManager.js # Session management component
│       └── app.js           # Main application logic
├── test/                    # Test files
│   ├── test_api_models.py   # API model tests
│   ├── test_api_endpoints.py # API endpoint tests
│   ├── test_websocket.py    # WebSocket tests
│   ├── test_performance.py  # Performance tests
│   ├── test_edge_cases.py   # Edge case tests
│   ├── browser_compatibility.py # Browser compatibility tests
│   ├── test_filesystem.py   # Filesystem operations tests
│   ├── test_image_processing.py # Image processing tests
│   ├── test_session.py      # Session management tests
│   ├── test_tagging.py      # Tag management tests
│   ├── test_integration.py  # Integration tests
│   └── run_tests.py         # Test runner script
├── docs/                    # Documentation
│   ├── user_guide.md        # User documentation
│   └── developer_guide.md   # Developer documentation
├── setup.py                 # Package setup script
├── MANIFEST.in              # Package file inclusion
├── LICENSE                  # MIT license
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker compose configuration
├── requirements.txt         # Project dependencies
├── activate_env.sh          # Environment activation script
└── README.md                # Project README
```

## Potential Improvements

### Code Architecture
1. **State Management**: Consider implementing a more robust state management pattern (e.g., State machine)
2. **Dependency Injection**: Formalize dependency injection throughout the application for better testability
3. **API Versioning**: Add explicit API versioning for future compatibility
4. **Async Operations**: Increase use of async/await for file operations to improve scalability

### Development Workflow
1. **CI/CD Pipeline**: Add GitHub Actions or similar for automated testing and deployment
2. **Code Quality Metrics**: Integrate tools like SonarQube or CodeClimate
3. **Pre-commit Hooks**: Add pre-commit hooks for linting and formatting

### User Experience
1. **Keyboard Shortcuts**: Enhance keyboard navigation capabilities
2. **Tag Categories**: Implement grouping of tags by categories
3. **Batch Processing**: Add support for batch operations on multiple images
4. **Theme Support**: Add light/dark theme support

### Performance
1. **Image Caching**: Implement client-side caching for better performance
2. **Lazy Loading**: Add lazy loading for large tag lists
3. **Database Storage**: Consider SQLite or similar for larger datasets instead of JSON files

## Future Enhancements
After completing the core implementation, the following enhancements could be considered:
- Batch processing mode (non-interactive)
- Tag suggestions based on image content using ML
- Custom tag categories or grouping
- Search and filter capabilities for large tag sets
- Progress statistics and summary reporting
- Remote access with proper authentication and security
- Tag import/export functionality
- Backup and archive features
- Multi-user support
