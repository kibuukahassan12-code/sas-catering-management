from datetime import datetime
from decimal import Decimal
from functools import wraps

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from functools import wraps

# No-op login_required - all access allowed
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

from models import (
    CateringItem,
    Client,
    ClientActivity,
    Event,
    # HireOrder,  # Commented out - hire order functionality removed
    # HireOrderItem,  # Commented out - hire order functionality removed
    IncomingLead,
    Ingredient,
    InventoryItem,
    Invoice,
    InvoiceStatus,
    Quotation,
    QuotationLine,
    QuotationSource,
    RecipeItem,
    Task,
    TaskStatus,
    Transaction,
    TransactionType,
    User,
    UserRole,
    db,
)
from utils import get_decimal, paginate_query, role_required, has_permission, require_permission
from utils.permissions import no_rbac

core_bp = Blueprint("core", __name__)


@core_bp.route("/offline")
def offline():
    """Offline fallback page for PWA."""
    return render_template("offline.html")


@core_bp.route("/pwa-test")
@login_required
def pwa_test():
    """PWA test and debug page."""
    return render_template("pwa_test.html")


def _get_role_redirect(user):
    """
    Get the appropriate redirect URL based on user's role.
    
    Args:
        user: User object
        
    Returns:
        URL string for redirect
    """
    # Check role_obj (new RBAC system)
    role_name = None
    if hasattr(user, 'role_obj') and user.role_obj:
        role_name = user.role_obj.name
    
    # Role-based redirects
    if role_name == "Admin":
        return url_for("core.dashboard")  # Admin goes to main dashboard
    elif role_name == "HireManager":
        return url_for("hire.orders_list")
    elif role_name == "EventManager":
        return url_for("events.events_list")
    elif role_name == "InventoryManager":
        return url_for("inventory.ingredients_list")
    elif role_name == "Finance":
        return url_for("accounting.dashboard")
    
    # Fallback to legacy role enum (backward compatibility)
    if hasattr(user, 'role'):
        if user.role == UserRole.Admin:
            return url_for("core.dashboard")
        elif user.role == UserRole.HireManager:
            return url_for("hire.orders_list")
        elif user.role == UserRole.SalesManager:
            return url_for("core.dashboard")
    
    # Default redirect
    return url_for("core.dashboard")


