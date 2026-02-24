#!/usr/bin/env python3
"""
COMPREHENSIVE MODULE SEEDING - Populates ALL modules with sample data
This script ensures every module has data for proper dashboard display.
"""
import os
import sys
os.environ["SECRET_KEY"] = "sas-management-system-secret-key-2024-production"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import (
    db, User, Client, Event, IncomingLead, Invoice, InvoiceStatus,
    Task, TaskStatus, InventoryItem, Announcement, UserRole,
    MenuCategory, MenuItem, MenuPackage, BakeryItem, BakeryOrder,
    ProductionOrder, ProductionBudget, ProductionBudgetStatus,
    Employee, Department, POSProduct, POSOrder, Quotation, QuotationLine,
    CateringItem, Recipe, Ingredient, Supplier, PurchaseOrder
)
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from decimal import Decimal

app = create_app()

def seed_all_modules():
    """Comprehensive seeding of ALL modules."""
    with app.app_context():
        print("=" * 80)
        print("COMPREHENSIVE MODULE SEEDING - ALL MODULES")
        print("=" * 80)
        print()
        
        # 1. ADMIN USER
        print("[1/15] Ensuring admin user...")
        admin = User.query.filter_by(email="admin@sas.com").first()
        if not admin:
            admin = User(
                email="admin@sas.com",
                username="admin",
                role=UserRole.Admin,
                is_admin=True,
                first_login=False,
                must_change_password=False,
                force_password_change=False
            )
            admin.set_password("password")
            db.session.add(admin)
            db.session.commit()
            print("  [OK] Admin user created")
        else:
            admin.set_password("password")
            admin.first_login = False
            admin.must_change_password = False
            admin.force_password_change = False
            db.session.commit()
            print("  [OK] Admin user exists, password reset")
        
        # 2. CLIENTS (CRM Module) - Force create if less than 10
        print("\n[2/15] Seeding Clients (CRM)...")
        if Client.query.count() < 10:
            client_data = [
                {"name": "Elite Weddings Ltd.", "email": "events@eliteweddings.com", "phone": "+256 700 111 222", "contact_person": "Sara Lee"},
                {"name": "Corporate Gatherings Co.", "email": "info@corpgatherings.com", "phone": "+256 700 333 444", "contact_person": "Daniel O."},
                {"name": "Grand Hotel", "email": "catering@grandhotel.com", "phone": "+256 700 555 666", "contact_person": "Robert Johnson"},
                {"name": "ABC Corporation", "email": "events@abc-corp.com", "phone": "+256 700 777 888", "contact_person": "John Doe"},
                {"name": "Tech Startup Inc", "email": "contact@techstartup.com", "phone": "+256 700 999 000", "contact_person": "Jane Smith"},
                {"name": "University Events", "email": "events@university.ac.ug", "phone": "+256 700 111 333", "contact_person": "Mary Johnson"},
                {"name": "Charity Foundation", "email": "info@charity.org", "phone": "+256 700 222 444", "contact_person": "David Brown"},
                {"name": "Wedding Planners Ltd", "email": "contact@weddingplanners.com", "phone": "+256 700 333 555", "contact_person": "Sarah Wilson"},
                {"name": "Corporate Events Hub", "email": "info@corpevents.com", "phone": "+256 700 444 666", "contact_person": "Michael Davis"},
                {"name": "Luxury Catering Co", "email": "events@luxurycatering.com", "phone": "+256 700 555 777", "contact_person": "Emily Taylor"},
            ]
            clients_created = 0
            for c_data in client_data:
                if not Client.query.filter_by(email=c_data["email"]).first():
                    client = Client(**c_data)
                    db.session.add(client)
                    clients_created += 1
            db.session.commit()
            print(f"  [OK] Created {clients_created} clients (Total: {Client.query.count()})")
        else:
            print(f"  [OK] Clients already exist (Total: {Client.query.count()})")
        
        # 3. EVENTS (Events Module)
        print("\n[3/15] Seeding Events...")
        clients = Client.query.all()
        if clients:
            event_data = [
                {"title": "Corporate Annual Dinner", "status": "Confirmed", "quoted_value": 5000000, "guest_count": 200, "days_offset": 7},
                {"title": "Wedding Reception", "status": "Confirmed", "quoted_value": 8000000, "guest_count": 150, "days_offset": 10},
                {"title": "Product Launch Event", "status": "Draft", "quoted_value": 3000000, "guest_count": 100, "days_offset": 14},
                {"title": "Birthday Celebration", "status": "Confirmed", "quoted_value": 2000000, "guest_count": 50, "days_offset": 5},
                {"title": "Charity Gala", "status": "Confirmed", "quoted_value": 6000000, "guest_count": 300, "days_offset": 12},
                {"title": "Corporate Training", "status": "Confirmed", "quoted_value": 1500000, "guest_count": 40, "days_offset": 3},
                {"title": "Kukyala", "status": "Confirmed", "quoted_value": 4000000, "guest_count": 120, "days_offset": 8},
                {"title": "COP Lunch", "status": "Confirmed", "quoted_value": 2500000, "guest_count": 80, "days_offset": 6},
                {"title": "Graduation Party", "status": "Draft", "quoted_value": 3500000, "guest_count": 90, "days_offset": 15},
                {"title": "Anniversary Celebration", "status": "Confirmed", "quoted_value": 4500000, "guest_count": 110, "days_offset": 9},
            ]
            events_created = 0
            for i, e_data in enumerate(event_data):
                if not Event.query.filter_by(title=e_data["title"]).first():
                    client = clients[i % len(clients)]
                    event = Event(
                        title=e_data["title"],
                        client_id=client.id,
                        client_name=client.name,
                        client_email=client.email,
                        client_phone=client.phone,
                        status=e_data["status"],
                        quoted_value=Decimal(str(e_data["quoted_value"])),
                        guest_count=e_data["guest_count"],
                        date=date.today() + timedelta(days=e_data["days_offset"]),
                        event_date=date.today() + timedelta(days=e_data["days_offset"]),
                    )
                    db.session.add(event)
                    events_created += 1
            db.session.commit()
            print(f"  [OK] Created {events_created} events (Total: {Event.query.count()})")
        
        # 4. CRM PIPELINE LEADS
        print("\n[4/15] Seeding CRM Pipeline Leads...")
        leads_data = [
            {"client_name": "Tech Startup Inc", "email": "contact@techstartup.com", "phone": "+256 700 999 000", "pipeline_stage": "New Lead", "estimated_value": 4000000},
            {"client_name": "University Event", "email": "events@university.ac.ug", "phone": "+256 700 111 333", "pipeline_stage": "Qualified", "estimated_value": 6000000},
            {"client_name": "Charity Gala", "email": "info@charity.org", "phone": "+256 700 222 444", "pipeline_stage": "Proposal Sent", "estimated_value": 5000000},
            {"client_name": "Corporate Summit", "email": "summit@corp.com", "phone": "+256 700 333 555", "pipeline_stage": "Negotiation", "estimated_value": 7000000},
            {"client_name": "Wedding Planning", "email": "wedding@planners.com", "phone": "+256 700 444 666", "pipeline_stage": "Awaiting Payment", "estimated_value": 5500000},
        ]
        leads_created = 0
        for lead_data in leads_data:
            if not IncomingLead.query.filter_by(email=lead_data["email"]).first():
                lead = IncomingLead(
                    client_name=lead_data["client_name"],
                    email=lead_data["email"],
                    phone=lead_data["phone"],
                    pipeline_stage=lead_data["pipeline_stage"],
                    estimated_value=Decimal(str(lead_data["estimated_value"])),
                    timestamp=datetime.utcnow() - timedelta(days=leads_created),
                )
                db.session.add(lead)
                leads_created += 1
        db.session.commit()
        print(f"  [OK] Created {leads_created} leads (Total: {IncomingLead.query.count()})")
        
        # 5. INVOICES (Accounting Module)
        print("\n[5/15] Seeding Invoices (Accounting)...")
        events = Event.query.filter_by(status="Confirmed").all()
        invoices_created = 0
        for i, event in enumerate(events[:10]):
            if not Invoice.query.filter_by(event_id=event.id).first():
                invoice = Invoice(
                    client_id=event.client_id,
                    event_id=event.id,
                    invoice_number=f"INV-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    total_amount_ugx=event.quoted_value,
                    status=InvoiceStatus.Issued if i % 2 == 0 else InvoiceStatus.Paid,
                    issue_date=date.today() - timedelta(days=5 + i),
                    due_date=date.today() + timedelta(days=25 - i),
                )
                db.session.add(invoice)
                invoices_created += 1
        db.session.commit()
        print(f"  [OK] Created {invoices_created} invoices (Total: {Invoice.query.count()})")
        
        # 6. TASKS
        print("\n[6/15] Seeding Tasks...")
        tasks_data = [
            {"title": "Prepare menu for Corporate Dinner", "status": TaskStatus.Pending, "due_date": 2},
            {"title": "Order ingredients for Wedding", "status": TaskStatus.InProgress, "due_date": 1},
            {"title": "Finalize event timeline", "status": TaskStatus.Pending, "due_date": 3},
            {"title": "Confirm guest count", "status": TaskStatus.Pending, "due_date": 4},
            {"title": "Setup equipment", "status": TaskStatus.InProgress, "due_date": 1},
        ]
        tasks_created = 0
        for task_data in tasks_data:
            if not Task.query.filter_by(title=task_data["title"]).first():
                task = Task(
                    title=task_data["title"],
                    assigned_user_id=admin.id,
                    status=task_data["status"],
                    due_date=date.today() + timedelta(days=task_data["due_date"]),
                    created_at=datetime.utcnow(),
                )
                db.session.add(task)
                tasks_created += 1
        db.session.commit()
        print(f"  [OK] Created {tasks_created} tasks (Total: {Task.query.count()})")
        
        # 7. INVENTORY ITEMS (Hire/Inventory Module)
        print("\n[7/15] Seeding Inventory Items...")
        inventory_data = [
            {"name": "Chairs", "stock_count": 500, "unit": "pieces", "status": "Available"},
            {"name": "Tables", "stock_count": 50, "unit": "pieces", "status": "Available"},
            {"name": "Table Cloths", "stock_count": 8, "unit": "pieces", "status": "Low Stock"},
            {"name": "Tents", "stock_count": 15, "unit": "pieces", "status": "Available"},
            {"name": "Sound System", "stock_count": 5, "unit": "sets", "status": "Low Stock"},
            {"name": "Projector", "stock_count": 3, "unit": "units", "status": "Low Stock"},
        ]
        inventory_created = 0
        for inv_data in inventory_data:
            if not InventoryItem.query.filter_by(name=inv_data["name"]).first():
                item = InventoryItem(**inv_data)
                db.session.add(item)
                inventory_created += 1
        db.session.commit()
        print(f"  [OK] Created {inventory_created} inventory items (Total: {InventoryItem.query.count()})")
        
        # 8. MENU CATEGORIES & ITEMS (Menu Builder Module) - Force create
        print("\n[8/15] Seeding Menu Categories & Items...")
        menu_categories = [
            {"name": "Main Courses", "description": "Hearty main dishes"},
            {"name": "Appetizers", "description": "Starter dishes"},
            {"name": "Desserts", "description": "Sweet treats"},
            {"name": "Beverages", "description": "Drinks and refreshments"},
        ]
        menu_items_data = [
            {"name": "Grilled Chicken", "category": "Main Courses", "cost": 4500, "price": 8500},
            {"name": "Beef Steak", "category": "Main Courses", "cost": 6000, "price": 12000},
            {"name": "Fish Fillet", "category": "Main Courses", "cost": 5000, "price": 9500},
            {"name": "Spring Rolls", "category": "Appetizers", "cost": 2000, "price": 5000},
            {"name": "Chocolate Cake", "category": "Desserts", "cost": 2500, "price": 6000},
            {"name": "Fruit Salad", "category": "Desserts", "cost": 1800, "price": 4500},
        ]
        categories_created = 0
        items_created = 0
        for cat_data in menu_categories:
            cat = MenuCategory.query.filter_by(name=cat_data["name"]).first()
            if not cat:
                cat = MenuCategory(name=cat_data["name"], description=cat_data["description"], is_active=True)
                db.session.add(cat)
                db.session.flush()
                categories_created += 1
            else:
                cat = MenuCategory.query.filter_by(name=cat_data["name"]).first()
            for item_data in menu_items_data:
                if item_data["category"] == cat_data["name"]:
                    if not MenuItem.query.filter_by(name=item_data["name"]).first():
                        margin = ((item_data["price"] - item_data["cost"]) / item_data["price"]) * 100
                        item = MenuItem(
                            name=item_data["name"],
                            category_id=cat.id,
                            cost_per_portion=Decimal(str(item_data["cost"])),
                            selling_price=Decimal(str(item_data["price"])),
                            margin_percent=margin,
                            is_available=True
                        )
                        db.session.add(item)
                        items_created += 1
        db.session.commit()
        print(f"  [OK] Created {categories_created} categories, {items_created} menu items (Total Categories: {MenuCategory.query.count()}, Total Items: {MenuItem.query.count()})")
        
        # 9. BAKERY ITEMS (Bakery Module) - Force create
        print("\n[9/15] Seeding Bakery Items...")
        if BakeryItem.query.count() == 0:
            bakery_items_data = [
                {"name": "Chocolate Cake", "price": 15000, "cost": 8000},
                {"name": "Vanilla Cupcakes", "price": 5000, "cost": 2500},
                {"name": "Bread Loaf", "price": 3000, "cost": 1500},
                {"name": "Croissants", "price": 4000, "cost": 2000},
                {"name": "Apple Pie", "price": 6000, "cost": 3000},
                {"name": "Donuts", "price": 3500, "cost": 1800},
            ]
            bakery_created = 0
            for item_data in bakery_items_data:
                if not BakeryItem.query.filter_by(name=item_data["name"]).first():
                    item = BakeryItem(
                        name=item_data["name"],
                        selling_price=Decimal(str(item_data["price"])),
                        cost_per_unit=Decimal(str(item_data["cost"])),
                        is_available=True
                    )
                    db.session.add(item)
                    bakery_created += 1
            db.session.commit()
            print(f"  [OK] Created {bakery_created} bakery items (Total: {BakeryItem.query.count()})")
        else:
            print(f"  [OK] Bakery items already exist (Total: {BakeryItem.query.count()})")
        
        # 10. PRODUCTION ORDERS (Production Module) - Force create
        print("\n[10/15] Seeding Production Orders...")
        if ProductionOrder.query.count() == 0:
            production_orders_created = 0
            events = Event.query.filter_by(status="Confirmed").limit(5).all()
            for i, event in enumerate(events):
                order = ProductionOrder(
                    event_id=event.id,
                    order_number=f"PROD-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    status="Pending",
                    target_date=event.date,
                )
                db.session.add(order)
                production_orders_created += 1
            db.session.commit()
            print(f"  [OK] Created {production_orders_created} production orders (Total: {ProductionOrder.query.count()})")
        else:
            print(f"  [OK] Production orders already exist (Total: {ProductionOrder.query.count()})")
        
        # 11. EMPLOYEES (HR Module)
        print("\n[11/15] Seeding Employees (HR)...")
        employees_data = [
            {"name": "John Doe", "email": "john.doe@sas.com", "phone": "+256 700 111 111", "position": "Chef"},
            {"name": "Jane Smith", "email": "jane.smith@sas.com", "phone": "+256 700 222 222", "position": "Event Manager"},
            {"name": "Mike Johnson", "email": "mike.johnson@sas.com", "phone": "+256 700 333 333", "position": "Waiter"},
        ]
        employees_created = 0
        for emp_data in employees_data:
            if not Employee.query.filter_by(email=emp_data["email"]).first():
                employee = Employee(
                    name=emp_data["name"],
                    email=emp_data["email"],
                    phone=emp_data["phone"],
                    position=emp_data["position"],
                    is_active=True
                )
                db.session.add(employee)
                employees_created += 1
        db.session.commit()
        print(f"  [OK] Created {employees_created} employees (Total: {Employee.query.count()})")
        
        # 12. POS PRODUCTS (POS Module)
        print("\n[12/15] Seeding POS Products...")
        pos_products_data = [
            {"name": "Coffee", "price": 5000, "cost": 2000},
            {"name": "Tea", "price": 3000, "cost": 1000},
            {"name": "Sandwich", "price": 8000, "cost": 4000},
            {"name": "Juice", "price": 4000, "cost": 1500},
        ]
        pos_created = 0
        for prod_data in pos_products_data:
            if not POSProduct.query.filter_by(name=prod_data["name"]).first():
                product = POSProduct(
                    name=prod_data["name"],
                    price=Decimal(str(prod_data["price"])),
                    cost=Decimal(str(prod_data["cost"])),
                    is_available=True,
                    is_active=True
                )
                db.session.add(product)
                pos_created += 1
        db.session.commit()
        print(f"  [OK] Created {pos_created} POS products (Total: {POSProduct.query.count()})")
        
        # 13. QUOTATIONS (Quotes Module)
        print("\n[13/15] Seeding Quotations...")
        quotations_created = 0
        clients = Client.query.limit(5).all()
        for i, client in enumerate(clients):
            if not Quotation.query.filter_by(client_id=client.id).first():
                quotation = Quotation(
                    client_id=client.id,
                    quotation_number=f"QUO-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    total_amount=Decimal("5000000"),
                    status="Draft"
                )
                db.session.add(quotation)
                quotations_created += 1
        db.session.commit()
        print(f"  [OK] Created {quotations_created} quotations (Total: {Quotation.query.count()})")
        
        # 14. SUPPLIERS & PURCHASE ORDERS - Force create
        print("\n[14/15] Seeding Suppliers & Purchase Orders...")
        if Supplier.query.count() == 0:
            suppliers_data = [
                {"name": "Fresh Foods Ltd", "email": "orders@freshfoods.com", "phone": "+256 700 111 999"},
                {"name": "Kitchen Supplies Co", "email": "sales@kitchensupplies.com", "phone": "+256 700 222 888"},
                {"name": "Beverage Distributors", "email": "sales@beverages.com", "phone": "+256 700 333 777"},
                {"name": "Meat Suppliers Inc", "email": "orders@meatsuppliers.com", "phone": "+256 700 444 666"},
            ]
            suppliers_created = 0
            for sup_data in suppliers_data:
                supplier = Supplier(**sup_data, is_active=True)
                db.session.add(supplier)
                db.session.flush()
                suppliers_created += 1
                # Create purchase order
                po = PurchaseOrder(
                    supplier_id=supplier.id,
                    order_number=f"PO-{datetime.now().strftime('%Y%m%d')}-{suppliers_created:03d}",
                    total_amount=Decimal("2000000"),
                    status="Pending"
                )
                db.session.add(po)
            db.session.commit()
            print(f"  [OK] Created {suppliers_created} suppliers with purchase orders (Total Suppliers: {Supplier.query.count()})")
        else:
            print(f"  [OK] Suppliers already exist (Total: {Supplier.query.count()})")
        
        # 15. ANNOUNCEMENTS
        print("\n[15/15] Seeding Announcements...")
        announcements_data = [
            {"title": "Welcome to SAS Management System", "message": "All modules are now active. Dashboard shows real-time metrics."},
            {"title": "SAS AI Features Enabled", "message": "AI-powered insights, recommendations, and automation are now available."},
            {"title": "System Update Complete", "message": "All modules including CRM, Production, HR, and AI Suite are restored."},
            {"title": "staff party", "message": "we have an upcoming staff party end of this month"},
        ]
        announcements_created = 0
        for ann_data in announcements_data:
            if not Announcement.query.filter_by(title=ann_data["title"]).first():
                announcement = Announcement(
                    title=ann_data["title"],
                    message=ann_data["message"],
                    created_by=admin.id,
                    created_at=datetime.utcnow(),
                )
                db.session.add(announcement)
                announcements_created += 1
        db.session.commit()
        print(f"  [OK] Created {announcements_created} announcements (Total: {Announcement.query.count()})")
        
        # Enable AI Features
        print("\n[EXTRA] Enabling SAS AI Features...")
        try:
            from sas_management.ai.models import ensure_default_ai_features
            ensure_default_ai_features()
            print("  [OK] SAS AI features enabled")
        except Exception as e:
            print(f"  [WARN] AI features: {e}")
        
        print("\n" + "=" * 80)
        print("SEEDING COMPLETE - SUMMARY")
        print("=" * 80)
        print(f"Clients: {Client.query.count()}")
        print(f"Events: {Event.query.count()}")
        print(f"Leads: {IncomingLead.query.count()}")
        print(f"Invoices: {Invoice.query.count()}")
        print(f"Tasks: {Task.query.count()}")
        print(f"Inventory Items: {InventoryItem.query.count()}")
        print(f"Menu Items: {MenuItem.query.count()}")
        print(f"Bakery Items: {BakeryItem.query.count()}")
        print(f"Production Orders: {ProductionOrder.query.count()}")
        print(f"Employees: {Employee.query.count()}")
        print(f"POS Products: {POSProduct.query.count()}")
        print(f"Quotations: {Quotation.query.count()}")
        print(f"Suppliers: {Supplier.query.count()}")
        print(f"Announcements: {Announcement.query.count()}")
        print("=" * 80)
        print("\nAll modules have been seeded with sample data!")
        print("Login: admin@sas.com / password")
        print()

if __name__ == "__main__":
    seed_all_modules()
