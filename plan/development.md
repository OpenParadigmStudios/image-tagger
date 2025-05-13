# CivitAI Flux Dev LoRA Tagging Assistant - Development Guidelines

## Code Style and Conventions

### Documentation and Planning
- Any code change suggestion should be accompanied by corresponding documentation or plan updates when relevant
- Update progress.md when completing implementation steps
- Keep project.md in sync with actual implementation decisions
- Create a step-XX-done.md file when completing a step to document the implementation details and decisions
- Any new guidelines similar to the ones in this file that come up during coding should be worked into this document

### Python Environment
- Use Python 3.8+ as specified in project.md
- Using `uv` for dependency management and virtual environments
- Run Python with `python3` command rather than `python` to ensure proper version
- Virtual environment is located at `.venv/` in the project root

### IDE Configuration
- Cursor IDE is configured to use the project's virtual environment
- VS Code settings are stored in `.vscode/settings.json`
- Python interpreter path is set to `.venv/bin/python3`
- Editor is configured to use spaces (4 spaces per indentation level)
- Editor will trim trailing whitespace and add final newlines

### Code Style
- Use spaces for indentation (4 spaces per indentation level)
- No trailing whitespace on lines of code
- Include empty line at the end of files
- Follow PEP 8 style guidelines
- Use type hints throughout the code for better IDE support and documentation
- Write comprehensive docstrings following Google Python Style Guide

