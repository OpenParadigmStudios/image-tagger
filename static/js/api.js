/**
 * CivitAI Flux Dev LoRA Tagging Assistant
 * API Client for server communication
 */

/**
 * API Client for handling HTTP requests to the server
 */
class ApiClient {
    /**
     * Get the list of all images
     * @param {number} limit - Maximum number of images to return
     * @param {number} offset - Number of images to skip
     * @returns {Promise<Object>} - Image list data
     */
    async getImages(limit = 100, offset = 0) {
        try {
            const response = await fetch(`/api/images/?limit=${limit}&offset=${offset}`);
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching images:', error);
            throw error;
        }
    }

    /**
     * Get information about a specific image
     * @param {string} imageId - Image ID
     * @returns {Promise<Object>} - Image information
     */
    async getImageInfo(imageId) {
        try {
            const response = await fetch(`/api/images/${imageId}`);
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching image info for ID ${imageId}:`, error);
            throw error;
        }
    }

    /**
     * Get the URL for an image file
     * @param {string} imageId - Image ID
     * @returns {string} - Image URL
     */
    getImageUrl(imageId) {
        return `/api/images/${imageId}/file`;
    }

    /**
     * Get tags for a specific image
     * @param {string} imageId - Image ID
     * @returns {Promise<Object>} - Image tags data
     */
    async getImageTags(imageId) {
        try {
            const response = await fetch(`/api/images/${imageId}/tags`);
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching tags for image ID ${imageId}:`, error);
            throw error;
        }
    }

    /**
     * Update tags for a specific image
     * @param {string} imageId - Image ID
     * @param {Array<string>} tags - List of tags
     * @returns {Promise<Object>} - Updated image tags
     */
    async updateImageTags(imageId, tags) {
        try {
            const response = await fetch(`/api/images/${imageId}/tags`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_id: imageId,
                    tags: tags
                }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error updating tags for image ID ${imageId}:`, error);
            throw error;
        }
    }

    /**
     * Get all available tags
     * @returns {Promise<Object>} - Tags data
     */
    async getAllTags() {
        try {
            const response = await fetch('/api/tags/');
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching all tags:', error);
            throw error;
        }
    }

    /**
     * Add a new tag
     * @param {string} tagName - Tag name
     * @returns {Promise<Object>} - Updated tags list
     */
    async addTag(tagName) {
        try {
            const response = await fetch('/api/tags/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: tagName
                }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error adding tag "${tagName}":`, error);
            throw error;
        }
    }

    /**
     * Delete a tag
     * @param {string} tagName - Tag name
     * @returns {Promise<Object>} - Updated tags list
     */
    async deleteTag(tagName) {
        try {
            const response = await fetch(`/api/tags/${encodeURIComponent(tagName)}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error deleting tag "${tagName}":`, error);
            throw error;
        }
    }

    /**
     * Get application status
     * @returns {Promise<Object>} - Status data
     */
    async getStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching application status:', error);
            throw error;
        }
    }
}

// Export a singleton instance
export const api = new ApiClient();
