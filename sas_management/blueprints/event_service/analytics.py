"""
Event Service - Analytics Functions
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from sas_management.models import db
from sas_management.blueprints.event_service.models import (
    EventServiceEvent,
    EventServiceOrder,
    EventCosting,
    EventStaffAssignment,
)


def get_event_statistics():
    """Get overall event statistics."""
    total_events = EventServiceEvent.query.count()
    upcoming_events = EventServiceEvent.query.filter(
        EventServiceEvent.event_date >= datetime.utcnow()
    ).count()
    completed_events = EventServiceEvent.query.filter(
        EventServiceEvent.status == "Completed"
    ).count()
    
    return {
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "completed_events": completed_events,
    }


def get_revenue_analytics(start_date=None, end_date=None):
    """Get revenue analytics for events."""
    query = EventServiceOrder.query
    
    if start_date:
        query = query.join(EventServiceEvent).filter(
            EventServiceEvent.event_date >= start_date
        )
    if end_date:
        query = query.join(EventServiceEvent).filter(
            EventServiceEvent.event_date <= end_date
        )
    
    total_revenue = db.session.query(func.sum(EventServiceOrder.total_price)).scalar() or 0
    
    return {
        "total_revenue": float(total_revenue),
        "order_count": query.count(),
    }


def get_cost_analytics(event_id=None):
    """Get cost analytics for events."""
    query = EventCosting.query
    
    if event_id:
        query = query.filter(EventCosting.event_id == event_id)
    
    total_costs = db.session.query(func.sum(EventCosting.total_cost)).scalar() or 0
    
    return {
        "total_costs": float(total_costs),
        "costing_items": query.count(),
    }


def get_staff_utilization():
    """Get staff utilization analytics."""
    total_assignments = EventStaffAssignment.query.count()
    active_assignments = EventStaffAssignment.query.filter(
        EventStaffAssignment.status == "Assigned"
    ).count()
    
    return {
        "total_assignments": total_assignments,
        "active_assignments": active_assignments,
    }

