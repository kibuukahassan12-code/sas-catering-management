#!/usr/bin/env python3
"""
Quick System Restoration - Restores dashboard data and enables all modules.
"""
import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set SECRET_KEY before importing app
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "sas-management-system-secret-key-2024-production")

from sas_management.app import create_app
from sas_management.models import (
    db, User, Role, Client, Event, IncomingLead, Invoice, InvoiceStatus,
    Task, TaskStatus, InventoryItem, Announcement, UserRole
)
from werkzeug.security import generate_password_hash

def restore_system():
    """Quick restoration of essential dashboard data."""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("SAS MANAGEMENT SYSTEM - QUICK RESTORATION")
        print("=" * 70)
        print()
        
        # 1. Ensure admin user
        print("[1/8] Ensuring admin user...")
        admin = User.query.filter_by(email="admin@sas.com").first()
        if not admin:
            admin = User(
                email="admin@sas.com",
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role=UserRole.Admin,
                is_admin=True,
                first_login=False,
                must_change_password=False
            )
            db.session.add(admin)
            db.session.commit()
            print("  [OK] Created admin user")
        else:
            print("  [OK] Admin user exists")
        
        # 2. Create sample clients
        print("\n[2/8] Creating sample clients...")
        clients_data = [
            {"name": "Elite Weddings Ltd.", "email": "events@eliteweddings.com", "phone": "+256 700 111 222", "contact_person": "Sara Lee"},
            {"name": "Corporate Gatherings Co.", "email": "info@corpgatherings.com", "phone": "+256 700 333 444", "contact_person": "Daniel O."},
            {"name": "Grand Hotel", "email": "catering@grandhotel.com", "phone": "+256 700 555 666", "contact_person": "Robert Johnson"},
            {"name": "ABC Corporation", "email": "events@abc-corp.com", "phone": "+256 700 777 888", "contact_person": "John Doe"},
        ]
        clients_created = 0
        for client_data in clients_data:
            if not Client.query.filter_by(email=client_data["email"]).first():
                client = Client(**client_data)
                db.session.add(client)
                clients_created += 1
        db.session.commit()
        print(f"  [OK] Created {clients_created} clients")
        
        # 3. Create sample events
        print("\n[3/8] Creating sample events...")
        clients = Client.query.all()
        if clients:
            events_data = [
                {"title": "Corporate Annual Dinner", "status": "Confirmed", "quoted_value": 5000000, "guest_count": 200},
                {"title": "Wedding Reception", "status": "Confirmed", "quoted_value": 8000000, "guest_count": 150},
                {"title": "Product Launch Event", "status": "Draft", "quoted_value": 3000000, "guest_count": 100},
                {"title": "Birthday Celebration", "status": "Confirmed", "quoted_value": 2000000, "guest_count": 50},
            ]
            events_created = 0
            for i, event_data in enumerate(events_data):
                if Event.query.filter_by(title=event_data["title"]).first():
                    continue
                client = clients[i % len(clients)]
                event = Event(
                    title=event_data["title"],
                    client_id=client.id,
                    client_name=client.name,
                    client_email=client.email,
                    client_phone=client.phone,
                    status=event_data["status"],
                    quoted_value=Decimal(str(event_data["quoted_value"])),
                    guest_count=event_data["guest_count"],
                    date=date.today() + timedelta(days=7 + i * 3),
                    event_date=date.today() + timedelta(days=7 + i * 3),
                )
                db.session.add(event)
                events_created += 1
            db.session.commit()
            print(f"  [OK] Created {events_created} events")
        else:
            print("  [WARN] No clients found, skipping events")
        
        # 4. Create sample leads (CRM Pipeline)
        print("\n[4/8] Creating CRM pipeline leads...")
        leads_data = [
            {"client_name": "Tech Startup Inc", "email": "contact@techstartup.com", "phone": "+256 700 999 000", "pipeline_stage": "New Lead", "estimated_value": 4000000},
            {"client_name": "University Event", "email": "events@university.ac.ug", "phone": "+256 700 111 333", "pipeline_stage": "Qualified", "estimated_value": 6000000},
            {"client_name": "Charity Gala", "email": "info@charity.org", "phone": "+256 700 222 444", "pipeline_stage": "Proposal Sent", "estimated_value": 5000000},
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
        print(f"  [OK] Created {leads_created} leads")
        
        # 5. Create sample invoices
        print("\n[5/8] Creating sample invoices...")
        events = Event.query.filter_by(status="Confirmed").limit(2).all()
        invoices_created = 0
        for event in events:
            if not Invoice.query.filter_by(event_id=event.id).first():
                invoice = Invoice(
                    client_id=event.client_id,
                    event_id=event.id,
                    invoice_number=f"INV-{datetime.now().strftime('%Y%m%d')}-{invoices_created + 1:03d}",
                    total_amount_ugx=event.quoted_value,
                    status=InvoiceStatus.Issued,
                    issue_date=date.today() - timedelta(days=5),
                    due_date=date.today() + timedelta(days=25),
                )
                db.session.add(invoice)
                invoices_created += 1
        db.session.commit()
        print(f"  [OK] Created {invoices_created} invoices")
        
        # 6. Create sample tasks
        print("\n[6/8] Creating sample tasks...")
        tasks_data = [
            {"title": "Prepare menu for Corporate Dinner", "status": TaskStatus.Pending, "due_date": date.today() + timedelta(days=2)},
            {"title": "Order ingredients for Wedding", "status": TaskStatus.InProgress, "due_date": date.today() + timedelta(days=1)},
            {"title": "Finalize event timeline", "status": TaskStatus.Pending, "due_date": date.today() + timedelta(days=3)},
        ]
        tasks_created = 0
        for task_data in tasks_data:
            if not Task.query.filter_by(title=task_data["title"]).first():
                task = Task(
                    title=task_data["title"],
                    assigned_user_id=admin.id,
                    status=task_data["status"],
                    due_date=task_data["due_date"],
                    created_at=datetime.utcnow(),
                )
                db.session.add(task)
                tasks_created += 1
        db.session.commit()
        print(f"  [OK] Created {tasks_created} tasks")
        
        # 7. Create sample inventory items
        print("\n[7/8] Creating sample inventory items...")
        inventory_data = [
            {"name": "Chairs", "stock_count": 500, "unit": "pieces"},
            {"name": "Tables", "stock_count": 50, "unit": "pieces"},
            {"name": "Table Cloths", "stock_count": 8, "unit": "pieces"},  # Low stock
            {"name": "Tents", "stock_count": 15, "unit": "pieces"},
        ]
        inventory_created = 0
        for inv_data in inventory_data:
            if not InventoryItem.query.filter_by(name=inv_data["name"]).first():
                item = InventoryItem(
                    name=inv_data["name"],
                    stock_count=inv_data["stock_count"],
                    unit=inv_data["unit"],
                    status="Available" if inv_data["stock_count"] > 10 else "Low Stock",
                )
                db.session.add(item)
                inventory_created += 1
        db.session.commit()
        print(f"  [OK] Created {inventory_created} inventory items")
        
        # 8. Ensure announcements exist
        print("\n[8/8] Ensuring announcements...")
        if Announcement.query.count() == 0:
            announcements = [
                {"title": "Welcome to SAS Management System", "message": "All modules are now active. Dashboard shows real-time metrics."},
                {"title": "SAS AI Features Enabled", "message": "AI-powered insights, recommendations, and automation are now available."},
                {"title": "System Update Complete", "message": "All modules including CRM, Production, HR, and AI Suite are restored."},
            ]
            for ann_data in announcements:
                announcement = Announcement(
                    title=ann_data["title"],
                    message=ann_data["message"],
                    created_by=admin.id,
                    created_at=datetime.utcnow(),
                )
                db.session.add(announcement)
            db.session.commit()
            print("  [OK] Created announcements")
        else:
            print("  [OK] Announcements already exist")
        
        # 9. Enable AI features
        print("\n[9/9] Enabling SAS AI features...")
        try:
            from sas_management.ai.models import ensure_default_ai_features
            ensure_default_ai_features()
            print("  [OK] SAS AI features enabled")
        except Exception as e:
            print(f"  [WARN] Error enabling AI: {e}")
        
        print("\n" + "=" * 70)
        print("RESTORATION COMPLETE!")
        print("=" * 70)
        print("\nDashboard data restored:")
        print(f"   - {Client.query.count()} clients")
        print(f"   - {Event.query.count()} events")
        print(f"   - {IncomingLead.query.count()} leads")
        print(f"   - {Invoice.query.count()} invoices")
        print(f"   - {Task.query.count()} tasks")
        print(f"   - {InventoryItem.query.count()} inventory items")
        print("\nLogin credentials:")
        print("   Email: admin@sas.com")
        print("   Password: admin123")
        print("\nAccess: http://127.0.0.1:5000/dashboard")
        print()

if __name__ == "__main__":
    restore_system()
