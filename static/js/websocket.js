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
        this.messageQueue = [];
        this.connectionAttempts = 0;
        this.maxConnectionAttempts = 5;
        this.messageHandlers = new Map();

        // Default message handlers
        this.registerHandler('pong', () => {
            // Ping response received, connection is active
            this.connectionAttempts = 0; // Reset connection attempts on successful ping
        });

        // Register connect handler
        this.registerHandler('connect', (data) => {
            console.log('Connected to server:', data);
            // Request session data immediately after connecting
            this.sendMessage('session_request');
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
    async connect() {
        return new Promise((resolve) => {
            if (this.socket && this.connected) {
                resolve(true);
                return;
            }

            // Increment connection attempts
            this.connectionAttempts++;

            // Clear any existing reconnect timeout
            if (this.reconnectTimeout) {
                clearTimeout(this.reconnectTimeout);
                this.reconnectTimeout = null;
            }

            // Check max connection attempts
            if (this.connectionAttempts > this.maxConnectionAttempts) {
                console.error(`Failed to connect after ${this.maxConnectionAttempts} attempts`);
                this.dispatchEvent('connectionStatusChanged', { connected: false });
                resolve(false);
                return;
            }

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            console.log(`Connecting to WebSocket server at ${wsUrl}...`);

            try {
                this.socket = new WebSocket(wsUrl);

                this.socket.onopen = () => {
                    console.log('WebSocket connection established');
                    this.connected = true;
                    this.startPingInterval();

                    // Reset connection attempts on successful connection
                    this.connectionAttempts = 0;

                    // Send initial heartbeat immediately
                    this.sendMessage('heartbeat');

                    // Process any queued messages
                    this.processQueue();

                    this.dispatchEvent('connectionStatusChanged', { connected: true });
                    resolve(true);
                };

                this.socket.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        console.log('WebSocket message received:', message.type);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };

                this.socket.onclose = (event) => {
                    console.log(`WebSocket connection closed: Code ${event.code}`);
                    this.handleDisconnect();
                    resolve(false);
                };

                this.socket.onerror = (error) => {
                    console.error('WebSocket Error:', error);
                    this.handleDisconnect();
                    resolve(false);
                };
            } catch (error) {
                console.error('Error creating WebSocket connection:', error);
                this.handleDisconnect();
                resolve(false);
            }
        });
    }

    /**
     * Handle a WebSocket disconnect
     */
    handleDisconnect() {
        this.connected = false;
        this.stopPingInterval();

        this.dispatchEvent('connectionStatusChanged', { connected: false });

        // Attempt to reconnect after delay, with increasing backoff
        const reconnectDelay = Math.min(1000 * Math.pow(1.5, this.connectionAttempts), 30000);
        console.log(`Will attempt to reconnect in ${reconnectDelay}ms`);

        this.reconnectTimeout = setTimeout(() => this.connect(), reconnectDelay);
    }

    /**
     * Process queued messages
     */
    processQueue() {
        if (this.messageQueue.length > 0) {
            console.log(`Processing ${this.messageQueue.length} queued messages`);

            while (this.messageQueue.length > 0) {
                const { type, data } = this.messageQueue.shift();
                this.sendMessage(type, data);
            }
        }
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
     * @returns {boolean} - True if the message was sent successfully
     */
    sendMessage(type, data = {}) {
        if (!this.connected || !this.socket) {
            console.warn(`Cannot send message ${type}: WebSocket not connected, queuing...`);
            this.messageQueue.push({ type, data });

            // Try to connect if not connected
            if (!this.connected && !this.reconnectTimeout) {
                this.connect();
            }

            return false;
        }

        try {
            const message = JSON.stringify({ type, data });
            this.socket.send(message);
            return true;
        } catch (error) {
            console.error(`Error sending message ${type}:`, error);
            this.messageQueue.push({ type, data });
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
            try {
                this.socket.close(1000, "Intentional disconnect");
            } catch (e) {
                console.error("Error closing WebSocket connection:", e);
            }
            this.socket = null;
        }

        this.connected = false;
        this.dispatchEvent('connectionStatusChanged', { connected: false });
    }
}

// Export a singleton instance
export const websocket = new WebSocketClient();
