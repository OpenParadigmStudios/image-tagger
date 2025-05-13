# Step 3: Build Image Renaming and Copying Functionality

## Overview
In this step, we'll implement the functionality to rename image files with unique identifiers and copy them to the output directory. This builds on Steps 1 and 2, using the command-line arguments and file system operations already established. These functions will later be exposed through FastAPI endpoints.

## Requirements
- Generate unique names for each image file
- Copy images from the input directory to the output directory
- Preserve original file extensions
- Create corresponding empty text files for each image
- Track the mapping between original and new filenames
- Handle resume functionality by skipping already processed images
- Prepare for integration with FastAPI endpoints

## Implementation Details

### Core Libraries
- `shutil`: For file copying operations
- `uuid`: For generating unique identifiers (optional approach)
- `pathlib`: For path manipulation
- `os`: For file operations
- `pillow`: For validating and processing images

### Naming Strategies

#### 1. Sequential Numbering
- Format: `{prefix}_{number}.{extension}`
- Example: `img_001.jpg`, `img_002.png`
- Implementation:
  - Track the highest number used so far
  - Pad with leading zeros for consistent sorting (e.g., 001, 002)
  - Use prefix from command-line argument

#### 2. UUID-based (Alternative Approach)
- Format: `{prefix}_{uuid}.{extension}`
- Example: `img_5f3a12bc.jpg`
- Implementation:
  - Generate random UUID
  - Use shortened version for readability
  - Use prefix from command-line argument

### Functions to Implement

#### 1. `generate_unique_filename(original_path, prefix, processed_images)`
- Purpose: Create a unique filename for an image
- Input:
  - `original_path`: Path to the original image file
  - `prefix`: String prefix for the filename
  - `processed_images`: Dictionary of already processed images
- Output: A unique filename string
- Operations:
  - Extract original extension
  - Generate sequential number or UUID
  - Combine prefix, number/UUID, and extension
  - Check against existing files to ensure uniqueness

#### 2. `copy_image_to_output(original_path, output_dir, new_filename)`
- Purpose: Copy an image to the output directory with the new name
- Input:
  - `original_path`: Path to the original image file
  - `output_dir`: Path to the output directory
  - `new_filename`: The generated unique filename
- Output: Path to the copied file
- Operations:
  - Create full destination path
  - Copy the file using shutil
  - Verify copy was successful
  - Return the new path

#### 3. `create_text_file(image_path)`
- Purpose: Create an empty text file with the same name as the image but .txt extension
- Input: Path to the image file
- Output: Path to the created text file
- Operations:
  - Generate path with .txt extension
  - Create empty file
  - Return the path to the text file

#### 4. `process_image(original_path, output_dir, prefix, processed_images)`
- Purpose: Handle the complete processing of a single image
- Input:
  - `original_path`: Path to the original image
  - `output_dir`: Path to the output directory
  - `prefix`: Filename prefix to use
  - `processed_images`: Dictionary of already processed images
- Output:
  - Updated processed_images dictionary
  - Path to the new image
  - Path to the corresponding text file
- Operations:
  - Check if image already processed (in resume mode)
  - Generate unique filename
  - Copy image to output directory
  - Create corresponding text file
  - Update processed_images dictionary

#### 5. `get_next_sequence_number(processed_images, prefix)`
- Purpose: Find the next available sequence number for naming
- Input:
  - `processed_images`: Dictionary of processed images
  - `prefix`: Filename prefix being used
- Output: Integer representing next available number
- Operations:
  - Extract numbers from existing filenames with same prefix
  - Find maximum number
  - Return maximum + 1

#### 6. `validate_image_with_pillow(file_path)`
- Purpose: Replace deprecated imghdr with Pillow for image validation
- Input: Path to the image file
- Output: Boolean indicating if file is a valid image
- Operations:
  - Try to open and verify the image with Pillow
  - Return true if successful, false otherwise

### Error Handling
- Handle file permission errors during copying
- Deal with duplicate filenames (though should be prevented by design)
- Handle disk space issues
- Log detailed error information for debugging

## Code Structure

### Integration with Previous Steps
- Use the validated input directory from Step 1
- Use the output directory created in Step 2
- Use the processed_images dictionary from Step 2 when in resume mode
- Use the prefix from command-line arguments in Step 1

### Integration with Web Architecture
- Design functions to be callable from FastAPI endpoints
- Make sure file paths are validated for security
- Use appropriate error responses for web API context
- Prepare for asynchronous operation where appropriate

### Processing Flow
1. Get list of image files from `scan_image_files()` (Step 2)
2. Set up output directory using `setup_directory_structure()` (Step 2)
3. If resuming, load processed_images using `get_processed_images()` (Step 2)
4. For each unprocessed image:
   - Process using `process_image()`
   - Update session state using `save_session_state()` (Step 2)

## Testing Strategy
- Test with various image types and extensions
- Test sequential numbering works correctly
- Test resume functionality by processing in multiple sessions
- Test error cases (permissions, disk space)
- Test with large numbers of files to ensure naming scheme scales
- Test the functions can be properly called from a web context

## Implementation Steps
1. Replace deprecated imghdr with Pillow-based image validation
2. Implement the filename generation function
3. Create the image copying function
4. Develop the text file creation function
5. Build the main image processing function
6. Add sequence numbering helper
7. Integrate with file system operations from Step 2
8. Add proper error handling and logging
9. Test with various image sets and scenarios

## Next Steps After Completion
Once this step is complete, we'll be able to:
- Process a directory of images
- Create uniquely named copies in the output directory
- Generate corresponding empty text files
- Track which images have been processed
- Prepare for the next steps of server setup and tag management
