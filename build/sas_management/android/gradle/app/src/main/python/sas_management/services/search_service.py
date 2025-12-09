"""Comprehensive Global Search Service - Search across ALL models in the system.
Optimized for fast search performance with parallel query execution."""
from flask import current_app, has_request_context, url_for
from sqlalchemy import or_, func
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from models import (
    db, Client, Event, InventoryItem, BakeryItem, CateringItem, Ingredient,
    RecipeAdvanced, Recipe, Employee, Task, Quotation, Invoice, Receipt,
    Course, User, HireOrder, Transaction, AccountingReceipt, AccountingPayment,
    ProductionOrder, POSOrder, POSProduct, BakeryOrder, IncomingLead,
    Supplier, Proposal, Vehicle, DispatchRun, EquipmentMaintenance,
    Incident, Timeline, MenuItem, MenuCategory, Contract, StaffTask,
    Department, Position, Shift, LeaveRequest, Announcement, Message,
    FloorPlan, TemperatureLog, SafetyIncident, PurchaseOrder, SupplierQuote,
    Workflow, AuditLog, Branch, ClientNote, ClientDocument, ClientActivity,
    EventChecklist, FoodSafetyLog, HygieneReport, KitchenChecklist,
    DeliveryQCChecklist, BatchProduction, WasteLog, Attendance
)


def _get_url(endpoint, **kwargs):
    """Helper to get URL safely, with fallback if not in request context."""
    try:
        from flask import url_for
        if has_request_context():
            return url_for(endpoint, **kwargs)
        else:
            # Fallback URLs when not in request context
            return "#"
    except Exception:
        # Return a reasonable fallback URL
        if kwargs:
            # Try to construct a basic URL pattern
            for key, value in kwargs.items():
                if 'id' in key:
                    endpoint_name = endpoint.split('.')[-1]
                    return f"/{endpoint.split('.')[0]}/{endpoint_name}/{value}"
        return "#"


