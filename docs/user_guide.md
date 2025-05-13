# CivitAI Flux Dev LoRA Tagging Assistant - User Guide

## Introduction

Welcome to the CivitAI Flux Dev LoRA Tagging Assistant! This tool helps you create tag files for CivitAI Flux Dev LoRA model training by providing an intuitive web interface for viewing images and assigning tags.

## Installation

### Prerequisites

Before installing the CivitAI Tagger, ensure you have:

- Python 3.8 or higher installed
- A modern web browser (Chrome, Firefox, or Safari)
- Basic knowledge of command-line operations

### Installation Methods

#### Method 1: Install from PyPI (Recommended)

```bash
# Install the package
pip install civitai-tagger

# Verify installation
civitai-tagger --version
```

#### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/username/civitai-tagger.git
cd civitai-tagger

# Install in development mode
pip install -e .
```

## Getting Started

### Basic Usage

To start the application with the default settings:

```bash
# Using the installed package
civitai-tagger /path/to/your/images

# Or if installed from source
python main.py /path/to/your/images
```

This will:
1. Start the application server on localhost:8000
2. Open your default web browser to the application interface
3. Scan the specified directory for images
4. Create an output directory for processed files

### Command Line Options

The application supports various command-line options:

| Option                  | Description                                      | Default     |
|-------------------------|--------------------------------------------------|-------------|
| `-o, --output-dir`      | Name of the output directory                     | "output"    |
| `-r, --resume`          | Resume a previous session                        | False       |
| `-p, --prefix`          | Prefix for renamed image files                   | "img"       |
| `-v, --verbose`         | Enable verbose logging                           | False       |
| `-a, --auto-save`       | Auto-save interval in seconds                    | 60          |
| `--host`                | Host IP address for the web server               | "127.0.0.1" |
| `--port`                | Port number for the web server                   | 8000        |

Example with options:

```bash
civitai-tagger /path/to/images -o custom_output -p lora_ -a 120 --port 8080 -v
```

## Using the Web Interface

### Main Interface Overview

The web interface consists of several main areas:

1. **Navigation Bar** - Contains session controls and progress information
2. **Image Viewer** - Displays the current image with navigation controls
3. **Tag Manager** - Shows available tags and allows tag selection
4. **Tag Search/Filter** - Helps find tags in large tag collections
5. **Recent Tags** - Shows recently used tags for quick access

### Navigating Images

- Use the **Next** and **Previous** buttons to move between images
- The current image number and total count are displayed in the navigation bar
- You can use keyboard shortcuts:
  - **Right Arrow** - Next image
  - **Left Arrow** - Previous image
  - **Ctrl+S** - Save current tags

### Managing Tags

#### Adding Tags

There are several ways to add tags to the current image:

1. Click on an existing tag in the tag list
2. Type a new tag in the tag input field and press Enter
3. Click on a recently used tag

#### Removing Tags

To remove a tag from the current image:
1. Click the "x" next to the tag in the selected tags section
2. Click on the tag again in the tag list to toggle it off

#### Filtering Tags

For large tag collections, use the search/filter box to find specific tags:
1. Type in the search box to filter tags
2. The tag list will update in real-time to show matching tags

### Session Management

#### Saving Progress

Your progress is automatically saved:
- At the auto-save interval (default: every 60 seconds)
- When navigating between images
- When you exit the application properly

#### Resuming a Session

To resume a previous session:
1. Run the application with the `-r` or `--resume` flag
2. The application will load the previous session state
3. You'll continue from where you left off

#### Exiting Properly

To ensure all your work is saved:
1. Close the application by clicking the "Exit" button
2. Or close the browser window and stop the server with Ctrl+C

## Working with Files

### Image Directory Preparation

For best results:
1. Organize your images in a single directory
2. Use consistent image formats (JPG, PNG, etc.)
3. Remove any non-image files from the directory

### Output Directory Structure

After processing, the output directory will contain:
- Renamed image files with the specified prefix
- Text files with the same base name as the images
- A `tags.txt` file containing all used tags
- A `session.json` file with session information

Example output structure:
```
output/
├── img_001.jpg
├── img_001.txt
├── img_002.jpg
├── img_002.txt
└── tags.txt
└── session.json
```

### Tag File Format

The tag files are simple text files with one tag per line:
```
tag1
tag2
tag3
```

## Troubleshooting

### Common Issues

#### Application doesn't start

Check:
- Python version is 3.8 or higher
- All dependencies are installed
- The specified image directory exists and is readable

#### Images aren't loading

Check:
- Image formats are supported (JPG, PNG, GIF, BMP)
- Image files aren't corrupted
- You have permission to read the files

#### Changes aren't saving

Check:
- You have write permission to the output directory
- Disk space is available
- The application is running properly

### Error Messages

| Error Message | Possible Solution |
|---------------|-------------------|
| "Directory not found" | Verify the path to your image directory |
| "No image files found" | Ensure directory contains supported image formats |
| "Permission denied" | Check file and directory permissions |
| "Server error" | Check logs for details, restart application |

### Getting Help

If you encounter issues not covered in this guide:
1. Check the logs (enable verbose mode with `-v`)
2. Check for known issues in the GitHub repository
3. Submit a new issue with detailed information about the problem

## Best Practices

### Efficient Tagging Workflow

1. **Preparation**: Group similar images together in your source directory
2. **Organization**: Start with general tags, then add specific details
3. **Consistency**: Use consistent tag formats and conventions
4. **Regular Saves**: Save your work frequently (automatic with auto-save)
5. **Backups**: Make backups of your output directory periodically

### Tag Management Tips

1. **Standardize Case**: Decide on lowercase, title case, or specific conventions
2. **Use Specific Tags**: Be descriptive but concise
3. **Group Related Tags**: Consider grouping related concepts
4. **Avoid Duplication**: Use consistent terminology for similar concepts
5. **Use Multi-word Tags**: When necessary for clarity

## Advanced Usage

### Running on a Remote Server

To access the application from other devices on your network:

```bash
civitai-tagger /path/to/images --host 0.0.0.0 --port 8080
```

Then access from other devices using your server's IP address:
```
http://server-ip-address:8080
```

### Batch Processing

For large collections, consider processing in batches:
1. Organize images into manageable subdirectories
2. Process each subdirectory separately
3. Combine tag files if needed

## Appendix

### Keyboard Shortcuts

| Shortcut    | Action         |
|-------------|----------------|
| Right Arrow | Next image     |
| Left Arrow  | Previous image |
| Ctrl+S      | Save tags      |
| Ctrl+F      | Focus tag search |
| Tab         | Move between inputs |

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff, .tif)
- WebP (.webp)
