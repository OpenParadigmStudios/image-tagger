/**
 * CivitAI Flux Dev LoRA Tagging Assistant
 * Main application JavaScript
 */

import { api } from './api.js';
import { websocket } from './websocket.js';
import { imageViewer } from './imageViewer.js';
import { tagManager } from './tagManager.js';
import { sessionManager } from './sessionManager.js';

/**
 * Initialize the application
 */
async function initializeApp() {
    console.log('Initializing application...');

    // Set up event listener for image loading
    document.getElementById('preview-image').addEventListener('load', function (event) {
        // Update image dimensions when loaded
        const img = event.target;
        if (img.naturalWidth && img.naturalHeight) {
            document.getElementById('image-dimensions').textContent =
                `${img.naturalWidth} × ${img.naturalHeight}`;
        }
    });

    // Set up event listener for session state
    document.addEventListener('ws:session_update', (e) => {
        console.log('Session state received:', e.detail);

        // If we have images but no current image loaded, request the first image
        if (e.detail.stats && e.detail.stats.total_images > 0) {
            // Either load the current position or the first image (index 0)
            const imageIdToLoad = e.detail.current_position !== null ? e.detail.current_position : '0';
            console.log('Loading initial image:', imageIdToLoad);
            websocket.sendMessage('get_image', { image_id: imageIdToLoad });
        }
    });

    // Connect to WebSocket server
    await websocket.connect();

    // Initialize components
    await sessionManager.initialize();

    // Request initial session state and tags
    websocket.sendMessage('session_request');
    websocket.sendMessage('get_tags');
}

// Start the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeApp);
