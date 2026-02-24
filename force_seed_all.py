#!/usr/bin/env python3
"""
FORCE SEED ALL MODULES - Creates data for ALL modules regardless of existing data
This ensures every module has sample data for dashboard display.
"""
import os
import sys
os.environ["SECRET_KEY"] = "sas-management-system-secret-key-2024-production"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import (
    db, User, Client, Event, IncomingLead, Invoice, InvoiceStatus,
    Task, TaskStatus, InventoryItem, Announcement, UserRole,
    MenuCategory, MenuItem, BakeryItem, ProductionOrder, ProductionBudgetStatus,
    Employee, POSProduct, Quotation, Supplier, PurchaseOrder
)
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from decimal import Decimal

app = create_app()

def force_seed_all():
    """Force create data for ALL modules."""
    with app.app_context():
        print("=" * 80)
        print("FORCE SEEDING ALL MODULES")
        print("=" * 80)
        print()
        
        # Admin
        admin = User.query.filter_by(email="admin@sas.com").first()
        if not admin:
            admin = User(email="admin@sas.com", username="admin", role=UserRole.Admin, is_admin=True, first_login=False)
            admin.set_password("password")
            db.session.add(admin)
            db.session.commit()
        else:
            admin.set_password("password")
            admin.first_login = False
            db.session.commit()
        print("[OK] Admin user ready")
        
        # Ensure we have clients
        if Client.query.count() < 5:
            for i in range(5):
                client = Client(
                    name=f"Client {i+1}",
                    email=f"client{i+1}@example.com",
                    phone=f"+256 700 {100+i:03d} {200+i:03d}",
                    contact_person=f"Contact {i+1}"
                )
                db.session.add(client)
            db.session.commit()
        clients = Client.query.all()
        print(f"[OK] Clients: {Client.query.count()}")
        
        # Ensure we have events
        if Event.query.count() < 10:
            for i in range(10):
                client = clients[i % len(clients)]
                event = Event(
                    title=f"Event {i+1}",
                    client_id=client.id,
                    client_name=client.name,
                    client_email=client.email,
                    client_phone=client.phone,
                    status="Confirmed" if i % 2 == 0 else "Draft",
                    quoted_value=Decimal(str(1000000 + i * 500000)),
                    guest_count=50 + i * 10,
                    date=date.today() + timedelta(days=i+1),
                    event_date=date.today() + timedelta(days=i+1),
                )
                db.session.add(event)
            db.session.commit()
        print(f"[OK] Events: {Event.query.count()}")
        
        # Menu Categories & Items
        if MenuCategory.query.count() == 0:
            cat1 = MenuCategory(name="Main Courses", description="Main dishes", is_active=True)
            cat2 = MenuCategory(name="Appetizers", description="Starters", is_active=True)
            cat3 = MenuCategory(name="Desserts", description="Sweet treats", is_active=True)
            db.session.add_all([cat1, cat2, cat3])
            db.session.flush()
            
            items = [
                MenuItem(name="Grilled Chicken", category_id=cat1.id, price=Decimal("8500"), is_available=True),
                MenuItem(name="Beef Steak", category_id=cat1.id, price=Decimal("12000"), is_available=True),
                MenuItem(name="Spring Rolls", category_id=cat2.id, price=Decimal("5000"), is_available=True),
                MenuItem(name="Chocolate Cake", category_id=cat3.id, price=Decimal("6000"), is_available=True),
            ]
            db.session.add_all(items)
            db.session.commit()
        print(f"[OK] Menu Categories: {MenuCategory.query.count()}, Menu Items: {MenuItem.query.count()}")
        
        # Bakery Items
        if BakeryItem.query.count() == 0:
            bakery_items = [
                BakeryItem(name="Chocolate Cake", price_ugx=Decimal("15000"), is_available=True),
                BakeryItem(name="Vanilla Cupcakes", price_ugx=Decimal("5000"), is_available=True),
                BakeryItem(name="Bread Loaf", price_ugx=Decimal("3000"), is_available=True),
            ]
            db.session.add_all(bakery_items)
            db.session.commit()
        print(f"[OK] Bakery Items: {BakeryItem.query.count()}")
        
        # Production Orders
        if ProductionOrder.query.count() == 0:
            events = Event.query.filter_by(status="Confirmed").limit(5).all()
            for i, event in enumerate(events):
                order = ProductionOrder(
                    reference=f"PROD-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    event_id=event.id,
                    status="Planned",
                    total_portions=event.guest_count or 50,
                )
                db.session.add(order)
            db.session.commit()
        print(f"[OK] Production Orders: {ProductionOrder.query.count()}")
        
        # Employees
        if Employee.query.count() == 0:
            employees = [
                Employee(first_name="John", last_name="Doe", email="john.doe@sas.com", phone="+256 700 111 111", position="Chef", is_active=True),
                Employee(first_name="Jane", last_name="Smith", email="jane.smith@sas.com", phone="+256 700 222 222", position="Event Manager", is_active=True),
                Employee(first_name="Mike", last_name="Johnson", email="mike.johnson@sas.com", phone="+256 700 333 333", position="Waiter", is_active=True),
            ]
            db.session.add_all(employees)
            db.session.commit()
        print(f"[OK] Employees: {Employee.query.count()}")
        
        # Suppliers
        if Supplier.query.count() == 0:
            suppliers = [
                Supplier(name="Fresh Foods Ltd", email="orders@freshfoods.com", phone="+256 700 111 999", is_active=True),
                Supplier(name="Kitchen Supplies Co", email="sales@kitchensupplies.com", phone="+256 700 222 888", is_active=True),
            ]
            db.session.add_all(suppliers)
            db.session.commit()
        print(f"[OK] Suppliers: {Supplier.query.count()}")
        
        # Leads
        if IncomingLead.query.count() < 5:
            leads = [
                IncomingLead(client_name="Tech Startup", email="contact@techstartup.com", phone="+256 700 999 000", pipeline_stage="New Lead", estimated_value=Decimal("4000000")),
                IncomingLead(client_name="University Event", email="events@university.ac.ug", phone="+256 700 111 333", pipeline_stage="Qualified", estimated_value=Decimal("6000000")),
            ]
            db.session.add_all(leads)
            db.session.commit()
        print(f"[OK] Leads: {IncomingLead.query.count()}")
        
        # Invoices
        if Invoice.query.count() < 5:
            events = Event.query.filter_by(status="Confirmed").limit(5).all()
            for i, event in enumerate(events):
                invoice = Invoice(
                    client_id=event.client_id,
                    event_id=event.id,
                    invoice_number=f"INV-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}",
                    total_amount_ugx=event.quoted_value,
                    status=InvoiceStatus.Issued,
                    issue_date=date.today() - timedelta(days=5),
                    due_date=date.today() + timedelta(days=25),
                )
                db.session.add(invoice)
            db.session.commit()
        print(f"[OK] Invoices: {Invoice.query.count()}")
        
        # Tasks
        if Task.query.count() < 3:
            tasks = [
                Task(title="Prepare menu", assigned_user_id=admin.id, status=TaskStatus.Pending, due_date=date.today() + timedelta(days=2)),
                Task(title="Order ingredients", assigned_user_id=admin.id, status=TaskStatus.InProgress, due_date=date.today() + timedelta(days=1)),
            ]
            db.session.add_all(tasks)
            db.session.commit()
        print(f"[OK] Tasks: {Task.query.count()}")
        
        # Inventory
        if InventoryItem.query.count() < 5:
            items = [
                InventoryItem(name="Chairs", stock_count=500, unit="pieces", status="Available"),
                InventoryItem(name="Tables", stock_count=50, unit="pieces", status="Available"),
                InventoryItem(name="Table Cloths", stock_count=8, unit="pieces", status="Low Stock"),
            ]
            db.session.add_all(items)
            db.session.commit()
        print(f"[OK] Inventory Items: {InventoryItem.query.count()}")
        
        # Announcements
        if Announcement.query.count() < 3:
            announcements = [
                Announcement(title="Welcome to SAS Management System", message="All modules are active.", created_by=admin.id),
                Announcement(title="SAS AI Features Enabled", message="AI-powered insights available.", created_by=admin.id),
            ]
            db.session.add_all(announcements)
            db.session.commit()
        print(f"[OK] Announcements: {Announcement.query.count()}")
        
        # AI Features
        try:
            from sas_management.ai.models import ensure_default_ai_features
            ensure_default_ai_features()
            print("[OK] AI Features enabled")
        except:
            pass
        
        print("\n" + "=" * 80)
        print("FORCE SEEDING COMPLETE!")
        print("=" * 80)
        print(f"Clients: {Client.query.count()}")
        print(f"Events: {Event.query.count()}")
        print(f"Menu Items: {MenuItem.query.count()}")
        print(f"Bakery Items: {BakeryItem.query.count()}")
        print(f"Production Orders: {ProductionOrder.query.count()}")
        print(f"Employees: {Employee.query.count()}")
        print(f"Suppliers: {Supplier.query.count()}")
        print(f"Leads: {IncomingLead.query.count()}")
        print(f"Invoices: {Invoice.query.count()}")
        print(f"Tasks: {Task.query.count()}")
        print(f"Inventory: {InventoryItem.query.count()}")
        print("=" * 80)
        print()

if __name__ == "__main__":
    force_seed_all()
