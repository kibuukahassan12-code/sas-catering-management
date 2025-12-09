"""Seed sample data for Enterprise Modules."""
import os
import sys
import json
from datetime import date, datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import (
    db, Client, Event, ClientPortalUser, Proposal, Vehicle, User,
    Supplier, PurchaseOrder, HACCPChecklist, TemperatureLog, Branch,
    Timeline, QualityChecklist
)
from werkzeug.security import generate_password_hash


def seed_enterprise_data():
    """Seed sample data for enterprise modules."""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("Seeding Enterprise Modules sample data...")
        print("=" * 70)
        
        # ============================================================
        # 1. CLIENT PORTAL - Demo Client
        # ============================================================
        print("\n[1/9] Creating demo client portal user...")
        try:
            client = Client.query.filter_by(email="client@example.com").first()
            if not client:
                client = Client(
                    name="Demo Client Company",
                    contact_person="John Doe",
                    email="client@example.com",
                    phone="+256 700 123 456"
                )
                db.session.add(client)
                db.session.flush()
            
            # Create portal user
            portal_user = ClientPortalUser.query.filter_by(email="client@example.com").first()
            if not portal_user:
                portal_user = ClientPortalUser(
                    client_id=client.id,
                    email="client@example.com",
                    password_hash=generate_password_hash("password123"),
                    is_active=True
                )
                db.session.add(portal_user)
                print("   [OK] Demo client portal user created (email: client@example.com, password: password123)")
            else:
                print("   [SKIP] Client portal user already exists")
        except Exception as e:
            print(f"   [ERROR] Error creating client portal user: {e}")
        
        db.session.commit()
        
        # ============================================================
        # 2. PROPOSAL - Sample Proposal
        # ============================================================
        print("\n[2/9] Creating sample proposal...")
        try:
            event = Event.query.first()
            if event:
                proposal = Proposal.query.filter_by(event_id=event.id).first()
                if not proposal:
                    proposal = Proposal(
                        client_id=event.client_id,
                        event_id=event.id,
                        title=f"Proposal for {event.event_name}",
                        json_blocks=json.dumps([{"type": "header", "text": "Event Proposal"}]),
                        total_cost=Decimal("500000.00"),
                        markup_percent=20.0,
                        status="draft"
                    )
                    db.session.add(proposal)
                    print("   [OK] Sample proposal created")
        except Exception as e:
            print(f"   [ERROR] Error creating proposal: {e}")
        
        db.session.commit()
        
        # ============================================================
        # 3. DISPATCH - Vehicle & Driver
        # ============================================================
        print("\n[3/9] Creating sample vehicle...")
        try:
            driver = User.query.filter_by(role='KitchenStaff').first()
            vehicle = Vehicle.query.filter_by(reg_no="UAB-123A").first()
            if not vehicle:
                vehicle = Vehicle(
                    reg_no="UAB-123A",
                    driver_id=driver.id if driver else None,
                    vehicle_type="van",
                    capacity_kg=Decimal("500.00"),
                    status="available"
                )
                db.session.add(vehicle)
                print("   [OK] Sample vehicle created (UAB-123A)")
        except Exception as e:
            print(f"   [ERROR] Error creating vehicle: {e}")
        
        db.session.commit()
        
        # ============================================================
        # 4. SUPPLIER - Sample Supplier
        # ============================================================
        print("\n[4/9] Creating sample supplier...")
        try:
            supplier = Supplier.query.filter_by(email="supplier@example.com").first()
            if not supplier:
                supplier = Supplier(
                    name="Premium Food Supplies Ltd",
                    contact_person="Jane Supplier",
                    email="supplier@example.com",
                    phone="+256 700 999 888",
                    rating=4.5,
                    lead_time_days=7,
                    default_currency="UGX"
                )
                db.session.add(supplier)
                print("   [OK] Sample supplier created")
        except Exception as e:
            print(f"   [ERROR] Error creating supplier: {e}")
        
        db.session.commit()
        
        # ============================================================
        # 5. FOOD SAFETY - HACCP Checklist & Temperature Log
        # ============================================================
        print("\n[5/9] Creating food safety data...")
        try:
            checklist = HACCPChecklist.query.filter_by(name="Standard Food Safety").first()
            if not checklist:
                checklist = HACCPChecklist(
                    name="Standard Food Safety",
                    items_json=json.dumps([
                        {"item": "Temperature check", "required": True},
                        {"item": "Sanitation check", "required": True}
                    ])
                )
                db.session.add(checklist)
            
            user = User.query.first()
            if user:
                temp_log = TemperatureLog(
                    item="Refrigerator #1",
                    temp_c=Decimal("4.0"),
                    location="Main Kitchen",
                    recorded_by=user.id,
                    notes="Normal operating temperature"
                )
                db.session.add(temp_log)
                print("   [OK] Sample HACCP checklist and temperature log created")
        except Exception as e:
            print(f"   [ERROR] Error creating food safety data: {e}")
        
        db.session.commit()
        
        # ============================================================
        # 6. TIMELINE - Sample Timeline
        # ============================================================
        print("\n[6/9] Creating sample timeline...")
        try:
            event = Event.query.first()
            if event:
                timeline = Timeline.query.filter_by(event_id=event.id).first()
                if not timeline:
                    timeline = Timeline(
                        event_id=event.id,
                        json_timeline=json.dumps([
                            {"time": "06:00", "task": "Prep vegetables", "assignee": "Kitchen Staff"},
                            {"time": "08:00", "task": "Start cooking", "assignee": "Chef"}
                        ]),
                        created_by=user.id if user else None
                    )
                    db.session.add(timeline)
                    print("   [OK] Sample timeline created")
        except Exception as e:
            print(f"   [ERROR] Error creating timeline: {e}")
        
        db.session.commit()
        
        # ============================================================
        # 7. QUALITY CHECKLIST
        # ============================================================
        print("\n[7/9] Creating quality checklist...")
        try:
            qc = QualityChecklist.query.filter_by(name="Standard Quality Check").first()
            if not qc:
                qc = QualityChecklist(
                    name="Standard Quality Check",
                    items_json=json.dumps([
                        {"item": "Food presentation", "pass": True},
                        {"item": "Temperature check", "pass": True}
                    ])
                )
                db.session.add(qc)
                print("   [OK] Sample quality checklist created")
        except Exception as e:
            print(f"   [ERROR] Error creating quality checklist: {e}")
        
        db.session.commit()
        
        # ============================================================
        # 8. BRANCH - Default Branch
        # ============================================================
        print("\n[8/9] Creating default branch...")
        try:
            branch = Branch.query.filter_by(name="Main Branch").first()
            if not branch:
                branch = Branch(
                    name="Main Branch",
                    address="Kampala, Uganda",
                    timezone="Africa/Kampala",
                    is_active=True
                )
                db.session.add(branch)
                print("   [OK] Default branch created")
        except Exception as e:
            print(f"   [ERROR] Error creating branch: {e}")
        
        db.session.commit()
        
        # ============================================================
        # 9. COPY SAMPLE ASSET
        # ============================================================
        print("\n[9/9] Copying sample asset...")
        try:
            source_path = "/mnt/data/drwa.JPG"
            dest_dir = os.path.join(app.instance_path, "assets")
            dest_path = os.path.join(dest_dir, "sample_asset.jpg")
            
            os.makedirs(dest_dir, exist_ok=True)
            
            if os.path.exists(source_path):
                import shutil
                shutil.copy2(source_path, dest_path)
                print(f"   [OK] Sample asset copied to {dest_path}")
            else:
                # Create placeholder
                with open(dest_path, 'w') as f:
                    f.write("# Sample asset placeholder\n")
                print(f"   [WARN] Source file not found. Created placeholder at {dest_path}")
        except Exception as e:
            print(f"   [ERROR] Could not copy sample asset: {e}")
        
        print("\n" + "=" * 70)
        print("[SUCCESS] Enterprise modules sample data seeded successfully!")
        print("=" * 70)
        print("\nTest credentials:")
        print("   Client Portal: client@example.com / password123")
        print("\nAll enterprise modules ready for testing!")


if __name__ == "__main__":
    seed_enterprise_data()

