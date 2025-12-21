"""
Event Service Business Logic

Service layer functions for Event Service operations.
"""
from datetime import datetime, date
from decimal import Decimal
from sas_management.models import db
from sas_management.service.models import (
    ServiceEvent,
    ServiceEventItem,
    ServiceStaffAssignment,
    ServiceChecklistItem,
)
from sas_management.service.utils import calculate_event_total_cost


def create_service_event(title=None, event_type=None, client_id=None, event_date=None, 
                        venue=None, guest_count=None, status="Planned", notes=None):
    """
    Create a new service event.
    
    Args:
        title: Event title (optional - defaults to "Untitled Event" if not provided)
        event_type: Type of event (Wedding, Kwanjula, etc.)
        client_id: Optional client ID
        event_date: Event date
        venue: Venue name
        guest_count: Number of guests
        status: Initial status (default: "Planned")
        notes: Additional notes
        
    Returns:
        ServiceEvent: Created event object
        
    Raises:
        Exception: If database operation fails
    """
    try:
        # Provide default title if not provided (title is now nullable)
        if not title or not title.strip():
            title = "Untitled Event"
        
        event = ServiceEvent(
            title=title,
            event_type=event_type,
            client_id=client_id,
            event_date=event_date,
            venue=venue,
            guest_count=guest_count,
            status=status,
            notes=notes
        )
        db.session.add(event)
        db.session.commit()
        return event
    except Exception as e:
        db.session.rollback()
        raise


def add_event_item(service_event_id, item_name, category=None, quantity=1, unit_cost=0):
    """
    Add an item to a service event.
    
    Args:
        service_event_id: ID of the service event
        item_name: Name of the item
        category: Category (Food, Equipment, Staff, Logistics)
        quantity: Quantity needed
        unit_cost: Cost per unit
        
    Returns:
        ServiceEventItem: Created item object
        
    Raises:
        Exception: If database operation fails
    """
    try:
        item = ServiceEventItem(
            service_event_id=service_event_id,
            item_name=item_name,
            category=category,
            quantity=quantity,
            unit_cost=Decimal(str(unit_cost))
        )
        item.calculate_total()
        db.session.add(item)
        db.session.commit()
        return item
    except Exception as e:
        db.session.rollback()
        raise


def assign_staff(service_event_id, staff_id=None, role=None, shift=None, notes=None):
    """
    Assign staff to a service event.
    
    Args:
        service_event_id: ID of the service event
        staff_id: Optional User ID
        role: Staff role
        shift: Shift (Morning, Afternoon, Evening, Full Day)
        notes: Additional notes
        
    Returns:
        ServiceStaffAssignment: Created assignment object
        
    Raises:
        Exception: If database operation fails
    """
    try:
        assignment = ServiceStaffAssignment(
            service_event_id=service_event_id,
            staff_id=staff_id,
            role=role,
            shift=shift,
            notes=notes
        )
        db.session.add(assignment)
        db.session.commit()
        return assignment
    except Exception as e:
        db.session.rollback()
        raise


def add_checklist_item(service_event_id, description, stage=None):
    """
    Add a checklist item to a service event.
    
    Args:
        service_event_id: ID of the service event
        description: Task description
        stage: Stage (Preparation, Setup, Service, Teardown)
        
    Returns:
        ServiceChecklistItem: Created checklist item object
        
    Raises:
        Exception: If database operation fails
    """
    try:
        item = ServiceChecklistItem(
            service_event_id=service_event_id,
            description=description,
            stage=stage,
            completed=False
        )
        db.session.add(item)
        db.session.commit()
        return item
    except Exception as e:
        db.session.rollback()
        raise


def toggle_checklist_item(checklist_item_id):
    """
    Toggle completion status of a checklist item.
    
    Args:
        checklist_item_id: ID of the checklist item
        
    Returns:
        bool: New completion status, or None if item not found
        
    Raises:
        Exception: If database operation fails
    """
    try:
        item = ServiceChecklistItem.query.get(checklist_item_id)
        if not item:
            return None
        item.completed = not item.completed
        item.updated_at = datetime.utcnow()
        db.session.commit()
        return item.completed
    except Exception as e:
        db.session.rollback()
        raise


def update_event_status(service_event_id, new_status):
    """
    Update the status of a service event.
    
    Args:
        service_event_id: ID of the service event
        new_status: New status (Planned, Confirmed, In Progress, Completed)
        
    Returns:
        ServiceEvent: Updated event object, or None if event not found
        
    Raises:
        Exception: If database operation fails
    """
    try:
        event = ServiceEvent.query.get(service_event_id)
        if not event:
            return None
        event.status = new_status
        event.updated_at = datetime.utcnow()
        db.session.commit()
        return event
    except Exception as e:
        db.session.rollback()
        raise

