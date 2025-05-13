# Step 1: Set Up Basic Command Line Argument Parsing

## Overview
In this step, we'll establish the command-line interface for our CivitAI Flux Dev LoRA Tagging Assistant. This will allow users to provide the necessary input directory path and optional configuration settings.

## Requirements
- Accept a directory path as the primary input
- Validate that the provided path exists and is a directory
- Handle optional arguments for configuration
- Provide help text and usage information
- Establish a structure that will support future functionality

## Implementation Details

### Core Libraries
- `argparse`: Python's standard library for command-line argument parsing
- `pathlib`: For path validation and manipulation (more modern and object-oriented than os)
- `typing`: For type hints to improve code quality and IDE support

### Arguments to Implement

#### Required Arguments
1. `input_directory`: The path to the directory containing images to process
   - Type: string (will be converted to Path object)
   - Validation: Must exist and be a directory

#### Optional Arguments
1. `--output-dir`, `-o`: Specify a custom output directory name (default: "output")
   - Type: string
   - Default: "output"

2. `--resume`, `-r`: Flag to resume from a previous session
   - Type: boolean flag
   - Default: False

3. `--prefix`, `-p`: Prefix for renamed image files
   - Type: string
   - Default: "img"

4. `--verbose`, `-v`: Enable verbose logging
   - Type: boolean flag
   - Default: False
   
5. `--auto-save`, `-a`: Time interval in seconds for auto-saving session state
   - Type: integer
   - Default: 60 (1 minute)

### Validation Logic
- Check if input directory exists using pathlib
- Check if input directory contains image files
- If resuming, check if session state exists
- Create output directory if it doesn't exist

### Error Handling
- Clear error messages for common issues:
  - Directory does not exist
  - Path exists but is not a directory
  - Directory contains no valid images
  - Cannot create output directory (permissions)
- Use custom exceptions for specific error cases
- Enable debug output when verbose flag is active

## Code Structure

### Function Breakdown
1. `parse_arguments()`: Set up and process command line arguments
2. `validate_directory(path: Path) -> bool`: Verify directory exists and contains images
3. `setup_output_directory(input_dir: Path, output_name: str) -> Path`: Create the output directory
4. `setup_logging(verbose: bool)`: Configure logging based on verbosity level

### Main Entry Point
- Create a `main()` function that calls the argument parsing
- Add a standard `if __name__ == "__main__":` block
- Keep the main script modular for future integration
- Use dataclasses to structure arguments and application configuration

## Example Usage
```
# Basic usage with just input directory
python civitai_tagger.py /path/to/images

# Specifying custom output directory name
python civitai_tagger.py /path/to/images -o custom_output

# Resume previous session
python civitai_tagger.py /path/to/images -r

# Combine multiple options
python civitai_tagger.py /path/to/images -o custom_output -p lora_ -r -v

# Set auto-save interval to 2 minutes
python civitai_tagger.py /path/to/images -a 120
```

## Testing Strategy
- Test with valid directory paths
- Test with non-existent paths
- Test with paths to files instead of directories
- Test with empty directories
- Test the resume flag with and without existing session data
- Test with various combinations of optional arguments

## Implementation Steps
1. Create a new Python file `civitai_tagger.py`
2. Import required libraries
3. Create a configuration dataclass for application settings
4. Implement the argument parsing function
5. Add validation logic for the input directory
6. Implement the output directory setup
7. Create logging configuration function
8. Create the main function that integrates these components
9. Test the script with various input scenarios

## Next Steps After Completion
Once this step is complete, we'll be able to:
- Accept an input directory path
- Validate the input
- Set up the output directory structure
- Configure logging based on verbosity
- Prepare for the next step of scanning and processing images 