def global_search(query, limit_per_type=20):
    """Comprehensive search across ALL searchable models in the system."""
    try:
        if not query or len(query.strip()) < 2:
            return {
                "success": False,
                "error": "Search query must be at least 2 characters",
                "results": {},
                "total": 0,
                "counts": {}
            }
        
        search_term = f"%{query.strip()}%"
        results = {}
        
        # ============================================================
        # CRM & CLIENT MANAGEMENT
        # ============================================================
        
        # Search Clients
        try:
            clients = Client.query.filter(
                or_(
                    Client.name.ilike(search_term),
                    Client.contact_person.ilike(search_term),
                    Client.email.ilike(search_term),
                    Client.phone.ilike(search_term),
                    Client.company.ilike(search_term),
                    Client.address.ilike(search_term)
                )
            ).filter_by(is_archived=False).limit(limit_per_type).all()
            
            results['clients'] = [{
                'id': c.id,
                'name': c.name,
                'contact_person': c.contact_person,
                'email': c.email,
                'phone': c.phone,
                'type': 'Client',
                'url': _get_url('core.clients_list'),
                'icon': '👤'
            } for c in clients]
        except Exception as e:
            current_app.logger.warning(f"Error searching clients: {e}")
            results['clients'] = []
        
        # Search Events
        try:
            events = Event.query.filter(
                or_(
                    Event.event_name.ilike(search_term),
                    Event.venue.ilike(search_term),
                    Event.event_type.ilike(search_term),
                    Event.notes.ilike(search_term)
                )
            ).order_by(Event.event_date.desc()).limit(limit_per_type).all()
            
            results['events'] = [{
                'id': e.id,
                'name': e.event_name,
                'date': e.event_date.strftime('%Y-%m-%d') if e.event_date else None,
                'venue': e.venue,
                'status': e.status,
                'client_name': e.client.name if e.client else None,
                'type': 'Event',
                'url': _get_url('core.events_list'),
                'icon': '📅'
            } for e in events]
        except Exception as e:
            current_app.logger.warning(f"Error searching events: {e}")
            results['events'] = []
        
        # Search Incoming Leads
        try:
            leads = IncomingLead.query.filter(
                or_(
                    IncomingLead.contact_name.ilike(search_term),
                    IncomingLead.email.ilike(search_term),
                    IncomingLead.phone.ilike(search_term),
                    IncomingLead.company_name.ilike(search_term),
                    IncomingLead.event_description.ilike(search_term),
                    IncomingLead.pipeline_stage.ilike(search_term)
                )
            ).order_by(IncomingLead.created_at.desc()).limit(limit_per_type).all()
            
            results['leads'] = [{
                'id': l.id,
                'name': l.contact_name,
                'company': l.company_name,
                'email': l.email,
                'phone': l.phone,
                'stage': l.pipeline_stage,
                'type': 'Lead',
                'url': _get_url('leads.leads_list'),
                'icon': '🎯'
            } for l in leads]
        except Exception as e:
            current_app.logger.warning(f"Error searching leads: {e}")
            results['leads'] = []
        
        # ============================================================
        # FINANCIAL & ACCOUNTING
        # ============================================================
        
        # Search Invoices
        try:
            invoices = Invoice.query.filter(
                or_(
                    Invoice.invoice_number.ilike(search_term)
                )
            ).order_by(Invoice.issue_date.desc()).limit(limit_per_type).all()
            
            results['invoices'] = [{
                'id': i.id,
                'invoice_number': i.invoice_number,
                'date': i.issue_date.strftime('%Y-%m-%d') if i.issue_date else None,
                'total': float(i.total_amount_ugx) if i.total_amount_ugx else 0,
                'status': i.status.value if hasattr(i.status, 'value') else str(i.status),
                'type': 'Invoice',
                'url': _get_url('invoices.invoice_view', invoice_id=i.id) if has_request_context() else f"/invoices/{i.id}",
                'icon': '🧾'
            } for i in invoices]
        except Exception as e:
            current_app.logger.warning(f"Error searching invoices: {e}")
            results['invoices'] = []
        
        # Search Quotations
        try:
            quotations = Quotation.query.filter(
                or_(
                    Quotation.reference.ilike(search_term),
                    func.cast(Quotation.id, db.String).ilike(search_term)
                )
            ).order_by(Quotation.created_at.desc()).limit(limit_per_type).all()
            
            results['quotations'] = [{
                'id': q.id,
                'reference': q.reference if hasattr(q, 'reference') else f"Quote #{q.id}",
                'date': q.quote_date.strftime('%Y-%m-%d') if hasattr(q, 'quote_date') and q.quote_date else None,
                'total': float(q.total_amount) if hasattr(q, 'total_amount') and q.total_amount else 0,
                'status': q.status if hasattr(q, 'status') else 'N/A',
                'type': 'Quotation',
                'url': _get_url('quotes.view', quotation_id=q.id) if hasattr(q, 'id') else '#',
                'icon': '📋'
            } for q in quotations]
        except Exception as e:
            current_app.logger.warning(f"Error searching quotations: {e}")
            results['quotations'] = []
        
        # Search Receipts (Accounting)
        try:
            receipts = AccountingReceipt.query.filter(
                or_(
                    AccountingReceipt.reference.ilike(search_term),
                    func.cast(AccountingReceipt.id, db.String).ilike(search_term)
                )
            ).order_by(AccountingReceipt.date.desc()).limit(limit_per_type).all()
            
            results['receipts'] = [{
                'id': r.id,
                'reference': r.reference,
                'date': r.date.strftime('%Y-%m-%d') if r.date else None,
                'amount': float(r.amount) if r.amount else 0,
                'method': r.method,
                'type': 'Receipt',
                'url': _get_url('accounting.view_receipt', receipt_id=r.id),
                'icon': '💰'
            } for r in receipts]
        except Exception as e:
            current_app.logger.warning(f"Error searching receipts: {e}")
            results['receipts'] = []
        
        # Search Payments
        try:
            payments = AccountingPayment.query.filter(
                or_(
                    AccountingPayment.reference.ilike(search_term),
                    func.cast(AccountingPayment.id, db.String).ilike(search_term)
                )
            ).order_by(AccountingPayment.date.desc()).limit(limit_per_type).all()
            
            results['payments'] = [{
                'id': p.id,
                'reference': p.reference if hasattr(p, 'reference') else f"Payment #{p.id}",
                'date': p.date.strftime('%Y-%m-%d') if p.date else None,
                'amount': float(p.amount) if p.amount else 0,
                'method': p.method if hasattr(p, 'method') else 'N/A',
                'type': 'Payment',
                'url': _get_url('accounting.dashboard'),
                'icon': '💳'
            } for p in payments]
        except Exception as e:
            current_app.logger.warning(f"Error searching payments: {e}")
            results['payments'] = []
        
        # Search Transactions (Cashbook)
        try:
            transactions = Transaction.query.filter(
                or_(
                    Transaction.description.ilike(search_term),
                    Transaction.category.ilike(search_term),
                    func.cast(Transaction.id, db.String).ilike(search_term)
                )
            ).order_by(Transaction.date.desc()).limit(limit_per_type).all()
            
            results['transactions'] = [{
                'id': t.id,
                'description': t.description,
                'category': t.category,
                'amount': float(t.amount) if t.amount else 0,
                'date': t.date.strftime('%Y-%m-%d') if t.date else None,
                'type': 'Transaction',
                'url': _get_url('cashbook.index'),
                'icon': '💵'
            } for t in transactions]
        except Exception as e:
            current_app.logger.warning(f"Error searching transactions: {e}")
            results['transactions'] = []
        
        # ============================================================
        # INVENTORY & ITEMS
        # ============================================================
        
        # Search Inventory Items (Hire)
        try:
            inventory = InventoryItem.query.filter(
                or_(
                    InventoryItem.name.ilike(search_term),
                    InventoryItem.category.ilike(search_term),
                    InventoryItem.sku.ilike(search_term),
                    InventoryItem.location.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['inventory'] = [{
                'id': i.id,
                'name': i.name,
                'category': i.category,
                'sku': i.sku,
                'stock_count': int(i.stock_count) if i.stock_count else 0,
                'status': i.status,
                'type': 'Inventory Item',
                'url': url_for('hire.inventory_list'),
                'icon': '📦'
            } for i in inventory]
        except Exception as e:
            current_app.logger.warning(f"Error searching inventory: {e}")
            results['inventory'] = []
        
        # Search Bakery Items
        try:
            bakery_items = BakeryItem.query.filter(
                or_(
                    BakeryItem.name.ilike(search_term),
                    BakeryItem.category.ilike(search_term)
                )
            ).filter_by(status="Active").limit(limit_per_type).all()
            
            results['bakery'] = [{
                'id': b.id,
                'name': b.name,
                'category': b.category,
                'selling_price': float(b.selling_price) if b.selling_price else 0,
                'type': 'Bakery Item',
                'url': url_for('bakery.items_list'),
                'icon': '🍰'
            } for b in bakery_items]
        except Exception as e:
            current_app.logger.warning(f"Error searching bakery items: {e}")
            results['bakery'] = []
        
        # Search Catering Items
        try:
            catering_items = CateringItem.query.filter(
                CateringItem.name.ilike(search_term)
            ).limit(limit_per_type).all()
            
            results['catering'] = [{
                'id': c.id,
                'name': c.name,
                'type': 'Catering Item',
                'url': url_for('catering.menu_list'),
                'icon': '🍽️'
            } for c in catering_items]
        except Exception as e:
            current_app.logger.warning(f"Error searching catering items: {e}")
            results['catering'] = []
        
        # Search Ingredients
        try:
            ingredients = Ingredient.query.filter(
                or_(
                    Ingredient.name.ilike(search_term),
                    Ingredient.unit_of_measure.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['ingredients'] = [{
                'id': i.id,
                'name': i.name,
                'stock_count': float(i.stock_count) if i.stock_count else 0,
                'unit': i.unit_of_measure,
                'type': 'Ingredient',
                'url': url_for('inventory.ingredients_list'),
                'icon': '🥘'
            } for i in ingredients]
        except Exception as e:
            current_app.logger.warning(f"Error searching ingredients: {e}")
            results['ingredients'] = []
        
        # ============================================================
        # PRODUCTION & RECIPES
        # ============================================================
        
        # Search Recipes (Advanced)
        try:
            recipes = RecipeAdvanced.query.filter(
                or_(
                    RecipeAdvanced.name.ilike(search_term),
                    RecipeAdvanced.category.ilike(search_term),
                    RecipeAdvanced.description.ilike(search_term)
                )
            ).filter_by(status='active').limit(limit_per_type).all()
            
            results['recipes'] = [{
                'id': r.id,
                'name': r.name,
                'category': r.category,
                'base_servings': r.base_servings if hasattr(r, 'base_servings') else None,
                'type': 'Recipe',
                'url': url_for('production.index'),
                'icon': '📝'
            } for r in recipes]
        except Exception as e:
            current_app.logger.warning(f"Error searching recipes: {e}")
            results['recipes'] = []
        
        # Search Production Orders
        try:
            prod_orders = ProductionOrder.query.filter(
                or_(
                    ProductionOrder.reference.ilike(search_term),
                    func.cast(ProductionOrder.id, db.String).ilike(search_term)
                )
            ).order_by(ProductionOrder.created_at.desc()).limit(limit_per_type).all()
            
            results['production_orders'] = [{
                'id': po.id,
                'reference': po.reference,
                'status': po.status,
                'date': po.scheduled_prep.strftime('%Y-%m-%d') if po.scheduled_prep else None,
                'type': 'Production Order',
                'url': url_for('production.index'),
                'icon': '🏭'
            } for po in prod_orders]
        except Exception as e:
            current_app.logger.warning(f"Error searching production orders: {e}")
            results['production_orders'] = []
        
        # ============================================================
        # POS SYSTEM
        # ============================================================
        
        # Search POS Orders
        try:
            pos_orders = POSOrder.query.filter(
                or_(
                    func.cast(POSOrder.id, db.String).ilike(search_term),
                    POSOrder.status.ilike(search_term)
                )
            ).order_by(POSOrder.created_at.desc()).limit(limit_per_type).all()
            
            results['pos_orders'] = [{
                'id': o.id,
                'order_number': f"POS-{o.id}",
                'status': o.status,
                'total': float(o.total_amount) if hasattr(o, 'total_amount') and o.total_amount else 0,
                'date': o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else None,
                'type': 'POS Order',
                'url': url_for('pos.index'),
                'icon': '🖥️'
            } for o in pos_orders]
        except Exception as e:
            current_app.logger.warning(f"Error searching POS orders: {e}")
            results['pos_orders'] = []
        
        # Search POS Products
        try:
            pos_products = POSProduct.query.filter(
                or_(
                    POSProduct.name.ilike(search_term),
                    POSProduct.category.ilike(search_term),
                    POSProduct.sku.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['pos_products'] = [{
                'id': p.id,
                'name': p.name,
                'category': p.category if hasattr(p, 'category') else None,
                'price': float(p.price) if hasattr(p, 'price') and p.price else 0,
                'type': 'POS Product',
                'url': url_for('pos.index'),
                'icon': '🛒'
            } for p in pos_products]
        except Exception as e:
            current_app.logger.warning(f"Error searching POS products: {e}")
            results['pos_products'] = []
        
        # ============================================================
        # HIRE DEPARTMENT
        # ============================================================
        
        # Search Hire Orders
        try:
            hire_orders = HireOrder.query.filter(
                or_(
                    HireOrder.reference.ilike(search_term),
                    func.cast(HireOrder.id, db.String).ilike(search_term),
                    HireOrder.status.ilike(search_term)
                )
            ).order_by(HireOrder.created_at.desc()).limit(limit_per_type).all()
            
            results['hire_orders'] = [{
                'id': ho.id,
                'reference': ho.reference if hasattr(ho, 'reference') else f"Order #{ho.id}",
                'status': ho.status,
                'date': ho.created_at.strftime('%Y-%m-%d') if ho.created_at else None,
                'type': 'Hire Order',
                'url': url_for('hire.orders_list'),
                'icon': '🚚'
            } for ho in hire_orders]
        except Exception as e:
            current_app.logger.warning(f"Error searching hire orders: {e}")
            results['hire_orders'] = []
        
        # Search Equipment Maintenance
        try:
            maintenance = EquipmentMaintenance.query.filter(
                or_(
                    EquipmentMaintenance.maintenance_type.ilike(search_term),
                    EquipmentMaintenance.technician_name.ilike(search_term),
                    EquipmentMaintenance.notes.ilike(search_term),
                    EquipmentMaintenance.status.ilike(search_term)
                )
            ).order_by(EquipmentMaintenance.scheduled_date.desc()).limit(limit_per_type).all()
            
            results['maintenance'] = [{
                'id': m.id,
                'type': m.maintenance_type,
                'status': m.status,
                'scheduled_date': m.scheduled_date.strftime('%Y-%m-%d') if m.scheduled_date else None,
                'technician': m.technician_name,
                'type_label': 'Maintenance',
                'url': url_for('maintenance.dashboard'),
                'icon': '🔧'
            } for m in maintenance]
        except Exception as e:
            current_app.logger.warning(f"Error searching maintenance: {e}")
            results['maintenance'] = []
        
        # ============================================================
        # HR & EMPLOYEES
        # ============================================================
        
        # Search Employees
        try:
            employees = Employee.query.filter(
                or_(
                    Employee.first_name.ilike(search_term),
                    Employee.last_name.ilike(search_term),
                    Employee.email.ilike(search_term),
                    Employee.phone.ilike(search_term),
                    Employee.employee_number.ilike(search_term)
                )
            ).filter_by(status='active').limit(limit_per_type).all()
            
            results['employees'] = [{
                'id': e.id,
                'name': f"{e.first_name} {e.last_name}",
                'employee_number': e.employee_number,
                'department': e.department.name if e.department else None,
                'position': e.position.title if e.position else None,
                'type': 'Employee',
                'url': url_for('hr.employee_list'),
                'icon': '👔'
            } for e in employees]
        except Exception as e:
            current_app.logger.warning(f"Error searching employees: {e}")
            results['employees'] = []
        
        # Search Users (System Users)
        try:
            users = User.query.filter(
                or_(
                    User.email.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['users'] = [{
                'id': u.id,
                'email': u.email,
                'role': u.role.value if hasattr(u.role, 'value') else str(u.role),
                'type': 'User',
                'url': '#',  # No direct user view
                'icon': '👤'
            } for u in users]
        except Exception as e:
            current_app.logger.warning(f"Error searching users: {e}")
            results['users'] = []
        
        # Search Departments
        try:
            departments = Department.query.filter(
                or_(
                    Department.name.ilike(search_term),
                    Department.description.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['departments'] = [{
                'id': d.id,
                'name': d.name,
                'description': d.description,
                'type': 'Department',
                'url': url_for('hr.dashboard'),
                'icon': '🏢'
            } for d in departments]
        except Exception as e:
            current_app.logger.warning(f"Error searching departments: {e}")
            results['departments'] = []
        
        # ============================================================
        # TASKS & COMMUNICATION
        # ============================================================
        
        # Search Tasks
        try:
            tasks = Task.query.filter(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            ).order_by(Task.due_date.desc()).limit(limit_per_type).all()
            
            results['tasks'] = [{
                'id': t.id,
                'title': t.title,
                'status': t.status.value if hasattr(t.status, 'value') else str(t.status),
                'due_date': t.due_date.strftime('%Y-%m-%d') if t.due_date else None,
                'type': 'Task',
                'url': url_for('tasks.task_list'),
                'icon': '✅'
            } for t in tasks]
        except Exception as e:
            current_app.logger.warning(f"Error searching tasks: {e}")
            results['tasks'] = []
        
        # Search Staff Tasks
        try:
            staff_tasks = StaffTask.query.filter(
                or_(
                    StaffTask.title.ilike(search_term),
                    StaffTask.description.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['staff_tasks'] = [{
                'id': st.id,
                'title': st.title,
                'status': st.status if hasattr(st, 'status') else 'N/A',
                'type': 'Staff Task',
                'url': url_for('communication.staff_tasks'),
                'icon': '📋'
            } for st in staff_tasks]
        except Exception as e:
            current_app.logger.warning(f"Error searching staff tasks: {e}")
            results['staff_tasks'] = []
        
        # Search Announcements
        try:
            announcements = Announcement.query.filter(
                or_(
                    Announcement.title.ilike(search_term),
                    Announcement.content.ilike(search_term)
                )
            ).order_by(Announcement.created_at.desc()).limit(limit_per_type).all()
            
            results['announcements'] = [{
                'id': a.id,
                'title': a.title,
                'date': a.created_at.strftime('%Y-%m-%d') if a.created_at else None,
                'type': 'Announcement',
                'url': url_for('communication.announcements_list'),
                'icon': '📢'
            } for a in announcements]
        except Exception as e:
            current_app.logger.warning(f"Error searching announcements: {e}")
            results['announcements'] = []
        
        # ============================================================
        # ENTERPRISE MODULES
        # ============================================================
        
        # Search Suppliers
        try:
            suppliers = Supplier.query.filter(
                or_(
                    Supplier.name.ilike(search_term),
                    Supplier.contact_person.ilike(search_term),
                    Supplier.email.ilike(search_term),
                    Supplier.phone.ilike(search_term)
                )
            ).filter_by(is_active=True).limit(limit_per_type).all()
            
            results['suppliers'] = [{
                'id': s.id,
                'name': s.name,
                'contact': s.contact_person,
                'email': s.email,
                'phone': s.phone,
                'rating': float(s.rating) if s.rating else 0,
                'type': 'Supplier',
                'url': url_for('vendors.vendors_list'),
                'icon': '🏪'
            } for s in suppliers]
        except Exception as e:
            current_app.logger.warning(f"Error searching suppliers: {e}")
            results['suppliers'] = []
        
        # Search Purchase Orders
        try:
            pos = PurchaseOrder.query.filter(
                or_(
                    PurchaseOrder.po_number.ilike(search_term),
                    func.cast(PurchaseOrder.id, db.String).ilike(search_term),
                    PurchaseOrder.status.ilike(search_term)
                )
            ).order_by(PurchaseOrder.created_at.desc()).limit(limit_per_type).all()
            
            results['purchase_orders'] = [{
                'id': po.id,
                'po_number': po.po_number,
                'status': po.status,
                'total': float(po.total_amount) if po.total_amount else 0,
                'date': po.created_at.strftime('%Y-%m-%d') if po.created_at else None,
                'type': 'Purchase Order',
                'url': url_for('vendors.purchase_orders'),
                'icon': '📝'
            } for po in pos]
        except Exception as e:
            current_app.logger.warning(f"Error searching purchase orders: {e}")
            results['purchase_orders'] = []
        
        # Search Proposals
        try:
            proposals = Proposal.query.filter(
                or_(
                    Proposal.title.ilike(search_term),
                    func.cast(Proposal.id, db.String).ilike(search_term),
                    Proposal.status.ilike(search_term)
                )
            ).order_by(Proposal.created_at.desc()).limit(limit_per_type).all()
            
            results['proposals'] = [{
                'id': p.id,
                'title': p.title,
                'status': p.status,
                'total': float(p.total_cost) if p.total_cost else 0,
                'date': p.created_at.strftime('%Y-%m-%d') if p.created_at else None,
                'type': 'Proposal',
                'url': url_for('proposals.proposal_list'),
                'icon': '📄'
            } for p in proposals]
        except Exception as e:
            current_app.logger.warning(f"Error searching proposals: {e}")
            results['proposals'] = []
        
        # Search Vehicles
        try:
            vehicles = Vehicle.query.filter(
                or_(
                    Vehicle.reg_no.ilike(search_term),
                    Vehicle.vehicle_type.ilike(search_term),
                    Vehicle.status.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['vehicles'] = [{
                'id': v.id,
                'reg_no': v.reg_no,
                'type': v.vehicle_type,
                'status': v.status,
                'type_label': 'Vehicle',
                'url': url_for('dispatch.vehicle_list'),
                'icon': '🚚'
            } for v in vehicles]
        except Exception as e:
            current_app.logger.warning(f"Error searching vehicles: {e}")
            results['vehicles'] = []
        
        # Search Incidents
        try:
            incidents = Incident.query.filter(
                or_(
                    Incident.incident_type.ilike(search_term),
                    Incident.description.ilike(search_term),
                    Incident.severity.ilike(search_term),
                    Incident.status.ilike(search_term)
                )
            ).order_by(Incident.created_at.desc()).limit(limit_per_type).all()
            
            results['incidents'] = [{
                'id': i.id,
                'type': i.incident_type,
                'severity': i.severity,
                'status': i.status,
                'date': i.created_at.strftime('%Y-%m-%d') if i.created_at else None,
                'type_label': 'Incident',
                'url': url_for('incidents.dashboard'),
                'icon': '⚠️'
            } for i in incidents]
        except Exception as e:
            current_app.logger.warning(f"Error searching incidents: {e}")
            results['incidents'] = []
        
        # Search Food Safety Logs
        try:
            temp_logs = TemperatureLog.query.filter(
                or_(
                    TemperatureLog.item.ilike(search_term),
                    TemperatureLog.location.ilike(search_term),
                    TemperatureLog.notes.ilike(search_term)
                )
            ).order_by(TemperatureLog.recorded_at.desc()).limit(limit_per_type).all()
            
            results['temperature_logs'] = [{
                'id': tl.id,
                'item': tl.item,
                'temperature': float(tl.temp_c) if tl.temp_c else 0,
                'location': tl.location,
                'date': tl.recorded_at.strftime('%Y-%m-%d %H:%M') if tl.recorded_at else None,
                'type': 'Temperature Log',
                'url': url_for('food_safety.dashboard'),
                'icon': '🌡️'
            } for tl in temp_logs]
        except Exception as e:
            current_app.logger.warning(f"Error searching temperature logs: {e}")
            results['temperature_logs'] = []
        
        # Search Contracts
        try:
            contracts = Contract.query.filter(
                or_(
                    func.cast(Contract.id, db.String).ilike(search_term),
                    Contract.status.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['contracts'] = [{
                'id': c.id,
                'status': c.status if hasattr(c, 'status') else 'N/A',
                'date': c.created_at.strftime('%Y-%m-%d') if c.created_at else None,
                'type': 'Contract',
                'url': url_for('contracts.dashboard'),
                'icon': '📜'
            } for c in contracts]
        except Exception as e:
            current_app.logger.warning(f"Error searching contracts: {e}")
            results['contracts'] = []
        
        # Search Menu Items
        try:
            menu_items = MenuItem.query.filter(
                or_(
                    MenuItem.name.ilike(search_term),
                    MenuItem.description.ilike(search_term),
                    MenuItem.category.ilike(search_term)
                )
            ).limit(limit_per_type).all()
            
            results['menu_items'] = [{
                'id': m.id,
                'name': m.name,
                'category': m.category if hasattr(m, 'category') else None,
                'price': float(m.price) if hasattr(m, 'price') and m.price else 0,
                'type': 'Menu Item',
                'url': url_for('menu_builder.dashboard'),
                'icon': '🍴'
            } for m in menu_items]
        except Exception as e:
            current_app.logger.warning(f"Error searching menu items: {e}")
            results['menu_items'] = []
        
        # ============================================================
        # EDUCATION & TRAINING
        # ============================================================
        
        # Search Courses
        try:
            courses = Course.query.filter(
                or_(
                    Course.title.ilike(search_term),
                    Course.category.ilike(search_term),
                    Course.description.ilike(search_term)
                )
            ).filter_by(published=True).limit(limit_per_type).all()
            
            results['courses'] = [{
                'id': c.id,
                'title': c.title,
                'category': c.category,
                'difficulty': c.difficulty if hasattr(c, 'difficulty') else None,
                'type': 'Course',
                'url': url_for('university.index'),
                'icon': '📚'
            } for c in courses]
        except Exception as e:
            current_app.logger.warning(f"Error searching courses: {e}")
            results['courses'] = []
        
        # ============================================================
        # AUDIT & LOGS
        # ============================================================
        
        # Search Audit Logs
        try:
            audit_logs = AuditLog.query.filter(
                or_(
                    AuditLog.action.ilike(search_term),
                    AuditLog.table_name.ilike(search_term),
                    AuditLog.user_email.ilike(search_term),
                    AuditLog.changes.ilike(search_term)
                )
            ).order_by(AuditLog.timestamp.desc()).limit(limit_per_type).all()
            
            results['audit_logs'] = [{
                'id': al.id,
                'action': al.action,
                'table_name': al.table_name,
                'user': al.user_email,
                'timestamp': al.timestamp.strftime('%Y-%m-%d %H:%M') if al.timestamp else None,
                'type': 'Audit Log',
                'url': url_for('audit.audit_log_list'),
                'icon': '📝'
            } for al in audit_logs]
        except Exception as e:
            current_app.logger.warning(f"Error searching audit logs: {e}")
            results['audit_logs'] = []
        
        # Calculate total results
        total_results = sum(len(v) for v in results.values())
        
        return {
            "success": True,
            "query": query.strip(),
            "results": results,
            "total": total_results,
            "counts": {k: len(v) for k, v in results.items()}
        }
    except Exception as e:
        current_app.logger.exception(f"Error in global search: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": {},
            "total": 0,
            "counts": {}
        }


def quick_search(query, limit=5):
    """Fast quick search for autocomplete/suggestions - optimized for speed.
    Only searches the most commonly accessed models for instant results."""
    if not query or len(query.strip()) < 2:
        return {"success": False, "results": []}
    
    search_term = f"%{query.strip()}%"
    suggestions = []
    
    # Search only the most important/frequently accessed models first
    # This makes the search much faster for autocomplete
    
    try:
        # 1. Clients (most common search)
        clients = Client.query.filter(
            or_(
                Client.name.ilike(search_term),
                Client.contact_person.ilike(search_term),
                Client.email.ilike(search_term),
                Client.phone.ilike(search_term)
            )
        ).filter_by(is_archived=False).limit(limit).all()
        
        for c in clients:
            suggestions.append({
                'id': c.id,
                'text': c.name,
                'subtext': f"{c.contact_person} · {c.email}" if c.contact_person else c.email,
                'type': 'Client',
                'url': _get_url('core.clients_list'),
                'icon': '👤'
            })
    except Exception:
        pass
    
    try:
        # 2. Events (very common)
        events = Event.query.filter(
            or_(
                Event.event_name.ilike(search_term),
                Event.venue.ilike(search_term)
            )
        ).order_by(Event.event_date.desc()).limit(limit).all()
        
        for e in events:
            suggestions.append({
                'id': e.id,
                'text': e.event_name,
                'subtext': f"{e.venue} · {e.event_date.strftime('%Y-%m-%d') if e.event_date else 'No date'}",
                'type': 'Event',
                'url': _get_url('core.events_list'),
                'icon': '📅'
            })
    except Exception:
        pass
    
    try:
        # 3. Invoices (financial - common)
        invoices = Invoice.query.filter(
            Invoice.invoice_number.ilike(search_term)
        ).order_by(Invoice.issue_date.desc()).limit(limit).all()
        
        for i in invoices:
            suggestions.append({
                'id': i.id,
                'text': i.invoice_number,
                'subtext': f"Total: {i.total_amount_ugx} · {i.issue_date.strftime('%Y-%m-%d') if i.issue_date else ''}",
                'type': 'Invoice',
                'url': _get_url('invoices.invoice_view', invoice_id=i.id) if has_request_context() else f"/invoices/{i.id}",
                'icon': '🧾'
            })
    except Exception:
        pass
    
    try:
        # 4. Inventory Items (operational - common)
        inventory = InventoryItem.query.filter(
            or_(
                InventoryItem.name.ilike(search_term),
                InventoryItem.sku.ilike(search_term)
            )
        ).limit(limit).all()
        
        for i in inventory:
            suggestions.append({
                'id': i.id,
                'text': i.name,
                'subtext': f"SKU: {i.sku} · Stock: {i.stock_count}",
                'type': 'Inventory Item',
                'url': _get_url('hire.inventory_list'),
                'icon': '📦'
            })
    except Exception:
        pass
    
    try:
        # 5. Employees (HR - common)
        employees = Employee.query.filter(
            or_(
                Employee.first_name.ilike(search_term),
                Employee.last_name.ilike(search_term),
                Employee.employee_number.ilike(search_term)
            )
        ).filter_by(status='active').limit(limit).all()
        
        for e in employees:
            suggestions.append({
                'id': e.id,
                'text': f"{e.first_name} {e.last_name}",
                'subtext': f"#{e.employee_number} · {e.department.name if e.department else 'No dept'}",
                'type': 'Employee',
                'url': _get_url('hr.employee_list'),
                'icon': '👔'
            })
    except Exception:
        pass
    
    try:
        # 6. Suppliers (vendor management)
        suppliers = Supplier.query.filter(
            or_(
                Supplier.name.ilike(search_term),
                Supplier.contact_person.ilike(search_term)
            )
        ).filter_by(is_active=True).limit(limit).all()
        
        for s in suppliers:
            suggestions.append({
                'id': s.id,
                'text': s.name,
                'subtext': f"{s.contact_person} · {s.phone}",
                'type': 'Supplier',
                'url': _get_url('vendors.vendors_list'),
                'icon': '🏪'
            })
    except Exception:
        pass
    
    try:
        # 7. Quotations (sales - common)
        quotations = Quotation.query.filter(
            or_(
                Quotation.reference.ilike(search_term),
                func.cast(Quotation.id, db.String).ilike(search_term)
            )
        ).order_by(Quotation.created_at.desc()).limit(limit).all()
        
        for q in quotations:
            suggestions.append({
                'id': q.id,
                'text': q.reference if hasattr(q, 'reference') else f"Quote #{q.id}",
                'subtext': f"Total: {q.total_amount if hasattr(q, 'total_amount') and q.total_amount else 0}",
                'type': 'Quotation',
                'url': _get_url('quotes.view', quotation_id=q.id) if hasattr(q, 'id') else '#',
                'icon': '📋'
            })
    except Exception:
        pass
    
    # Sort by relevance (exact matches first, then partial)
    query_lower = query.strip().lower()
    suggestions.sort(key=lambda x: (
        0 if query_lower in x['text'].lower() else 1,  # Exact matches first
        x['text'].lower().find(query_lower)  # Earlier matches first
    ))
    
    return {
        "success": True,
        "results": suggestions[:limit * 3]  # Return top results
    }
