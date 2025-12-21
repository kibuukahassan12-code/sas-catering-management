"""
Operations Chat Assistant AI Service

Provides rule-based answers about operations, workflows, and checklists.
"""
from flask import current_app


def run(payload, user):
    """
    Run Operations Chat AI service.
    
    Args:
        payload: dict with 'question' (required)
        user: Current user object
    
    Returns:
        dict: {
            'success': bool,
            'answer': str,
            'related_topics': list,
            'error': str (if failed)
        }
    """
    try:
        question = payload.get('question', '').strip().lower()
        
        if not question:
            return {
                'success': False,
                'error': 'Question is required',
                'answer': '',
                'related_topics': []
            }
        
        # Rule-based NLP matching
        answer, related_topics = _answer_question(question, user)
        
        return {
            'success': True,
            'answer': answer,
            'related_topics': related_topics
        }
        
    except Exception as e:
        current_app.logger.exception(f"Operations Chat AI error: {e}")
        return {
            'success': False,
            'error': str(e),
            'answer': 'I apologize, but I encountered an error processing your question.',
            'related_topics': []
        }


def _answer_question(question, user):
    """Answer question using rule-based logic."""
    related_topics = []
    
    # Event operations
    if any(word in question for word in ['event', 'catering', 'booking']):
        answer = """Event operations in SAS include:
• Creating and managing event bookings
• Assigning staff to events
• Managing event timelines and checklists
• Tracking event costs and revenue
• Generating event reports

You can access events through the Events module."""
        related_topics = ['Events', 'Staff Assignment', 'Timelines', 'Checklists']
    
    # Inventory operations
    elif any(word in question for word in ['inventory', 'stock', 'item', 'supply']):
        answer = """Inventory operations include:
• Tracking stock levels
• Managing inventory items
• Monitoring reorder levels
• Recording stock adjustments
• Viewing inventory reports

Access inventory through the Inventory module."""
        related_topics = ['Inventory', 'Stock Management', 'Reorder Levels']
    
    # Staff operations
    elif any(word in question for word in ['staff', 'employee', 'attendance', 'shift']):
        answer = """Staff operations include:
• Managing employee records
• Tracking attendance
• Assigning staff to events
• Viewing staff schedules
• Performance tracking

Access staff management through the HR module."""
        related_topics = ['HR', 'Attendance', 'Schedules', 'Performance']
    
    # Workflow
    elif any(word in question for word in ['workflow', 'process', 'procedure', 'how to']):
        answer = """Common workflows in SAS:
1. Event Booking: Create event → Assign staff → Set timeline → Track progress
2. Inventory: Check stock → Reorder if needed → Receive items → Update stock
3. Staff Management: Add employee → Assign to events → Track attendance → Review performance

For specific workflows, please ask about the module (Events, Inventory, HR, etc.)."""
        related_topics = ['Events', 'Inventory', 'HR', 'Workflows']
    
    # Checklists
    elif any(word in question for word in ['checklist', 'task', 'todo', 'complete']):
        answer = """Checklists help track event preparation:
• Event checklists are created per event
• Items can be marked as complete
• Progress is tracked automatically
• Checklists include setup, preparation, service, and cleanup tasks

View checklists in the Events module for each event."""
        related_topics = ['Events', 'Checklists', 'Tasks']
    
    # Default
    else:
        answer = """I can help you with:
• Event operations and workflows
• Inventory management
• Staff and HR operations
• Checklists and task management
• System navigation

Please ask a specific question about any of these areas."""
        related_topics = ['Events', 'Inventory', 'HR', 'General Help']
    
    return answer, related_topics

