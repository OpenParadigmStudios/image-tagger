/**
 * CivitAI Flux Dev LoRA Tagging Assistant
 * Tag Manager Module
 */

import { api } from './api.js';
import { websocket } from './websocket.js';

/**
 * Tag Manager class to handle tag selection and management
 */
class TagManager {
    /**
     * Initialize the tag manager
     */
    constructor() {
        // State
        this.tags = [];
        this.selectedTags = [];
        this.currentImageId = null;
        this.pendingTagUpdates = false;

        // Elements
        this.elements = {
            newTagInput: document.getElementById('new-tag'),
            addTagButton: document.getElementById('add-tag-button'),
            allTagsContainer: document.getElementById('all-tags'),
            saveTagsButton: document.getElementById('save-tags-button')
        };

        // Bind methods
        this.addNewTag = this.addNewTag.bind(this);
        this.toggleTagSelection = this.toggleTagSelection.bind(this);
        this.saveTags = this.saveTags.bind(this);
        this.loadTags = this.loadTags.bind(this);

        // Event listeners
        this.elements.addTagButton.addEventListener('click', this.addNewTag);
        this.elements.newTagInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addNewTag();
        });
        this.elements.saveTagsButton.addEventListener('click', this.saveTags);

        // Listen for image loaded event
        document.addEventListener('imageLoaded', (e) => this.handleImageLoaded(e.detail));

        // WebSocket event listeners
        document.addEventListener('ws:session_state', (e) => this.handleSessionState(e.detail));
        document.addEventListener('ws:tag_update', (e) => this.handleTagUpdate(e.detail));
        document.addEventListener('ws:tags_update', (e) => this.handleTagsUpdate(e.detail));
        document.addEventListener('ws:tags_updated', (e) => this.handleTagsUpdate(e.detail));
        document.addEventListener('ws:image_data', (e) => this.handleImageData(e.detail));
        document.addEventListener('ws:tags_saved', (e) => this.handleTagsSaved(e.detail));
        document.addEventListener('ws:connect', () => this.requestTags());
    }

    /**
     * Request all tags from the server on connection
     */
    requestTags() {
        websocket.sendMessage('get_tags');
    }

    /**
     * Handle session state update
     * @param {Object} data - Session state data
     */
    handleSessionState(data) {
        if (data.tags) {
            this.tags = data.tags;
            this.renderTagList();
        }
    }

    /**
     * Handle tag update from WebSocket
     * @param {Object} data - Tag update data
     */
    handleTagUpdate(data) {
        console.log('Received tag update:', data);

        // Update tags list from all_tags field if present
        if (data.all_tags) {
            this.tags = data.all_tags;
            console.log('Updated master tag list, now has', this.tags.length, 'tags');
        }

        // If this update is for the current image, update selected tags
        if (data.image_id === this.currentImageId) {
            console.log('Updating selected tags for current image:', data.tags);
            this.selectedTags = data.tags || [];
            this.pendingTagUpdates = false;
        }

        // Always render the tag list to show updates
        this.renderTagList();
        this.updateSaveButton(this.currentImageId === data.image_id);
    }

    /**
     * Handle tags update from WebSocket
     * @param {Object} data - Tags update data
     */
    handleTagsUpdate(data) {
        console.log('Received tags update:', data);
        if (data.tags) {
            this.tags = data.tags;
            console.log('Updated all tags, now has', this.tags.length, 'tags');
            this.renderTagList();
        }
    }

    /**
     * Handle image data from WebSocket
     * @param {Object} data - Image data
     */
    handleImageData(data) {
        if (data.id) {
            this.currentImageId = data.id;
            this.selectedTags = data.tags || [];
            this.renderTagList();
            this.updateSaveButton();
        }
    }

    /**
     * Handle tags saved event
     * @param {Object} data - Tags saved data
     */
    handleTagsSaved(data) {
        if (data.image_id === this.currentImageId) {
            this.selectedTags = data.tags || [];
            this.pendingTagUpdates = false;
            this.renderTagList();
            this.updateSaveButton(true);
        }
    }

    /**
     * Handle image loaded event
     * @param {Object} data - Image loaded data
     */
    handleImageLoaded(data) {
        this.currentImageId = data.imageId;
        this.selectedTags = data.tags || [];
        this.renderTagList();
        this.updateSaveButton();
    }

    /**
     * Load all available tags from the server
     */
    async loadTags() {
        try {
            const response = await api.getAllTags();
            this.tags = response.tags || [];
            this.renderTagList();
        } catch (error) {
            console.error('Error loading tags:', error);
        }
    }

    /**
     * Add a new tag
     */
    async addNewTag() {
        const newTag = this.elements.newTagInput.value.trim();

        if (!newTag) return;

        try {
            // Send to server
            await api.addTag(newTag);

            // Clear input
            this.elements.newTagInput.value = '';

            // Add to our local list of tags if not already present
            if (!this.tags.includes(newTag)) {
                this.tags.push(newTag);
                this.tags.sort();
            }

            // Select this tag for the current image if one is loaded
            if (this.currentImageId !== null && !this.selectedTags.includes(newTag)) {
                this.selectedTags.push(newTag);
                this.pendingTagUpdates = true;
                this.updateSaveButton();
            }

            // Update UI
            this.renderTagList();
        } catch (error) {
            console.error(`Error adding tag "${newTag}":`, error);
        }
    }

    /**
     * Toggle tag selection
     * @param {string} tag - Tag to toggle
     * @param {HTMLElement} element - Tag DOM element
     */
    toggleTagSelection(tag, element) {
        const index = this.selectedTags.indexOf(tag);

        if (index >= 0) {
            // Remove tag
            this.selectedTags.splice(index, 1);
            element.classList.remove('selected');
        } else {
            // Add tag
            this.selectedTags.push(tag);
            element.classList.add('selected');
        }

        this.pendingTagUpdates = true;
        this.updateSaveButton();
    }

    /**
     * Save tags for the current image
     */
    async saveTags() {
        if (!this.currentImageId) {
            console.warn('No image selected, cannot save tags');
            return;
        }

        if (!this.pendingTagUpdates) {
            console.log('No pending tag updates to save');
            return;
        }

        try {
            console.log(`Saving tags for image ${this.currentImageId}:`, this.selectedTags);

            // First use HTTP API to ensure persistence
            const apiResponse = await api.updateImageTags(this.currentImageId, this.selectedTags);
            console.log('API response for updateImageTags:', apiResponse);

            // Then send via WebSocket for real-time update
            websocket.sendMessage('update_tags', {
                image_id: this.currentImageId,
                tags: this.selectedTags
            });

            // Disable save button
            this.pendingTagUpdates = false;
            this.updateSaveButton(true);
        } catch (error) {
            console.error('Error saving tags:', error);
            // Try to revert UI to pending state
            this.updateSaveButton(false);
        }
    }

    /**
     * Update the save button state
     * @param {boolean} saved - Whether tags were just saved
     */
    updateSaveButton(saved = false) {
        if (saved) {
            this.elements.saveTagsButton.disabled = true;
            this.elements.saveTagsButton.textContent = 'Saved';
            setTimeout(() => {
                this.elements.saveTagsButton.textContent = 'Save Tags';
                this.elements.saveTagsButton.disabled = !this.currentImageId || !this.pendingTagUpdates;
            }, 1500);
        } else {
            this.elements.saveTagsButton.disabled = !this.currentImageId || !this.pendingTagUpdates;
            this.elements.saveTagsButton.textContent = 'Save Tags';
        }
    }

    /**
     * Render the tag list
     */
    renderTagList() {
        const allTagsContainer = this.elements.allTagsContainer;
        allTagsContainer.innerHTML = '';

        // Sort alphabetically
        const sortedTags = [...this.tags].sort();

        // Create tag elements
        sortedTags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'tag';
            if (this.selectedTags.includes(tag)) {
                tagElement.classList.add('selected');
            }
            tagElement.textContent = tag;
            tagElement.addEventListener('click', () => this.toggleTagSelection(tag, tagElement));

            allTagsContainer.appendChild(tagElement);
        });
    }
}

// Create and export the tag manager instance
export const tagManager = new TagManager();
