/**
 * CivitAI Flux Dev LoRA Tagging Assistant
 * Main application JavaScript
 */

// Application state
const appState = {
    connected: false,
    sessionInfo: {
        totalImages: 0,
        processedImages: 0,
        currentPosition: null,
        tags: []
    },
    selectedTags: [],
    recentlyUsedTags: []
};

// Elements
const elements = {
    connectionStatus: document.getElementById('connection-status'),
    previewImage: document.getElementById('preview-image'),
    imageName: document.getElementById('image-name'),
    imageDimensions: document.getElementById('image-dimensions'),
    prevButton: document.getElementById('prev-button'),
    nextButton: document.getElementById('next-button'),
    tagFilter: document.getElementById('tag-filter'),
    newTagInput: document.getElementById('new-tag'),
    addTagButton: document.getElementById('add-tag-button'),
    recentTags: document.getElementById('recent-tags'),
    allTags: document.getElementById('all-tags'),
    saveTagsButton: document.getElementById('save-tags-button'),
    totalImages: document.getElementById('total-images'),
    processedImages: document.getElementById('processed-images'),
    progressBar: document.getElementById('progress-bar'),
    saveSessionButton: document.getElementById('save-session-button'),
    exitButton: document.getElementById('exit-button'),
    statusMessage: document.getElementById('status-message')
};

// WebSocket connection
let socket;

/**
 * Initialize the WebSocket connection
 */
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        appState.connected = true;
        elements.connectionStatus.textContent = 'Connected';
        elements.connectionStatus.classList.add('connected');
        updateStatusMessage('Connected to server');
    };

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    socket.onclose = () => {
        appState.connected = false;
        elements.connectionStatus.textContent = 'Disconnected';
        elements.connectionStatus.classList.remove('connected');
        elements.connectionStatus.classList.add('disconnected');
        updateStatusMessage('Connection to server lost, attempting to reconnect...');

        // Try to reconnect after 3 seconds
        setTimeout(initWebSocket, 3000);
    };

    socket.onerror = (error) => {
        console.error('WebSocket Error:', error);
        updateStatusMessage('Connection error occurred');
    };
}

/**
 * Handle incoming WebSocket messages
 * @param {Object} message - The message object
 */
function handleWebSocketMessage(message) {
    console.log('Received message:', message);

    switch (message.type) {
        case 'session_state':
            updateSessionState(message.data);
            break;
        case 'image_tags':
            updateImageTags(message.data);
            break;
        case 'tags_updated':
            refreshTagList();
            break;
        case 'pong':
            // Handle ping response
            break;
        default:
            console.warn('Unknown message type:', message.type);
    }
}

/**
 * Update the session state with data from server
 * @param {Object} data - Session state data
 */
function updateSessionState(data) {
    appState.sessionInfo.totalImages = data.total_images || 0;
    appState.sessionInfo.processedImages = data.processed_images || 0;
    appState.sessionInfo.currentPosition = data.current_position;

    if (data.tags) {
        appState.sessionInfo.tags = data.tags;
        renderTagList();
    }

    // Update UI elements
    elements.totalImages.textContent = appState.sessionInfo.totalImages;
    elements.processedImages.textContent = appState.sessionInfo.processedImages;

    // Update progress bar
    const progressPercent = appState.sessionInfo.totalImages > 0
        ? (appState.sessionInfo.processedImages / appState.sessionInfo.totalImages) * 100
        : 0;
    elements.progressBar.style.width = `${progressPercent}%`;

    // Enable/disable navigation buttons based on current position
    updateNavigationButtons();

    updateStatusMessage('Session state updated');
}

/**
 * Update the image tags in the UI
 * @param {Object} data - Image tags data
 */
function updateImageTags(data) {
    appState.selectedTags = data.tags || [];
    renderSelectedTags();
    updateStatusMessage('Image tags loaded');
}

/**
 * Render the full tag list in the UI
 */
function renderTagList() {
    const allTagsContainer = elements.allTags;
    allTagsContainer.innerHTML = '';

    // Sort tags alphabetically
    const sortedTags = [...appState.sessionInfo.tags].sort();

    // Filter tags if filter input has value
    const filterText = elements.tagFilter.value.toLowerCase();
    const filteredTags = filterText
        ? sortedTags.filter(tag => tag.toLowerCase().includes(filterText))
        : sortedTags;

    // Create tag elements
    filteredTags.forEach(tag => {
        const tagElement = document.createElement('div');
        tagElement.className = 'tag';
        tagElement.textContent = tag;
        tagElement.addEventListener('click', () => toggleTagSelection(tag, tagElement));

        // Check if this tag is selected
        if (appState.selectedTags.includes(tag)) {
            tagElement.classList.add('selected');
        }

        allTagsContainer.appendChild(tagElement);
    });

    // Also update recent tags
    renderRecentTags();
}

/**
 * Render the recently used tags
 */
