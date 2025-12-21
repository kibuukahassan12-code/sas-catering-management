"""
Event Service Department - Authoritative Models

These are the SINGLE source of truth for Event Service data.
No duplicate models should exist elsewhere.
"""
from datetime import datetime, date
from decimal import Decimal
from sas_management.models import db
from sqlalchemy.orm import relationship


class ServiceEvent(db.Model):
    """Service Event - Main event record for service department."""
    __tablename__ = "service_events"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)  # Made nullable for safety - can be empty initially
    event_type = db.Column(db.String(100), nullable=True)  # Wedding, Kwanjula, Kukyala, Kuhingira, Nikah, Corporate, etc.
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)  # Optional link to Client
    event_date = db.Column(db.Date, nullable=True)
    venue = db.Column(db.String(255), nullable=True)
    guest_count = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Planned")  # Planned, Confirmed, In Progress, Completed
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", backref="service_events")
    items = relationship("ServiceEventItem", back_populates="service_event", cascade="all, delete-orphan")
    staff_assignments = relationship("ServiceStaffAssignment", back_populates="service_event", cascade="all, delete-orphan")
    checklist_items = relationship("ServiceChecklistItem", back_populates="service_event", cascade="all, delete-orphan")
    # New relationships for operational management
    checklists = relationship("ServiceChecklist", back_populates="service_event", cascade="all, delete-orphan")
    item_movements = relationship("ServiceItemMovement", back_populates="service_event", cascade="all, delete-orphan")
    team_leaders = relationship("ServiceTeamLeader", back_populates="service_event", cascade="all, delete-orphan")
    team_assignments = relationship("ServiceTeamAssignment", back_populates="service_event", cascade="all, delete-orphan")
    
    def __repr__(self):
        title_display = self.title or "Untitled"
        return f'<ServiceEvent {self.id}: {title_display}>'


class ServiceEventItem(db.Model):
    """Service Event Item - Items, equipment, or services needed for an event."""
    __tablename__ = "service_event_items"
    
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey("service_events.id", ondelete="CASCADE"), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # Food, Equipment, Staff, Logistics
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_event = relationship("ServiceEvent", back_populates="items")
    
    def __repr__(self):
        return f'<ServiceEventItem {self.id}: {self.item_name}>'
    
    def calculate_total(self):
        """Calculate total_cost from quantity * unit_cost."""
        self.total_cost = Decimal(str(self.quantity)) * Decimal(str(self.unit_cost))
        return self.total_cost


class ServiceStaffAssignment(db.Model):
    """Service Staff Assignment - Staff assigned to service events."""
    __tablename__ = "service_staff_assignments"
    
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey("service_events.id", ondelete="CASCADE"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # Optional link to User
    role = db.Column(db.String(100), nullable=True)  # Manager, Server, Chef, etc.
    shift = db.Column(db.String(50), nullable=True)  # Morning, Afternoon, Evening, Full Day
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    service_event = relationship("ServiceEvent", back_populates="staff_assignments")
    staff = relationship("User", backref="service_assignments")  # Optional - safe if User doesn't exist
    
    def __repr__(self):
        return f'<ServiceStaffAssignment {self.id}: Event {self.service_event_id}>'


class ServiceChecklistItem(db.Model):
    """Service Checklist Item - Task checklist for service events."""
    __tablename__ = "service_checklist_items"
    
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey("service_events.id", ondelete="CASCADE"), nullable=False)
    stage = db.Column(db.String(50), nullable=True)  # Preparation, Setup, Service, Teardown
    description = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_event = relationship("ServiceEvent", back_populates="checklist_items")
    
    def __repr__(self):
        return f'<ServiceChecklistItem {self.id}: {self.description[:30]}>'


class ServiceChecklist(db.Model):
    """Service Checklist - Phase-based checklist for service events."""
    __tablename__ = "service_checklists"
    
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey("service_events.id", ondelete="CASCADE"), nullable=False)
    phase = db.Column(db.String(50), nullable=False)  # pre_event, on_site, post_event
    title = db.Column(db.String(255), nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    assigned_staff = db.Column(db.String(255), nullable=True)  # Staff name or ID
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_event = relationship("ServiceEvent", back_populates="checklists")
    items = relationship("ServiceChecklistItemNew", back_populates="checklist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ServiceChecklist {self.id}: {self.title} ({self.phase})>'


class ServiceChecklistItemNew(db.Model):
    """Service Checklist Item - Individual items within a checklist."""
    __tablename__ = "service_checklist_items_new"
    
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey("service_checklists.id", ondelete="CASCADE"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_done = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    checklist = relationship("ServiceChecklist", back_populates="items")
    
    def __repr__(self):
        return f'<ServiceChecklistItemNew {self.id}: {self.description[:30]}>'


class ServiceItemMovement(db.Model):
    """Service Item Movement - Track items taken and returned for events."""
    __tablename__ = "service_item_movements"
    
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey("service_events.id", ondelete="CASCADE"), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    quantity_taken = db.Column(db.Integer, nullable=False, default=0)
    quantity_returned = db.Column(db.Integer, nullable=False, default=0)
    condition_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="returned")  # returned, partial, missing
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_event = relationship("ServiceEvent", back_populates="item_movements")
    
    def __repr__(self):
        return f'<ServiceItemMovement {self.id}: {self.item_name} ({self.status})>'
    
    def update_status(self):
        """Update status based on quantities."""
        if self.quantity_returned >= self.quantity_taken:
            self.status = "returned"
        elif self.quantity_returned > 0:
            self.status = "partial"
        else:
            self.status = "missing"


class ServiceTeamLeader(db.Model):
    """Service Team Leader - Team leader assignment for service events."""
    __tablename__ = "service_team_leaders"
    
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey("service_events.id", ondelete="CASCADE"), nullable=False)
    staff_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    responsibilities = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_event = relationship("ServiceEvent", back_populates="team_leaders")
    
    def __repr__(self):
        return f'<ServiceTeamLeader {self.id}: {self.staff_name}>'


class PartTimeServiceStaff(db.Model):
    """Part-Time Service Staff - Part-time staff members for service events."""
    __tablename__ = "part_time_service_staff"
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(100), nullable=True)  # Server, Chef, Waiter, etc.
    pay_rate = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = relationship("ServiceTeamAssignment", back_populates="staff")
    
    def __repr__(self):
        return f'<PartTimeServiceStaff {self.id}: {self.full_name}>'


class ServiceTeamAssignment(db.Model):
    """Service Team Assignment - Assign part-time staff to service events."""
    __tablename__ = "service_team_assignments_new"
    
    id = db.Column(db.Integer, primary_key=True)
    service_event_id = db.Column(db.Integer, db.ForeignKey("service_events.id", ondelete="CASCADE"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("part_time_service_staff.id", ondelete="CASCADE"), nullable=False)
    attendance_status = db.Column(db.String(50), nullable=True)  # confirmed, present, absent, pending
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service_event = relationship("ServiceEvent", back_populates="team_assignments")
    staff = relationship("PartTimeServiceStaff", back_populates="assignments")
    
    def __repr__(self):
        return f'<ServiceTeamAssignment {self.id}: Event {self.service_event_id}, Staff {self.staff_id}>'