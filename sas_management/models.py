# SAS Best Foods Management System - Database Models
# Complete models.py file with all required models

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from enum import Enum
from decimal import Decimal
import json

# Database instance - SINGLE INSTANCE ONLY
db = SQLAlchemy()

# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    Admin = "Admin"
    SalesManager = "SalesManager"
    KitchenStaff = "KitchenStaff"
    Waiter = "Waiter"
    Cleaner = "Cleaner"
    Driver = "Driver"
    HireManager = "HireManager"
    BakeryManager = "BakeryManager"

class InvoiceStatus(str, Enum):
    Draft = "Draft"
    Issued = "Issued"
    Paid = "Paid"
    Overdue = "Overdue"
    Cancelled = "Cancelled"

class TransactionType(str, Enum):
    Income = "Income"
    Expense = "Expense"

class TaskStatus(str, Enum):
    Pending = "Pending"
    InProgress = "In Progress"
    Complete = "Complete"
    Cancelled = "Cancelled"

class QuotationSource(str, Enum):
    Catering = "Catering"
    Bakery = "Bakery"
    Hire = "Hire"

# Production budgeting
class ProductionBudgetStatus(str, Enum):
    Draft = "Draft"
    Submitted = "Submitted"
    Approved = "Approved"
    Rejected = "Rejected"

class BudgetItemCategory(str, Enum):
    FoodItems = "Food Items"
    Sauces = "Sauces"
    MarketAccessories = "Market Accessories"
    Spices = "Spices"
    Fruits = "Fruits"
    TeaBeverages = "Tea & Beverages"
    Transport = "Transport"
    Hire = "Hire"
    ProductionLabour = "Production Labour"
    ServiceLabour = "Service Labour"

# ============================================================================
# CORE MODELS
# ============================================================================

# RBAC MODELS — FULL BACKEND RBAC WITH STABLE RELATIONSHIPS


class RolePermission(db.Model):

    __tablename__ = "role_permissions"

    id = db.Column(db.Integer, primary_key=True)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    permission_id = db.Column(db.Integer, db.ForeignKey("permissions.id"))



    role = db.relationship(

        "Role",

        overlaps="permissions,roles"

    )

    permission = db.relationship(

        "Permission",

        overlaps="permissions,roles"

    )


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False, unique=True)  # Legacy field for backward compatibility
    name = db.Column(db.String(200), nullable=False, unique=False)  # Human-readable permission name
    group = db.Column(db.String(100))  # Legacy field for backward compatibility
    module = db.Column(db.String(100), nullable=True)  # e.g. 'event_service', 'accounting'
    action = db.Column(db.String(50), nullable=True)  # e.g. 'view', 'create', 'edit', 'delete', 'approve'
    description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship(

        "Role",

        secondary="role_permissions",

        back_populates="permissions",

        overlaps="role_permissions"

    )





# Many-to-many association table for Group-Role relationship
group_roles = db.Table(
    'group_roles',
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# Many-to-many association table for User-Role relationship
user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)


class Group(db.Model):
    """Group model for organizing roles and permissions."""
    __tablename__ = "groups"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Many-to-many: Group <-> Role
    roles = db.relationship(
        "Role",
        secondary="group_roles",
        back_populates="groups",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Group {self.name}>"
    
    def get_all_permissions(self):
        """Get all permissions from all roles in this group."""
        permissions = set()
        for role in self.roles:
            for permission in role.permissions:
                permissions.add(permission)
        return list(permissions)
    
    def get_permission_count(self):
        """Get the total count of unique permissions across all roles."""
        return len(self.get_all_permissions())
    
    def get_role_count(self):
        """Get the count of roles in this group."""
        return self.roles.count()


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_system_role = db.Column(db.Boolean, default=False, nullable=False)  # True for ADMIN
    system_protected = db.Column(db.Boolean, default=False, nullable=False)  # True for ADMIN (cannot be deleted/modified)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Many-to-many: Role <-> Permission
    permissions = db.relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        overlaps="role_permissions"
    )

    # Many-to-many: Role <-> User (via user_roles table)
    users = db.relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="dynamic"
    )
    
    # Many-to-many: Role <-> Group
    groups = db.relationship(
        "Group",
        secondary="group_roles",
        back_populates="roles",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Role {self.name}>"


class User(UserMixin, db.Model):
    """User authentication and management."""
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    
    # Password change flags (must_change_password is primary, force_password_change for backward compatibility)
    must_change_password = db.Column(db.Boolean, default=False)
    force_password_change = db.Column(db.Boolean, default=False)  # Legacy field, kept for compatibility
    first_login = db.Column(db.Boolean, default=True)
    
    # Legacy single role (for backward compatibility)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    role_obj = db.relationship("Role", foreign_keys=[role_id], backref="legacy_users", lazy=True)
    
    # Legacy role enum field (for backward compatibility with old schema)
    role = db.Column(db.Enum(UserRole), nullable=True)
    
    # Temporary role assignment fields
    previous_role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    role_expiry_date = db.Column(db.DateTime, nullable=True)
    role_expires_at = db.Column(db.DateTime, nullable=True)  # Alias for role_expiry_date (for compatibility)
    is_temporary_role = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps (created_at may exist in DB)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    
    # Many-to-many: User <-> Role
    roles = db.relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="dynamic"
    )
    
    def get_primary_role(self):
        """Get the primary role (first role or legacy role_id)."""
        if self.roles.count() > 0:
            return self.roles.first()
        return self.role_obj
    
    @property
    def is_admin(self):
        """Check if user has Admin role - bypasses all permission checks."""
        try:
            # Check legacy role enum field first
            if self.role == UserRole.Admin:
                return True
            # Check role_obj name
            if self.role_obj and hasattr(self.role_obj, 'name'):
                if self.role_obj.name == 'Admin':
                    return True
            # Check roles relationship
            if self.roles.count() > 0:
                for role in self.roles:
                    if role.name == 'Admin':
                        return True
            return False
        except Exception:
            return False
    
    # Add this helper safely:
    def is_super_admin(self):
        """Check if user is SuperAdmin - bypasses all permission checks."""
        try:
            # PRIORITY 1: Grant admin access to first user (system owner)
            # This ensures the first user always has admin access
            if hasattr(self, 'id') and self.id == 1:
                return True
            
            # PRIORITY 2: Hardcoded admin emails - always grant full access
            # Add your email here for permanent admin access
            ADMIN_EMAILS = [
                # Add your email addresses here (case-insensitive)
                # Example: "admin@example.com",
                # Example: "your-email@gmail.com",
            ]
            
            # Check if email is in admin list (case-insensitive)
            if self.email and ADMIN_EMAILS:
                if self.email.lower() in [e.lower() for e in ADMIN_EMAILS]:
                    return True
            
            # PRIORITY 3: Check role-based SuperAdmin
            if hasattr(self, 'role_obj') and self.role_obj:
                if hasattr(self.role_obj, 'name'):
                    role_name = self.role_obj.name.lower() if self.role_obj.name else ""
                    if role_name == "superadmin":
                        return True
            
            return False
        except Exception as e:
            # If any error occurs, check if it's the first user as fallback
            try:
                if hasattr(self, 'id') and self.id == 1:
                    return True
            except:
                pass
            return False
    
    def has_permission(self, code):
        """Check if user has a specific permission. Admin always has full access."""
        # Admin bypass: If user is Admin, grant all permissions
        if self.is_admin:
            return True
        # ALL PERMISSIONS GRANTED - No restrictions for non-admin users
        return True
    
    def get_role_name(self):
        """Get the role name for display purposes."""
        try:
            primary_role = self.get_primary_role()
            if primary_role:
                return primary_role.name
            return "Unassigned"
        except:
            return "Unassigned"
    
    def has_role(self, role_name):
        """Check if user has a specific role. Admin always has all roles."""
        # Admin bypass: If user is Admin, grant all roles
        if self.is_admin:
            return True
        # ALL ROLES GRANTED - No restrictions for non-admin users
        return True
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Client(db.Model):
    """Client management."""
    __tablename__ = "client"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    company = db.Column(db.String(255), nullable=True)
    address = db.Column(db.Text, nullable=True)
    preferred_channel = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = db.relationship("Event", back_populates="client", cascade="all, delete-orphan")
    notes = db.relationship("ClientNote", back_populates="client", cascade="all, delete-orphan")
    documents = db.relationship("ClientDocument", back_populates="client", cascade="all, delete-orphan")
    activities = db.relationship("ClientActivity", back_populates="client", cascade="all, delete-orphan")
    communications = db.relationship("ClientCommunication", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Client {self.name}>'


# ============================================================================
# EVENT STATUS ENUM
# ============================================================================

class EventStatus(str, Enum):
    NotStarted = "Not Started"
    AwaitingPayment = "Awaiting Payment"
    Confirmed = "Confirmed"
    Planning = "Planning"
    Preparing = "Preparing"
    InProgress = "In Progress"
    Done = "Done"


# ============================================================================
# VENUE MODEL
# ============================================================================

class Venue(db.Model):
    """Venue management for events."""
    __tablename__ = "venue"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=True)
    layout_description = db.Column(db.Text, nullable=True)
    capacity = db.Column(db.Integer, nullable=True)
    google_maps_link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    events = db.relationship("Event", back_populates="venue_obj")
    
    def __repr__(self):
        return f'<Venue {self.name}>'


# ============================================================================
# MENU PACKAGE MODEL
# ============================================================================

class MenuPackage(db.Model):
    """Menu packages for events."""
    __tablename__ = "menu_package"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price_per_guest = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text, nullable=True)
    items = db.Column(db.Text, nullable=True)  # Stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    events = db.relationship("Event", back_populates="menu_package_obj")
    
    @property
    def items_list(self):
        """Parse items JSON string to Python list."""
        if not self.items:
            return []
        try:
            parsed = json.loads(self.items)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            # If items is already a list (legacy data), return as is
            if isinstance(self.items, list):
                return self.items
            return []
    
    def __repr__(self):
        return f"<MenuPackage {self.name}>"


# ============================================================================
# EVENT MODEL (NEW INDUSTRY-GRADE)
# ============================================================================

