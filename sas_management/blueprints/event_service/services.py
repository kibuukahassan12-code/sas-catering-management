"""
Event Service - Business Logic Services
"""
from datetime import datetime
from decimal import Decimal
from sas_management.models import db
from sas_management.blueprints.event_service.models import (
    EventServiceEvent,
    EventServiceOrder,
    EventCosting,
    EventStaffAssignment,
    EventVendor,
    EventTimeline,
    EventDocument,
    EventChecklist,
    EventMessage,
    EventReport,
)


def create_event(title, description, event_date, client_id=None, venue=None, guest_count=0, created_by=None):
    """Create a new event."""
    event = EventServiceEvent(
        title=title,
        description=description,
        event_date=event_date,
        client_id=client_id,
        venue=venue,
        guest_count=guest_count,
        created_by=created_by,
        status="Planning"
    )
    db.session.add(event)
    db.session.commit()
    return event


def add_service_order(event_id, service_name, quantity, unit_price, notes=None):
    """Add a service order to an event."""
    total_price = Decimal(quantity) * Decimal(unit_price)
    order = EventServiceOrder(
        event_id=event_id,
        service_name=service_name,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        notes=notes,
        status="Pending"
    )
    db.session.add(order)
    db.session.commit()
    return order


def add_costing(event_id, item_name, category, quantity, unit_cost, is_quoted=False):
    """Add a costing item to an event."""
    total_cost = Decimal(quantity) * Decimal(unit_cost)
    costing = EventCosting(
        event_id=event_id,
        item_name=item_name,
        category=category,
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=total_cost,
        is_quoted=is_quoted,
        quotation_date=datetime.utcnow() if is_quoted else None
    )
    db.session.add(costing)
    db.session.commit()
    return costing


def assign_staff(event_id, staff_id, role=None, start_time=None, end_time=None, hourly_rate=None):
    """Assign staff to an event."""
    assignment = EventStaffAssignment(
        event_id=event_id,
        staff_id=staff_id,
        role=role,
        start_time=start_time,
        end_time=end_time,
        hourly_rate=hourly_rate,
        status="Assigned"
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment


def add_vendor(event_id, vendor_name, vendor_contact=None, service_provided=None, cost=0.00):
    """Add a vendor to an event."""
    vendor = EventVendor(
        event_id=event_id,
        vendor_name=vendor_name,
        vendor_contact=vendor_contact,
        service_provided=service_provided,
        cost=cost,
        status="Pending"
    )
    db.session.add(vendor)
    db.session.commit()
    return vendor


def add_timeline_item(event_id, title, description, scheduled_time):
    """Add a timeline item to an event."""
    timeline = EventTimeline(
        event_id=event_id,
        title=title,
        description=description,
        scheduled_time=scheduled_time,
        status="Scheduled",
        completed=False
    )
    db.session.add(timeline)
    db.session.commit()
    return timeline


def add_document(event_id, filename, file_path, file_type=None, file_size=None, description=None, uploaded_by=None):
    """Add a document to an event."""
    document = EventDocument(
        event_id=event_id,
        filename=filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        description=description,
        uploaded_by=uploaded_by
    )
    db.session.add(document)
    db.session.commit()
    return document


def add_checklist_item(event_id, item_name, description=None, category=None, due_date=None):
    """Add a checklist item to an event."""
    checklist = EventChecklist(
        event_id=event_id,
        item_name=item_name,
        description=description,
        category=category,
        completed=False,
        due_date=due_date
    )
    db.session.add(checklist)
    db.session.commit()
    return checklist


def add_message(event_id, sender_id, message, message_type="General"):
    """Add a message to an event."""
    message_obj = EventMessage(
        event_id=event_id,
        sender_id=sender_id,
        message=message,
        message_type=message_type,
        is_read=False
    )
    db.session.add(message_obj)
    db.session.commit()
    return message_obj


def generate_report(event_id, report_type, title, content, generated_by=None):
    """Generate a report for an event."""
    report = EventReport(
        event_id=event_id,
        report_type=report_type,
        title=title,
        content=content,
        generated_by=generated_by
    )
    db.session.add(report)
    db.session.commit()
    return report

