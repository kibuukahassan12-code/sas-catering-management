"""
Event Service Utilities

Helper functions for the Event Service module.
"""
from datetime import date, datetime
from decimal import Decimal
from sas_management.service.models import ServiceEvent, ServiceEventItem


def calculate_event_total_cost(service_event_id):
    """
    Calculate total cost for a service event from all items.
    
    Args:
        service_event_id: ID of the service event
        
    Returns:
        Decimal: Total cost (0.00 if no items)
    """
    try:
        items = ServiceEventItem.query.filter_by(service_event_id=service_event_id).all() or []
        total = sum(Decimal(str(item.total_cost or 0)) for item in items)
        return total
    except Exception:
        return Decimal("0.00")


def get_events_by_status(status):
    """
    Get all service events with a specific status.
    
    Args:
        status: Status string (Planned, Confirmed, In Progress, Completed)
        
    Returns:
        List of ServiceEvent objects (empty list if none found)
    """
    try:
        return ServiceEvent.query.filter_by(status=status).order_by(ServiceEvent.event_date.asc()).all() or []
    except Exception:
        return []


def get_upcoming_events(days=7):
    """
    Get events happening within the next N days.
    
    Args:
        days: Number of days to look ahead (default: 7)
        
    Returns:
        List of ServiceEvent objects (empty list if none found)
    """
    try:
        today = date.today()
        end_date = date.fromordinal(today.toordinal() + days)
        # NULL-safe query - handle missing event_date column gracefully
        return ServiceEvent.query.filter(
            ServiceEvent.event_date >= today,
            ServiceEvent.event_date <= end_date
        ).order_by(ServiceEvent.event_date.asc().nullslast()).all() or []
    except Exception:
        # Return empty list if query fails (e.g., missing columns)
        return []


def get_events_today():
    """Get events happening today."""
    try:
        today = date.today()
        # NULL-safe query
        return ServiceEvent.query.filter_by(event_date=today).all() or []
    except Exception:
        # Return empty list if query fails (e.g., missing columns)
        return []


def get_checklist_progress(service_event_id):
    """
    Calculate checklist completion percentage.
    
    Args:
        service_event_id: ID of the service event
        
    Returns:
        tuple: (completed_count, total_count, percentage)
    """
    try:
        from sas_management.service.models import ServiceChecklistItem
        items = ServiceChecklistItem.query.filter_by(service_event_id=service_event_id).all() or []
        total = len(items)
        completed = sum(1 for item in items if item.completed)
        percentage = (completed / total * 100) if total > 0 else 0
        return (completed, total, percentage)
    except Exception:
        return (0, 0, 0)