class Event(db.Model):
    """Industry-grade Event management."""
    __tablename__ = "event"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    client_name = db.Column(db.String(255), nullable=False)
    client_phone = db.Column(db.String(50), nullable=True)
    client_email = db.Column(db.String(200), nullable=True)
    event_type = db.Column(db.String(255), nullable=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    event_date = db.Column(db.Date, nullable=True)  # Legacy field for backward compatibility
    start_time = db.Column(db.String(50), nullable=True)
    end_time = db.Column(db.String(50), nullable=True)
    guest_count = db.Column(db.Integer, nullable=False, default=0)
    menu_package_id = db.Column(db.Integer, db.ForeignKey("menu_package.id"), nullable=True)
    budget_estimate = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    quoted_value = db.Column(db.Float, default=0.0)  # Legacy field for backward compatibility
    actual_cost = db.Column(db.Numeric(12, 2), nullable=True)
    # Budgeting & Cost Sheet fields
    labor_cost = db.Column(db.Float, default=0.0)
    transport_cost = db.Column(db.Float, default=0.0)
    equipment_cost = db.Column(db.Float, default=0.0)
    ingredients_cost = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    profit = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Not Started')  # Support both enum and string
    notes = db.Column(db.Text, nullable=True)
    signature_path = db.Column(db.String(500), nullable=True)  # Path to client signature image
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Legacy support - keep client_id for backward compatibility
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)

    # Relationships
    venue_obj = db.relationship("Venue", back_populates="events")
    menu_package_obj = db.relationship("MenuPackage", back_populates="events")
    client = db.relationship("Client", back_populates="events", foreign_keys=[client_id])
    timelines = db.relationship("EventTimeline", back_populates="event", cascade="all, delete-orphan", order_by="EventTimeline.due_date")
    staff_assignments = db.relationship("EventStaffAssignment", back_populates="event", cascade="all, delete-orphan")
    checklist_items = db.relationship("EventChecklistItem", back_populates="event", cascade="all, delete-orphan")
    vendor_assignments = db.relationship("EventVendorAssignment", back_populates="event", cascade="all, delete-orphan")
    # Legacy relationships (kept for backward compatibility)
    menu_selections = db.relationship("EventMenuSelection", back_populates="event", cascade="all, delete-orphan")
    documents = db.relationship("EventDocument", back_populates="event", cascade="all, delete-orphan")
    communications = db.relationship("EventCommunication", back_populates="event", cascade="all, delete-orphan")
    checklists = db.relationship("EventChecklist", back_populates="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Event {self.title}>'
    
    def get_checklist_progress(self):
        """Calculate checklist completion percentage."""
        items = self.checklist_items
        if not items:
            return 0
        completed = sum(1 for item in items if item.completed)
        return int((completed / len(items)) * 100) if items else 0
    
    def calculate_costs(self):
        """Calculate total cost and profit from individual cost components."""
        self.total_cost = (
            (self.labor_cost or 0)
            + (self.transport_cost or 0)
            + (self.equipment_cost or 0)
            + (self.ingredients_cost or 0)
        )
        self.profit = (self.quoted_value or 0) - self.total_cost

    # ---------------------------------------------------------------------
    # Template compatibility aliases (legacy templates use these names)
    # ---------------------------------------------------------------------
    @property
    def event_name(self):
        """Legacy alias for title (used by older templates/services)."""
        return self.title

    @event_name.setter
    def event_name(self, value):
        self.title = value

    @property
    def venue(self):
        """Legacy alias for venue name (string)."""
        try:
            return self.venue_obj.name if self.venue_obj else None
        except Exception:
            return None
    
    @property
    def floor_plan_id(self):
        """Get the floor plan ID for this event, if one exists."""
        # FloorPlan is defined later in this file, but at runtime it's available
        # Use a try-except to handle cases where the model might not be loaded yet
        try:
            # Import here to avoid circular dependencies
            floor_plan = FloorPlan.query.filter_by(event_id=self.id).first()
            return floor_plan.id if floor_plan else None
        except (NameError, AttributeError):
            # Fallback to raw SQL if FloorPlan isn't available yet
            from sqlalchemy import text
            from sqlalchemy.orm import object_session
            session = object_session(self)
            if session:
                result = session.execute(
                    text("SELECT id FROM floor_plan WHERE event_id = :event_id LIMIT 1"),
                    {"event_id": self.id}
                ).fetchone()
                return result[0] if result else None
            return None


# ============================================================================
# CLIENT-RELATED MODELS
# ============================================================================

class ClientNote(db.Model):
    """Notes for clients."""
    __tablename__ = "client_note"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client", back_populates="notes")
    user = db.relationship("User")

    # Template/API compatibility: older code uses `content`
    @property
    def content(self):
        return self.note

    @content.setter
    def content(self, value):
        self.note = value

    def __repr__(self):
        return f'<ClientNote {self.id}>'


class ClientDocument(db.Model):
    """Documents for clients."""
    __tablename__ = "client_document"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client", back_populates="documents")
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<ClientDocument {self.title}>'


class ClientActivity(db.Model):
    """Activity log for clients."""
    __tablename__ = "client_activity"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client", back_populates="activities")
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<ClientActivity {self.activity_type}>'


class ClientCommunication(db.Model):
    """Client communications."""
    __tablename__ = "client_communication"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    communication_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    direction = db.Column(db.String(20), nullable=False, default="Outbound")
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client", back_populates="communications")
    user = db.relationship("User")
    event = db.relationship("Event")
    
    def __repr__(self):
        return f'<ClientCommunication {self.communication_type}>'


# ============================================================================
# EVENT-RELATED MODELS
# ============================================================================

# ============================================================================
# EVENT TIMELINE MODEL
# ============================================================================

class EventTimeline(db.Model):
    """Event timeline and milestones."""
    __tablename__ = "event_timeline"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    phase = db.Column(db.String(50), nullable=False)  # Planning, Prep, Execution, Post-Event
    description = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event", back_populates="timelines")
    
    def __repr__(self):
        return f'<EventTimeline {self.phase} - {self.description[:30]}>'


# ============================================================================
# EVENT STAFF ASSIGNMENT MODEL (UPDATED)
# ============================================================================

class EventStaffAssignment(db.Model):
    """Staff role assignments for events."""
    __tablename__ = "event_staff_assignment"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    staff_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False)  # chef, waiter, driver, cleaner, logistics
    assigned_hours = db.Column(db.Numeric(5, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Optional user_id for linking to User model (backward compatibility)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    event = db.relationship("Event", back_populates="staff_assignments")
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<EventStaffAssignment {self.staff_name} - {self.role}>'


# ============================================================================
# EVENT CHECKLIST ITEM MODEL (NEW)
# ============================================================================

class EventChecklistItem(db.Model):
    """Event checklist items."""
    __tablename__ = "event_checklist_item"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # Equipment, Staff, Deliverables, Misc
    completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event", back_populates="checklist_items")
    
    def __repr__(self):
        status = "✓" if self.completed else "○"
        return f'<EventChecklistItem {status} {self.item_name}>'


# ============================================================================
# VENDOR MODEL
# ============================================================================

class Vendor(db.Model):
    """Vendor and partner management."""
    __tablename__ = "vendor"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)  # tents, décor, transport, etc
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    event_assignments = db.relationship("EventVendorAssignment", back_populates="vendor")
    
    def __repr__(self):
        return f'<Vendor {self.name}>'


# ============================================================================
# EVENT VENDOR ASSIGNMENT MODEL
# ============================================================================

class EventVendorAssignment(db.Model):
    """Vendor assignments to events."""
    __tablename__ = "event_vendor_assignment"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendor.id"), nullable=False)
    role_in_event = db.Column(db.String(200), nullable=True)
    cost = db.Column(db.Numeric(12, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event", back_populates="vendor_assignments")
    vendor = db.relationship("Vendor", back_populates="event_assignments")
    
    def __repr__(self):
        return f'<EventVendorAssignment {self.vendor.name if self.vendor else "Unknown"}>'


class EventMenuSelection(db.Model):
    """Menu items selected for an event."""
    __tablename__ = "event_menu_selection"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    line_total_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    dietary_notes = db.Column(db.Text, nullable=True)
    added_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    event = db.relationship("Event", back_populates="menu_selections")
    
    def __repr__(self):
        return f'<EventMenuSelection {self.item_name}>'


class EventDocument(db.Model):
    """Documents for events."""
    __tablename__ = "event_document"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    file_type = db.Column(db.String(50), nullable=True)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    event = db.relationship("Event", back_populates="documents")
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<EventDocument {self.title}>'


class EventCommunication(db.Model):
    """Communications for events."""
    __tablename__ = "event_communication"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    communication_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    direction = db.Column(db.String(20), nullable=False, default="Outbound")
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    event = db.relationship("Event", back_populates="communications")
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<EventCommunication {self.communication_type}>'


class EventChecklist(db.Model):
    """Event checklists."""
    __tablename__ = "event_checklist"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    checklist_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    
    event = db.relationship("Event", back_populates="checklists")
    creator = db.relationship("User", foreign_keys=[created_by])
    items = db.relationship("ChecklistItem", back_populates="checklist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<EventChecklist {self.checklist_type}>'


class ChecklistItem(db.Model):
    """Individual items in an event checklist."""
    __tablename__ = "checklist_item"
    
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey("event_checklist.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    
    checklist = db.relationship("EventChecklist", back_populates="items")
    completer = db.relationship("User", foreign_keys=[completed_by])
    
    def __repr__(self):
        status = "✓" if self.is_completed else "○"
        return f'<ChecklistItem {status} {self.description[:50]}>'


# ============================================================================
# AI CONVERSATION MODEL
# ============================================================================


class AIConversation(db.Model):
    """
    Persistent conversation memory for SAS AI Chat.

    Stores a JSON payload of messages and optional summaries, keyed by user.
    """
    __tablename__ = "ai_conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(100), nullable=True)
    messages = db.Column(db.Text, nullable=False, default="[]")  # JSON-encoded list/log
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User")

    def __repr__(self):
        return f"<AIConversation user_id={self.user_id} id={self.id}>"


# ============================================================================
# INVOICE & ACCOUNTING MODELS
# ============================================================================

class Invoice(db.Model):
    """Invoice management."""
    __tablename__ = "invoice"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    total_amount_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    status = db.Column(db.Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.Draft)
    
    event = db.relationship("Event")
    receipts = db.relationship("Receipt", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class Receipt(db.Model):
    """Receipt records."""
    __tablename__ = "receipt"
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    amount_received_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    payment_method = db.Column(db.String(50), nullable=False, default="Cash")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    invoice = db.relationship("Invoice", back_populates="receipts")
    
    def __repr__(self):
        return f'<Receipt {self.receipt_number}>'


class Transaction(db.Model):
    """Financial transactions."""
    __tablename__ = "transaction"
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    related_event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    related_event = db.relationship("Event")
    
    def __repr__(self):
        return f'<Transaction {self.type} {self.amount}>'


# ============================================================================
# ACCOUNTING MODELS
# ============================================================================

class Account(db.Model):
    """Chart of accounts."""
    __tablename__ = "account"
    
    id = db.Column(db.Integer, primary_key=True)
    account_code = db.Column(db.String(50), unique=True, nullable=False)
    account_name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    parent = db.relationship("Account", remote_side=[id])
    
    def __repr__(self):
        return f'<Account {self.account_code} - {self.account_name}>'


class AccountingPayment(db.Model):
    """Accounting payment records."""
    __tablename__ = "accounting_payment"
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    reference = db.Column(db.String(100), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=True)
    received_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    invoice = db.relationship("Invoice")
    account = db.relationship("Account")
    receiver = db.relationship("User")
    receipts = db.relationship("AccountingReceipt", back_populates="payment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<AccountingPayment {self.amount}>'


class AccountingReceipt(db.Model):
    """Accounting receipt records."""
    __tablename__ = "accounting_receipt"
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("accounting_payment.id"), nullable=False)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    issued_to = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    issued_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="UGX")
    method = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    pdf_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    payment = db.relationship("AccountingPayment", back_populates="receipts")
    client = db.relationship("Client")
    issuer = db.relationship("User", foreign_keys=[issued_by])
    
    def __repr__(self):
        return f'<AccountingReceipt {self.reference}>'


class BankStatement(db.Model):
    """Bank statement records."""
    __tablename__ = "bank_statement"
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    statement_date = db.Column(db.Date, nullable=False)
    balance = db.Column(db.Numeric(12, 2), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    account = db.relationship("Account")
    
    def __repr__(self):
        return f'<BankStatement {self.statement_date}>'


class Journal(db.Model):
    """Accounting journals."""
    __tablename__ = "journal"
    
    id = db.Column(db.Integer, primary_key=True)
    journal_number = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    creator = db.relationship("User")
    entries = db.relationship("JournalEntry", back_populates="journal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Journal {self.journal_number}>'


class JournalEntry(db.Model):
    """Journal entries."""
    __tablename__ = "journal_entry"
    
    id = db.Column(db.Integer, primary_key=True)
    journal_id = db.Column(db.Integer, db.ForeignKey("journal.id"), nullable=False)
    entry_date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    journal = db.relationship("Journal", back_populates="entries")
    lines = db.relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<JournalEntry {self.id}>'


class JournalEntryLine(db.Model):
    """Journal entry lines."""
    __tablename__ = "journal_entry_line"
    
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey("journal_entry.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)
    debit = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    credit = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    description = db.Column(db.Text, nullable=True)
    
    entry = db.relationship("JournalEntry", back_populates="lines")
    account = db.relationship("Account")
    
    def __repr__(self):
        return f'<JournalEntryLine {self.id}>'


# ============================================================================
# QUOTATION MODELS
# ============================================================================

class Quotation(db.Model):
    """Quotation management."""
    __tablename__ = "quotation"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    title = db.Column(db.String(200), nullable=True)  # Quote Title
    event_type = db.Column(db.String(50), nullable=True)  # Wedding, Kwanjula, Kukyala, Kuhingira, Nikkah
    quote_date = db.Column(db.Date, nullable=False, default=date.today)
    expiry_date = db.Column(db.Date, nullable=False)
    event_date = db.Column(db.Date, nullable=True)  # Event Date
    venue = db.Column(db.String(200), nullable=True)  # Venue name or address
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    tax = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)  # Tax amount
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)  # Total amount
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client")
    event = db.relationship("Event")
    lines = db.relationship("QuotationLine", back_populates="quotation", cascade="all, delete-orphan")
    
    @property
    def items(self):
        """Compatibility property: alias for lines."""
        return self.lines
    
    def __repr__(self):
        return f'<Quotation {self.id}>'


class QuotationLine(db.Model):
    """Quotation line items."""
    __tablename__ = "quotation_line"
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotation.id"), nullable=False)
    source_type = db.Column(db.Enum(QuotationSource), nullable=True)  # Made optional for custom items
    source_reference = db.Column(db.String(100), nullable=True)  # Reference to source item
    item_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)  # Item description
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    line_total = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    
    quotation = db.relationship("Quotation", back_populates="lines")
    
    def __repr__(self):
        return f'<QuotationLine {self.item_name}>'


# ============================================================================
# CATERING & MENU MODELS
# ============================================================================

class CateringItem(db.Model):
    """Catering menu items."""
    __tablename__ = "catering_item"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Keep existing size
    description = db.Column(db.Text, nullable=True)  # Keep for backward compatibility
    selling_price_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    price_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)  # legacy
    estimated_cogs_ugx = db.Column(db.Numeric(12, 2), nullable=True)
    category = db.Column(db.String(100), nullable=True)  # Keep for backward compatibility
    is_available = db.Column(db.Boolean, nullable=False, default=True)  # Keep for backward compatibility
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    # Relationship to recipe items
    recipe_items = db.relationship("RecipeItem", back_populates="catering_item", cascade="all, delete-orphan")
    
    def get_current_price(self):
        """Get the current selling price from price history or model field."""
        try:
            # Try to get from price history first
            from sqlalchemy import desc
            latest_price = PriceHistory.query.filter_by(
                item_id=self.id,
                item_type="CATERING"
            ).order_by(desc(PriceHistory.effective_date)).first()
            
            if latest_price:
                return latest_price.price_ugx
            
            # Fall back to model fields
            return self.selling_price_ugx or self.price_ugx or Decimal('0.00')
        except Exception:
            return self.selling_price_ugx or self.price_ugx or Decimal('0.00')
    
    @property
    def selling_price(self):
        """Property to get selling price."""
        return self.get_current_price()
    
    def __repr__(self):
        return f'<CateringItem {self.name}>'


class BakeryItem(db.Model):
    """Bakery items."""
    __tablename__ = "bakery_item"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    category = db.Column(db.String(100), nullable=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.String(50), default="Active")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BakeryItem {self.name}>'


class BakeryOrder(db.Model):
    """Bakery orders."""
    __tablename__ = "bakery_order"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    delivery_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    order_status = db.Column(db.String(50), default="Pending")
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    balance_due = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = db.relationship("Client")
    event = db.relationship("Event")
    items = db.relationship("BakeryOrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<BakeryOrder {self.id}>'
    
    def calculate_balance(self):
        """Calculate balance due."""
        self.balance_due = max(Decimal('0.00'), Decimal(str(self.total_amount or 0)) - Decimal(str(self.amount_paid or 0)))
        return self.balance_due


class BakeryOrderItem(db.Model):
    """Bakery order line items."""
    __tablename__ = "bakery_order_item"
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("bakery_order.id"), nullable=False)
    bakery_item_id = db.Column(db.Integer, db.ForeignKey("bakery_item.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    line_total = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    
    order = db.relationship("BakeryOrder", back_populates="items")
    bakery_item = db.relationship("BakeryItem")
    
    def __repr__(self):
        return f'<BakeryOrderItem {self.id}>'


class BakeryProductionTask(db.Model):
    """Bakery production tasks."""
    __tablename__ = "bakery_production_task"
    
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey("bakery_order_item.id"), nullable=True)
    bakery_item_id = db.Column(db.Integer, db.ForeignKey("bakery_item.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    scheduled_time = db.Column(db.DateTime, nullable=True)
    completed_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    order_item = db.relationship("BakeryOrderItem")
    bakery_item = db.relationship("BakeryItem")
    assignee = db.relationship("User")
    
    def __repr__(self):
        return f'<BakeryProductionTask {self.id}>'


class Ingredient(db.Model):
    """Ingredients inventory."""
    __tablename__ = "ingredient"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)  # Keep existing size
    # Used by recipe builder
    unit_cost_ugx = db.Column(db.Numeric(12, 2), nullable=True)
    # Optional fields that many systems use
    unit = db.Column(db.String(50), nullable=True)
    # Keep for backward compatibility
    unit_of_measure = db.Column(db.String(50), nullable=False, default="kg")  # Keep for backward compatibility
    stock_count = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)  # Keep for backward compatibility
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'


class IngredientStockMovement(db.Model):
    """Audit log of ingredient stock movements (use/reserve/release/adjustment)."""
    __tablename__ = "ingredient_stock_movement"

    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), nullable=False)

    # Optional linkage to a production order (when stock is reserved/released for an order)
    production_order_id = db.Column(db.Integer, db.ForeignKey("production_order.id"), nullable=True)

    # Positive adds stock; negative deducts stock
    quantity_change = db.Column(db.Numeric(12, 3), nullable=False, default=0.0)
    resulting_stock = db.Column(db.Numeric(12, 3), nullable=True)

    movement_type = db.Column(db.String(50), nullable=False, default="adjustment")  # reserve, release, adjustment
    note = db.Column(db.Text, nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ingredient = db.relationship("Ingredient")
    creator = db.relationship("User", foreign_keys=[created_by])
    production_order = db.relationship("ProductionOrder", foreign_keys=[production_order_id])

    def __repr__(self):
        return f"<IngredientStockMovement ingredient_id={self.ingredient_id} change={self.quantity_change}>"


class RecipeItem(db.Model):
    """Recipe components."""
    __tablename__ = "recipe_item"
    
    id = db.Column(db.Integer, primary_key=True)
    catering_item_id = db.Column(db.Integer, db.ForeignKey("catering_item.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), nullable=False)
    quantity_required = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    
    catering_item = db.relationship("CateringItem", back_populates="recipe_items")
    ingredient = db.relationship("Ingredient")
    
    def __repr__(self):
        return f'<RecipeItem {self.ingredient_id}>'


class PriceHistory(db.Model):
    """Price history for catering and bakery items."""
    __tablename__ = "price_history"
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # "CATERING" or "BAKERY"
    price_ugx = db.Column(db.Numeric(12, 2), nullable=False)
    effective_date = db.Column(db.Date, nullable=False, default=date.today)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<PriceHistory {self.item_type} {self.item_id} - {self.price_ugx}>'


# ============================================================================
# INVENTORY & HIRE MODELS
# ============================================================================

class InventoryItem(db.Model):
    """Inventory items."""
    __tablename__ = "inventory_item"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    stock_count = db.Column(db.Integer, nullable=False, default=0)
    unit_price_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    rental_price = db.Column(db.Numeric(10, 2), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    sku = db.Column(db.String(100), nullable=True)
    replacement_cost = db.Column(db.Numeric(10, 2), nullable=True)
    condition = db.Column(db.String(50), nullable=True, default="Good")
    location = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=True, default="Available")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # order_items = db.relationship("HireOrderItem", back_populates="inventory_item")  # Commented out - hire orders removed
    
    def __repr__(self):
        return f'<InventoryItem {self.name}>'


# ============================================================================
# PRODUCTION DAILY-USE INVENTORY MODELS
# ============================================================================

class ProductionInventoryItem(db.Model):
    """Production department daily-use inventory items (knives, pans, boards, etc)."""
    __tablename__ = "production_inventory_item"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=True)  # e.g. Tools, Cookware, Utensils
    unit = db.Column(db.String(50), nullable=True, default="pcs")  # e.g. pcs, sets
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_quantity = db.Column(db.Integer, nullable=False, default=0)
    condition = db.Column(db.String(50), nullable=True, default="Good")
    location = db.Column(db.String(100), nullable=True)  # e.g. Kitchen, Store, Van
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ProductionInventoryItem {self.id} {self.name}>"


class ProductionInventoryMovement(db.Model):
    """Audit log of production inventory quantity changes."""
    __tablename__ = "production_inventory_movement"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("production_inventory_item.id"), nullable=False)

    # Positive adds quantity; negative deducts quantity
    quantity_change = db.Column(db.Integer, nullable=False, default=0)
    resulting_quantity = db.Column(db.Integer, nullable=True)
    movement_type = db.Column(db.String(50), nullable=False, default="adjustment")  # opening, adjustment
    note = db.Column(db.Text, nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    item = db.relationship("ProductionInventoryItem", foreign_keys=[item_id])
    creator = db.relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ProductionInventoryMovement item_id={self.item_id} change={self.quantity_change}>"


# Hire Order Models
class Order(db.Model):
    """Equipment hire orders."""
    __tablename__ = "hire_order"
    
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(255), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    event_date = db.Column(db.Date, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)
    pickup_date = db.Column(db.Date, nullable=True)
    delivery_address = db.Column(db.Text, nullable=True)
    telephone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    amount_paid = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    balance_due = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    reference = db.Column(db.String(50), nullable=True, unique=True)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    client = db.relationship("Client", foreign_keys=[client_id])
    event = db.relationship("Event", foreign_keys=[event_id])
    
    def __repr__(self):
        return f'<Order {self.id} - {self.client_name}>'
    
    def calculate_balance(self):
        """Calculate balance due."""
        discount = Decimal(str(self.discount_amount or 0))
        subtotal = Decimal(str(self.total_cost or 0))
        final_total = max(Decimal('0.00'), subtotal - discount)
        self.balance_due = max(Decimal('0.00'), final_total - Decimal(str(self.amount_paid or 0)))
        return self.balance_due


class OrderItem(db.Model):
    """Hire order line items."""
    __tablename__ = "hire_order_item"
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("hire_order.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Relationships
    order = db.relationship("Order", back_populates="items")
    inventory_item = db.relationship("InventoryItem")
    
    def __repr__(self):
        return f'<OrderItem {self.id} - Order {self.order_id}>'


# ============================================================================
# CRM MODELS
# ============================================================================

class IncomingLead(db.Model):
    """CRM incoming leads."""
    __tablename__ = "incoming_lead"
    
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    inquiry_type = db.Column(db.String(100), nullable=True)
    message = db.Column(db.Text, nullable=True)
    pipeline_stage = db.Column(db.String(50), nullable=False, default="New Lead")
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    converted_client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    converted_event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assigned_user = db.relationship("User")
    converted_client = db.relationship("Client", foreign_keys=[converted_client_id])
    converted_event = db.relationship("Event", foreign_keys=[converted_event_id])
    
    def __repr__(self):
        return f'<IncomingLead {self.client_name}>'


class Task(db.Model):
    """Task management."""
    __tablename__ = "task"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum(TaskStatus), nullable=False, default=TaskStatus.Pending)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")
    assigned_user = db.relationship("User")
    
    def __repr__(self):
        return f'<Task {self.title}>'


# ============================================================================
# BUSINESS INTELLIGENCE MODELS
# ============================================================================

class BIEventProfitability(db.Model):
    """Event profitability analysis aggregated data."""
    __tablename__ = "bi_event_profitability"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    revenue = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    cost_of_goods = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    labor_cost = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    overhead_cost = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    profit = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    margin_percent = db.Column(db.Float, nullable=False, default=0.0)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")
    
    def __repr__(self):
        return f'<BIEventProfitability Event {self.event_id} Margin {self.margin_percent}%>'


class BIIngredientPriceTrend(db.Model):
    """Ingredient price trend data."""
    __tablename__ = "bi_ingredient_price_trend"
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    inventory_item = db.relationship("InventoryItem")
    
    def __repr__(self):
        return f'<BIIngredientPriceTrend {self.date}>'


class BISalesForecast(db.Model):
    """Sales forecast data."""
    __tablename__ = "bi_sales_forecast"
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_date = db.Column(db.Date, nullable=False)
    predicted_revenue = db.Column(db.Numeric(14, 2), nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BISalesForecast {self.forecast_date}>'


class BIStaffPerformance(db.Model):
    """Staff performance metrics."""
    __tablename__ = "bi_staff_performance"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    metric_date = db.Column(db.Date, nullable=False)
    performance_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<BIStaffPerformance User {self.user_id}>'


class BIBakeryDemand(db.Model):
    """Bakery demand forecast."""
    __tablename__ = "bi_bakery_demand"
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=True)
    forecast_date = db.Column(db.Date, nullable=False)
    predicted_demand = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BIBakeryDemand {self.forecast_date}>'


class BICustomerBehavior(db.Model):
    """Customer behavior analysis."""
    __tablename__ = "bi_customer_behavior"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    behavior_type = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client")
    
    def __repr__(self):
        return f'<BICustomerBehavior {self.behavior_type}>'


class BIPOSHeatmap(db.Model):
    """POS heatmap data."""
    __tablename__ = "bi_pos_heatmap"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer, nullable=False)
    transaction_count = db.Column(db.Integer, nullable=False, default=0)
    revenue = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BIPOSHeatmap {self.date} {self.hour}>'


# ============================================================================
# FLOOR PLANNER MODELS
# ============================================================================

class FloorPlan(db.Model):
    """Floor plan designs - Professional event layout designer."""
    __tablename__ = 'floor_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    data = db.Column(db.Text, nullable=True)  # Primary JSON storage field - MUST EXIST
    layout_json = db.Column(db.Text, nullable=True)  # Optional legacy field
    thumbnail = db.Column(db.LargeBinary, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    event = db.relationship("Event", backref=db.backref("floor_plan", uselist=False))
    creator = db.relationship("User", foreign_keys=[created_by])
    seating_assignments = db.relationship("SeatingAssignment", back_populates="floorplan", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<FloorPlan {self.name}>'


class SeatingAssignment(db.Model):
    """Seating assignments for floor plans."""
    __tablename__ = "seating_assignment"
    
    id = db.Column(db.Integer, primary_key=True)
    floorplan_id = db.Column(db.Integer, db.ForeignKey('floor_plan.id'), nullable=False)
    guest_name = db.Column(db.String(120), nullable=True)
    table_number = db.Column(db.String(50), nullable=True)
    seat_number = db.Column(db.String(50), nullable=True)
    special_requests = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    floorplan = db.relationship("FloorPlan", back_populates="seating_assignments")
    
    def __repr__(self):
        return f'<SeatingAssignment {self.guest_name or "Unassigned"}>'


# ============================================================================
# EMPLOYEE/HR MODELS
# ============================================================================

class PayrollRecord(db.Model):
    """Payroll records."""
    __tablename__ = "payroll_record"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    pay_date = db.Column(db.Date, nullable=False, default=date.today)
    amount_ugx = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<PayrollRecord {self.user_id} - {self.pay_date}>'


class AuditLog(db.Model):
    """Audit log for system activities."""
    __tablename__ = "audit_log"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(100), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'


class RoleAssignmentLog(db.Model):
    """Audit log for role assignments."""
    __tablename__ = "role_assignment_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    affected_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    old_role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    new_role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=True)
    is_bulk_assignment = db.Column(db.Boolean, default=False, nullable=False)
    is_temporary = db.Column(db.Boolean, default=False, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    admin_user = db.relationship("User", foreign_keys=[admin_user_id], backref="role_assignments_made")
    affected_user = db.relationship("User", foreign_keys=[affected_user_id], backref="role_assignments_received")
    old_role = db.relationship("Role", foreign_keys=[old_role_id])
    new_role = db.relationship("Role", foreign_keys=[new_role_id])
    
    def __repr__(self):
        return f'<RoleAssignmentLog admin={self.admin_user_id} user={self.affected_user_id} role={self.new_role_id}>'


class Department(db.Model):
    """Departments."""
    __tablename__ = "department"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    manager = db.relationship("User", foreign_keys=[manager_id])
    employees = db.relationship("Employee", back_populates="department")
    
    def __repr__(self):
        return f'<Department {self.name}>'


class Position(db.Model):
    """Job positions."""
    __tablename__ = "position"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    department = db.relationship("Department")
    employees = db.relationship("Employee", back_populates="position_obj")
    
    def __repr__(self):
        return f'<Position {self.title}>'


class Employee(db.Model):
    """Employee records."""
    __tablename__ = "employee"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    employee_number = db.Column(db.String(50), unique=True, nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"), nullable=True)
    position_id = db.Column(db.Integer, db.ForeignKey("position.id"), nullable=True)
    position = db.Column(db.String(100), nullable=True)  # Legacy field
    hire_date = db.Column(db.Date, nullable=True)
    monthly_salary = db.Column(db.Numeric(10, 2), default=0)  # Monthly salary amount
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    status = db.Column(db.String(20), default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship("User")
    department = db.relationship("Department", back_populates="employees")
    position_obj = db.relationship("Position", back_populates="employees")
    
    @property
    def full_name(self):
        """Get employee's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Employee {self.first_name} {self.last_name}>'


class Attendance(db.Model):
    """Employee attendance records."""
    __tablename__ = "attendance"
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    clock_in = db.Column(db.DateTime, nullable=True)
    clock_out = db.Column(db.DateTime, nullable=True)
    hours_worked = db.Column(db.Numeric(5, 2), nullable=True)
    status = db.Column(db.String(50), nullable=True)  # Present, Absent, Late, etc.
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    employee = db.relationship("Employee")
    
    def __repr__(self):
        return f'<Attendance {self.employee_id} - {self.date}>'


class Shift(db.Model):
    """Work shifts."""
    __tablename__ = "shift"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    department = db.relationship("Department")
    assignments = db.relationship("ShiftAssignment", back_populates="shift")
    
    def __repr__(self):
        return f'<Shift {self.name}>'


class ShiftAssignment(db.Model):
    """Shift assignments to employees."""
    __tablename__ = "shift_assignment"
    
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey("shift.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    assignment_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    shift = db.relationship("Shift", back_populates="assignments")
    employee = db.relationship("Employee")
    
    def __repr__(self):
        return f'<ShiftAssignment {self.employee_id} - {self.assignment_date}>'


class LeaveRequest(db.Model):
    """Employee leave requests."""
    __tablename__ = "leave_request"
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employee.id"), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # Annual, Sick, Maternity, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Pending")  # Pending, Approved, Rejected
    approved_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    employee = db.relationship("Employee")
    approver = db.relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<LeaveRequest {self.employee_id} - {self.leave_type}>'


class PayrollExport(db.Model):
    """Payroll export records."""
    __tablename__ = "payroll_export"
    
    id = db.Column(db.Integer, primary_key=True)
    export_date = db.Column(db.Date, nullable=False, default=date.today)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    employee_count = db.Column(db.Integer, nullable=False, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    creator = db.relationship("User")
    
    def __repr__(self):
        return f'<PayrollExport {self.export_date}>'


# ============================================================================
# PRODUCTION MODELS
# ============================================================================

class Recipe(db.Model):
    """Production recipes."""
    __tablename__ = "recipe"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Keep existing size
    description = db.Column(db.Text, nullable=True)
    portions = db.Column(db.Integer, nullable=False, default=1)   # base portions
    cost_per_portion = db.Column(db.Numeric(10, 2), nullable=True)  # Keep existing precision
    ingredients = db.Column(db.Text, nullable=True)  # JSON list of {"ingredient_id": x, "qty": y, "unit": "kg"}
    instructions = db.Column(db.Text, nullable=True)  # Keep for backward compatibility
    prep_time_mins = db.Column(db.Integer, nullable=True, default=0)
    cook_time_mins = db.Column(db.Integer, nullable=True, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recipe {self.name}>'


class ProductionOrder(db.Model):
    """Production orders."""
    __tablename__ = "production_order"
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), unique=True, nullable=False)  # Keep existing size
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    scheduled_prep = db.Column(db.DateTime, nullable=True)
    scheduled_cook = db.Column(db.DateTime, nullable=True)
    scheduled_pack = db.Column(db.DateTime, nullable=True)
    scheduled_load = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Planned")
    total_portions = db.Column(db.Integer, nullable=False, default=0)
    total_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)  # Keep existing
    
    # Relationships
    items = db.relationship("ProductionOrderItem", back_populates="order", cascade="all, delete-orphan")
    event = db.relationship("Event")
    # Keep for backward compatibility
    line_items = db.relationship("ProductionLineItem", back_populates="order", cascade="all, delete-orphan")  # Keep for backward compatibility
    
    def __repr__(self):
        return f'<ProductionOrder {self.reference}>'


class ProductionOrderItem(db.Model):
    """Production order items."""
    __tablename__ = "production_order_item"
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("production_order.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=True)
    recipe_name = db.Column(db.String(255), nullable=True)
    portions = db.Column(db.Integer, nullable=False, default=1)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    line_total = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    
    order = db.relationship("ProductionOrder", back_populates="items")
    recipe = db.relationship("Recipe")
    
    def __repr__(self):
        return f'<ProductionOrderItem order={self.order_id} recipe={self.recipe_name}>'


class ProductionLineItem(db.Model):
    """Production order line items."""
    __tablename__ = "production_line_item"
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("production_order.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    recipe_name = db.Column(db.String(200), nullable=False)
    portions = db.Column(db.Integer, nullable=False, default=1)
    unit = db.Column(db.String(50), nullable=False, default="portion")
    status = db.Column(db.String(50), nullable=False, default="Pending")
    
    order = db.relationship("ProductionOrder", back_populates="line_items")  # Updated back_populates
    recipe = db.relationship("Recipe")
    
    def __repr__(self):
        return f'<ProductionLineItem {self.recipe_name}>'


class ProductionBudget(db.Model):
    """Production budget proposal for an event (submitted to admin for approval)."""
    __tablename__ = "production_budget"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    status = db.Column(db.Enum(ProductionBudgetStatus), nullable=False, default=ProductionBudgetStatus.Draft)
    submitted_at = db.Column(db.DateTime, nullable=True)

    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    admin_recommendations = db.Column(db.Text, nullable=True)

    total_cost_ugx = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = db.relationship("Event", foreign_keys=[event_id])
    creator = db.relationship("User", foreign_keys=[created_by])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    items = db.relationship("ProductionBudgetItem", back_populates="budget", cascade="all, delete-orphan")

    def recalc_totals(self):
        try:
            total = Decimal("0.00")
            for it in (self.items or []):
                total += Decimal(str(getattr(it, "total_cost_ugx", 0) or 0))
            self.total_cost_ugx = total
        except Exception:
            # keep previous total if anything weird happens
            pass
        return self.total_cost_ugx

    def __repr__(self):
        return f"<ProductionBudget event_id={self.event_id} status={self.status}>"


class ProductionBudgetItem(db.Model):
    """Line items for a ProductionBudget."""
    __tablename__ = "production_budget_item"

    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey("production_budget.id"), nullable=False)
    category = db.Column(db.Enum(BudgetItemCategory), nullable=False, default=BudgetItemCategory.FoodItems)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False, default=1)
    unit_cost_ugx = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    total_cost_ugx = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    budget = db.relationship("ProductionBudget", back_populates="items")

    def recalc(self):
        try:
            q = Decimal(str(self.quantity or 0))
            u = Decimal(str(self.unit_cost_ugx or 0))
            self.total_cost_ugx = q * u
        except Exception:
            pass
        return self.total_cost_ugx

    def __repr__(self):
        return f"<ProductionBudgetItem {self.category} {self.description}>"


# Equipment List Status Enum
class EquipmentListStatus(str, Enum):
    Draft = "Draft"
    Submitted = "Submitted"
    Approved = "Approved"
    Rejected = "Rejected"


class EventEquipmentList(db.Model):
    """Catering equipment list for an event (prepared by service department)."""
    __tablename__ = "event_equipment_list"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    status = db.Column(db.Enum(EquipmentListStatus), nullable=False, default=EquipmentListStatus.Draft)
    title = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    submitted_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewer_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = db.relationship("Event", foreign_keys=[event_id])
    creator = db.relationship("User", foreign_keys=[created_by])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    items = db.relationship("EventEquipmentItem", back_populates="equipment_list", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<EventEquipmentList event_id={self.event_id} status={self.status}>"


class EventEquipmentItem(db.Model):
    """Line items for an EventEquipmentList."""
    __tablename__ = "event_equipment_item"

    id = db.Column(db.Integer, primary_key=True)
    equipment_list_id = db.Column(db.Integer, db.ForeignKey("event_equipment_list.id"), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=True)
    
    item_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.Text, nullable=True)
    
    # For tracking during event
    checked_out = db.Column(db.Boolean, nullable=False, default=False)
    checked_out_at = db.Column(db.DateTime, nullable=True)
    checked_out_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    
    checked_in = db.Column(db.Boolean, nullable=False, default=False)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    checked_in_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    
    condition_notes = db.Column(db.Text, nullable=True)  # Notes on condition after return
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    equipment_list = db.relationship("EventEquipmentList", back_populates="items")
    inventory_item = db.relationship("InventoryItem", foreign_keys=[inventory_item_id])
    checkout_user = db.relationship("User", foreign_keys=[checked_out_by])
    checkin_user = db.relationship("User", foreign_keys=[checked_in_by])

    def __repr__(self):
        return f"<EventEquipmentItem {self.item_name} qty={self.quantity}>"


class KitchenChecklist(db.Model):
    """Kitchen checklists."""
    __tablename__ = "kitchen_checklist"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # NEW FIELDS REQUIRED BY ROUTES
    title = db.Column(db.String(255), nullable=True)
    checklist_type = db.Column(db.String(100), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    
    # EXISTING FIELDS (keep yours)
    checklist_date = db.Column(db.Date, nullable=True)
    checked_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    status = db.Column(db.String(50), nullable=True, default="Pending")
    notes = db.Column(db.Text, nullable=True)
    items = db.Column(db.Text, nullable=True)  # JSON encoded items
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # CREATED / UPDATED
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    # RELATIONSHIPS
    event = db.relationship("Event", foreign_keys=[event_id])
    checker = db.relationship("User", foreign_keys=[checked_by])
    creator = db.relationship("User", foreign_keys=[created_by])
    # Keep for backward compatibility
    checklist_items = db.relationship("KitchenChecklistItem", back_populates="checklist", cascade="all, delete-orphan")  # Keep for backward compatibility
    
    def __repr__(self):
        return f'<KitchenChecklist {self.title or self.id}>'


class KitchenChecklistItem(db.Model):
    """Kitchen checklist items."""
    __tablename__ = "kitchen_checklist_item"
    
    id = db.Column(db.Integer, primary_key=True)
    checklist_id = db.Column(db.Integer, db.ForeignKey("kitchen_checklist.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    checklist = db.relationship("KitchenChecklist", back_populates="checklist_items")
    completer = db.relationship("User", foreign_keys=[completed_by])
    
    def __repr__(self):
        return f'<KitchenChecklistItem {self.id}>'


class DeliveryQCChecklist(db.Model):
    """Delivery quality control checklists."""
    __tablename__ = "delivery_qc_checklist"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)  # Keep for backward compatibility
    title = db.Column(db.String(255), nullable=True)  # Keep for backward compatibility
    delivery_date = db.Column(db.Date, nullable=True)
    delivery_time = db.Column(db.Time, nullable=True)
    checked_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    temperature_check = db.Column(db.String(255), nullable=True)
    packaging_integrity = db.Column(db.String(50), nullable=True, default="Good")
    presentation = db.Column(db.String(50), nullable=True, default="Acceptable")
    quantity_verified = db.Column(db.Boolean, nullable=False, default=False)
    customer_satisfaction = db.Column(db.Text, nullable=True)
    issues = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")  # Keep for backward compatibility
    creator = db.relationship("User", foreign_keys=[created_by])
    checker = db.relationship("User", foreign_keys=[checked_by])  # Keep for backward compatibility
    
    def __repr__(self):
        return f'<DeliveryQCChecklist {self.title or self.id}>'


class FoodSafetyLog(db.Model):
    """Food safety logs."""
    __tablename__ = "food_safety_log"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    log_date = db.Column(db.Date, nullable=True)
    log_time = db.Column(db.Time, nullable=True)
    logged_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    item_description = db.Column(db.Text, nullable=True)
    temperature = db.Column(db.Numeric(8, 2), nullable=True)
    action_taken = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=True, default="Normal")
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event", foreign_keys=[event_id])
    creator = db.relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<FoodSafetyLog {self.log_date}>'


class HygieneReport(db.Model):
    """Hygiene reports."""
    __tablename__ = "hygiene_report"
    
    id = db.Column(db.Integer, primary_key=True)
    report_time = db.Column(db.Time, nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    inspected_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    checklist_items = db.Column(db.Text, nullable=True)
    overall_rating = db.Column(db.String(50), nullable=True, default="Good")
    issues_found = db.Column(db.Text, nullable=True)
    corrective_actions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=True, default="Completed")
    follow_up_date = db.Column(db.Date, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Keep for backward compatibility
    report_date = db.Column(db.Date, nullable=True)  # Keep for backward compatibility
    area = db.Column(db.String(100), nullable=True)  # Keep for backward compatibility
    rating = db.Column(db.Integer, nullable=True)  # Keep for backward compatibility
    notes = db.Column(db.Text, nullable=True)  # Keep for backward compatibility
    
    event = db.relationship("Event", foreign_keys=[event_id])
    creator = db.relationship("User", foreign_keys=[created_by])
    inspector = db.relationship("User", foreign_keys=[inspected_by])  # Keep for backward compatibility
    
    def __repr__(self):
        return f'<HygieneReport {self.area} - {self.report_date}>'


# ============================================================================
# UNIVERSITY MODELS
# ============================================================================

class Course(db.Model):
    """Training courses."""
    __tablename__ = "course"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    duration_hours = db.Column(db.Integer, nullable=True)
    published = db.Column(db.Boolean, nullable=False, default=False)
    target_role = db.Column(db.Enum(UserRole), nullable=True)
    mandatory = db.Column(db.Boolean, nullable=False, default=False)
    required_for_role = db.Column(db.Enum(UserRole), nullable=True)
    required_for_department = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    lessons = db.relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    quizzes = db.relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Course {self.title}>'


class Lesson(db.Model):
    """Course lessons."""
    __tablename__ = "lesson"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    course = db.relationship("Course", back_populates="lessons")
    resources = db.relationship("LessonResource", back_populates="lesson", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Lesson {self.title}>'


class LessonResource(db.Model):
    """Lesson resources."""
    __tablename__ = "lesson_resource"
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=True)
    resource_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    lesson = db.relationship("Lesson", back_populates="resources")
    
    def __repr__(self):
        return f'<LessonResource {self.title}>'


class Material(db.Model):
    """Course materials."""
    __tablename__ = "material"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    material_type = db.Column(db.String(50), nullable=True)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    course = db.relationship("Course")
    
    def __repr__(self):
        return f'<Material {self.title}>'


class Enrollment(db.Model):
    """Course enrollments."""
    __tablename__ = "enrollment"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    course = db.relationship("Course", back_populates="enrollments")
    user = db.relationship("User")
    progress = db.relationship("CourseProgress", back_populates="enrollment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Enrollment {self.user_id} -> {self.course_id}>'


class CourseProgress(db.Model):
    """Course progress tracking."""
    __tablename__ = "course_progress"
    
    id = db.Column(db.Integer, primary_key=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey("enrollment.id"), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    enrollment = db.relationship("Enrollment", back_populates="progress")
    lesson = db.relationship("Lesson")
    
    def __repr__(self):
        return f'<CourseProgress {self.enrollment_id}>'


class Quiz(db.Model):
    """Course quizzes."""
    __tablename__ = "quiz"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    course = db.relationship("Course", back_populates="quizzes")
    questions = db.relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Quiz {self.title}>'


class QuizQuestion(db.Model):
    """Quiz questions."""
    __tablename__ = "quiz_question"
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False, default="multiple_choice")
    order_index = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    quiz = db.relationship("Quiz", back_populates="questions")
    answers = db.relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<QuizQuestion {self.id}>'


class QuizAnswer(db.Model):
    """Quiz answer options."""
    __tablename__ = "quiz_answer"
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_question.id"), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    
    question = db.relationship("QuizQuestion", back_populates="answers")
    
    def __repr__(self):
        return f'<QuizAnswer {self.id}>'


class QuizAttempt(db.Model):
    """Quiz attempts."""
    __tablename__ = "quiz_attempt"
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    score = db.Column(db.Float, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    quiz = db.relationship("Quiz")
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<QuizAttempt {self.user_id} -> {self.quiz_id}>'


class Certificate(db.Model):
    """Course completion certificates."""
    __tablename__ = "certificate"
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    certificate_number = db.Column(db.String(100), unique=True, nullable=False)
    issued_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    file_path = db.Column(db.String(500), nullable=True)
    
    course = db.relationship("Course")
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<Certificate {self.certificate_number}>'


# ============================================================================
# COMMUNICATION MODELS
# ============================================================================

class Announcement(db.Model):
    """Company announcements."""
    __tablename__ = "announcement"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    creator = db.relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<Announcement {self.title}>'


class Message(db.Model):
    """Chat messages (channel-based). Supports text and attachments."""
    __tablename__ = "message"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    channel = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    attachment_path = db.Column(db.String(500), nullable=True)
    attachment_type = db.Column(db.String(50), nullable=True)  # 'document' | 'voice' | 'image'
    original_filename = db.Column(db.String(255), nullable=True)
    
    user = db.relationship("User")
    
    def __repr__(self):
        return f'<Message {self.channel}>'


class DirectMessageThread(db.Model):
    """Direct message threads between users."""
    __tablename__ = "direct_message_thread"
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user1 = db.relationship("User", foreign_keys=[user1_id])
    user2 = db.relationship("User", foreign_keys=[user2_id])
    messages = db.relationship("DirectMessage", back_populates="thread", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<DirectMessageThread {self.user1_id}-{self.user2_id}>'


class DirectMessage(db.Model):
    """Direct messages (1:1). Supports text, documents, voice notes, images."""
    __tablename__ = "direct_message"
    
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("direct_message_thread.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.String(500), nullable=True)
    attachment_type = db.Column(db.String(50), nullable=True)  # 'document' | 'voice' | 'image'
    original_filename = db.Column(db.String(255), nullable=True)
    read = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    thread = db.relationship("DirectMessageThread", back_populates="messages")
    sender = db.relationship("User")
    
    def __repr__(self):
        return f'<DirectMessage {self.id}>'


class EventMessageThread(db.Model):
    """Event message threads."""
    __tablename__ = "event_message_thread"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    event = db.relationship("Event")
    messages = db.relationship("EventMessage", back_populates="thread", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<EventMessageThread Event {self.event_id}>'


class EventMessage(db.Model):
    """Event messages."""
    __tablename__ = "event_message"
    
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("event_message_thread.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    thread = db.relationship("EventMessageThread", back_populates="messages")
    sender = db.relationship("User")
    
    def __repr__(self):
        return f'<EventMessage {self.id}>'


class DepartmentMessage(db.Model):
    """Department-wide messages."""
    __tablename__ = "department_message"
    
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    sender = db.relationship("User")
    
    def __repr__(self):
        return f'<DepartmentMessage {self.department}>'


class BulletinPost(db.Model):
    """Bulletin board posts."""
    __tablename__ = "bulletin_post"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    attachment_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = db.relationship("User")
    
    def __repr__(self):
        return f'<BulletinPost {self.title}>'


# ============================================================================
# SAS OFFICE - FILE MANAGEMENT MODELS
# ============================================================================

class OfficeFolder(db.Model):
    """Folders in SAS Office file management system."""
    __tablename__ = "office_folder"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("office_folder.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent = db.relationship("OfficeFolder", remote_side=[id], backref="subfolders")
    creator = db.relationship("User")
    files = db.relationship("OfficeFile", back_populates="folder", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<OfficeFolder {self.name}>'


class OfficeFile(db.Model):
    """Files in SAS Office file management system."""
    __tablename__ = "office_file"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(500), nullable=False)
    file_path = db.Column(db.String(1000), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    file_type = db.Column(db.String(100), nullable=True)  # MIME type or category: document, image, video, etc.
    folder_id = db.Column(db.Integer, db.ForeignKey("office_folder.id"), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    folder = db.relationship("OfficeFolder", back_populates="files")
    uploader = db.relationship("User")
    
    def __repr__(self):
        return f'<OfficeFile {self.name}>'


# ============================================================================
# POS MODELS
# ============================================================================

class POSDevice(db.Model):
    """POS devices/terminals."""
    __tablename__ = "pos_device"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    terminal_code = db.Column(db.String(64), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    shifts = db.relationship("POSShift", back_populates="device", cascade="all, delete-orphan")
    orders = db.relationship("POSOrder", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<POSDevice {self.terminal_code}>'


class POSShift(db.Model):
    """POS shifts."""
    __tablename__ = "pos_shift"
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("pos_device.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    starting_cash = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    ending_cash = db.Column(db.Numeric(12, 2), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="open")
    
    device = db.relationship("POSDevice", back_populates="shifts")
    user = db.relationship("User")
    orders = db.relationship("POSOrder", back_populates="shift", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<POSShift {self.id} - {self.status}>'


class POSOrder(db.Model):
    """POS orders."""
    __tablename__ = "pos_order"
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(120), unique=True, nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey("pos_shift.id"), nullable=True)
    device_id = db.Column(db.Integer, db.ForeignKey("pos_device.id"), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    client_name = db.Column(db.String(255), nullable=True)
    client_phone = db.Column(db.String(50), nullable=True)
    order_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    tax_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    discount_amount = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    status = db.Column(db.String(50), nullable=False, default="draft")
    is_delivery = db.Column(db.Boolean, nullable=False, default=False)
    delivery_date = db.Column(db.DateTime, nullable=True)
    delivery_address = db.Column(db.String(255), nullable=True)
    delivery_driver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shift = db.relationship("POSShift", back_populates="orders")
    device = db.relationship("POSDevice", back_populates="orders")
    client = db.relationship("Client")
    driver = db.relationship("User", foreign_keys=[delivery_driver_id])
    lines = db.relationship("POSOrderLine", back_populates="order", cascade="all, delete-orphan")
    payments = db.relationship("POSPayment", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<POSOrder {self.reference}>'


class POSOrderLine(db.Model):
    """POS order line items."""
    __tablename__ = "pos_order_line"
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("pos_order.id"), nullable=False)
    product_id = db.Column(db.Integer, nullable=True)
    product_name = db.Column(db.String(255), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    line_total = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    note = db.Column(db.String(255), nullable=True)
    is_kitchen_item = db.Column(db.Boolean, nullable=False, default=True)
    
    order = db.relationship("POSOrder", back_populates="lines")
    
    def __repr__(self):
        return f'<POSOrderLine {self.product_name}>'


class POSPayment(db.Model):
    """POS payments."""
    __tablename__ = "pos_payment"
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("pos_order.id"), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False, default=0.00)
    method = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    order = db.relationship("POSOrder", back_populates="payments")
    receipt = db.relationship("POSReceipt", back_populates="payment", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<POSPayment {self.method} - {self.amount}>'


class POSProduct(db.Model):
    """POS products."""
    __tablename__ = "pos_product"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    barcode = db.Column(db.String(100), nullable=True)
    sku = db.Column(db.String(100), nullable=True)
    tax_rate = db.Column(db.Numeric(5, 2), nullable=False, default=18.00)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)  # Alias for is_available for compatibility
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    creator = db.relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<POSProduct {self.name}>'


class POSReceipt(db.Model):
    """POS receipts."""
    __tablename__ = "pos_receipt"
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("pos_payment.id"), nullable=False)
    receipt_ref = db.Column(db.String(50), unique=True, nullable=False)
    pdf_path = db.Column(db.String(500), nullable=True)
    issued_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Legacy field for backward compatibility
    order_id = db.Column(db.Integer, db.ForeignKey("pos_order.id"), nullable=True)
    receipt_number = db.Column(db.String(100), nullable=True)
    
    payment = db.relationship("POSPayment", back_populates="receipt")
    order = db.relationship("POSOrder")
    
    def __repr__(self):
        return f'<POSReceipt {self.receipt_ref}>'


# ============================================================================
# AUTOMATION MODELS
# ============================================================================

class Workflow(db.Model):
    """Automation workflows."""
    __tablename__ = "workflow"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    trigger_type = db.Column(db.String(100), nullable=False)
    trigger_config = db.Column(db.Text, nullable=True)  # JSON
    actions = db.Column(db.Text, nullable=True)  # JSON
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Workflow {self.name}>'


class ActionLog(db.Model):
    """Workflow action execution logs."""
    __tablename__ = "action_log"
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey("workflow.id"), nullable=True)
    action_type = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # Success, Failed, Pending
    result = db.Column(db.Text, nullable=True)
    run_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    workflow = db.relationship("Workflow")
    
    def __repr__(self):
        return f'<ActionLog {self.action_type} - {self.status}>'


# ============================================================================
# CONTRACT MODELS
# ============================================================================

class ContractTemplate(db.Model):
    """Contract templates."""
    __tablename__ = "contract_template"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    contracts = db.relationship("Contract", back_populates="template")
    
    def __repr__(self):
        return f'<ContractTemplate {self.name}>'


class Contract(db.Model):
    """Contracts."""
    __tablename__ = "contract"
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey("contract_template.id"), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    contract_number = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Draft")  # Draft, Sent, Signed, Cancelled
    signed_at = db.Column(db.DateTime, nullable=True)
    signed_by = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    template = db.relationship("ContractTemplate", back_populates="contracts")
    event = db.relationship("Event")
    client = db.relationship("Client")
    
    def __repr__(self):
        return f'<Contract {self.contract_number}>'


# ============================================================================
# MENU BUILDER MODELS
# ============================================================================

class MenuCategory(db.Model):
    """Menu categories."""
    __tablename__ = "menu_category"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    items = db.relationship("MenuItem", back_populates="category")
    
    def __repr__(self):
        return f'<MenuCategory {self.name}>'


class MenuItem(db.Model):
    """Menu items."""
    __tablename__ = "menu_item"
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("menu_category.id"), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    cost = db.Column(db.Numeric(12, 2), nullable=True, default=0.00)
    margin_percent = db.Column(db.Numeric(5, 2), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    category = db.relationship("MenuCategory", back_populates="items")
    # package_items relationship removed - MenuPackageItem model removed to avoid conflicts
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'


# MenuPackage model moved to Events section (line ~410) to avoid duplicate table definition
# Old MenuPackage and MenuPackageItem removed - using JSON items field in MenuPackage instead


# ============================================================================
# DISPATCH MODELS
# ============================================================================

class Vehicle(db.Model):
    """Vehicles."""
    __tablename__ = "vehicle"
    
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    make = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    capacity = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    dispatch_runs = db.relationship("DispatchRun", back_populates="vehicle")
    
    # Properties for template compatibility
    @property
    def name(self):
        """Return vehicle name as make + model."""
        if self.make and self.model:
            return f"{self.make} {self.model}"
        return self.make or self.model or f"Vehicle {self.id}"
    
    @property
    def plate_number(self):
        """Alias for registration_number."""
        return self.registration_number
    
    @property
    def type(self):
        """Return vehicle type (using model as type)."""
        return self.model or "N/A"
    
    @property
    def status(self):
        """Return status string based on is_active."""
        if self.is_active:
            return "active"
        return "inactive"
    
    def __repr__(self):
        return f'<Vehicle {self.registration_number}>'


class DispatchRun(db.Model):
    """Dispatch runs."""
    __tablename__ = "dispatch_run"
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    run_date = db.Column(db.Date, nullable=False, default=date.today)
    departure_time = db.Column(db.DateTime, nullable=True)
    arrival_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Scheduled")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    vehicle = db.relationship("Vehicle", back_populates="dispatch_runs")
    driver = db.relationship("User")
    event = db.relationship("Event")
    load_items = db.relationship("LoadSheetItem", back_populates="dispatch_run", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<DispatchRun {self.id}>'


class LoadSheetItem(db.Model):
    """Load sheet items."""
    __tablename__ = "load_sheet_item"
    
    id = db.Column(db.Integer, primary_key=True)
    dispatch_run_id = db.Column(db.Integer, db.ForeignKey("dispatch_run.id"), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit = db.Column(db.String(50), nullable=True)
    
    dispatch_run = db.relationship("DispatchRun", back_populates="load_items")
    
    def __repr__(self):
        return f'<LoadSheetItem {self.item_name}>'


# ============================================================================
# VENDOR MODELS
# ============================================================================

class Supplier(db.Model):
    """Suppliers."""
    __tablename__ = "supplier"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    quotes = db.relationship("SupplierQuote", back_populates="supplier")
    purchase_orders = db.relationship("PurchaseOrder", back_populates="supplier")
    
    def __repr__(self):
        return f'<Supplier {self.name}>'


class SupplierQuote(db.Model):
    """Supplier quotes."""
    __tablename__ = "supplier_quote"
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"), nullable=False)
    quote_number = db.Column(db.String(100), nullable=False)
    quote_date = db.Column(db.Date, nullable=False, default=date.today)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    supplier = db.relationship("Supplier", back_populates="quotes")
    
    def __repr__(self):
        return f'<SupplierQuote {self.quote_number}>'


class PurchaseOrder(db.Model):
    """Purchase orders."""
    __tablename__ = "purchase_order"
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("supplier.id"), nullable=False)
    order_number = db.Column(db.String(100), unique=True, nullable=True)
    po_number = db.Column(db.String(100), unique=True, nullable=True)  # Alternative field name
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    po_date = db.Column(db.Date, nullable=True)  # Alternative field name
    expected_date = db.Column(db.Date, nullable=True)
    reference = db.Column(db.String(255), nullable=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    status = db.Column(db.String(50), nullable=False, default="Draft")
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    items_json = db.Column(db.Text, nullable=True)  # Legacy JSON storage
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    
    supplier = db.relationship("Supplier", back_populates="purchase_orders")
    creator = db.relationship("User", foreign_keys=[created_by])
    items = db.relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<PurchaseOrder {self.order_number or self.po_number or self.id}>'


class PurchaseOrderItem(db.Model):
    """Purchase order line items."""
    __tablename__ = "purchase_order_item"
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_order.id"), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    sku = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Numeric(12, 3), nullable=False, default=1.0)
    unit_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    tax_percent = db.Column(db.Numeric(5, 2), nullable=False, default=0.00)
    line_total = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    purchase_order = db.relationship("PurchaseOrder", back_populates="items")
    
    def __repr__(self):
        return f'<PurchaseOrderItem {self.description[:30]}>'


# ============================================================================
# TIMELINE MODELS
# ============================================================================

class Timeline(db.Model):
    """Event timelines."""
    __tablename__ = "timeline"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Scheduled")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")
    
    def __repr__(self):
        return f'<Timeline {self.title}>'


# ============================================================================
# PROPOSAL MODELS
# ============================================================================

class Proposal(db.Model):
    """Proposals."""
    __tablename__ = "proposal"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    proposal_number = db.Column(db.String(100), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    total_value = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    status = db.Column(db.String(50), nullable=False, default="Draft")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client")
    event = db.relationship("Event")
    
    def __repr__(self):
        return f'<Proposal {self.proposal_number}>'


# ============================================================================
# INCIDENT MODELS
# ============================================================================

class Incident(db.Model):
    """Incidents."""
    __tablename__ = "incident"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(50), nullable=False, default="Low")
    status = db.Column(db.String(50), nullable=False, default="Open")
    reported_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")
    reporter = db.relationship("User")
    
    def __repr__(self):
        return f'<Incident {self.title}>'


class QualityChecklist(db.Model):
    """Quality checklists."""
    __tablename__ = "quality_checklist"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    checklist_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")
    
    def __repr__(self):
        return f'<QualityChecklist {self.title}>'


# ============================================================================
# EQUIPMENT MAINTENANCE MODELS
# ============================================================================

class EquipmentMaintenance(db.Model):
    """Equipment maintenance records."""
    __tablename__ = "equipment_maintenance"
    
    id = db.Column(db.Integer, primary_key=True)
    hire_item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=True)  # Keep for backward compatibility
    maintenance_type = db.Column(db.String(50), nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    completed_date = db.Column(db.Date, nullable=True)
    technician_name = db.Column(db.String(255), nullable=True)
    cost = db.Column(db.Numeric(12, 2), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="scheduled")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    inventory_item = db.relationship("InventoryItem", foreign_keys=[hire_item_id])
    
    def __repr__(self):
        return f'<EquipmentMaintenance {self.maintenance_type}>'


class EquipmentConditionReport(db.Model):
    """Equipment condition reports."""
    __tablename__ = "equipment_condition_report"
    
    id = db.Column(db.Integer, primary_key=True)
    hire_item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=True)  # Keep for backward compatibility
    condition_rating = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(50), nullable=True)  # Keep for backward compatibility
    report_date = db.Column(db.Date, nullable=False, default=date.today)
    issues_found = db.Column(db.Text, nullable=True)
    recommended_action = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reported_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)  # Keep for backward compatibility
    notes = db.Column(db.Text, nullable=True)  # Keep for backward compatibility
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    inventory_item = db.relationship("InventoryItem", foreign_keys=[hire_item_id])
    reporter = db.relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<EquipmentConditionReport {self.condition_rating}>'


class EquipmentDepreciation(db.Model):
    """Equipment depreciation records."""
    __tablename__ = "equipment_depreciation"
    
    id = db.Column(db.Integer, primary_key=True)
    hire_item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey("inventory_item.id"), nullable=True)  # Keep for backward compatibility
    purchase_price = db.Column(db.Numeric(12, 2), nullable=False)
    salvage_value = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    useful_life_years = db.Column(db.Integer, nullable=False)
    calculated_value = db.Column(db.Numeric(12, 2), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    last_updated = db.Column(db.Date, nullable=False, default=date.today)
    depreciation_date = db.Column(db.Date, nullable=True)  # Keep for backward compatibility
    depreciation_amount = db.Column(db.Numeric(12, 2), nullable=True)  # Keep for backward compatibility
    current_value = db.Column(db.Numeric(12, 2), nullable=True)  # Keep for backward compatibility
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    inventory_item = db.relationship("InventoryItem", foreign_keys=[hire_item_id])
    
    def __repr__(self):
        return f'<EquipmentDepreciation {self.hire_item_id}>'


# ============================================================================
# FOOD SAFETY MODELS
# ============================================================================

class HACCPChecklist(db.Model):
    """HACCP checklists."""
    __tablename__ = "haccp_checklist"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    checklist_date = db.Column(db.Date, nullable=False, default=date.today)
    completed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")
    completer = db.relationship("User")
    
    def __repr__(self):
        return f'<HACCPChecklist {self.checklist_date}>'


class TemperatureLog(db.Model):
    """Temperature logs."""
    __tablename__ = "temperature_log"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    log_date = db.Column(db.Date, nullable=False, default=date.today)
    temperature = db.Column(db.Numeric(5, 2), nullable=False)
    location = db.Column(db.String(100), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")
    recorder = db.relationship("User")
    
    def __repr__(self):
        return f'<TemperatureLog {self.temperature}>'


class SafetyIncident(db.Model):
    """Safety incidents."""
    __tablename__ = "safety_incident"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    incident_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(50), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    event = db.relationship("Event")
    reporter = db.relationship("User")
    
    def __repr__(self):
        return f'<SafetyIncident {self.incident_type}>'


# ============================================================================
# BRANCH MODELS
# ============================================================================

class Branch(db.Model):
    """Branches."""
    __tablename__ = "branch"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Branch {self.name}>'


# ============================================================================
# MOBILE STAFF MODELS
# ============================================================================

class StaffTask(db.Model):
    """Staff tasks for mobile app."""
    __tablename__ = "staff_task"
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Pending")
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    task = db.relationship("Task")
    assignee = db.relationship("User")
    
    def __repr__(self):
        return f'<StaffTask {self.id}>'


# ============================================================================
# CLIENT PORTAL MODELS
# ============================================================================

class ClientPortalUser(db.Model):
    """Client portal users."""
    __tablename__ = "client_portal_user"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client")
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<ClientPortalUser {self.email}>'


class ClientEventLink(db.Model):
    """Client event links for portal."""
    __tablename__ = "client_event_link"
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    access_code = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    client = db.relationship("Client")
    event = db.relationship("Event")
    
    def __repr__(self):
        return f'<ClientEventLink {self.client_id}-{self.event_id}>'


# ============================================================================
# PRODUCTION RECIPES MODELS
# ============================================================================

class RecipeAdvanced(db.Model):
    """Advanced recipe management."""
    __tablename__ = "recipe_advanced"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    servings = db.Column(db.Integer, nullable=False, default=1)
    prep_time = db.Column(db.Integer, nullable=True)
    cook_time = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    ingredients = db.relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<RecipeAdvanced {self.name}>'


class RecipeIngredient(db.Model):
    """Recipe ingredients."""
    __tablename__ = "recipe_ingredient"
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe_advanced.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(50), nullable=True)
    
    recipe = db.relationship("RecipeAdvanced", back_populates="ingredients")
    ingredient = db.relationship("Ingredient")
    
    def __repr__(self):
        return f'<RecipeIngredient {self.id}>'


class BatchProduction(db.Model):
    """Batch production records."""
    __tablename__ = "batch_production"
    
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe_advanced.id"), nullable=True)
    batch_number = db.Column(db.String(100), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    production_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    recipe = db.relationship("RecipeAdvanced")
    
    def __repr__(self):
        return f'<BatchProduction {self.batch_number}>'


class WasteLog(db.Model):
    """Waste logs."""
    __tablename__ = "waste_log"
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), nullable=True)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    log_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    ingredient = db.relationship("Ingredient")
    
    def __repr__(self):
        return f'<WasteLog {self.log_date}>'


# ============================================================================
# EVENT PROFITABILITY MODELS (ADDED AT END)
# ============================================================================

class EventCostItem(db.Model):
    """Cost items for event profitability analysis."""
    __tablename__ = "event_cost_item"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    category = db.Column(db.String(100), nullable=True)  # Food, Labor, Equipment, Transport, etc.
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship("Event", backref="cost_items")
    
    def __repr__(self):
        return f'<EventCostItem {self.description} - {self.amount}>'


class EventRevenueItem(db.Model):
    """Revenue items for event profitability analysis."""
    __tablename__ = "event_revenue_item"
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    category = db.Column(db.String(100), nullable=True)  # Catering, Equipment Hire, Additional Services, etc.
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    event = db.relationship("Event", backref="revenue_items")
    
    def __repr__(self):
        return f'<EventRevenueItem {self.description} - {self.amount}>'


# ============================================================================
# REQUIRED FUNCTIONS
# ============================================================================

def seed_initial_data(db_instance):
    """Populate the database with baseline records if empty."""
    try:
        # Check if User table exists and has required columns
        from sqlalchemy import inspect, text
        inspector = inspect(db_instance.engine)
        
        if "user" in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns("user")]
            # Only query if table has expected structure
            if "email" in columns:
                if not User.query.filter_by(email="admin@sas.com").first():
                    admin = User(email="admin@sas.com", role=UserRole.Admin)
                    admin.set_password("password")
                    db_instance.session.add(admin)
        else:
            # Table doesn't exist yet, will be created by db.create_all()
            admin = User(email="admin@sas.com", role=UserRole.Admin)
            admin.set_password("password")
            db_instance.session.add(admin)
        
        # Check if Client table exists
        if "client" in inspector.get_table_names():
            if Client.query.count() == 0:
                client_one = Client(
                    name="Elite Weddings Ltd.",
                    contact_person="Sara Lee",
                    phone="+2547000001",
                    email="events@eliteweddings.com",
                )
                client_two = Client(
                    name="Corporate Gatherings Co.",
                    contact_person="Daniel O.",
                    phone="+2547000002",
                    email="info@corpgatherings.com",
                )
                db_instance.session.add(client_one)
                db_instance.session.add(client_two)
        else:
            # Table doesn't exist yet
            client_one = Client(
                name="Elite Weddings Ltd.",
                contact_person="Sara Lee",
                phone="+2547000001",
                email="events@eliteweddings.com",
            )
            client_two = Client(
                name="Corporate Gatherings Co.",
                contact_person="Daniel O.",
                phone="+2547000002",
                email="info@corpgatherings.com",
            )
            db_instance.session.add(client_one)
            db_instance.session.add(client_two)

        # Seed example announcements (once) so dashboards always have content.
        # Only seed if announcement table exists and is empty.
        try:
            if "announcement" in inspector.get_table_names():
                if Announcement.query.count() == 0:
                    admin_user = User.query.filter_by(email="admin@sas.com").first() or User.query.first()
                    created_by = admin_user.id if admin_user else 1
                    now = datetime.utcnow()
                    db_instance.session.add(
                        Announcement(
                            title="Welcome to SAS Management System",
                            message="Team,\n\nAll dashboards now show company announcements. Use this feed to share critical updates across departments.\n\n— Management",
                            created_by=created_by,
                            created_at=now,
                        )
                    )
                    db_instance.session.add(
                        Announcement(
                            title="Kitchen Operations: Daily Checklist",
                            message="Reminder: Complete the Kitchen Checklist before 10:00 AM daily.\n\n- Hygiene log\n- Temperature log\n- Stock level checks\n\nThank you.",
                            created_by=created_by,
                            created_at=now,
                        )
                    )
                    db_instance.session.add(
                        Announcement(
                            title="Finance Update",
                            message="Cashbook & Accounting: Ensure all income/expense transactions are recorded the same day.\n\nBalance Sheet is available (Daily/Weekly/Monthly/Yearly).",
                            created_by=created_by,
                            created_at=now,
                        )
                    )
        except Exception:
            # Never block startup because sample announcements failed.
            pass
        
        db_instance.session.commit()
    except Exception as e:
        # If there's a schema mismatch, rollback and let db.create_all() handle it
        db_instance.session.rollback()
        # Silently fail - the database will be created/updated by db.create_all()
        pass


def configure_relationship_ordering():
    """Configure order_by for relationships that use forward references."""
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
    pass


def setup_audit_logging():
    """Set up audit logging functionality."""
    # Stub function - implement based on your requirements
    pass


class ActivityLog(db.Model):
    """Activity logging for user actions."""
    __tablename__ = "activity_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    action = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    url = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref="activity_logs")
    
    def __repr__(self):
        return f'<ActivityLog user_id={self.user_id} action={self.action}>'
