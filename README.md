# CivitAI Flux Dev LoRA Tagging Assistant

A Python application with a web interface to assist in creating tag files for CivitAI Flux Dev LoRA model training.

## Overview

This tool helps you process a directory of images and create corresponding text files with tags for each image. It provides a web-based interface for adding tags, maintains a collection of previously used tags, and supports interrupting and resuming the tagging process.

## Current Status

This project is being developed in steps. Current implementation:

- ✅ Step 1: Command Line Argument Parsing
- ✅ Step 2: File System Operations
- ⬜ Step 3: Image Renaming and Copying
- ⬜ Step 4: Server Implementation with FastAPI
- ⬜ Step 5: Tag Management System with API
- ⬜ Step 6: Web Client Interface
- ⬜ Step 7: Integration and Workflow Completion
- ⬜ Step 8: Testing with Sample Images
- ⬜ Step 9: Refinement and Enhancements

## Requirements

- Python 3.8 or higher
- UV package manager (recommended)
- Modern web browser (Chrome, Firefox, Safari)

## Installation

1. Clone the repository
2. Navigate to the project directory
3. Set up environment and install dependencies:

### Using UV (Recommended)

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows

# Install dependencies
uv pip install -r requirements.txt
```

### Using pip (Alternative)

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Quick Environment Activation

For convenience, an activation script is provided:

```bash
# On Unix/macOS
./activate_env.sh
```

## IDE Setup

This project includes configuration for Cursor IDE and VS Code:

- `.vscode/settings.json` - Configures the Python interpreter and editor settings
- `.python-version` - Specifies the Python version for tools like pyenv
- `.gitignore` - Excludes virtual environments and other generated files

When opening the project in Cursor IDE, it will automatically use the configured virtual environment.

## Usage

```bash
# Basic usage with just input directory
python3 main.py /path/to/images

# Specifying custom output directory name
python3 main.py /path/to/images -o custom_output

# Resume previous session
python3 main.py /path/to/images -r

# Use a specific host and port
python3 main.py /path/to/images --host 0.0.0.0 --port 8080

# Combine multiple options
python3 main.py /path/to/images -o custom_output -p lora_ -r -v

# Set auto-save interval to 2 minutes
python3 main.py /path/to/images -a 120
```

## Command Line Arguments

- `input_directory`: Path to the directory containing images to process (required)
- `-o, --output-dir`: Specify a custom output directory name (default: "output")
- `-r, --resume`: Resume from a previous session (default: False)
- `-p, --prefix`: Prefix for renamed image files (default: "img")
- `-v, --verbose`: Enable verbose logging (default: False)
- `-a, --auto-save`: Time interval in seconds for auto-saving session state (default: 60)
- `--host`: Host IP address for the web server (default: "127.0.0.1")
- `--port`: Port number for the web server (default: 8000)

## How It Works

1. When you start the application, it launches a web server and opens a browser window
2. The web interface allows you to view images and add tags
3. Tags are saved to corresponding text files for each image
4. Your progress is automatically saved and can be resumed later
5. The application generates output files in the specified output directory

## Project Structure

- `main.py`: Main entry point
- `core/`: Core functionality modules
- `server/`: Web server and API implementation
- `models/`: Data models for API requests/responses
- `static/`: Web client files (HTML, CSS, JavaScript)
- `test/`: Test files

## Development

### Running Tests

```bash
# To be implemented
```

For more detailed development guidelines, see [plan/development.md](plan/development.md).

## License

TBD

## Roadmap

1. ✅ Set up basic command-line argument parsing
2. ✅ Implement file system operations
3. ⬜ Build image renaming and copying functionality
4. ⬜ Develop tag management system
5. ⬜ Create session state tracking and persistence
6. ⬜ Create GUI for image preview and tag selection
7. ⬜ Implement save/exit and resume functionality
8. ⬜ Connect all components into a complete workflow
9. ⬜ Test with sample image directories
10. ⬜ Refine based on testing feedback
