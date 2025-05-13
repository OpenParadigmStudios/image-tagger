/**
 * CivitAI Flux Dev LoRA Tagging Assistant
 * Image Viewer Module
 */

import { api } from './api.js';
import { websocket } from './websocket.js';

/**
 * Image Viewer class to handle image display and navigation
 */
class ImageViewer {
    /**
     * Initialize the image viewer
     */
    constructor() {
        // State
        this.currentImageId = null;
        this.totalImages = 0;
        this.imageInfo = null;

        // Elements
        this.elements = {
            image: document.getElementById('preview-image'),
            imageName: document.getElementById('image-name'),
            imageDimensions: document.getElementById('image-dimensions'),
            prevButton: document.getElementById('prev-button'),
            nextButton: document.getElementById('next-button')
        };

        // Bind methods
        this.loadImage = this.loadImage.bind(this);
        this.previousImage = this.previousImage.bind(this);
        this.nextImage = this.nextImage.bind(this);
        this.updateNavigationButtons = this.updateNavigationButtons.bind(this);

        // Event listeners
        this.elements.prevButton.addEventListener('click', this.previousImage);
        this.elements.nextButton.addEventListener('click', this.nextImage);

        // WebSocket event listeners
        document.addEventListener('ws:session_state', (e) => this.handleSessionState(e.detail));
        document.addEventListener('ws:image_data', (e) => this.handleImageData(e.detail));
    }

    /**
     * Initialize the image viewer
     * @param {number} totalImages - Total number of images
     */
    initialize(totalImages) {
        this.totalImages = totalImages;
        this.updateNavigationButtons();
    }

    /**
     * Handle session state update
     * @param {Object} data - Session state data
     */
    handleSessionState(data) {
        this.totalImages = data.total_images || 0;

        // If we have a current position from the server and no image loaded
        if (data.current_position !== null && this.currentImageId === null) {
            this.loadImage(data.current_position);
        } else {
            this.updateNavigationButtons();
        }
    }

    /**
     * Handle image data from WebSocket
     * @param {Object} data - Image data
     */
    handleImageData(data) {
        console.log('Received image data:', data);
        this.imageInfo = data;
        this.currentImageId = data.id;

        // Update image with loading status
        this.elements.image.classList.add('loading');

        // Create a new image object to preload and handle errors
        const imgLoader = new Image();
        imgLoader.onload = () => {
            // Once loaded, update the displayed image
            this.elements.image.src = data.url;
            this.elements.image.classList.remove('loading');
            this.elements.imageName.textContent = data.original_name;

            // Update dimensions if available
            if (imgLoader.naturalWidth && imgLoader.naturalHeight) {
                this.elements.imageDimensions.textContent =
                    `${imgLoader.naturalWidth} × ${imgLoader.naturalHeight}`;
            }

            // Dispatch event that image has been loaded
            const event = new CustomEvent('imageLoaded', {
                detail: {
                    imageId: data.id,
                    tags: data.tags || []
                }
            });
            document.dispatchEvent(event);
        };

        imgLoader.onerror = () => {
            console.error('Failed to load image:', data.url);
            this.elements.image.src = '/static/assets/placeholder.png';
            this.elements.image.classList.remove('loading');
            this.elements.imageName.textContent = `Error loading: ${data.original_name}`;
            this.elements.imageDimensions.textContent = '';
        };

        // Start loading the image
        imgLoader.src = data.url;

        // Update navigation buttons
        this.updateNavigationButtons();
    }

    /**
     * Load an image by ID
     * @param {string} imageId - Image ID to load
     */
    async loadImage(imageId) {
        if (imageId === this.currentImageId) return;

        try {
            // Set loading state
            this.elements.image.classList.add('loading');
            this.elements.imageName.textContent = 'Loading...';
            this.elements.imageDimensions.textContent = '';

            // Request image data via WebSocket for real-time updates
            websocket.sendMessage('get_image', { image_id: imageId });

            this.currentImageId = imageId;
            this.updateNavigationButtons();
        } catch (error) {
            console.error(`Error loading image ${imageId}:`, error);
            this.elements.imageName.textContent = 'Error loading image';
        } finally {
            this.elements.image.classList.remove('loading');
        }
    }

    /**
     * Navigate to the previous image
     */
    previousImage() {
        if (this.currentImageId === null) return;

        const currentIndex = parseInt(this.currentImageId);
        if (currentIndex > 0) {
            this.loadImage((currentIndex - 1).toString());
        }
    }

    /**
     * Navigate to the next image
     */
    nextImage() {
        if (this.currentImageId === null) return;

        const currentIndex = parseInt(this.currentImageId);
        if (currentIndex < this.totalImages - 1) {
            this.loadImage((currentIndex + 1).toString());
        }
    }

    /**
     * Update the state of navigation buttons
     */
    updateNavigationButtons() {
        if (this.currentImageId === null) {
            this.elements.prevButton.disabled = true;
            this.elements.nextButton.disabled = true;
            return;
        }

        const currentIndex = parseInt(this.currentImageId);
        this.elements.prevButton.disabled = currentIndex <= 0;
        this.elements.nextButton.disabled = currentIndex >= this.totalImages - 1;
    }

    /**
     * Handle image load event to update dimensions
     * @param {Event} event - Image load event
     */
    handleImageLoad(event) {
        const img = event.target;
        if (img.naturalWidth && img.naturalHeight) {
            this.elements.imageDimensions.textContent =
                `${img.naturalWidth} × ${img.naturalHeight}`;
        } else {
            this.elements.imageDimensions.textContent = '';
        }
    }
}

// Create and export the image viewer instance
export const imageViewer = new ImageViewer();
