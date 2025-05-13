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

### Frontend Development
- Keep JavaScript code clean and well-organized
- Use ES6+ syntax for modern browser compatibility
- Separate concerns: HTML for structure, CSS for styling, JS for behavior
- Consider Vue.js for more complex UI components if needed
- Follow responsive design principles for mobile compatibility
- Implement proper error handling on the client side
- Use WebSocket for real-time communication with server

### Testing
- Run unit tests before submitting changes
- Use unittest framework for test organization
- Create tests for all new functionality
- Use temporary directories and files for clean testing
- Test both backend API and frontend functionality
- Implement integration tests for the complete workflow

### Error Handling
- Use appropriate logging levels (error, warning, info, debug)
- Implement comprehensive error handling with meaningful messages
- Fail early when critical errors occur
- Use try/except blocks with specific exception types for precise error handling
- Provide clear error feedback to users via the web interface

### Version Control
- Keep commit messages clear and descriptive
- Reference related issues or changes when applicable
- Exclude .venv/ directory from version control
- Exclude generated files and caches

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
python3 civitai_tagger.py /path/to/images
```

The server will automatically open a web browser to the application interface.
