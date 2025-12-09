"""Event Checklist Service - Managing service and production checklists for events."""
from datetime import datetime, date
from flask import current_app

from models import (
    db, EventChecklist, ChecklistItem, Event, User
)


def get_or_create_checklist(event_id, checklist_type):
    """Get or create a checklist for an event. Returns checklist object."""
    try:
        # Validate checklist type
        if checklist_type not in ['service', 'production']:
            raise ValueError("Checklist type must be 'service' or 'production'")
        
        # Check if checklist exists
        checklist = EventChecklist.query.filter_by(
            event_id=event_id,
            checklist_type=checklist_type
        ).first()
        
        if not checklist:
            # Create new checklist with default items
            event = Event.query.get(event_id)
            if not event:
                raise ValueError("Event not found")
            
            title = "Service Checklist" if checklist_type == 'service' else "Production Checklist"
            
            checklist = EventChecklist(
                event_id=event_id,
                checklist_type=checklist_type,
                title=title,
                created_by=None  # Can be set by caller
            )
            db.session.add(checklist)
            db.session.flush()  # Get checklist.id
            
            # Add default items based on type
            default_items = get_default_items(checklist_type)
            for idx, item_data in enumerate(default_items):
                item = ChecklistItem(
                    checklist_id=checklist.id,
                    description=item_data['description'],
                    order_index=idx,
                    category=item_data.get('category'),
                    due_date=item_data.get('due_date')
                )
                db.session.add(item)
            
            db.session.commit()
        
        return {"success": True, "checklist": checklist}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error getting/creating checklist: {e}")
        return {"success": False, "error": str(e)}


def get_default_items(checklist_type):
    """Get default checklist items based on type."""
    if checklist_type == 'service':
        return [
            {"description": "Confirm event date, time, and venue with client", "category": "Pre-Event"},
            {"description": "Send event confirmation email/SMS to client", "category": "Pre-Event"},
            {"description": "Assign staff roles and send schedules", "category": "Pre-Event"},
            {"description": "Prepare and pack serving equipment", "category": "Setup"},
            {"description": "Load vehicles with all required items", "category": "Setup"},
            {"description": "Arrive at venue and unload equipment", "category": "Setup"},
            {"description": "Set up serving stations and buffet tables", "category": "Setup"},
            {"description": "Coordinate with venue staff", "category": "Setup"},
            {"description": "Begin food service at scheduled time", "category": "Service"},
            {"description": "Monitor food levels and replenish as needed", "category": "Service"},
            {"description": "Ensure staff follow service standards", "category": "Service"},
            {"description": "Handle guest requests and dietary requirements", "category": "Service"},
            {"description": "Pack up all equipment after service", "category": "Cleanup"},
            {"description": "Clean and sanitize all equipment", "category": "Cleanup"},
            {"description": "Load vehicles for return", "category": "Cleanup"},
            {"description": "Return all items to warehouse", "category": "Cleanup"},
            {"description": "Send follow-up thank you message to client", "category": "Post-Event"},
        ]
    else:  # production
        return [
            {"description": "Review menu selections and quantities", "category": "Planning"},
            {"description": "Calculate ingredient requirements", "category": "Planning"},
            {"description": "Check ingredient availability in inventory", "category": "Planning"},
            {"description": "Create production schedule", "category": "Planning"},
            {"description": "Prepare prep lists for kitchen staff", "category": "Pre-Production"},
            {"description": "Pull ingredients from inventory", "category": "Pre-Production"},
            {"description": "Set up workstations and equipment", "category": "Pre-Production"},
            {"description": "Begin food preparation", "category": "Production"},
            {"description": "Monitor cooking times and temperatures", "category": "Production"},
            {"description": "Conduct quality checks on prepared items", "category": "Production"},
            {"description": "Package items according to transport needs", "category": "Packaging"},
            {"description": "Label all packages with event name and date", "category": "Packaging"},
            {"description": "Store items at proper temperatures", "category": "Packaging"},
            {"description": "Load transport containers/vehicles", "category": "Packaging"},
            {"description": "Document waste and losses", "category": "Documentation"},
            {"description": "Update inventory records", "category": "Documentation"},
            {"description": "Clean kitchen and equipment", "category": "Cleanup"},
        ]


def add_checklist_item(checklist_id, description, category=None, order_index=None, due_date=None):
    """Add an item to a checklist."""
    try:
        db.session.begin()
        
        checklist = EventChecklist.query.get(checklist_id)
        if not checklist:
            raise ValueError("Checklist not found")
        
        # Auto-determine order_index if not provided
        if order_index is None:
            max_order = db.session.query(db.func.max(ChecklistItem.order_index)).filter_by(checklist_id=checklist_id).scalar() or 0
            order_index = max_order + 1
        
        item = ChecklistItem(
            checklist_id=checklist_id,
            description=description.strip(),
            order_index=order_index,
            category=category,
            due_date=due_date
        )
        
        db.session.add(item)
        db.session.commit()
        
        return {"success": True, "item_id": item.id, "item": item}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error adding checklist item: {e}")
        return {"success": False, "error": str(e)}


def toggle_checklist_item(item_id, completed_by=None, notes=None):
    """Toggle completion status of a checklist item."""
    try:
        db.session.begin()
        
        item = ChecklistItem.query.get(item_id)
        if not item:
            raise ValueError("Checklist item not found")
        
        item.is_completed = not item.is_completed
        
        if item.is_completed:
            item.completed_at = datetime.utcnow()
            item.completed_by = completed_by
        else:
            item.completed_at = None
            item.completed_by = None
        
        if notes:
            item.notes = notes
        
        # Update checklist updated_at
        item.checklist.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {"success": True, "item": item, "is_completed": item.is_completed}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error toggling checklist item: {e}")
        return {"success": False, "error": str(e)}


def update_checklist_item(item_id, description=None, category=None, order_index=None, due_date=None, notes=None):
    """Update checklist item details."""
    try:
        db.session.begin()
        
        item = ChecklistItem.query.get(item_id)
        if not item:
            raise ValueError("Checklist item not found")
        
        if description is not None:
            item.description = description.strip()
        if category is not None:
            item.category = category
        if order_index is not None:
            item.order_index = order_index
        if due_date is not None:
            item.due_date = due_date
        if notes is not None:
            item.notes = notes
        
        # Update checklist updated_at
        item.checklist.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {"success": True, "item": item}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating checklist item: {e}")
        return {"success": False, "error": str(e)}


def delete_checklist_item(item_id):
    """Delete a checklist item."""
    try:
        db.session.begin()
        
        item = ChecklistItem.query.get(item_id)
        if not item:
            raise ValueError("Checklist item not found")
        
        checklist_id = item.checklist_id
        db.session.delete(item)
        
        # Update checklist updated_at
        checklist = EventChecklist.query.get(checklist_id)
        if checklist:
            checklist.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error deleting checklist item: {e}")
        return {"success": False, "error": str(e)}


def get_event_checklists(event_id):
    """Get all checklists for an event."""
    try:
        checklists = EventChecklist.query.filter_by(event_id=event_id).all()
        
        # Ensure both service and production checklists exist
        service_checklist = next((c for c in checklists if c.checklist_type == 'service'), None)
        production_checklist = next((c for c in checklists if c.checklist_type == 'production'), None)
        
        return {
            "success": True,
            "service": service_checklist,
            "production": production_checklist,
            "all": checklists
        }
    except Exception as e:
        current_app.logger.exception(f"Error getting event checklists: {e}")
        return {"success": False, "error": str(e), "service": None, "production": None, "all": []}

