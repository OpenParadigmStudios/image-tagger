# CivitAI Flux Dev LoRA Tagging Assistant - Web Migration Plan

## Overview

This document outlines the plan to migrate the CivitAI Flux Dev LoRA Tagging Assistant from a planned PyQt6-based desktop application to a web-based application using WebSockets for real-time communication.

## Migration Rationale

A web-based interface offers several advantages:
1. Platform independence - accessible from any device with a modern web browser
2. Responsive design capabilities for different screen sizes
3. Familiar UI patterns for users (like dropdowns, buttons, form elements)
4. Potentially easier to update and maintain
5. No need for Qt-specific knowledge

## Technical Approach

### Server-Side Architecture
1. Use **FastAPI** framework for the backend server:
   - High performance async framework
   - Built-in WebSocket support
   - Automatic API documentation
   - Type checking with Pydantic models (compatible with existing dataclasses)

2. Use **Uvicorn** as the ASGI server to run FastAPI application

3. Implement WebSocket endpoints for real-time communication:
   - Image browsing and selection
   - Tag management
   - Session state updates

4. Add static file serving for:
   - Serving web UI assets (HTML, CSS, JS)
   - Securely serving image files with proper validation

### Client-Side Architecture
1. Use modern JavaScript with optional Vue.js for the frontend:
   - Lightweight and focused on UI interaction
   - Component-based architecture
   - Reactive data binding

2. Use Bootstrap CSS framework for responsive design (optional)

3. Implement WebSocket client for real-time communication

4. Create three main view components:
   - Image preview panel
   - Tag management panel (selection, creation, deletion)
   - Session control panel (navigation, save, exit)

### Data Flow Changes
1. Replace direct file system operations with API endpoints
2. Implement secure file access validation
3. Add session management with WebSocket connections
4. Use a similar session state structure with web-specific additions

## Implementation Steps

### Step 1: Project Restructuring
1. Update requirements.txt to replace PyQt6 with web dependencies
2. Create a basic project structure with server and client folders
3. Update documentation to reflect the architectural change

### Step 2: Server Implementation
1. Create a FastAPI application with basic endpoints
2. Set up static file serving for the web UI
3. Implement image file discovery and listing API
4. Set up WebSocket connection management
5. Implement session state management via WebSockets

### Step 3: Client Implementation
1. Create basic HTML/CSS/JS structure
2. Implement WebSocket connection and message handling
3. Create image preview component
4. Create tag management interface
5. Implement session controls (navigation, save, exit)

### Step 4: Integration
1. Connect client UI to server WebSocket endpoints
2. Implement image loading and preview
3. Add tag selection, creation, and updating
4. Implement session persistence and state synchronization

### Step 5: Security and Error Handling
1. Add proper input validation and sanitization
2. Implement secure file access patterns
3. Add comprehensive error handling
4. Ensure session data integrity

### Step 6: Testing
1. Unit tests for server components
2. Integration tests for client-server communication
3. End-to-end testing of the complete workflow

### Step 7: Refinement
1. UI/UX improvements based on testing
2. Performance optimizations
3. Documentation updates

## Package Dependencies

### Server Dependencies
- fastapi: Web framework with WebSocket support
- uvicorn: ASGI server for running FastAPI
- python-multipart: For handling file uploads
- pillow: Image processing and validation
- websockets: WebSocket protocol implementation

### Client Dependencies
- Vue.js (optional): Frontend framework
- Bootstrap (optional): CSS framework
- vanilla JavaScript with fetch API and WebSocket API

## Timeline Estimate

- Step 1: Project Restructuring - 1 day
- Step 2: Server Implementation - 3-4 days
- Step 3: Client Implementation - 3-4 days
- Step 4: Integration - 2-3 days
- Step 5: Security and Error Handling - 1-2 days
- Step 6: Testing - 2-3 days
- Step 7: Refinement - 1-2 days

Total estimated time: 2-3 weeks depending on complexity and feature scope.