### Code Quality
- Follow the Single Responsibility Principle: each function should do one thing well
- Keep functions small and focused (<50 lines when possible)
- Use meaningful, descriptive variable and function names
- Write self-documenting code that clearly communicates intent
- Avoid deep nesting of conditionals and loops (prefer early returns)
- Prefer composition over inheritance
- Use dataclasses for structured data
- Avoid global state; use dependency injection instead
- Write idiomatic Python using built-in features when appropriate
- Apply DRY (Don't Repeat Yourself) principle to eliminate duplication
- Follow SOLID principles when designing classes

### Design Patterns
- **State Pattern**: Consider implementing a formal state machine for session management
- **Observer Pattern**: Continue using the current observer pattern for WebSocket notifications
- **Factory Pattern**: Consider using factories for complex object creation
- **Repository Pattern**: Implement for data access abstraction (especially if moving to database storage)
- **Strategy Pattern**: Use for implementing alternative algorithms (e.g., different tagging strategies)
- **Dependency Injection**: Formalize dependency injection throughout the application

### Asynchronous Programming
- Use `async`/`await` for I/O-bound operations, especially file operations
- Properly handle task cancellation and cleanup
- Use structured concurrency patterns for task management
- Be mindful of thread safety when mixing synchronous and asynchronous code
- Use proper error handling in asynchronous contexts
- Consider using asyncio's synchronization primitives for coordination

### Error Handling
- Use appropriate logging levels (error, warning, info, debug)
- Implement comprehensive error handling with meaningful messages
- Fail early when critical errors occur
- Use try/except blocks with specific exception types for precise error handling
- Provide clear error feedback to users via the web interface
- Consider defining custom exception types for application-specific errors
- Always include original exception details in logs when catching and re-raising
- Use context managers for resource cleanup (especially file operations)

### File Structure
- Main server functionality in civitai_tagger.py
- Client web files in static/ directory
- API routes in server/ directory
- Core functionality in core/ directory
- Data models in models/ directory
- Unit tests in test/ directory
- Planning documents in plan/ directory
- Keep README.md up to date with current functionality and usage instructions
- IDE configuration in .vscode/ directory
- Environment activation script in activate_env.sh

### Backend Development
- Use FastAPI for the backend framework
- Implement WebSocket communication for real-time updates
- Use Pydantic models for data validation and API schemas
- Use Path objects from pathlib for file operations
- Organize API endpoints into logical router groups
- Apply proper error handling with HTTP status codes
- Use async functions where appropriate for file I/O
- Implement proper dependency injection with FastAPI
- Use middleware for cross-cutting concerns (logging, error handling)
- Implement proper request validation with Pydantic models
- Keep endpoint handlers small and delegate to service functions

### REST API Design
- Follow RESTful principles consistently
- Use appropriate HTTP methods (GET, POST, PUT, DELETE)
- Implement proper status codes for different scenarios
- Consider implementing API versioning (e.g., /api/v1/)
- Use consistent naming conventions for endpoints
- Implement proper pagination for large collections
- Add comprehensive API documentation with OpenAPI
- Consider adding rate limiting for public-facing endpoints
- Implement proper CORS configuration
- Add request validation using Pydantic models

### Frontend Development
- Keep JavaScript code clean and well-organized
- Use ES6+ syntax for modern browser compatibility
- Separate concerns: HTML for structure, CSS for styling, JS for behavior
- Follow responsive design principles for mobile compatibility
- Implement proper error handling on the client side
- Use WebSocket for real-time communication with server
- Use JavaScript modules (ES6 modules) for code organization
- Follow component-based architecture for UI elements
- Use event-driven programming for component communication
- Prioritize user experience with responsive UI feedback
- Follow accessibility best practices

### JavaScript Architecture
- Modular structure with separate files for distinct functionality
- Main modules:
  - `api.js`: Client for REST API communication
  - `websocket.js`: WebSocket connection management
  - `imageViewer.js`: Image display and navigation
  - `tagManager.js`: Tag selection and management
  - `sessionManager.js`: Session state and control
  - `app.js`: Main application orchestration
- Import/export pattern for module dependencies
- Event-based communication between components
- Singleton instances for service classes
- Use promises or async/await for asynchronous operations
- Implement proper error handling and recovery in async operations
- Validate data before sending to server
- Follow the Observer pattern for UI updates

### Performance Optimization
- Implement client-side caching for images and tag data
- Use lazy loading for large datasets
- Consider using a database for large collections instead of JSON files
- Optimize WebSocket message size and frequency
- Implement pagination for large collections
- Add compression for static assets
- Consider using HTTP/2 for multiple parallel requests
- Profile and optimize critical path operations
- Implement batch processing for operations on multiple files
- Add proper indexes if moving to database storage

### Security Considerations
- Validate all user inputs on both client and server
- Implement proper path traversal prevention
- Use secure file operations to prevent race conditions
- Add proper CORS configuration
- Consider implementing some form of authentication for multi-user scenarios
- Implement rate limiting for public-facing APIs
- Regularly update dependencies for security patches
- Use content security policy headers
- Add timeout mechanisms for long-running operations
- Implement proper handling of sensitive data (if applicable)

### Testing
- Run unit tests before submitting changes
- Use unittest framework for test organization
- Create tests for all new functionality
- Use temporary directories and files for clean testing
- Test both backend API and frontend functionality
- Implement integration tests for the complete workflow
- Use mocks and stubs for external dependencies
- Aim for high test coverage in core functionality
- Test happy paths and error conditions
- Write test utility functions for common testing patterns
- Use parameterized tests for testing multiple input variations

### Version Control
- Keep commit messages clear and descriptive
- Reference related issues or changes when applicable
- Exclude .venv/ directory from version control
- Exclude generated files and caches
- Commit logical units of work
- Use feature branches for significant changes
- Review code before committing

## Known Preferences
- Preference for pathlib over os.path for path operations
- Dataclasses for structured data representation
- Atomic file operations with temporary files and backups
- Modular design with separate functions for distinct functionality
- Consistent error handling and logging patterns
- FastAPI for modern web server implementation
- Responsive web design for multiple screen sizes

## Environment Setup

### Activating the Environment
To activate the environment, you can:
1. Use the provided script: `./activate_env.sh`
2. Activate manually: `source .venv/bin/activate`

### Using with Cursor IDE
Cursor IDE will automatically use the configured Python interpreter in `.venv/bin/python3`
as specified in `.vscode/settings.json`.

### Running the Server
After activating the environment, start the server:
```
python3 main.py /path/to/images
```

The server will automatically open a web browser to the application interface.

### Running the Application
- Use `main.py` to start the web server:
  ```bash
  python3 main.py <image_directory>
  ```
- The server will be accessible at `http://localhost:8000`
- A browser window should open automatically
- For development, you can use browser developer tools to debug

## Continuous Integration
For future implementation:
- Consider setting up GitHub Actions or similar CI/CD pipeline
- Automate testing on multiple Python versions
- Implement code quality checks
- Automate deployment to PyPI
- Add Docker image building and publishing

## Refactoring Guidelines
- Identify and eliminate code duplication first
- Move functionality to appropriate modules based on responsibility
- Break down large functions into smaller, focused ones
- Update tests when refactoring implementation
- Preserve behavior when refactoring - validate with tests
- Document the reasons for significant refactoring
- Prefer consistent patterns throughout the codebase
- When adding new functionality, follow existing patterns
- Use comments to explain complex logic or design decisions
- Focus on readability and maintainability over cleverness

## Documentation Strategy
- User documentation in docs/user_guide.md
- Developer documentation in docs/developer_guide.md
- API documentation using OpenAPI/Swagger
- README.md for quick start and overview
- Inline code documentation through comprehensive docstrings
- Implementation details in step-XX-done.md files
- Step plans in step-XX.md files
- Overall project status in progress.md
- Project architecture and requirements in project.md

## Future Architecture Considerations
- Consider migration to SQLite or similar for larger datasets
- Evaluate GraphQL for more flexible API queries if needed
- Consider implementing a plugin system for extensibility
- Evaluate containerization for easier deployment
- Consider implementing a proper CLI interface with sub-commands
- Evaluate internationalization support for non-English users
- Consider implementing a proper authentication system for multi-user scenarios
