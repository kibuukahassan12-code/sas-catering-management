// SAS AI Chat - ChatGPT-style functionality
let sessionId = null;
let isTyping = false;
let messageCount = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set welcome timestamp
    const timestampEl = document.getElementById('welcome-timestamp');
    if (timestampEl) {
        timestampEl.textContent = formatTimestamp(new Date());
    }
    
    // Initialize context and suggestions
    initializeContext();
    initializeSuggestions();
    initializeQuickActions();
    
    // Focus input
    const input = document.getElementById('chat-input');
    if (input) {
        input.focus();
    }
});

// Initialize context panel
function initializeContext() {
    const context = window.aiContext || {};
    
    // Update context display if needed
    if (context.currentModule) {
        const moduleEl = document.getElementById('context-module');
        if (moduleEl) {
            moduleEl.textContent = formatModuleName(context.currentModule);
        }
    }
    
    if (context.activeEvent) {
        const eventEl = document.getElementById('context-event');
        if (eventEl) {
            eventEl.textContent = context.activeEvent.title || `Event #${context.activeEvent.id}`;
        }
    }
}

// Initialize dynamic suggestions based on module
function initializeSuggestions() {
    const context = window.aiContext || {};
    const suggestionsContainer = document.getElementById('chat-suggestions');
    if (!suggestionsContainer) return;
    
    const module = (context.currentModule || 'general').toLowerCase();
    let suggestions = [];
    
    if (module === 'service') {
        suggestions = [
            { icon: '📋', text: 'Show event checklist' },
            { icon: '📦', text: 'Items taken vs returned' },
            { icon: '👥', text: 'Service team status' },
            { icon: '⚠️', text: 'Any issues today?' },
            { icon: '📊', text: 'Event summary' },
            { icon: '💰', text: 'Event costs' }
        ];
    } else if (module === 'finance' || module === 'financial') {
        suggestions = [
            { icon: '💰', text: 'What is this month revenue?' },
            { icon: '📈', text: 'Revenue trends' },
            { icon: '💵', text: 'Profit analysis' },
            { icon: '📊', text: 'Financial summary' }
        ];
    } else if (module === 'events') {
        suggestions = [
            { icon: '📅', text: 'Upcoming events' },
            { icon: '📋', text: 'Event details' },
            { icon: '👥', text: 'Event staff' }
        ];
    } else {
        // General suggestions
        suggestions = [
            { icon: '📊', text: 'How many events this month?' },
            { icon: '💰', text: 'What is this month revenue?' },
            { icon: '👥', text: 'Tell me about staff' },
            { icon: '📋', text: 'Show recent activity' }
        ];
    }
    
    // Render suggestions
    suggestionsContainer.innerHTML = suggestions.map(s => `
        <button class="ai-suggestion" onclick="sendSuggestion('${escapeHtml(s.text)}')">
            <span class="ai-suggestion-icon">${s.icon}</span>
            <span>${escapeHtml(s.text)}</span>
        </button>
    `).join('');
}

// Initialize quick actions based on context
function initializeQuickActions() {
    const context = window.aiContext || {};
    const quickActionsContainer = document.getElementById('quick-actions');
    if (!quickActionsContainer) return;
    
    const module = (context.currentModule || 'general').toLowerCase();
    let actions = [];
    
    if (module === 'service' && context.activeEvent) {
        actions = [
            { text: 'Show event checklist', prompt: 'Show event checklist' },
            { text: 'Items taken vs returned', prompt: 'Items taken vs returned' },
            { text: 'Service team status', prompt: 'Service team status' },
            { text: 'Any issues today?', prompt: 'Any issues today?' }
        ];
    } else {
        actions = [
            { text: 'Recent events', prompt: 'Show recent events' },
            { text: 'Monthly revenue', prompt: 'What is this month revenue?' },
            { text: 'Staff overview', prompt: 'Tell me about staff' }
        ];
    }
    
    // Render quick actions
    quickActionsContainer.innerHTML = actions.map(action => `
        <button class="ai-quick-action" onclick="fillPrompt('${escapeHtml(action.prompt)}')">
            ${escapeHtml(action.text)}
        </button>
    `).join('');
}

// Fill input with prompt from quick action
function fillPrompt(text) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = text;
        input.focus();
        autoResizeTextarea(input);
    }
}

// Send suggestion as message
function sendSuggestion(text) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = text;
    }
    sendMessage();
}

// Handle keyboard input
function handleChatKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Auto-resize textarea
function autoResizeTextarea(textarea) {
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// Send message
function sendMessage() {
    if (isTyping) return;
    
    const input = document.getElementById('chat-input');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    // Clear input
    input.value = '';
    autoResizeTextarea(input);
    
    // Add user message
    addMessage(message, 'user');
    
    // Hide suggestions after first message
    messageCount++;
    if (messageCount > 1) {
        hideSuggestions();
    }
    
    // Show typing indicator
    showTypingIndicator();
    
    // Disable input and send button
    setSendButtonState(true);
    disableInput();
    
    // Send to API
    isTyping = true;
    
    fetch('/sas-ai/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        })
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 503) {
                throw new Error('SAS AI is currently unavailable. Please try again later.');
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        hideTypingIndicator();
        isTyping = false;
        setSendButtonState(false);
        enableInput();
        
        if (data.success && data.reply) {
            // Store session ID
            if (data.session_id) {
                sessionId = data.session_id;
            }
            
            // Add AI reply
            addMessage(data.reply, 'assistant');
        } else {
            addMessage(
                data.message || 'I encountered an error. Please try again.',
                'assistant',
                true
            );
        }
    })
    .catch(error => {
        hideTypingIndicator();
        isTyping = false;
        setSendButtonState(false);
        enableInput();
        console.error('Chat error:', error);
        
        const errorMessage = error.message.includes('unavailable') 
            ? error.message 
            : 'SAS AI is unavailable. Please try again.';
        
        addMessage(errorMessage, 'assistant', true);
    });
}

