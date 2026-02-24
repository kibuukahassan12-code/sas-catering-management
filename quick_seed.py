#!/usr/bin/env python3
"""Quick seed script - creates essential dashboard data."""
import os
import sys
os.environ["SECRET_KEY"] = "sas-management-system-secret-key-2024-production"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import (
    db, User, Client, Event, IncomingLead, Invoice, InvoiceStatus,
    Task, TaskStatus, InventoryItem, Announcement, UserRole
)
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from decimal import Decimal

app = create_app()
with app.app_context():
    # Admin user
    admin = User.query.filter_by(email="admin@sas.com").first()
    if not admin:
        admin = User(
            email="admin@sas.com",
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role=UserRole.Admin,
            is_admin=True,
            first_login=False
        )
        db.session.add(admin)
        db.session.commit()
    
    # Clients
    if Client.query.count() == 0:
        clients = [
            Client(name="Elite Weddings Ltd.", email="events@eliteweddings.com", phone="+256 700 111 222", contact_person="Sara Lee"),
            Client(name="Corporate Gatherings Co.", email="info@corpgatherings.com", phone="+256 700 333 444", contact_person="Daniel O."),
            Client(name="Grand Hotel", email="catering@grandhotel.com", phone="+256 700 555 666", contact_person="Robert Johnson"),
        ]
        for c in clients:
            db.session.add(c)
        db.session.commit()
    
    # Events
    clients = Client.query.all()
    if clients and Event.query.count() == 0:
        events = [
            Event(title="Corporate Annual Dinner", client_id=clients[0].id, client_name=clients[0].name, status="Confirmed", quoted_value=5000000, guest_count=200, date=date.today() + timedelta(days=7)),
            Event(title="Wedding Reception", client_id=clients[1].id, client_name=clients[1].name, status="Confirmed", quoted_value=8000000, guest_count=150, date=date.today() + timedelta(days=10)),
            Event(title="Product Launch", client_id=clients[0].id, client_name=clients[0].name, status="Draft", quoted_value=3000000, guest_count=100, date=date.today() + timedelta(days=14)),
        ]
        for e in events:
            db.session.add(e)
        db.session.commit()
    
    # Leads
    if IncomingLead.query.count() == 0:
        leads = [
            IncomingLead(client_name="Tech Startup", email="contact@techstartup.com", phone="+256 700 999 000", pipeline_stage="New Lead", estimated_value=4000000),
            IncomingLead(client_name="University Event", email="events@university.ac.ug", phone="+256 700 111 333", pipeline_stage="Qualified", estimated_value=6000000),
        ]
        for l in leads:
            db.session.add(l)
        db.session.commit()
    
    # Invoices
    events = Event.query.filter_by(status="Confirmed").all()
    if events and Invoice.query.count() == 0:
        for i, event in enumerate(events[:2]):
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
    
    # Tasks
    if Task.query.count() == 0:
        tasks = [
            Task(title="Prepare menu for Corporate Dinner", assigned_user_id=admin.id, status=TaskStatus.Pending, due_date=date.today() + timedelta(days=2)),
            Task(title="Order ingredients", assigned_user_id=admin.id, status=TaskStatus.InProgress, due_date=date.today() + timedelta(days=1)),
        ]
        for t in tasks:
            db.session.add(t)
        db.session.commit()
    
    # Inventory
    if InventoryItem.query.count() == 0:
        items = [
            InventoryItem(name="Chairs", stock_count=500, unit="pieces", status="Available"),
            InventoryItem(name="Tables", stock_count=50, unit="pieces", status="Available"),
            InventoryItem(name="Table Cloths", stock_count=8, unit="pieces", status="Low Stock"),
        ]
        for i in items:
            db.session.add(i)
        db.session.commit()
    
    # Announcements
    if Announcement.query.count() == 0:
        announcements = [
            Announcement(title="Welcome to SAS Management System", message="All modules are active. Dashboard shows real-time metrics.", created_by=admin.id),
            Announcement(title="SAS AI Features Enabled", message="AI-powered insights and automation are available.", created_by=admin.id),
        ]
        for a in announcements:
            db.session.add(a)
        db.session.commit()
    
    # AI Features
    try:
        from sas_management.ai.models import ensure_default_ai_features
        ensure_default_ai_features()
    except:
        pass
    
    print("SUCCESS: Dashboard data restored!")
    print(f"Clients: {Client.query.count()}")
    print(f"Events: {Event.query.count()}")
    print(f"Leads: {IncomingLead.query.count()}")
    print(f"Invoices: {Invoice.query.count()}")
    print(f"Tasks: {Task.query.count()}")
    print(f"Inventory: {InventoryItem.query.count()}")
