"""SAS AI Memory - Session-based conversation history storage."""
from typing import List, Dict
from datetime import datetime


# In-memory conversation storage (per session)
# In production, consider using Redis or database
_conversations: Dict[str, List[Dict]] = {}


def get_conversation(session_id: str) -> List[Dict[str, str]]:
    """
    Get conversation history for a session.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        List of message dicts with 'role' and 'content'
    """
    if session_id not in _conversations:
        _conversations[session_id] = []
    return _conversations[session_id].copy()


def add_message(session_id: str, role: str, content: str, metadata: Dict = None):
    """
    Add a message to conversation history.
    
    Args:
        session_id: Unique session identifier
        role: Message role ('user' or 'assistant')
        content: Message content
        metadata: Optional metadata (intent, source, etc.)
    """
    if session_id not in _conversations:
        _conversations[session_id] = []
    
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if metadata:
        message.update(metadata)
    
    _conversations[session_id].append(message)
    
    # Keep only last 30 messages to prevent memory issues
    _conversations[session_id] = _conversations[session_id][-30:]


def clear_conversation(session_id: str):
    """Clear conversation history for a session."""
    if session_id in _conversations:
        del _conversations[session_id]


def get_conversation_summary(session_id: str, last_n: int = 5) -> str:
    """
    Get a text summary of recent conversation for context.
    
    Args:
        session_id: Unique session identifier
        last_n: Number of recent messages to include
        
    Returns:
        Formatted conversation summary
    """
    conversation = get_conversation(session_id)
    recent = conversation[-last_n:] if len(conversation) > last_n else conversation
    
    summary_parts = []
    for msg in recent:
        role = "User" if msg.get("role") == "user" else "Assistant"
        summary_parts.append(f"{role}: {msg.get('content', '')[:200]}")
    
    return "\n".join(summary_parts)

