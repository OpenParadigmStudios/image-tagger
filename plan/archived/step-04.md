# Step 4: Server Implementation with FastAPI

## Overview
In this step, we'll create a web server using FastAPI to serve the application. The server will provide endpoints for image listing, image viewing, and WebSocket communication for real-time tagging. This builds on the previous steps by exposing the file system operations and image processing functionality through a web interface.

## Requirements
- Create a FastAPI application with appropriate routes
- Set up static file serving for web UI assets
- Implement image file serving with proper security checks
- Create WebSocket endpoint for real-time communication
- Implement server-side session management
- Ensure the server can be started with the same command-line arguments

## Implementation Details

### Core Libraries
- `fastapi`: For building the API server
- `uvicorn`: ASGI server for running the FastAPI application
- `websockets`: For WebSocket protocol implementation
- `pydantic`: For data validation and settings management
- `jinja2` (optional): For server-side templating if needed

### Server Components

#### 1. Main Application
- Create the FastAPI application instance
- Configure server settings based on command-line arguments
- Set up middleware for logging, CORS, etc.
- Mount static files directory for serving web UI
- Include API routers for different functionality

#### 2. Static File Serving
- Serve the web UI files (HTML, CSS, JavaScript)
- Implement secure path validation to prevent directory traversal attacks
- Serve images from the input and output directories with proper validation

#### 3. API Endpoints
- `GET /api/images`: List all images in the input directory
- `GET /api/images/{image_id}`: Get information about a specific image
- `GET /api/processed`: List all processed images
- `GET /api/tags`: Get all existing tags
- `POST /api/tags`: Add a new tag
- `PUT /api/images/{image_id}/tags`: Update tags for an image

#### 4. WebSocket Endpoint
- `/ws`: Main WebSocket communication channel
- Handle session initialization and state updates
- Process real-time tagging operations
- Send notifications about processing status

#### 5. Server-Side Session Management
- Track connected clients
- Maintain session state across connections
- Synchronize file system operations with client requests

### Functions to Implement

#### 1. `start_server(config: AppConfig) -> None`
- Purpose: Initialize and start the FastAPI server
- Input: Application configuration object
- Operations:
  - Create the FastAPI app
  - Set up routes and endpoints
  - Configure and start Uvicorn server

#### 2. `get_image_list(input_dir: Path) -> List[Dict]`
- Purpose: Get a list of all images with metadata
- Input: Path to the input directory
- Output: List of image information dictionaries
- Operations:
  - Scan the directory for images
  - Extract metadata (size, dimensions, etc.)
  - Return formatted list for API response

#### 3. `serve_image(image_path: Path) -> Response`
- Purpose: Securely serve an image file
- Input: Path to the image file
- Output: FastAPI Response object with image data
- Operations:
  - Validate the path is within allowed directories
  - Set appropriate content type
  - Return file contents with caching headers

#### 4. `update_image_tags(image_id: str, tags: List[str]) -> Dict`
- Purpose: Update tags for a specific image
- Input: Image ID and list of tags
- Output: Dictionary with operation status
- Operations:
  - Find corresponding text file
  - Write tags to the file
  - Update master tags list if needed
  - Return success status and updated info

#### 5. `handle_websocket_connection(websocket: WebSocket, config: AppConfig) -> None`
- Purpose: Manage a WebSocket connection with a client
- Input: WebSocket object and application configuration
- Operations:
  - Accept the connection
  - Process incoming messages
  - Send updates on state changes
  - Handle disconnection gracefully

### Error Handling
- Implement proper HTTP error responses
- Handle WebSocket connection issues
- Validate all user inputs
- Provide detailed error messages for debugging
- Use try/except blocks for file operations

## Code Structure

### Integration with Previous Steps
- Use the image processing functions from Step 3
- Use the file system operations from Step 2
- Use the configuration parsing from Step 1

### Server Architecture
```
server/
  ├── main.py              # FastAPI application entry point
  ├── routers/             # API route definitions
  │   ├── images.py        # Image-related endpoints
  │   ├── tags.py          # Tag management endpoints
  │   └── websocket.py     # WebSocket handling
  ├── models/              # Pydantic models for data validation
  │   ├── config.py        # Server configuration model
  │   └── responses.py     # API response models
  └── static/              # Static files to serve (initial client code)
      ├── index.html       # Main HTML page
      ├── css/             # CSS files
      └── js/              # JavaScript files
```

### Processing Flow
1. Parse command-line arguments
2. Initialize the server with configuration
3. Start the server on the specified host and port
4. Serve the web interface when accessing the root URL
5. Handle API and WebSocket requests

## Testing Strategy
- Test API endpoints with client requests
- Test WebSocket communication
- Test static file serving
- Test image serving with different file types
- Test error handling for invalid inputs
- Test concurrent connections and load handling

## Implementation Steps
1. Create the basic FastAPI application structure
2. Set up static file serving for web assets
3. Implement API endpoints for image and tag operations
4. Create the WebSocket handler for real-time communication
5. Add session state management
6. Integrate with image processing functions from Step 3
7. Implement security validations for all inputs
8. Test the server functionality with mock clients

## Next Steps After Completion
Once this step is complete, we'll be able to:
- Start a web server hosting the application
- Access the server API endpoints
- Serve images from the input/output directories
- Set up the foundation for the web-based UI
- Prepare for implementing the client-side interface