// Add message to chat
function addMessage(text, role, isError = false) {
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-message ai-message-${role}`;
    
    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="ai-avatar ai-avatar-user">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z" fill="currentColor"/>
                    <path d="M12 14C7.58172 14 4 17.5817 4 22H20C20 17.5817 16.4183 14 12 14Z" fill="currentColor"/>
                </svg>
            </div>
            <div class="ai-message-content">
                <div class="ai-message-bubble ai-message-bubble-user">
                    <div class="ai-message-text">${escapeHtml(text)}</div>
                </div>
                <div class="ai-message-meta">
                    <span class="ai-timestamp">${formatTimestamp(new Date())}</span>
                </div>
            </div>
        `;
    } else {
        const renderedText = renderMarkdown(text);
        const errorClass = isError ? ' ai-message-bubble-error' : '';
        
        messageDiv.innerHTML = `
            <div class="ai-avatar ai-avatar-assistant">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="currentColor"/>
                </svg>
            </div>
            <div class="ai-message-content">
                <div class="ai-message-bubble ai-message-bubble-assistant${errorClass}">
                    <div class="ai-message-text">${renderedText}</div>
                </div>
                <div class="ai-message-meta">
                    <span class="ai-timestamp">${formatTimestamp(new Date())}</span>
                </div>
            </div>
        `;
    }
    
    messagesDiv.appendChild(messageDiv);
    scrollToBottom();
}

// Show typing indicator
function showTypingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="ai-avatar ai-avatar-assistant">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="currentColor"/>
            </svg>
        </div>
        <div class="ai-message-content">
            <div class="ai-message-bubble ai-message-bubble-assistant">
                <div class="ai-typing-dots">
                    <div class="ai-typing-dot"></div>
                    <div class="ai-typing-dot"></div>
                    <div class="ai-typing-dot"></div>
                </div>
            </div>
            <div class="ai-typing-label">SAS AI is typing…</div>
        </div>
    `;
    
    messagesDiv.appendChild(typingDiv);
    scrollToBottom();
}

// Hide typing indicator
function hideTypingIndicator() {
    const typingDiv = document.getElementById('typing-indicator');
    if (typingDiv) {
        typingDiv.remove();
    }
}

// Hide suggestions
function hideSuggestions() {
    const suggestions = document.getElementById('chat-suggestions');
    if (suggestions) {
        suggestions.style.display = 'none';
    }
}

// Set send button state
function setSendButtonState(disabled) {
    const sendButton = document.getElementById('send-button');
    if (sendButton) {
        sendButton.disabled = disabled;
    }
}

// Disable input
function disableInput() {
    const input = document.getElementById('chat-input');
    if (input) {
        input.disabled = true;
    }
}

// Enable input
function enableInput() {
    const input = document.getElementById('chat-input');
    if (input) {
        input.disabled = false;
        input.focus();
    }
}

// Scroll to bottom
function scrollToBottom() {
    const messagesDiv = document.getElementById('chat-messages');
    if (messagesDiv) {
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

// Format timestamp
function formatTimestamp(date) {
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const hours12 = hours % 12 || 12;
    const minutesStr = minutes.toString().padStart(2, '0');
    return `${hours12}:${minutesStr} ${ampm}`;
}

// Format module name
function formatModuleName(module) {
    return module
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Render Markdown to HTML
function renderMarkdown(text) {
    if (!text) return '';
    
    // Escape HTML first
    let html = escapeHtml(text);
    
    // Bold: **text**
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    
    // Italic: *text* (but not **text**)
    html = html.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>');
    
    // Code: `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Links: [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Lists
    const lines = html.split('\n');
    let inList = false;
    let result = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const listMatch = line.match(/^[-*]\s+(.+)$/);
        
        if (listMatch) {
            if (!inList) {
                result.push('<ul>');
                inList = true;
            }
            result.push(`<li>${listMatch[1]}</li>`);
        } else {
            if (inList) {
                result.push('</ul>');
                inList = false;
            }
            
            // Check for numbered list
            const numMatch = line.match(/^\d+\.\s+(.+)$/);
            if (numMatch) {
                if (!inList) {
                    result.push('<ol>');
                    inList = true;
                }
                result.push(`<li>${numMatch[1]}</li>`);
            } else {
                if (line.trim()) {
                    result.push(`<p>${line}</p>`);
                } else {
                    result.push('<br>');
                }
            }
        }
    }
    
    if (inList) {
        result.push('</ul>');
    }
    
    html = result.join('\n');
    
    // Blockquote: > text
    html = html.replace(/^&gt; (.*$)/gim, '<blockquote>$1</blockquote>');
    
    // Horizontal rule
    html = html.replace(/^---$/gim, '<hr>');
    
    // Clean up empty paragraphs
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>\s*<\/p>/g, '');
    
    // If no HTML tags were added, wrap in paragraph
    if (!html.includes('<')) {
        html = `<p>${html}</p>`;
    }
    
    return html;
}