function renderRecentTags() {
    const recentContainer = elements.recentTags;
    recentContainer.innerHTML = '';

    appState.recentlyUsedTags.forEach(tag => {
        const tagElement = document.createElement('div');
        tagElement.className = 'tag';
        tagElement.textContent = tag;
        tagElement.addEventListener('click', () => toggleTagSelection(tag, tagElement));

        // Check if this tag is selected
        if (appState.selectedTags.includes(tag)) {
            tagElement.classList.add('selected');
        }

        recentContainer.appendChild(tagElement);
    });
}

/**
 * Toggle selection of a tag
 * @param {string} tag - The tag text
 * @param {HTMLElement} element - The tag DOM element
 */
function toggleTagSelection(tag, element) {
    if (appState.selectedTags.includes(tag)) {
        // Remove tag from selection
        appState.selectedTags = appState.selectedTags.filter(t => t !== tag);
        element.classList.remove('selected');
    } else {
        // Add tag to selection
        appState.selectedTags.push(tag);
        element.classList.add('selected');

        // Add to recently used tags if not already there
        if (!appState.recentlyUsedTags.includes(tag)) {
            appState.recentlyUsedTags.unshift(tag);
            // Keep only 10 most recent tags
            if (appState.recentlyUsedTags.length > 10) {
                appState.recentlyUsedTags.pop();
            }
            renderRecentTags();
        }
    }

    // Enable save button when tags are selected
    elements.saveTagsButton.disabled = appState.selectedTags.length === 0;
}

/**
 * Render selected tags in the UI
 */
function renderSelectedTags() {
    // Update the class on all tag elements
    const tagElements = document.querySelectorAll('.tag');
    tagElements.forEach(element => {
        if (appState.selectedTags.includes(element.textContent)) {
            element.classList.add('selected');
        } else {
            element.classList.remove('selected');
        }
    });

    // Enable save button when tags are selected
    elements.saveTagsButton.disabled = appState.selectedTags.length === 0;
}

/**
 * Update the navigation buttons based on current position
 */
function updateNavigationButtons() {
    // This is a placeholder - actual logic would depend on the server implementation
    // Enable/disable based on whether we're at the first or last image
    elements.prevButton.disabled = false;
    elements.nextButton.disabled = false;
}

/**
 * Refresh the tag list from the server
 */
function refreshTagList() {
    // In a full implementation, we would fetch the updated tag list from the server
    // For now, we'll just re-render with what we have
    renderTagList();
}

/**
 * Update the status message
 * @param {string} message - The message to display
 */
function updateStatusMessage(message) {
    elements.statusMessage.textContent = message;

    // Clear the message after 3 seconds
    setTimeout(() => {
        if (elements.statusMessage.textContent === message) {
            elements.statusMessage.textContent = '';
        }
    }, 3000);
}

/**
 * Add a new tag
 */
function addNewTag() {
    const newTag = elements.newTagInput.value.trim();

    if (newTag && appState.connected) {
        // In a full implementation, we would send to server via WebSocket
        // For now, just add to local state
        if (!appState.sessionInfo.tags.includes(newTag)) {
            appState.sessionInfo.tags.push(newTag);
            renderTagList();
            updateStatusMessage(`Added new tag: ${newTag}`);

            // Select the new tag
            appState.selectedTags.push(newTag);
            renderSelectedTags();

            // Add to recently used
            if (!appState.recentlyUsedTags.includes(newTag)) {
                appState.recentlyUsedTags.unshift(newTag);
                // Keep only 10 most recent tags
                if (appState.recentlyUsedTags.length > 10) {
                    appState.recentlyUsedTags.pop();
                }
                renderRecentTags();
            }
        }

        // Clear the input
        elements.newTagInput.value = '';
    }
}

/**
 * Save the session state
 */
function saveSession() {
    if (appState.connected) {
        // In a full implementation, we would send to server via WebSocket
        updateStatusMessage('Session saved');
    }
}

/**
 * Exit the application
 */
function exitApplication() {
    if (confirm('Are you sure you want to exit? All unsaved changes will be lost.')) {
        // In a full implementation, we would send an exit message to the server
        window.close();
    }
}

/**
 * Initialize the application
 */
function initializeApp() {
    // Set up event listeners
    elements.tagFilter.addEventListener('input', renderTagList);
    elements.addTagButton.addEventListener('click', addNewTag);
    elements.newTagInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addNewTag();
    });
    elements.saveTagsButton.addEventListener('click', () => {
        // In a full implementation, we would send selected tags to server
        updateStatusMessage('Tags saved');
    });
    elements.saveSessionButton.addEventListener('click', saveSession);
    elements.exitButton.addEventListener('click', exitApplication);

    // Initialize WebSocket connection
    initWebSocket();

    // Set up heartbeat to keep connection alive
    setInterval(() => {
        if (appState.connected) {
            try {
                socket.send(JSON.stringify({ type: 'ping' }));
            } catch (error) {
                console.error('Error sending ping:', error);
            }
        }
    }, 30000); // Every 30 seconds
}

// Start the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initializeApp);
