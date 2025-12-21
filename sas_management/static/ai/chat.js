/**
 * SAS AI Chat - Frontend JavaScript
 * Handles chat interface interactions safely.
 */

(function() {
    'use strict';
    
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const emptyState = document.getElementById('emptyState');
    
    let isProcessing = false;
    
    // Auto-resize textarea
    if (chatInput) {
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Send on Enter (Shift+Enter for new line)
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!isProcessing) {
                    sendMessage();
                }
            }
        });
    }
    
    // Send button click
    if (sendButton) {
        sendButton.addEventListener('click', function() {
            if (!isProcessing) {
                sendMessage();
            }
        });
    }
    
    function sendMessage() {
        if (!chatInput || !chatMessages) return;
        
        const message = chatInput.value.trim();
        if (!message || isProcessing) return;
        
        // Hide empty state
        if (emptyState) {
            emptyState.style.display = 'none';
        }
        
        // Add user message
        addMessage('user', message);
        
        // Clear input
        chatInput.value = '';
        chatInput.style.height = 'auto';
        
        // Disable input
        setProcessing(true);
        
        // Show typing indicator
        const typingId = showTypingIndicator();
        
        // Send to backend
        fetch('/ai/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideTypingIndicator(typingId);
            const reply = data.reply || 'I received your message but couldn\'t generate a response.';
            addMessage('ai', reply);
            setProcessing(false);
        })
        .catch(error => {
            console.error('Chat error:', error);
            hideTypingIndicator(typingId);
            addMessage('ai', 'I encountered an error. Please try again later.');
            setProcessing(false);
        });
    }
    
    function addMessage(role, content) {
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? 'U' : 'AI';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    function showTypingIndicator() {
        if (!chatMessages) return null;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai';
        typingDiv.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'typing-indicator';
        typingContent.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        typingDiv.appendChild(avatar);
        typingDiv.appendChild(typingContent);
        
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
        
        return 'typing-indicator';
    }
    
    function hideTypingIndicator(id) {
        if (!id) return;
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }
    
    function setProcessing(processing) {
        isProcessing = processing;
        if (sendButton) {
            sendButton.disabled = processing;
        }
        if (chatInput) {
            chatInput.disabled = processing;
        }
    }
    
    function scrollToBottom() {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
    
    // Focus input on load
    if (chatInput) {
        setTimeout(() => chatInput.focus(), 100);
    }
})();

