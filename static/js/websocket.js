/**
 * CivitAI Flux Dev LoRA Tagging Assistant
 * WebSocket Communication Module
 */

/**
 * WebSocket client for real-time communication with the server
 */
class WebSocketClient {
    /**
     * Initialize the WebSocket client
     */
    constructor() {
        this.socket = null;
        this.connected = false;
        this.reconnectTimeout = null;
        this.pingInterval = null;
        this.messageHandlers = new Map();

        // Default message handlers
        this.registerHandler('pong', () => {
            // Ping response received, connection is active
        });
    }

    /**
     * Register a message handler for a specific message type
     * @param {string} messageType - The type of message to handle
     * @param {Function} handler - The handler function
     */
    registerHandler(messageType, handler) {
        this.messageHandlers.set(messageType, handler);
    }

    /**
     * Connect to the WebSocket server
     * @returns {Promise<boolean>} - True if connection is successful
     */
    connect() {
        return new Promise((resolve) => {
            if (this.socket && this.connected) {
                resolve(true);
                return;
            }

            // Clear any existing reconnect timeout
            if (this.reconnectTimeout) {
                clearTimeout(this.reconnectTimeout);
                this.reconnectTimeout = null;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                this.connected = true;
                this.startPingInterval();

                // Send initial heartbeat immediately
                this.sendMessage('heartbeat');

                this.dispatchEvent('connectionStatusChanged', { connected: true });
                resolve(true);
            };

            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.socket.onclose = () => {
                this.handleDisconnect();
                resolve(false);
            };

            this.socket.onerror = (error) => {
                console.error('WebSocket Error:', error);
                this.handleDisconnect();
                resolve(false);
            };
        });
    }

    /**
     * Handle a WebSocket disconnect
     */
    handleDisconnect() {
        this.connected = false;
        this.stopPingInterval();

        this.dispatchEvent('connectionStatusChanged', { connected: false });

        // Attempt to reconnect after 3 seconds
        this.reconnectTimeout = setTimeout(() => this.connect(), 3000);
    }

    /**
     * Start sending periodic ping messages to keep the connection alive
     */
    startPingInterval() {
        this.stopPingInterval();
        this.pingInterval = setInterval(() => {
            this.sendMessage('ping');
        }, 30000); // Every 30 seconds
    }

    /**
     * Stop the ping interval
     */
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    /**
     * Send a message to the server
     * @param {string} type - Message type
     * @param {Object} data - Message data
     */
    sendMessage(type, data = {}) {
        if (!this.connected || !this.socket) {
            console.warn('Cannot send message: WebSocket not connected');
            return false;
        }

        try {
            const message = JSON.stringify({ type, data });
            this.socket.send(message);
            return true;
        } catch (error) {
            console.error('Error sending message:', error);
            return false;
        }
    }

    /**
     * Handle incoming WebSocket messages
     * @param {Object} message - The parsed message object
     */
    handleMessage(message) {
        const { type, data } = message;

        // Dispatch event for this message type
        this.dispatchEvent(type, data);

        // Call registered handler if it exists
        const handler = this.messageHandlers.get(type);
        if (handler) {
            handler(data);
        }
    }

    /**
     * Dispatch a custom event
     * @param {string} eventName - Name of the event
     * @param {Object} detail - Event details
     */
    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(`ws:${eventName}`, { detail });
        document.dispatchEvent(event);
    }

    /**
     * Close the WebSocket connection
     */
    disconnect() {
        this.stopPingInterval();

        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }

        this.connected = false;
    }
}

// Export a singleton instance
export const websocket = new WebSocketClient();
