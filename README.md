# CivitAI Flux Dev LoRA Tagging Assistant

A Python application with a web interface to assist in creating tag files for CivitAI Flux Dev LoRA model training.

## Overview

This tool helps you process a directory of images and create corresponding text files with tags for each image. It provides a web-based interface for adding tags, maintains a collection of previously used tags, and supports interrupting and resuming the tagging process.

## Features

- Image scanning and processing from input directory
- Web-based user interface for tagging
- Real-time updates via WebSocket
- Tag management with search and filtering
- Session state persistence and resuming
- Automatic tag file generation
- Responsive design for various screen sizes
- Keyboard shortcuts for efficient workflow
- Docker support for containerized deployment

## Installation

### Method 1: Install from PyPI (Recommended)

```bash
# Install the package
pip install civitai-tagger

# Run the application
civitai-tagger /path/to/images
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/username/civitai-tagger.git
cd civitai-tagger

# Set up a virtual environment
# Option 1: Using UV (recommended)
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows

# Option 2: Using standard venv
python -m venv venv
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run the application
python main.py /path/to/images
```

### Method 3: Using Docker

```bash
# Clone the repository
git clone https://github.com/username/civitai-tagger.git
cd civitai-tagger

# Build and run using docker-compose
docker-compose up -d

# Or build and run manually
docker build -t civitai-tagger .
docker run -p 8000:8000 -v /path/to/images:/app/images civitai-tagger /app/images
```

## Quick Start

1. Install the application using one of the methods above
2. Run the application with your image directory:
   ```bash
   civitai-tagger /path/to/images
   ```
3. A web browser will automatically open to http://localhost:8000
4. Use the interface to view images and add tags
5. Tags are automatically saved as you navigate between images

## Usage

```bash
# Basic usage
civitai-tagger /path/to/images

# Custom output directory
civitai-tagger /path/to/images -o custom_output

# Resume previous session
civitai-tagger /path/to/images -r

# Custom file prefix
civitai-tagger /path/to/images -p lora_

# Verbose logging
civitai-tagger /path/to/images -v

# Custom auto-save interval (in seconds)
civitai-tagger /path/to/images -a 120

# Custom host and port
civitai-tagger /path/to/images --host 0.0.0.0 --port 8080

# Combined options
civitai-tagger /path/to/images -o custom_output -p lora_ -r -v -a 120 --host 0.0.0.0 --port 8080
```

## Command Line Arguments

| Option               | Description                                     | Default     |
|----------------------|-------------------------------------------------|-------------|
| `input_directory`    | Path to directory with images (required)        |             |
| `-o, --output-dir`   | Name of the output directory                    | "output"    |
| `-r, --resume`       | Resume from previous session                    | False       |
| `-p, --prefix`       | Prefix for renamed image files                  | "img"       |
| `-v, --verbose`      | Enable verbose logging                          | False       |
| `-a, --auto-save`    | Auto-save interval in seconds                   | 60          |
| `--host`             | Host IP address for the web server              | "127.0.0.1" |
| `--port`             | Port number for the web server                  | 8000        |

## Web Interface

The web interface provides an intuitive way to view and tag images:

- **Image Viewer** - Display and navigate through images
- **Tag Management** - Add, remove, and filter tags
- **Recently Used Tags** - Quick access to frequently used tags
- **Session Controls** - Navigate, save, and exit the session

### Keyboard Shortcuts

| Shortcut    | Action         |
|-------------|----------------|
| Right Arrow | Next image     |
| Left Arrow  | Previous image |
| Ctrl+S      | Save tags      |
| Ctrl+F      | Focus tag search |

## Documentation

Comprehensive documentation is available in the `docs` directory:

- [User Guide](docs/user_guide.md) - Detailed instructions for users
- [Developer Guide](docs/developer_guide.md) - Information for developers

## Docker Deployment

The application can be deployed using Docker:

```bash
# Using docker-compose (recommended)
docker-compose up -d

# Manual docker commands
docker build -t civitai-tagger .
docker run -p 8000:8000 -v $(pwd)/images:/app/images -v $(pwd)/output:/app/output civitai-tagger /app/images
```

## Development

### Requirements

- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Safari)
- See requirements.txt for dependencies

### Running Tests

```bash
# Run all tests
python -m test.run_tests

# Run tests with verbose output
python -m test.run_tests -v

# Run specific test modules
python -m test.run_tests -p api
```

### Package Building

```bash
# Install build tools
pip install build

# Build distribution packages
python -m build
```

## Project Status

The project has completed all planned implementation steps:

- ✅ Step 1: Command Line Argument Parsing
- ✅ Step 2: File System Operations
- ✅ Step 3: Image Renaming and Copying
- ✅ Step 4: Server Implementation with FastAPI
- ✅ Step 5: Tag Management System with API
- ✅ Step 6: Web Client Interface
- ✅ Step 7: Code Refactoring and Integration
- ✅ Step 8: Testing and Refinement
- ✅ Step 9: Documentation and Distribution

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

If you encounter issues:

1. Check the application logs (use `-v` for verbose logging)
2. Ensure you have the correct Python version (3.8+)
3. Verify all dependencies are installed correctly
4. Check file permissions for input and output directories
5. See the [User Guide](docs/user_guide.md) for more troubleshooting tips
