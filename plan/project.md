# CivitAI Flux Dev LoRA Tagging Assistant

## Project Overview
This Python application will assist in creating tag files for CivitAI Flux Dev LoRA model training. The tool will:
1. Process a directory of images
2. Create a corresponding text file for each image with the same name but `.txt` extension
3. Allow interactive tagging through a web-based interface
4. Maintain a collection of previously used tags for easy reuse
5. Support interrupting and resuming the tagging process

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
- **Platform**: macOS (Macbook Pro M3)
- **Language**: Python 3.8+ (preferred due to user familiarity)
- **Backend**: FastAPI with WebSocket support
- **Frontend**: HTML/CSS/JavaScript with optional Vue.js
- **File Naming**: Sequential numbering with configurable prefix for organized, predictable naming
- **Session State**: Store progress in a JSON file in the output directory with regular auto-saving

## Technical Approach

### Application Architecture
- **Client-Server Architecture**:
  - Server: FastAPI-based backend handling file operations and session management
  - Client: Web-based frontend for image viewing and tag management
  - WebSocket: For real-time communication between client and server
- **Command-line interface** for starting the server with directory input and configuration
- **Modular design** for easy maintenance and future enhancements

### Libraries to Use
- **Backend Framework**: FastAPI for high-performance API endpoints and WebSocket support
- **Server**: Uvicorn as the ASGI server
- **Image Processing**: Pillow (PIL fork) for wide format support and efficient image operations
- **File Management**: pathlib (more modern than os.path) for path operations
- **State Management**: json for human-readable session persistence
- **Validation**: Pydantic models (compatible with dataclasses) for robust data structures
- **Frontend**: HTML, CSS, JavaScript with optional Vue.js for reactive components
- **Testing**: pytest for automated testing

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

## Implementation Plan
1. Set up basic command-line argument parsing and server initialization
2. Implement file system operations (scanning, creating directories)
3. Build image renaming and copying functionality
4. Develop tag management system
5. Create session state tracking and persistence
6. Implement WebSocket communication and API endpoints
7. Create web-based UI for image preview and tag selection
8. Implement save/exit and resume functionality
9. Connect all components into a complete workflow
10. Test with sample image directories
11. Refine based on testing feedback

## Future Enhancements (Optional)
- Batch processing mode (non-interactive)
- Tag suggestions based on image content using ML
- Custom tag categories or grouping
- Search and filter capabilities for large tag sets
- Progress statistics and summary reporting
- Remote access with proper authentication and security
