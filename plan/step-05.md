# Step 5: Develop Tag Management System with API

## Overview
In this step, we'll implement the tag management system as API endpoints that will allow the client to create, store, and apply tags to images. This functionality is essential for the core purpose of the application - creating text files with appropriate tags for each image for CivitAI Flux Dev LoRA model training.

## Requirements
- Create API endpoints to manage the master list of tags
- Implement functions to read and write tags to text files
- Provide methods to add, remove, and update tags via API
- Enable associating tags with specific images through API calls
- Support persistent storage of tag data
- Integrate with the session state system and WebSocket for real-time updates

## Implementation Details

### Core Libraries
- `fastapi`: For API endpoint implementation
- `json`: For tag data serialization
- `pathlib`: For file path handling
- `pydantic`: For request/response models

### Tag Management Models

#### 1. `Tag` Pydantic Model
```python
class Tag(BaseModel):
    name: str
    description: Optional[str] = None
```

#### 2. `TagList` Pydantic Model
```python
class TagList(BaseModel):
    tags: List[str]
```

#### 3. `ImageTags` Pydantic Model
```python
class ImageTags(BaseModel):
    image_id: str
    tags: List[str]
```

### Tag Management API Endpoints

#### 1. `GET /api/tags`
- Purpose: Retrieve the master list of tags
- Response: TagList object containing all available tags

#### 2. `POST /api/tags`
- Purpose: Add a new tag to the master list
- Request: Tag object with the new tag information
- Response: Updated TagList or error message

#### 3. `DELETE /api/tags/{tag_name}`
- Purpose: Remove a tag from the master list
- Request: Tag name in the URL
- Response: Updated TagList or error message

#### 4. `GET /api/images/{image_id}/tags`
- Purpose: Get tags associated with a specific image
- Request: Image ID in the URL
- Response: ImageTags object with the image's tags

#### 5. `PUT /api/images/{image_id}/tags`
- Purpose: Update tags for a specific image
- Request: TagList object in the body, Image ID in the URL
- Response: Updated ImageTags or error message

### Tag Management Functions to Implement

#### 1. `load_tags(tags_file_path: Path) -> List[str]`
- Purpose: Load the existing tags from the tags file
- Input: Path to the tags file
- Output: List of existing tags
- Operations:
  - Open and read the tags file
  - Parse each line as a tag
  - Return list of tags
  - Handle case where file doesn't exist (return empty list)

#### 2. `save_tags(tags_file_path: Path, tags_list: List[str]) -> bool`
- Purpose: Save the current tags list to the tags file
- Input:
  - Path to the tags file
  - List of tags to save
- Output: Boolean indicating success
- Operations:
  - Sort tags alphabetically for consistency
  - Write each tag on a separate line
  - Handle file permissions and other errors

#### 3. `add_tag(tags_list: List[str], new_tag: str) -> List[str]`
- Purpose: Add a new tag to the tags list if it doesn't exist
- Input:
  - Current list of tags
  - New tag to add
- Output: Updated list of tags
- Operations:
  - Check if tag already exists (case-insensitive)
  - Clean/normalize the tag (trim whitespace, handle formatting)
  - Add to list if new
  - Return updated list

#### 4. `remove_tag(tags_list: List[str], tag_to_remove: str) -> List[str]`
- Purpose: Remove a tag from the tags list
- Input:
  - Current list of tags
  - Tag to remove
- Output: Updated list of tags
- Operations:
  - Find tag in list (case-insensitive)
  - Remove if found
  - Return updated list

#### 5. `get_image_tags(text_file_path: Path) -> List[str]`
- Purpose: Get the tags associated with a specific image
- Input: Path to the text file for the image
- Output: List of tags for the image
- Operations:
  - Read the text file
  - Parse content to extract tags (comma or newline separated)
  - Return list of tags
  - Handle case where file is empty or doesn't exist

#### 6. `save_image_tags(text_file_path: Path, tags_list: List[str]) -> bool`
- Purpose: Save tags for a specific image to its text file
- Input:
  - Path to the text file
  - List of tags to save
- Output: Boolean indicating success
- Operations:
  - Join tags with commas
  - Write to the text file
  - Handle file permissions and other errors

#### 7. `normalize_tag(tag: str) -> str`
- Purpose: Clean and standardize tag format
- Input: Raw tag string
- Output: Normalized tag string
- Operations:
  - Trim whitespace
  - Remove invalid characters
  - Handle case formatting (e.g., lowercase)
  - Apply any other standardization rules

#### 8. `broadcast_tag_update(websocket_manager, update_type: str, data: dict) -> None`
- Purpose: Broadcast tag updates to all connected clients
- Input:
  - WebSocket manager instance
  - Update type (e.g., "new_tag", "updated_image_tags")
  - Data related to the update
- Operations:
  - Format update message
  - Send to all connected clients via WebSocket

### Tag Data Structure
- Simple list of strings for the main tags list
- Text files with comma-separated values for image-specific tags
- WebSocket messages for real-time updates

### Error Handling
- Implement proper HTTP error responses for API endpoints
- Handle file I/O errors when reading/writing tag files
- Validate tags for format and content
- Log appropriate error messages

## Code Structure

### Integration with Previous Steps
- Use the FastAPI application from Step 4
- Use the output directory from Steps 1 and 2
- Use the text files created in Step 3
- Update the session state from Step 2 with tag information

### Tag Management Workflow
1. Initialize tag system by loading existing tags when server starts
2. When processing an image:
   - Client requests tags for the current image
   - Server sends the current image's tags and master tag list
   - Client displays tags for selection and editing
   - Client sends updated tags to server
   - Server saves selected tags to the image's text file
   - Server updates the master tags list if new tags added
   - Server broadcasts tag updates to all connected clients
   - Server updates session state

## Testing Strategy
- Test API endpoints for tag management
- Test loading and saving tags to the master list
- Test adding and removing tags
- Test associating tags with specific images
- Test tag normalization and formatting
- Test WebSocket broadcast of tag updates
- Test with various edge cases (empty files, special characters, etc.)

## Implementation Steps
1. Create Pydantic models for tag-related data
2. Implement the tag loading and saving functions
3. Create the tag addition and removal methods
4. Develop the image-specific tag handling functions
5. Add tag normalization functionality
6. Implement API endpoints for tag management
7. Add WebSocket notifications for tag updates
8. Integrate with the existing session state system
9. Add proper error handling and validation
10. Test all tag management functions and API endpoints

## Next Steps After Completion
Once this step is complete, we'll be able to:
- Maintain a master list of all tags through API endpoints
- Associate specific tags with individual images
- Save and load tag data persistently
- Broadcast tag updates to connected clients
- Prepare for implementing the client-side interface
