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
        this.recentlyUsedTags = [];
        this.currentImageId = null;
        this.filterText = '';

        // Elements
        this.elements = {
            tagFilter: document.getElementById('tag-filter'),
            newTagInput: document.getElementById('new-tag'),
            addTagButton: document.getElementById('add-tag-button'),
            recentTagsContainer: document.getElementById('recent-tags'),
            allTagsContainer: document.getElementById('all-tags'),
            saveTagsButton: document.getElementById('save-tags-button')
        };

        // Bind methods
        this.filterTags = this.filterTags.bind(this);
        this.addNewTag = this.addNewTag.bind(this);
        this.toggleTagSelection = this.toggleTagSelection.bind(this);
        this.saveTags = this.saveTags.bind(this);
        this.loadTags = this.loadTags.bind(this);

        // Event listeners
        this.elements.tagFilter.addEventListener('input', this.filterTags);
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
        // Update tags list
        if (data.tags) {
            this.tags = data.tags;
            this.renderTagList();
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
     * Filter tags based on input
     */
    filterTags() {
        this.filterText = this.elements.tagFilter.value.trim().toLowerCase();
        this.renderTagList();
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

            // Select this tag for the current image if one is loaded
            if (this.currentImageId !== null && !this.selectedTags.includes(newTag)) {
                this.selectedTags.push(newTag);
                this.addToRecentlyUsed(newTag);
                this.updateSaveButton();
            }
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
            this.addToRecentlyUsed(tag);
        }

        this.updateSaveButton();
    }

    /**
     * Add a tag to recently used
     * @param {string} tag - Tag to add to recently used
     */
    addToRecentlyUsed(tag) {
        // Remove if already exists
        const index = this.recentlyUsedTags.indexOf(tag);
        if (index >= 0) {
            this.recentlyUsedTags.splice(index, 1);
        }

        // Add to beginning
        this.recentlyUsedTags.unshift(tag);

        // Keep only 10 most recent
        if (this.recentlyUsedTags.length > 10) {
            this.recentlyUsedTags.pop();
        }

        this.renderRecentTags();
    }

    /**
     * Save tags for the current image
     */
    async saveTags() {
        if (!this.currentImageId) return;

        try {
            // Send to server via WebSocket for real-time update
            websocket.sendMessage('update_tags', {
                image_id: this.currentImageId,
                tags: this.selectedTags
            });

            // Also use HTTP API as fallback
            await api.updateImageTags(this.currentImageId, this.selectedTags);

            // Disable save button
            this.updateSaveButton(true);
        } catch (error) {
            console.error('Error saving tags:', error);
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
                this.elements.saveTagsButton.disabled = !this.currentImageId;
            }, 1500);
        } else {
            this.elements.saveTagsButton.disabled = !this.currentImageId;
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

        // Filter if needed
        const filteredTags = this.filterText
            ? sortedTags.filter(tag => tag.toLowerCase().includes(this.filterText))
            : sortedTags;

        // Create tag elements
        filteredTags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'tag';
            if (this.selectedTags.includes(tag)) {
                tagElement.classList.add('selected');
            }
            tagElement.textContent = tag;
            tagElement.addEventListener('click', () => this.toggleTagSelection(tag, tagElement));

            allTagsContainer.appendChild(tagElement);
        });

        // Update recent tags
        this.renderRecentTags();
    }

    /**
     * Render recently used tags
     */
    renderRecentTags() {
        const recentContainer = this.elements.recentTagsContainer;
        recentContainer.innerHTML = '';

        this.recentlyUsedTags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'tag';
            if (this.selectedTags.includes(tag)) {
                tagElement.classList.add('selected');
            }
            tagElement.textContent = tag;
            tagElement.addEventListener('click', () => this.toggleTagSelection(tag, tagElement));

            recentContainer.appendChild(tagElement);
        });
    }
}

// Create and export the tag manager instance
export const tagManager = new TagManager();