@core_bp.route("/", methods=["GET", "POST"])
@no_rbac
def login():
    """Login route with RBAC bypass."""
    # Rate limiting is applied via app.limiter decorator after app creation
    
    # If user is already authenticated, go directly to dashboard WITHOUT checking role or permissions
    if current_user.is_authenticated:
        if getattr(current_user, "force_password_change", False) or getattr(current_user, "first_login", True):
            return redirect(url_for("core.force_change_password"))
        return redirect(url_for("core.dashboard"))
    
    # Handle login form submission
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Login successful.", "success")
            
            # Check if user must change password or first login
            if getattr(user, 'must_change_password', False) or getattr(user, 'force_password_change', False) or getattr(user, 'first_login', True):
                return redirect(url_for("core.force_change_password"))
            
            # Redirect directly to dashboard WITHOUT checking role or permissions
            return redirect(url_for("core.dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    
    return render_template("login.html")


@core_bp.route("/force-change-password", methods=["GET", "POST"])
@login_required
def force_change_password():
    """Force password change on first login."""
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not new_password or not confirm_password:
            flash("Both password fields are required.", "danger")
            return render_template("auth/force_change_password.html")
        
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/force_change_password.html")
        
        if len(new_password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/force_change_password.html")
        
        current_user.set_password(new_password)
        current_user.first_login = False
        current_user.must_change_password = False
        current_user.force_password_change = False
        db.session.commit()
        flash("Password changed successfully. Please login again.", "success")
        return redirect(url_for("core.login"))
    
    return render_template("auth/force_change_password.html")


@core_bp.route("/dashboard")
@login_required
@no_rbac
def dashboard():
    """Dashboard with comprehensive error handling and improved metrics."""
    # If user has NO role_id → allow access (prevent redirect loop)
    if getattr(current_user, "role_id", None) is None:
        pass  # allow access
    
    # If super admin → return dashboard immediately
    if current_user.is_super_admin():
        # We'll still render the full dashboard, but skip permission checks
        pass
    
    try:

        # Initialize all variables with safe defaults
        clients = []
        events = []
        total_confirmed_quote = Decimal('0.00')
        active_clients = 0
        draft_events = 0
        pipeline_stats = {}
        pipeline_value = Decimal('0.00')
        paid_invoices = 0
        pending_invoices = 0
        overdue_invoices = 0
        pending_invoice_amount = Decimal('0.00')
        available_staff = 0
        low_stock_alerts = 0
        upcoming_events_count = 0
        upcoming_events = []
        tasks_today = 0
        recent_tasks = []
        top_clients = []
        announcements = []

        try:
            clients = Client.query.filter(Client.is_archived == False).order_by(Client.name.asc()).all()
            active_clients = len(clients)
        except Exception as e:
            current_app.logger.error(f"Error loading clients: {e}")
            flash("Error loading client data. Some metrics may be incomplete.", "warning")

        try:
            events = Event.query.order_by(Event.event_date.asc()).all()
        except Exception as e:
            current_app.logger.error(f"Error loading events: {e}")
            flash("Error loading event data. Some metrics may be incomplete.", "warning")

        try:
            total_confirmed_quote = (
                db.session.query(db.func.coalesce(db.func.sum(Event.quoted_value), 0))
                .filter(Event.status == "Confirmed")
                .scalar() or Decimal('0.00')
            )
        except Exception as e:
            current_app.logger.error(f"Error calculating confirmed quotes: {e}")

        try:
            draft_events = (
                db.session.query(db.func.count(Event.id))
                .filter(Event.status == "Draft")
                .scalar() or 0
            )
        except Exception as e:
            current_app.logger.error(f"Error counting draft events: {e}")
        
        # Pipeline metrics with error handling
        try:
            from models import IncomingLead
            from datetime import datetime, timedelta
            stages = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Awaiting Payment", "Confirmed", "Completed", "Lost"]
            for stage in stages:
                try:
                    pipeline_stats[stage] = IncomingLead.query.filter_by(pipeline_stage=stage).count()
                except Exception as e:
                    current_app.logger.error(f"Error counting leads for stage {stage}: {e}")
                    pipeline_stats[stage] = 0
        except Exception as e:
            current_app.logger.error(f"Error loading pipeline stats: {e}")
            flash("Error loading pipeline statistics.", "warning")
        
        # Calculate pipeline value with error handling
        try:
            pipeline_value = (
                db.session.query(db.func.coalesce(db.func.sum(Event.quoted_value), 0))
                .join(IncomingLead, IncomingLead.converted_event_id == Event.id)
                .filter(IncomingLead.pipeline_stage.in_(["Qualified", "Proposal Sent", "Negotiation", "Awaiting Payment"]))
                .scalar() or Decimal('0.00')
            )
        except Exception as e:
            current_app.logger.error(f"Error calculating pipeline value: {e}")
        
        # Invoice metrics with error handling
        try:
            from models import Invoice, InvoiceStatus, InventoryItem, Task, TaskStatus
            paid_invoices = Invoice.query.filter_by(status=InvoiceStatus.Paid).count()
            pending_invoices = Invoice.query.filter(Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft])).count()
            overdue_invoices = Invoice.query.filter_by(status=InvoiceStatus.Overdue).count()
            
            pending_invoice_amount = (
                db.session.query(db.func.coalesce(db.func.sum(Invoice.total_amount_ugx), 0))
                .filter(Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft]))
                .scalar() or Decimal('0.00')
            )
        except Exception as e:
            current_app.logger.error(f"Error loading invoice metrics: {e}")
            flash("Error loading invoice data.", "warning")
        
        try:
            available_staff = User.query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting staff: {e}")
        
        try:
            low_stock_alerts = InventoryItem.query.filter(InventoryItem.stock_count <= 10).count()
        except Exception as e:
            current_app.logger.error(f"Error checking low stock: {e}")
            flash("Error loading inventory alerts.", "warning")
        
        # Upcoming events with error handling
        try:
            from datetime import datetime, timedelta
            today = datetime.utcnow().date()
            next_30_days = today + timedelta(days=30)
            next_7_days = today + timedelta(days=7)
            upcoming_events_count = Event.query.filter(
                Event.event_date >= today,
                Event.event_date <= next_30_days
            ).count()
            
            upcoming_events = Event.query.filter(
                Event.event_date >= today,
                Event.event_date <= next_7_days
            ).order_by(Event.event_date.asc()).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"Error loading upcoming events: {e}")
        
        # Tasks with error handling
        try:
            from datetime import date
            today = date.today()
            tasks_today = Task.query.filter(
                Task.due_date <= today,
                Task.status != TaskStatus.Complete
            ).count()
            
            recent_tasks = Task.query.filter(
                Task.assigned_user_id == current_user.id,
                Task.status != TaskStatus.Complete
            ).order_by(Task.due_date.asc()).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"Error loading tasks: {e}")
        
        # Top clients with error handling
        try:
            from sqlalchemy import func
            top_clients_query = (
                db.session.query(Client, func.count(Event.id).label('event_count'))
                .join(Event, Client.id == Event.client_id)
                .filter(Client.is_archived == False)
                .group_by(Client.id)
                .order_by(func.count(Event.id).desc())
                .limit(5)
                .all()
            )
            top_clients = [{"client": client, "event_count": count} for client, count in top_clients_query]
        except Exception as e:
            current_app.logger.error(f"Error loading top clients: {e}")
        
        # Announcements with error handling
        try:
            from models import Announcement
            from sqlalchemy.orm import joinedload
            announcements = Announcement.query.options(joinedload(Announcement.creator)).order_by(Announcement.created_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error loading announcements: {e}")
            announcements = []
        
        # Build modules list (filtered by permissions)
        modules = []
        
        # Dashboard - always available
        modules.append({"name": "Dashboard", "url": url_for("core.dashboard")})
        
        # Clients CRM - ALL ACCESS GRANTED
        modules.append({"name": "Clients CRM", "url": url_for("core.clients_list")})
        
        # Events - ALL ACCESS GRANTED
        events_children = [
            {"name": "All Events", "url": url_for("events.events_list")},
            {"name": "Create Event", "url": url_for("events.event_create")},
            {"name": "Venues", "url": url_for("events.venues_list")},
            {"name": "Menu Packages", "url": url_for("events.menu_packages_list")},
            {"name": "Vendors", "url": url_for("events.vendors_manage")},
            {"name": "Floor Planner", "url": url_for("floorplanner.dashboard")},
            {"name": "Tasks", "url": url_for("tasks.task_list")},
        ]
        modules.append({
            "name": "Events",
            "url": url_for("events.events_list"),
            "children": events_children
        })
        # Hire Department - ALL ACCESS GRANTED
        hire_children = [
            {"name": "Hire Overview", "url": url_for("hire.index")},
            {"name": "Hire Inventory", "url": url_for("hire.inventory_list")},
            {"name": "Hire Orders", "url": url_for("hire.orders_list")},
            {"name": "Equipment Maintenance", "url": url_for("maintenance.dashboard")},
        ]
        modules.append({
            "name": "Hire Department",
            "url": url_for("hire.index"),
            "children": hire_children
        })
        
        modules.extend([
            {
                "name": "Production Department",
                "url": url_for("production.index"),
                "children": [
                    {"name": "Production Overview", "url": url_for("production.index")},
                    {"name": "Menu Builder", "url": url_for("menu_builder.dashboard")},
                    {"name": "Catering Menu", "url": url_for("catering.menu_list")},
                    {"name": "Ingredient Inventory", "url": url_for("inventory.ingredients_list")},
                    {"name": "Kitchen Checklist", "url": url_for("production.kitchen_checklist_list")},
                    {"name": "Delivery QC Checklist", "url": url_for("production.delivery_qc_list")},
                    {"name": "Food Safety Logs", "url": url_for("production.food_safety_list")},
                    {"name": "Hygiene Reports", "url": url_for("production.hygiene_reports_list")},
                ]
            },
            {
                "name": "Accounting Department",
                "url": url_for("accounting.dashboard"),
                "children": [
                    {"name": "Accounting Overview", "url": url_for("accounting.dashboard")},
                    {"name": "Receipting System", "url": url_for("accounting.receipts_list")},
                    {"name": "Quotations", "url": url_for("quotes.dashboard")},
                    {"name": "Invoices", "url": url_for("invoices.invoice_list")},
                    {"name": "Cashbook", "url": url_for("cashbook.index")},
                    {"name": "Financial Reports", "url": url_for("reports.reports_index")},
                ]
            },
            {
                "name": "Bakery Department",
                "url": url_for("bakery.dashboard"),
                "children": [
                    {"name": "Bakery Overview", "url": url_for("bakery.dashboard")},
                    {"name": "Bakery Menu", "url": url_for("bakery.items_list")},
                    {"name": "Bakery Orders", "url": url_for("bakery.orders_list")},
                    {"name": "Production Sheet", "url": url_for("bakery.production_sheet")},
                    {"name": "Reports", "url": url_for("bakery.reports")},
                ]
            },
            {"name": "POS System", "url": url_for("pos.index")},
            {
                "name": "HR Department",
                "url": url_for("hr.dashboard"),
                "children": [
                    {"name": "HR Overview", "url": url_for("hr.dashboard")},
                    {"name": "Employee Management", "url": url_for("hr.employee_list")},
                    {"name": "Roster Builder", "url": url_for("hr.roster_builder")},
                    {"name": "Leave Requests", "url": url_for("hr.leave_queue")},
                    {"name": "Attendance Review", "url": url_for("hr.attendance_review")},
                    {"name": "Payroll Export", "url": url_for("hr.payroll_export")},
                ]
            },
        ])
        
        # Add admin-only modules - ALL ACCESS GRANTED
        admin_module = {
            "name": "Admin",
            "url": url_for("admin.roles_list"),
            "children": [
                {"name": "Roles & Permissions", "url": url_for("admin.roles_list")},
                {"name": "User Role Assignment", "url": url_for("admin_users.users_assign")},
            ]
        }
        modules.append(admin_module)
        
        # Add Payroll to Accounting Department children if not already there
        accounting_dept = next((m for m in modules if m.get("name") == "Accounting Department"), None)
        if accounting_dept and "children" in accounting_dept:
            accounting_dept["children"].append({"name": "Payroll Management", "url": url_for("payroll.payroll_list")})
        
        # Get today's date for template
        from datetime import date
        today = date.today()
        
        return render_template(
            "dashboard.html",
            clients=clients,
            events=events,
            modules=modules,
            today=today,
            summary={
                "total_confirmed_quote": total_confirmed_quote,
                "active_clients": active_clients,
                "draft_events": draft_events,
                "total_events": len(events),
                "paid_invoices": paid_invoices,
                "pending_invoices": pending_invoices,
                "overdue_invoices": overdue_invoices,
                "pipeline_value": pipeline_value,
                "pending_invoice_amount": pending_invoice_amount,
                "available_staff": available_staff,
                "low_stock_alerts": low_stock_alerts,
                "upcoming_events_count": upcoming_events_count,
                "tasks_today": tasks_today,
            },
            pipeline_stats=pipeline_stats,
            top_clients=top_clients,
            upcoming_events=upcoming_events,
            recent_tasks=recent_tasks,
            announcements=announcements,
            CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
        )
    except Exception as e:
        current_app.logger.exception(f"Critical error in dashboard: {e}")
        # Return a minimal dashboard with error message
        return render_template(
            "dashboard.html",
            clients=[],
            events=[],
            modules=[],
            today=date.today() if 'date' in dir() else None,
            summary={
                "total_confirmed_quote": Decimal('0.00'),
                "active_clients": 0,
                "draft_events": 0,
                "total_events": 0,
                "paid_invoices": 0,
                "pending_invoices": 0,
                "overdue_invoices": 0,
                "pipeline_value": Decimal('0.00'),
                "pending_invoice_amount": Decimal('0.00'),
                "available_staff": 0,
                "low_stock_alerts": 0,
                "upcoming_events_count": 0,
                "tasks_today": 0,
            },
            pipeline_stats={},
            top_clients=[],
            upcoming_events=[],
            recent_tasks=[],
            announcements=[],
            CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
        )


# Dashboard API Endpoints for Charts and Data
@core_bp.route("/api/dashboard/events/upcoming")
@login_required
def api_dashboard_upcoming_events():
    """API endpoint for upcoming events data (next 30 days)."""
    allowed_roles = {UserRole.Admin, UserRole.SalesManager}
    from datetime import timedelta
    today = datetime.utcnow().date()
    next_30_days = today + timedelta(days=30)
    
    events = Event.query.filter(
        Event.event_date >= today,
        Event.event_date <= next_30_days
    ).order_by(Event.event_date.asc()).all()
    
    return jsonify({
        "count": len(events),
        "events": [
            {
                "id": e.id,
                "name": e.event_name,
                "client": e.client.name,
                "date": e.event_date.isoformat(),
                "guests": e.guest_count,
                "status": e.status,
                "quoted_value": float(e.quoted_value or 0)
            }
            for e in events
        ]
    })


@core_bp.route("/api/dashboard/pipeline")
@login_required
def api_dashboard_pipeline():
    """API endpoint for pipeline statistics."""
    allowed_roles = {UserRole.Admin, UserRole.SalesManager}
    stages = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Awaiting Payment", "Confirmed", "Completed", "Lost"]
    pipeline_stats = {}
    pipeline_values = {}
    
    for stage in stages:
        count = IncomingLead.query.filter_by(pipeline_stage=stage).count()
        pipeline_stats[stage] = count
        
        # Calculate total value for leads in this stage
        value = (
            db.session.query(db.func.coalesce(db.func.sum(Event.quoted_value), 0))
            .join(IncomingLead, IncomingLead.converted_event_id == Event.id)
            .filter(IncomingLead.pipeline_stage == stage)
            .scalar()
        )
        pipeline_values[stage] = float(value)
    
    return jsonify({
        "stages": stages,
        "counts": pipeline_stats,
        "values": pipeline_values
    })


@core_bp.route("/api/dashboard/invoices/pending")
@login_required
def api_dashboard_pending_invoices():
    """API endpoint for pending invoices data."""
    allowed_roles = {UserRole.Admin, UserRole.SalesManager}
    pending = Invoice.query.filter(Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft])).all()
    overdue = Invoice.query.filter_by(status=InvoiceStatus.Overdue).all()
    
    return jsonify({
        "pending_count": len(pending),
        "pending_amount": float(sum(float(i.total_amount_ugx or 0) for i in pending)),
        "overdue_count": len(overdue),
        "overdue_amount": float(sum(float(i.total_amount_ugx or 0) for i in overdue))
    })


