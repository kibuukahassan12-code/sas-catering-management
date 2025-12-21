"""
Event Service Blueprint - Database Models

All models use unique table names prefixed with 'event_service_' to avoid conflicts.
Core event models are imported from sas_management.models to avoid duplication.
"""
from datetime import datetime
from decimal import Decimal
from sas_management.models import (
    db,
    Event,
    EventTimeline,
    EventStaffAssignment,
    EventVendorAssignment,
    EventChecklist,
    EventChecklistItem,
    EventMessage,
    EventDocument,
    EventCostItem,
    EventRevenueItem
)


class EventServiceEvent(db.Model):
    """Main Event model for Event Service module."""
    __tablename__ = "event_service_events"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(255), nullable=True)
    guest_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(50), default="Planning")
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_orders = db.relationship("EventServiceOrder", back_populates="event", cascade="all, delete-orphan")
    costings = db.relationship("EventCosting", back_populates="event", cascade="all, delete-orphan")
    # Note: Core event models (EventStaffAssignment, EventDocument, EventChecklist, EventMessage, etc.)
    # are imported from sas_management.models and reference "event.id" not "event_service_events.id"
    # Relationships with these models may need adjustment if used with EventServiceEvent
    vendors = db.relationship("EventVendor", back_populates="event", cascade="all, delete-orphan")
    reports = db.relationship("EventReport", back_populates="event", cascade="all, delete-orphan")


class EventServiceOrder(db.Model):
    """Service orders for events."""
    __tablename__ = "event_service_orders"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event_service_events.id"), nullable=False)
    service_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    total_price = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    status = db.Column(db.String(50), default="Pending")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = db.relationship("EventServiceEvent", back_populates="service_orders")


class EventCosting(db.Model):
    """Costing and quotations for events."""
    __tablename__ = "event_service_costings"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event_service_events.id"), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # Labor, Materials, Equipment, etc.
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    is_quoted = db.Column(db.Boolean, nullable=False, default=False)
    quotation_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = db.relationship("EventServiceEvent", back_populates="costings")


# EventStaffAssignment is imported from sas_management.models
# The existing model uses table "event_staff_assignment" and references "event.id"
# Note: This may require relationship adjustments if used with EventServiceEvent


class EventVendor(db.Model):
    """Vendor assignments for events."""
    __tablename__ = "event_service_vendors"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event_service_events.id"), nullable=False)
    vendor_name = db.Column(db.String(200), nullable=False)
    vendor_contact = db.Column(db.String(200), nullable=True)
    service_provided = db.Column(db.String(200), nullable=True)
    cost = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    status = db.Column(db.String(50), default="Pending")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = db.relationship("EventServiceEvent", back_populates="vendors")


# EventTimeline is imported from sas_management.models
# The existing model uses table "event_timeline" and references "event.id"
# Note: This may require relationship adjustments if used with EventServiceEvent


# EventDocument is imported from sas_management.models
# The existing model uses table "event_document" and references "event.id"
# Note: This may require relationship adjustments if used with EventServiceEvent


# EventChecklist is imported from sas_management.models
# The existing model uses table "event_checklist" and references "event.id"
# Note: This may require relationship adjustments if used with EventServiceEvent


# EventMessage is imported from sas_management.models
# The existing model uses table "event_message" and references "event_message_thread.id"
# Note: This may require relationship adjustments if used with EventServiceEvent


class EventReport(db.Model):
    """Reports generated for events."""
    __tablename__ = "event_service_reports"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event_service_events.id"), nullable=False)
    report_type = db.Column(db.String(100), nullable=False)  # Financial, Performance, Summary, etc.
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    generated_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship("EventServiceEvent", back_populates="reports")
