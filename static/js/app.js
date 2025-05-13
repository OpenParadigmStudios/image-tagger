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

    // Connect to WebSocket server
    await websocket.connect();

    // Initialize components
    await sessionManager.initialize();

    // Request initial session state
    websocket.sendMessage('get_tags');
}

// Start the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeApp);
