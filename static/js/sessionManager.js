/**
 * CivitAI Flux Dev LoRA Tagging Assistant
 * Session Manager Module
 */

import { api } from './api.js';
import { websocket } from './websocket.js';
import { imageViewer } from './imageViewer.js';

/**
 * Session Manager class to handle session state and controls
 */
class SessionManager {
    /**
     * Initialize the session manager
     */
    constructor() {
        // State
        this.sessionInfo = {
            total_images: 0,
            processed_images: 0,
            current_position: null,
            version: null
        };

        // Elements
        this.elements = {
            totalImages: document.getElementById('total-images'),
            processedImages: document.getElementById('processed-images'),
            progressBar: document.getElementById('progress-bar'),
            saveButton: document.getElementById('save-session-button'),
            exitButton: document.getElementById('exit-button'),
            statusMessage: document.getElementById('status-message')
        };

        // Bind methods
        this.initialize = this.initialize.bind(this);
        this.updateSessionStatus = this.updateSessionStatus.bind(this);
        this.showStatusMessage = this.showStatusMessage.bind(this);
        this.saveSession = this.saveSession.bind(this);
        this.confirmExit = this.confirmExit.bind(this);

        // Event listeners
        this.elements.saveButton.addEventListener('click', this.saveSession);
        this.elements.exitButton.addEventListener('click', this.confirmExit);

        // WebSocket event listeners
        document.addEventListener('ws:session_update', (e) => this.handleSessionUpdate(e.detail));
        document.addEventListener('ws:stats_update', (e) => this.handleStatsUpdate(e.detail));
        document.addEventListener('ws:session_saved', (e) => this.handleSessionSaved(e.detail));
        document.addEventListener('ws:connect', () => this.handleConnection());
        document.addEventListener('ws:connectionStatusChanged', (e) => this.handleConnectionStatus(e.detail));

        // Handle image loaded events to track current position
        document.addEventListener('imageLoaded', (e) => this.handleImageLoaded(e.detail));
    }

    /**
     * Initialize the session manager
     */
    async initialize() {
        try {
            // Request initial session state
            console.log('Initializing session manager...');
            websocket.sendMessage('session_request');
            this.showStatusMessage('Session initialized', 'success');
        } catch (error) {
            console.error('Error initializing session:', error);
            this.showStatusMessage('Error initializing session', 'error');
        }
    }

    /**
     * Handle session state update from WebSocket
     * @param {Object} data - Session state data
     */
    handleSessionUpdate(data) {
        console.log('Session update received:', data);

        // Update session info
        this.sessionInfo = {
            ...this.sessionInfo,
            current_position: data.current_position,
            version: data.version,
            ...data.stats
        };

        // Update UI
        this.updateSessionStatus();

        // Initialize the image viewer with total images count
        if (this.sessionInfo.total_images > 0) {
            imageViewer.initialize(this.sessionInfo.total_images);

            // If no image is loaded yet and we have a valid current position, load it
            if (imageViewer.currentImageId === null && this.sessionInfo.current_position !== null) {
                console.log('Loading image from session position:', this.sessionInfo.current_position);
                websocket.sendMessage('get_image', { image_id: this.sessionInfo.current_position });
            } else if (imageViewer.currentImageId === null && this.sessionInfo.total_images > 0) {
                // Otherwise start with the first image
                console.log('No current position, loading first image');
                websocket.sendMessage('get_image', { image_id: '0' });
            }
        }
    }

    /**
     * Handle stats update from WebSocket
     * @param {Object} data - Stats data
     */
    handleStatsUpdate(data) {
        // Update session info with new stats
        this.sessionInfo = {
            ...this.sessionInfo,
            ...data
        };

        // Update UI
        this.updateSessionStatus();
    }

    /**
     * Handle session saved confirmation
     * @param {Object} data - Session saved data
     */
    handleSessionSaved(data) {
        this.showStatusMessage('Session saved successfully', 'success');
    }

    /**
     * Handle WebSocket connection event
     */
    handleConnection() {
        // Request session state when connected
        console.log('WebSocket connected, requesting session info...');
        websocket.sendMessage('session_request');

        this.showStatusMessage('Connected to server', 'success');
    }

    /**
     * Handle connection status change
     * @param {Object} data - Connection status data
     */
    handleConnectionStatus(data) {
        const connectionStatus = document.getElementById('connection-status');
        if (data.connected) {
            connectionStatus.textContent = 'Connected';
            connectionStatus.className = 'status-indicator connected';
            this.showStatusMessage('Connected to server', 'success');
        } else {
            connectionStatus.textContent = 'Disconnected';
            connectionStatus.className = 'status-indicator disconnected';
            this.showStatusMessage('Disconnected from server', 'error');
        }
    }

    /**
     * Handle image loaded event to track current position
     * @param {Object} data - Image loaded event data
     */
    handleImageLoaded(data) {
        // Update current position in session info
        this.sessionInfo.current_position = data.imageId;
        console.log('Current position updated:', this.sessionInfo.current_position);
    }

    /**
     * Update session status display
     */
    updateSessionStatus() {
        // Update counts
        this.elements.totalImages.textContent = this.sessionInfo.total_images || 0;
        this.elements.processedImages.textContent = this.sessionInfo.processed_images || 0;

        // Update progress bar
        const progress = this.sessionInfo.total_images > 0
            ? (this.sessionInfo.processed_images / this.sessionInfo.total_images) * 100
            : 0;
        this.elements.progressBar.style.width = `${progress}%`;
    }

    /**
     * Show a status message
     * @param {string} message - Message to display
     * @param {string} type - Message type (success, error, info)
     */
    showStatusMessage(message, type = 'info') {
        this.elements.statusMessage.textContent = message;
        this.elements.statusMessage.className = `status-message ${type}`;

        // Auto-clear the message after 5 seconds
        setTimeout(() => {
            this.elements.statusMessage.textContent = '';
            this.elements.statusMessage.className = 'status-message';
        }, 5000);
    }

    /**
     * Save the session
     */
    saveSession() {
        this.showStatusMessage('Saving session...', 'info');
        websocket.sendMessage('save_session');
    }

    /**
     * Confirm before exiting
     */
    confirmExit() {
        if (confirm('Are you sure you want to exit? Make sure to save your session first.')) {
            window.close();
        }
    }
}

// Create and export the session manager instance
export const sessionManager = new SessionManager();
