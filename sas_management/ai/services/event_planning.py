"""
Event Planning AI Service

Provides AI-powered event planning assistance including menu suggestions,
staff recommendations, timeline blocks, and cost estimates.
"""
from flask import current_app
from datetime import datetime, timedelta
from decimal import Decimal


def run(payload, user):
    """
    Run Event Planning AI service.
    
    Args:
        payload: dict with 'event_id' (required) or 'event_type' and 'guest_count'
        user: Current user object
    
    Returns:
        dict: {
            'success': bool,
            'suggested_menu': list,
            'required_staff_roles': list,
            'timeline_blocks': list,
            'estimated_cost': float,
            'error': str (if failed)
        }
    """
    try:
        from sas_management.models import Event, MenuPackage, Employee, EventStaffAssignment
        
        event_id = payload.get('event_id')
        event = None
        
        if event_id:
            event = Event.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': f'Event with ID {event_id} not found',
                    'suggested_menu': [],
                    'required_staff_roles': [],
                    'timeline_blocks': [],
                    'estimated_cost': 0.0
                }
        else:
            # Use provided event_type and guest_count for generic suggestions
            event_type = payload.get('event_type', 'General')
            guest_count = payload.get('guest_count', 50)
            
            return {
                'success': True,
                'suggested_menu': _suggest_menu(event_type, guest_count),
                'required_staff_roles': _suggest_staff_roles(event_type, guest_count),
                'timeline_blocks': _suggest_timeline(event_type),
                'estimated_cost': _estimate_cost(event_type, guest_count),
                'note': f'Generic suggestions for {event_type} event with {guest_count} guests'
            }
        
        # Event-specific suggestions
        guest_count = event.guest_count or 50
        event_type = event.event_type or 'General'
        
        # Suggested menu
        suggested_menu = _suggest_menu(event_type, guest_count)
        if event.menu_package_id:
            try:
                menu_pkg = MenuPackage.query.get(event.menu_package_id)
                if menu_pkg:
                    suggested_menu.insert(0, {
                        'name': menu_pkg.name,
                        'description': f'Current selection: {menu_pkg.name}',
                        'recommended': True
                    })
            except:
                pass
        
        # Required staff roles
        required_staff_roles = _suggest_staff_roles(event_type, guest_count)
        
        # Check existing staff assignments
        existing_staff = EventStaffAssignment.query.filter_by(event_id=event_id).all()
        assigned_roles = [s.role for s in existing_staff if hasattr(s, 'role')]
        
        # Timeline blocks
        timeline_blocks = _suggest_timeline(event_type)
        if event.date:
            # Adjust timeline to event date
            for block in timeline_blocks:
                if 'time' in block:
                    block['date'] = event.date.isoformat()
        
        # Estimated cost
        estimated_cost = _estimate_cost(event_type, guest_count)
        if event.budget_estimate:
            estimated_cost = float(event.budget_estimate)
        
        return {
            'success': True,
            'suggested_menu': suggested_menu,
            'required_staff_roles': required_staff_roles,
            'assigned_staff': [{'role': r} for r in assigned_roles],
            'timeline_blocks': timeline_blocks,
            'estimated_cost': estimated_cost,
            'event_title': event.title,
            'event_date': event.date.isoformat() if event.date else None
        }
        
    except Exception as e:
        current_app.logger.exception(f"Event Planning AI error: {e}")
        return {
            'success': False,
            'error': str(e),
            'suggested_menu': [],
            'required_staff_roles': [],
            'timeline_blocks': [],
            'estimated_cost': 0.0
        }


def _suggest_menu(event_type, guest_count):
    """Suggest menu items based on event type and guest count."""
    base_items = [
        {'name': 'Main Course', 'description': 'Primary dish selection', 'quantity': guest_count},
        {'name': 'Side Dishes', 'description': 'Complementary sides', 'quantity': int(guest_count * 1.5)},
        {'name': 'Beverages', 'description': 'Drinks and refreshments', 'quantity': guest_count * 2},
        {'name': 'Dessert', 'description': 'Sweet course', 'quantity': guest_count}
    ]
    
    if 'wedding' in event_type.lower():
        base_items.append({'name': 'Wedding Cake', 'description': 'Traditional wedding cake', 'quantity': 1})
    elif 'corporate' in event_type.lower():
        base_items.append({'name': 'Coffee Station', 'description': 'Professional coffee service', 'quantity': 1})
    
    return base_items


def _suggest_staff_roles(event_type, guest_count):
    """Suggest required staff roles."""
    roles = []
    
    # Base staff
    roles.append({'role': 'Event Manager', 'count': 1, 'priority': 'high'})
    roles.append({'role': 'Chef', 'count': 1 if guest_count < 100 else 2, 'priority': 'high'})
    roles.append({'role': 'Server', 'count': max(2, guest_count // 25), 'priority': 'high'})
    
    if guest_count > 50:
        roles.append({'role': 'Assistant Chef', 'count': 1, 'priority': 'medium'})
    if guest_count > 100:
        roles.append({'role': 'Bar Staff', 'count': 2, 'priority': 'medium'})
        roles.append({'role': 'Cleanup Crew', 'count': 2, 'priority': 'low'})
    
    return roles


def _suggest_timeline(event_type):
    """Suggest timeline blocks for event."""
    return [
        {'block': 'Setup', 'duration_hours': 2, 'time': '08:00', 'tasks': ['Venue preparation', 'Equipment setup']},
        {'block': 'Preparation', 'duration_hours': 3, 'time': '10:00', 'tasks': ['Food preparation', 'Staff briefing']},
        {'block': 'Service', 'duration_hours': 4, 'time': '13:00', 'tasks': ['Event execution', 'Guest service']},
        {'block': 'Cleanup', 'duration_hours': 2, 'time': '17:00', 'tasks': ['Equipment breakdown', 'Venue cleanup']}
    ]


def _estimate_cost(event_type, guest_count):
    """Estimate event cost."""
    base_cost_per_guest = 50000  # UGX
    cost = guest_count * base_cost_per_guest
    
    if 'wedding' in event_type.lower():
        cost *= 1.5
    elif 'corporate' in event_type.lower():
        cost *= 1.2
    
    return float(cost)

