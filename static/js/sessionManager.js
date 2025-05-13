/**
 * CivitAI Flux Dev LoRA Tagging Assistant
 * Session Manager Module
 */

import { api } from './api.js';
import { websocket } from './websocket.js';

/**
 * Session Manager class to handle session state and control
 */
class SessionManager {
    /**
     * Initialize the session manager
     */
    constructor() {
        // State
        this.sessionState = {
            totalImages: 0,
            processedImages: 0,
            currentPosition: null,
            lastUpdated: null
        };

        // Elements
        this.elements = {
            totalImages: document.getElementById('total-images'),
            processedImages: document.getElementById('processed-images'),
            progressBar: document.getElementById('progress-bar'),
            saveSessionButton: document.getElementById('save-session-button'),
            exitButton: document.getElementById('exit-button'),
            statusMessage: document.getElementById('status-message')
        };

        // Bind methods
        this.saveSession = this.saveSession.bind(this);
        this.exitSession = this.exitSession.bind(this);
        this.updateStatusMessage = this.updateStatusMessage.bind(this);

        // Event listeners
        this.elements.saveSessionButton.addEventListener('click', this.saveSession);
        this.elements.exitButton.addEventListener('click', this.exitSession);

        // WebSocket event listeners
        document.addEventListener('ws:session_state', (e) => this.handleSessionState(e.detail));
        document.addEventListener('ws:connectionStatusChanged', (e) => this.handleConnectionChange(e.detail));
    }

    /**
     * Initialize the session manager
     */
    async initialize() {
        try {
            // Get initial status
            const status = await api.getStatus();
            this.updateSessionState(status);
        } catch (error) {
            console.error('Error initializing session:', error);
            this.updateStatusMessage('Error loading session state', 'error');
        }
    }

    /**
     * Handle session state update from WebSocket
     * @param {Object} data - Session state data
     */
    handleSessionState(data) {
        this.updateSessionState({
            total_images: data.total_images,
            processed_images: data.processed_images,
            current_position: data.current_position
        });
    }

    /**
     * Handle connection status change
     * @param {Object} data - Connection status data
     */
    handleConnectionChange(data) {
        const connectionStatus = document.getElementById('connection-status');

        if (data.connected) {
            connectionStatus.textContent = 'Connected';
            connectionStatus.classList.add('connected');
            connectionStatus.classList.remove('disconnected');
            this.updateStatusMessage('Connected to server');
        } else {
            connectionStatus.textContent = 'Disconnected';
            connectionStatus.classList.remove('connected');
            connectionStatus.classList.add('disconnected');
            this.updateStatusMessage('Disconnected from server', 'warning');
        }
    }

    /**
     * Update session state with new data
     * @param {Object} data - Session state data
     */
    updateSessionState(data) {
        // Update state
        if (data.total_images !== undefined) {
            this.sessionState.totalImages = data.total_images;
        }

        if (data.processed_images !== undefined) {
            this.sessionState.processedImages = data.processed_images;
        }

        if (data.current_position !== undefined) {
            this.sessionState.currentPosition = data.current_position;
        }

        if (data.last_updated) {
            this.sessionState.lastUpdated = new Date(data.last_updated);
        }

        // Update UI
        this.elements.totalImages.textContent = this.sessionState.totalImages;
        this.elements.processedImages.textContent = this.sessionState.processedImages;

        // Update progress bar
        const progressPercent = this.sessionState.totalImages > 0
            ? (this.sessionState.processedImages / this.sessionState.totalImages) * 100
            : 0;
        this.elements.progressBar.style.width = `${progressPercent}%`;
    }

    /**
     * Save the current session state
     */
    async saveSession() {
        try {
            // Request save via WebSocket
            websocket.sendMessage('save_session');
            this.updateStatusMessage('Session saved');
        } catch (error) {
            console.error('Error saving session:', error);
            this.updateStatusMessage('Error saving session', 'error');
        }
    }

    /**
     * Exit the current session
     */
    exitSession() {
        if (confirm('Are you sure you want to exit? All unsaved changes will be lost.')) {
            // Save session before exiting
            this.saveSession().then(() => {
                window.close();
            });
        }
    }

    /**
     * Update the status message
     * @param {string} message - Message to display
     * @param {string} type - Message type (info, success, warning, error)
     */
    updateStatusMessage(message, type = 'info') {
        this.elements.statusMessage.textContent = message;

        // Remove existing classes
        this.elements.statusMessage.classList.remove('info', 'success', 'warning', 'error');

        // Add type class
        this.elements.statusMessage.classList.add(type);

        // Clear after delay unless it's an error
        if (type !== 'error') {
            setTimeout(() => {
                if (this.elements.statusMessage.textContent === message) {
                    this.elements.statusMessage.textContent = '';
                }
            }, 3000);
        }
    }
}

// Create and export the session manager instance
export const sessionManager = new SessionManager();