@core_bp.route("/api/dashboard/staff/availability")
@login_required
def api_dashboard_staff_availability():
    """API endpoint for staff availability data."""
    allowed_roles = {UserRole.Admin, UserRole.SalesManager}
    # All access allowed - no restrictions
    
    # Count users by role
    from sqlalchemy import func
    role_counts = (
        db.session.query(User.role, func.count(User.id).label('count'))
        .group_by(User.role)
        .all()
    )
    
    total_staff = User.query.count()
    
    return jsonify({
        "total_staff": total_staff,
        "by_role": {role.value: count for role, count in role_counts}
    })


@core_bp.route("/api/dashboard/inventory/low-stock")
@login_required
def api_dashboard_low_stock():
    """API endpoint for low stock inventory alerts."""
    allowed_roles = {UserRole.Admin, UserRole.SalesManager}
    # All access allowed - no restrictions
    
    low_stock = InventoryItem.query.filter(InventoryItem.stock_count <= 10).order_by(InventoryItem.stock_count.asc()).all()
    
    return jsonify({
        "count": len(low_stock),
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "stock_count": item.stock_count,
                "status": item.status
            }
            for item in low_stock
        ]
    })


@core_bp.route("/api/dashboard/revenue/stats")
@login_required
def api_dashboard_revenue_stats():
    """API endpoint for revenue statistics (last 6 months)."""
    allowed_roles = {UserRole.Admin, UserRole.SalesManager}
    from datetime import timedelta
    from calendar import month_abbr
    today = datetime.utcnow().date()
    
    # Get revenue data for last 6 months
    monthly_revenue = []
    monthly_expenses = []
    monthly_labels = []
    
    for i in range(5, -1, -1):
        month_start = (today - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_label = f"{month_abbr[month_start.month]} {month_start.year}"
        monthly_labels.append(month_label)
        
        # Calculate income for this month
        income = (
            db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0))
            .filter(Transaction.type == TransactionType.Income)
            .filter(Transaction.date >= month_start)
            .filter(Transaction.date <= month_end)
            .scalar()
        )
        
        # Calculate expenses for this month
        expenses = (
            db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0))
            .filter(Transaction.type == TransactionType.Expense)
            .filter(Transaction.date >= month_start)
            .filter(Transaction.date <= month_end)
            .scalar()
        )
        
        monthly_revenue.append(float(income))
        monthly_expenses.append(float(expenses))
    
    # Bookings over time (events by month)
    monthly_bookings = []
    for i in range(5, -1, -1):
        month_start = (today - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        bookings = Event.query.filter(
            Event.event_date >= month_start,
            Event.event_date <= month_end
        ).count()
        
        monthly_bookings.append(bookings)
    
    return jsonify({
        "labels": monthly_labels,
        "revenue": monthly_revenue,
        "expenses": monthly_expenses,
        "bookings": monthly_bookings
    })


@core_bp.route("/access_denied")
@login_required
def access_denied():
    return render_template("access_denied.html")


@core_bp.route("/logout")
@no_rbac
def logout():
    """Logout route with RBAC bypass."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("core.login"))


@core_bp.route("/clients")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def clients_list():
    # Filter out archived clients by default
    show_archived = request.args.get("archived", "false").lower() == "true"
    query = Client.query
    if not show_archived:
        query = query.filter(Client.is_archived == False)
    pagination = paginate_query(query.order_by(Client.name.asc()))
    return render_template(
        "clients.html", clients=pagination.items, pagination=pagination, show_archived=show_archived
    )


@core_bp.route("/clients/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def clients_add():
    if request.method == "POST":
        from datetime import datetime
        
        client = Client(
            name=request.form.get("name", "").strip(),
            contact_person=request.form.get("contact_person", "").strip(),
            phone=request.form.get("phone", "").strip(),
            email=request.form.get("email", "").strip(),
            company=request.form.get("company", "").strip() or None,
            address=request.form.get("address", "").strip() or None,
            preferred_channel=request.form.get("preferred_channel", "").strip() or None,
            tags=request.form.get("tags", "").strip() or None,
        )
        db.session.add(client)
        db.session.flush()
        
        # Create activity log
        activity = ClientActivity(
            client_id=client.id,
            user_id=current_user.id,
            activity_type="Created",
            description=f"Client created: {client.name}"
        )
        db.session.add(activity)
        db.session.commit()
        flash("Client added successfully.", "success")
        return redirect(url_for("core.clients_list"))

    return render_template("client_form.html", action="Add", client=None)


@core_bp.route("/clients/edit/<int:client_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def clients_edit(client_id):
    from datetime import datetime
    
    client = Client.query.get_or_404(client_id)

    if request.method == "POST":
        client.name = request.form.get("name", client.name).strip()
        client.contact_person = request.form.get(
            "contact_person", client.contact_person
        ).strip()
        client.phone = request.form.get("phone", client.phone).strip()
        client.email = request.form.get("email", client.email).strip()
        client.company = request.form.get("company", "").strip() or None
        client.address = request.form.get("address", "").strip() or None
        client.preferred_channel = request.form.get("preferred_channel", "").strip() or None
        client.tags = request.form.get("tags", "").strip() or None
        client.updated_at = datetime.utcnow()
        
        # Create activity log
        activity = ClientActivity(
            client_id=client.id,
            user_id=current_user.id,
            activity_type="Updated",
            description=f"Client profile updated"
        )
        db.session.add(activity)
        db.session.commit()
        flash("Client updated successfully.", "success")
        return redirect(url_for("core.clients_list"))

    return render_template("client_form.html", action="Edit", client=client)


@core_bp.route("/clients/delete/<int:client_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def clients_delete(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    flash("Client deleted.", "info")
    return redirect(url_for("core.clients_list"))


@core_bp.route("/events")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def events_list():
    pagination = paginate_query(Event.query.order_by(Event.event_date.desc()))
    return render_template(
        "events.html", events=pagination.items, pagination=pagination
    )


@core_bp.route("/events/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def events_add():
    clients = Client.query.order_by(Client.name.asc()).all()
    if not clients:
        flash("Create a client record before planning events.", "warning")
        return redirect(url_for("core.clients_add"))

    if request.method == "POST":
        client_id = request.form.get("client_id", type=int)
        if not client_id:
            flash("Please select a client for the event.", "danger")
            return render_template(
                "event_form.html",
                action="Add",
                event=None,
                clients=clients,
                statuses=["Draft", "Quotation Sent", "Awaiting Payment", "Confirmed", "Preparation", "In Progress", "Completed", "Cancelled"],
            )
        event_date_str = request.form.get("event_date", "")
        try:
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        except ValueError:
            event_date = datetime.utcnow().date()

        event = Event(
            client_id=client_id,
            event_name=request.form.get("event_name", "").strip(),
            event_type=request.form.get("event_type", "").strip() or None,
            event_date=event_date,
            event_time=request.form.get("event_time", "").strip() or None,
            guest_count=request.form.get("guest_count", type=int) or 0,
            venue=request.form.get("venue", "").strip() or None,
            venue_map_link=request.form.get("venue_map_link", "").strip() or None,
            status=request.form.get("status", "Draft"),
            quoted_value=get_decimal(request.form.get("quoted_value")),
            notes=request.form.get("notes", "").strip() or None,
        )
        db.session.add(event)
        db.session.commit()
        flash("Event created successfully.", "success")
        return redirect(url_for("core.events_list"))

    return render_template(
        "event_form.html",
        action="Add",
        event=None,
        clients=clients,
        statuses=["Draft", "Quotation Sent", "Awaiting Payment", "Confirmed", "Preparation", "In Progress", "Completed", "Cancelled"],
    )


def _calculate_event_cogs(event):
    """Calculate COGS for an event: ingredients + hire order costs."""
    from decimal import Decimal
    from sqlalchemy.orm import joinedload

    total_cogs = Decimal("0.00")

    # 1. Calculate COGS from HireOrders linked to this event
    # HireOrder functionality removed - commenting out
    # hire_orders = (
    #     HireOrder.query.filter_by(event_id=event.id)
    #     .options(joinedload(HireOrder.items).joinedload(HireOrderItem.inventory_item))
    #     .all()
    # )
    # for order in hire_orders:
    #     total_cogs += Decimal(order.total_cost or 0)

    # 2. Calculate COGS from Ingredients
    # Find quotations linked to this event to determine which catering items are used
    quotations = Quotation.query.filter_by(event_id=event.id).all()
    ingredient_usage = {}  # ingredient_id -> total_quantity_needed

    for quote in quotations:
        for line in quote.lines:
            if line.source_type == QuotationSource.Catering:
                # Find the catering item and its recipe
                # Try to find catering item by name (since we don't have direct ID link)
                catering_item = CateringItem.query.filter_by(
                    name=line.item_name
                ).first()
                if catering_item:
                    # Get recipe items for this catering item
                    recipe_items = RecipeItem.query.filter_by(
                        catering_item_id=catering_item.id
                    ).all()
                    # Scale by quantity in quotation line
                    scale_factor = Decimal(line.quantity or 1)
                    for recipe_item in recipe_items:
                        ing_id = recipe_item.ingredient_id
                        qty_needed = Decimal(recipe_item.quantity_required) * scale_factor
                        if ing_id in ingredient_usage:
                            ingredient_usage[ing_id] += qty_needed
                        else:
                            ingredient_usage[ing_id] = qty_needed

    # Calculate ingredient costs and deplete stock
    for ing_id, qty_needed in ingredient_usage.items():
        ingredient = Ingredient.query.get(ing_id)
        if ingredient:
            # Check stock availability
            if Decimal(ingredient.stock_count) < qty_needed:
                raise ValueError(
                    f"Insufficient stock for {ingredient.name}. "
                    f"Available: {ingredient.stock_count}, Required: {qty_needed}"
                )
            # Calculate cost
            ingredient_cost = Decimal(ingredient.unit_cost_ugx) * qty_needed
            total_cogs += ingredient_cost
            # Deplete stock
            ingredient.stock_count = max(
                Decimal(ingredient.stock_count) - qty_needed, Decimal("0")
            )

    # 3. Verify and deplete stock for HireOrder inventory items
    # HireOrder functionality removed - commenting out
    # Note: Stock may have been reduced when order was created, but we reduce again on confirmation
    # to ensure accuracy (this handles cases where orders were edited)
    # for order in hire_orders:
    #     for order_item in order.items:
    #         if order_item.inventory_item:
    #             inv_item = order_item.inventory_item
    #             qty_rented = order_item.quantity_rented
    #             # Check stock availability
    #             if inv_item.stock_count < qty_rented:
    #                 raise ValueError(
    #                     f"Insufficient stock for {inv_item.name}. "
    #                     f"Available: {inv_item.stock_count}, Required: {qty_rented}"
    #                 )
    #             # Deplete stock
    #             inv_item.stock_count = max(inv_item.stock_count - qty_rented, 0)

    return total_cogs


@core_bp.route("/events/edit/<int:event_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def events_edit(event_id):
    event = Event.query.get_or_404(event_id)
    clients = Client.query.order_by(Client.name.asc()).all()
    old_status = event.status

    if request.method == "POST":
        event.client_id = request.form.get("client_id", type=int) or event.client_id
        event.event_name = request.form.get("event_name", event.event_name).strip()
        event.event_type = request.form.get("event_type", "").strip() or None
        event.event_time = request.form.get("event_time", "").strip() or None
        event.venue = request.form.get("venue", "").strip() or None
        event.venue_map_link = request.form.get("venue_map_link", "").strip() or None
        event.notes = request.form.get("notes", "").strip() or None
        new_status = request.form.get("status", event.status)
        event.status = new_status
        event_date_str = request.form.get("event_date", "")
        try:
            event.event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
        event.guest_count = request.form.get("guest_count", type=int) or event.guest_count
        event.quoted_value = get_decimal(
            request.form.get("quoted_value"), fallback=str(event.quoted_value)
        )

        # If status is changing to "Confirmed", calculate COGS and deplete stock
        if new_status == "Confirmed" and old_status != "Confirmed":
            try:
                cogs_amount = _calculate_event_cogs(event)
                event.actual_cogs_ugx = cogs_amount

                # Create cashbook expense transaction
                expense = Transaction(
                    type=TransactionType.Expense,
                    category="COGS",
                    description=f"Cost of Goods Sold for event: {event.event_name}",
                    amount=cogs_amount,
                    date=datetime.utcnow().date(),
                    related_event_id=event.id,
                )
                db.session.add(expense)

                # Automatically create pre-defined tasks for confirmed events
                from datetime import timedelta
                event_date = event.event_date
                task_due_dates = {
                    "Finalize Ingredient Purchase": event_date - timedelta(days=7),
                    "Prepare Rental Load List": event_date - timedelta(days=3),
                    "Send Final Invoice": event_date - timedelta(days=5),
                }

                # Get admin user for task assignment (or assign to current user)
                admin_user = User.query.filter_by(role=UserRole.Admin).first()
                assigned_user = admin_user if admin_user else current_user

                for task_title, due_date in task_due_dates.items():
                    task = Task(
                        title=task_title,
                        description=f"Task for event: {event.event_name}",
                        event_id=event.id,
                        assigned_user_id=assigned_user.id,
                        due_date=due_date,
                        status=TaskStatus.Pending,
                    )
                    db.session.add(task)

                db.session.commit()
                flash(
                    f"Event confirmed. COGS calculated: {current_app.config.get('CURRENCY_PREFIX', 'UGX ')}{cogs_amount:,.2f}. Tasks created automatically.",
                    "success",
                )
            except ValueError as e:
                db.session.rollback()
                flash(f"Cannot confirm event: {str(e)}", "danger")
                return render_template(
                    "event_form.html",
                    action="Edit",
                    event=event,
                    clients=clients,
                    statuses=["Draft", "Quotation Sent", "Awaiting Payment", "Confirmed", "Preparation", "In Progress", "Completed", "Cancelled"],
                )
            except Exception as e:
                db.session.rollback()
                flash(f"Error calculating COGS: {str(e)}", "danger")
                return render_template(
                    "event_form.html",
                    action="Edit",
                    event=event,
                    clients=clients,
                    statuses=["Draft", "Quotation Sent", "Awaiting Payment", "Confirmed", "Preparation", "In Progress", "Completed", "Cancelled"],
                )
        else:
            db.session.commit()
            flash("Event updated successfully.", "success")

        return redirect(url_for("core.events_list"))

    return render_template(
        "event_form.html",
        action="Edit",
        event=event,
        clients=clients,
        statuses=["Draft", "Quotation Sent", "Awaiting Payment", "Confirmed", "Preparation", "In Progress", "Completed", "Cancelled"],
    )


@core_bp.route("/events/delete/<int:event_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def events_delete(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("core.events_list"))


# Public API endpoint - no authentication required
@core_bp.route("/api/new_lead", methods=["POST"])
def api_new_lead():
    """Public API endpoint to receive leads from external website."""

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    client_name = data.get("client_name", "").strip()
    client_email = data.get("client_email", "").strip()
    phone = data.get("phone", "").strip()
    inquiry_type = data.get("inquiry_type", "").strip()
    message = data.get("message", "").strip()

    # Validation
    if not client_name or not client_email or not message:
        return jsonify({"status": "error", "message": "Missing required fields: name, email, message"}), 400

    # Validate email format (basic)
    if "@" not in client_email:
        return jsonify({"status": "error", "message": "Invalid email format"}), 400

    # Create lead record
    try:
        lead = IncomingLead(
            client_name=client_name,
            client_email=client_email,
            phone=phone if phone else None,
            inquiry_type=inquiry_type if inquiry_type else "General",
            message=message,
            timestamp=datetime.utcnow(),
        )
        db.session.add(lead)
        db.session.commit()
        return jsonify({"status": "success", "message": "Lead received"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Failed to save lead"}), 500


# POS API Routes - Proxy routes to match frontend URL pattern /api/pos/*
# These routes forward requests to the POS blueprint functions

def pos_role_required(*roles):
    """Role check for POS proxy routes."""
    from models import UserRole
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({"status": "error", "message": "You do not have permission to access this resource."}), 403
                flash("You do not have permission to access this resource.", "warning")
                return redirect(url_for("core.access_denied"))
            return func(*args, **kwargs)
        return wrapper
    return decorator

@core_bp.route("/api/pos/shifts/start", methods=["POST"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_shift_start_proxy():
    """Proxy route for /api/pos/shifts/start -> forwards to POS blueprint"""
    from blueprints.pos import api_shift_start
    return api_shift_start()

@core_bp.route("/api/pos/shifts/<int:shift_id>/close", methods=["POST"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_shift_close_proxy(shift_id):
    """Proxy route for /api/pos/shifts/<id>/close -> forwards to POS blueprint"""
    from blueprints.pos import api_shift_close
    return api_shift_close(shift_id)

@core_bp.route("/api/pos/orders", methods=["GET", "POST"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_orders_proxy():
    """Proxy route for /api/pos/orders -> forwards to POS blueprint"""
    if request.method == "GET":
        from blueprints.pos import api_orders_list
        return api_orders_list()
    else:
        from blueprints.pos import api_order_create
        return api_order_create()

@core_bp.route("/api/pos/orders/<int:order_id>", methods=["GET"])
@login_required
def pos_order_detail_proxy(order_id):
    """Proxy route for /api/pos/orders/<id> -> forwards to POS blueprint"""
    from blueprints.pos import api_order_detail
    return api_order_detail(order_id)

@core_bp.route("/api/pos/orders/<int:order_id>/status", methods=["PATCH", "POST"])
@login_required
def pos_order_status_proxy(order_id):
    """Proxy route for /api/pos/orders/<id>/status -> forwards to POS blueprint"""
    from blueprints.pos import api_order_status
    return api_order_status(order_id)

@core_bp.route("/api/pos/orders/<int:order_id>/payments", methods=["POST", "GET"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_order_payment_proxy(order_id):
    """Proxy route for /api/pos/orders/<id>/payments -> forwards to POS blueprint"""
    if request.method == "GET":
        from blueprints.pos import api_order_payments_list
        return api_order_payments_list(order_id)
    else:
        from blueprints.pos import api_order_payment
        return api_order_payment(order_id)

@core_bp.route("/api/pos/orders/<int:order_id>/receipt", methods=["GET"])
@login_required
def pos_order_receipt_proxy(order_id):
    """Proxy route for /api/pos/orders/<id>/receipt -> forwards to POS blueprint"""
    from blueprints.pos import api_order_receipt
    return api_order_receipt(order_id)

@core_bp.route("/api/pos/products", methods=["GET", "POST"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_products_proxy():
    """Proxy route for /api/pos/products -> forwards to POS blueprint"""
    if request.method == "GET":
        from blueprints.pos import api_products
        return api_products()
    else:
        from blueprints.pos import api_product_create
        return api_product_create()

@core_bp.route("/api/pos/products/upload-image", methods=["POST"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_products_upload_image_proxy():
    """Proxy route for /api/pos/products/upload-image -> forwards to POS blueprint"""
    from blueprints.pos import api_product_upload_image
    return api_product_upload_image()

@core_bp.route("/api/pos/products/<int:product_id>", methods=["DELETE", "PUT"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_product_manage_proxy(product_id):
    """Proxy route for /api/pos/products/<id> -> forwards to POS blueprint"""
    from blueprints.pos import api_product_manage
    return api_product_manage(product_id)

@core_bp.route("/api/pos/devices", methods=["GET", "POST"])
@login_required
def pos_devices_proxy():
    """Proxy route for /api/pos/devices -> forwards to POS blueprint"""
    if request.method == "GET":
        from blueprints.pos import api_devices_list
        return api_devices_list()
    else:
        from blueprints.pos import api_device_create
        return api_device_create()

@core_bp.route("/pos/receipts/<int:receipt_id>/print", methods=["GET"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_receipt_print_proxy(receipt_id):
    """Proxy route for /pos/receipts/<id>/print -> forwards to POS blueprint"""
    from blueprints.pos import receipt_print
    return receipt_print(receipt_id)

@core_bp.route("/api/pos/receipts/<int:receipt_id>", methods=["GET"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_receipt_detail_proxy(receipt_id):
    """Proxy route for /api/pos/receipts/<id> -> forwards to POS blueprint"""
    from blueprints.pos import api_receipt_detail
    return api_receipt_detail(receipt_id)

@core_bp.route("/api/pos/devices/<int:device_id>/printer", methods=["GET", "POST", "PUT"])
@login_required
@pos_role_required(UserRole.Admin, UserRole.SalesManager)
def pos_device_printer_settings_proxy(device_id):
    """Proxy route for /api/pos/devices/<id>/printer -> forwards to POS blueprint"""
    from blueprints.pos import api_device_printer_settings
    return api_device_printer_settings(device_id)


