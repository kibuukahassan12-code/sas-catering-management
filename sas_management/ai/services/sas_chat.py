"""
SAS AI Chat Service

System-aware chat assistant that can answer questions about the SAS system.
"""
from flask import current_app
from datetime import date, timedelta


def run(payload, user):
    """
    Run SAS AI Chat service.
    
    Args:
        payload: dict with 'message' (required)
        user: Current user object
    
    Returns:
        dict: {
            'success': bool,
            'response': str,
            'error': str (if failed)
        }
    """
    try:
        message = payload.get('message', '').strip().lower()
        
        if not message:
            return {
                'success': False,
                'error': 'Message is required',
                'response': ''
            }
        
        # System-aware responses
        response = _generate_response(message, user)
        
        return {
            'success': True,
            'response': response
        }
        
    except Exception as e:
        current_app.logger.exception(f"SAS Chat AI error: {e}")
        return {
            'success': False,
            'error': str(e),
            'response': 'I apologize, but I encountered an error. Please try again.'
        }


def _generate_response(message, user):
    """Generate system-aware response."""
    # Events queries
    if any(word in message for word in ['event', 'events', 'how many events']):
        try:
            from sas_management.models import Event
            today = date.today()
            this_month = Event.query.filter(
                Event.date >= date(today.year, today.month, 1),
                Event.date < date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
            ).count()
            total_events = Event.query.count()
            return f"We have {this_month} event(s) this month and {total_events} total event(s) in the system."
        except:
            return "I can help you with events! You can view and manage events through the Events module."
    
    # Staff/HR queries
    elif any(word in message for word in ['staff', 'employee', 'who is on duty', 'on duty today']):
        try:
            from sas_management.models import Employee, Attendance
            today = date.today()
            on_duty = Attendance.query.filter_by(date=today, status='Present').count()
            total_staff = Employee.query.filter_by(is_active=True).count()
            return f"Today, {on_duty} staff member(s) are on duty. We have {total_staff} active staff members in total."
        except:
            return "I can help you with staff information! Check the HR module for staff details and attendance."
    
    # Revenue queries
    elif any(word in message for word in ['revenue', 'income', 'sales', 'money', 'this week', 'this month']):
        try:
            from sas_management.models import Event, Transaction
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
            month_start = date(today.year, today.month, 1)
            
            # Try to get revenue from events
            week_revenue = sum(float(e.quoted_value or 0) for e in Event.query.filter(
                Event.date >= week_start,
                Event.date <= today
            ).all())
            
            month_revenue = sum(float(e.quoted_value or 0) for e in Event.query.filter(
                Event.date >= month_start,
                Event.date <= today
            ).all())
            
            return f"This week's revenue: {week_revenue:,.0f} UGX. This month's revenue: {month_revenue:,.0f} UGX. For detailed financial reports, check the Accounting module."
        except:
            return "I can help you with revenue information! Check the Accounting module for detailed financial reports."
    
    # Inventory queries
    elif any(word in message for word in ['inventory', 'stock', 'items']):
        try:
            from sas_management.models import InventoryItem
            total_items = InventoryItem.query.count()
            low_stock = InventoryItem.query.filter(InventoryItem.stock_count <= 10).count()
            return f"We have {total_items} inventory item(s). {low_stock} item(s) are running low on stock."
        except:
            return "I can help you with inventory! Check the Inventory module for stock levels and management."
    
    # Default
    else:
        return """I'm SAS AI, your intelligent assistant. I can help you with:
• Events: "How many events this month?"
• Staff: "Who is on duty today?"
• Revenue: "What is my revenue this week?"
• Inventory: "What items are low on stock?"

Ask me anything about your SAS Management System!"""

