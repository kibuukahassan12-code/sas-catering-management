"""Seed sample production quality control data for SAS Best Foods."""
from app import create_app, db
from models import (
    KitchenChecklist, DeliveryQCChecklist, FoodSafetyLog, HygieneReport,
    Event, User, UserRole, Client
)
from datetime import date, datetime, timedelta, time
from decimal import Decimal
import json


def seed_production_quality_control_data():
    """Seed sample kitchen checklists, delivery QC, food safety logs, and hygiene reports."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Seeding Production Quality Control Sample Data...")
        print("=" * 60)
        
        # Check if sample data already exists
        existing_count = (
            KitchenChecklist.query.count() +
            DeliveryQCChecklist.query.count() +
            FoodSafetyLog.query.count() +
            HygieneReport.query.count()
        )
        
        if existing_count > 0:
            print(f"Sample quality control data already exists:")
            print(f"  Kitchen Checklists: {KitchenChecklist.query.count()}")
            print(f"  Delivery QC Checklists: {DeliveryQCChecklist.query.count()}")
            print(f"  Food Safety Logs: {FoodSafetyLog.query.count()}")
            print(f"  Hygiene Reports: {HygieneReport.query.count()}")
            print("\nTo add more data, delete existing records first or modify this script.")
            return
        
        # Get users for assignment
        admin = User.query.filter_by(role=UserRole.Admin).first()
        kitchen_staff = User.query.filter_by(role=UserRole.KitchenStaff).first()
        if not admin:
            print("⚠️  No admin user found. Creating one...")
            admin = User(email="admin@sas.com", role=UserRole.Admin)
            admin.set_password("password")
            db.session.add(admin)
            db.session.flush()
        
        if not kitchen_staff:
            kitchen_staff = User.query.filter_by(email="kitchen@sas.com").first()
            if not kitchen_staff:
                kitchen_staff = User(email="kitchen@sas.com", role=UserRole.KitchenStaff)
                kitchen_staff.set_password("password")
                db.session.add(kitchen_staff)
                db.session.flush()
        
        # Get events for linking
        events = Event.query.filter_by(status="Confirmed").limit(3).all()
        if not events:
            # Create a sample event if none exists
            client = Client.query.first()
            if client:
                sample_event = Event(
                    client_id=client.id,
                    event_name="Sample Wedding Event",
                    event_date=date.today() + timedelta(days=7),
                    guest_count=200,
                    status="Confirmed",
                    quoted_value=Decimal("500000.00")
                )
                db.session.add(sample_event)
                db.session.flush()
                events = [sample_event]
        
        # ============================
        # KITCHEN CHECKLISTS
        # ============================
        print("\n1. Creating Kitchen Checklists...")
        
        default_checklist_items = [
            {"name": "Equipment cleaned and sanitized", "status": "Checked", "note": ""},
            {"name": "Food storage temperatures checked", "status": "Checked", "note": "All fridges at 4°C"},
            {"name": "Personal hygiene verified", "status": "Checked", "note": "All staff wearing proper attire"},
            {"name": "Handwashing stations functional", "status": "Checked", "note": ""},
            {"name": "Food prep surfaces sanitized", "status": "Checked", "note": ""},
            {"name": "Waste disposal checked", "status": "Checked", "note": "Bins emptied"},
            {"name": "Ingredient inventory verified", "status": "Checked", "note": ""},
            {"name": "Allergen information displayed", "status": "Checked", "note": "Updated board"}
        ]
        
        for i in range(5):
            checklist_date = date.today() - timedelta(days=i)
            event_id = events[0].id if events and i < len(events) else None
            status = "Completed" if i < 3 else "In Progress" if i == 3 else "Pending"
            
            checklist = KitchenChecklist(
                checklist_date=checklist_date,
                event_id=event_id,
                checked_by=kitchen_staff.id if kitchen_staff else admin.id,
                items=json.dumps(default_checklist_items),
                status=status,
                notes=f"Daily kitchen checklist for {checklist_date.strftime('%Y-%m-%d')}",
                completed_at=datetime.now() - timedelta(days=i) if status == "Completed" else None
            )
            db.session.add(checklist)
            print(f"  ✓ Created kitchen checklist for {checklist_date.strftime('%Y-%m-%d')}")
        
        db.session.flush()
        
        # ============================
        # DELIVERY QC CHECKLISTS
        # ============================
        print("\n2. Creating Delivery QC Checklists...")
        
        if events:
            for i, event in enumerate(events[:3]):
                delivery_date = event.event_date if hasattr(event, 'event_date') else date.today() + timedelta(days=i+1)
                # Generate times: 2:30 PM, 3:00 PM, 3:30 PM
                hour = 14 + (i * 30) // 60
                minute = (30 + (i * 30)) % 60
                delivery_time = time(hour, minute)
                
                qc_checklist = DeliveryQCChecklist(
                    event_id=event.id,
                    delivery_date=delivery_date,
                    delivery_time=delivery_time,
                    checked_by=kitchen_staff.id if kitchen_staff else admin.id,
                    temperature_check=f"Hot: 68°C, Cold: 4°C",
                    packaging_integrity="Good",
                    presentation=["Excellent", "Good", "Acceptable"][i],
                    quantity_verified=True,
                    customer_satisfaction=["Excellent", "Good", "Fair"][i],
                    issues=None if i == 0 else "Minor delay in delivery time" if i == 1 else None,
                    notes=f"Delivery QC completed successfully for {event.event_name}" if hasattr(event, 'event_name') else "Delivery QC completed"
                )
                db.session.add(qc_checklist)
                print(f"  ✓ Created delivery QC checklist for event #{event.id}")
        else:
            # Create one standalone QC checklist
            qc_checklist = DeliveryQCChecklist(
                event_id=events[0].id if events else None,
                delivery_date=date.today(),
                delivery_time=time(15, 0),
                checked_by=kitchen_staff.id if kitchen_staff else admin.id,
                temperature_check="Hot: 65°C, Cold: 5°C",
                packaging_integrity="Good",
                presentation="Good",
                quantity_verified=True,
                customer_satisfaction="Good",
                notes="Sample delivery QC checklist"
            )
            db.session.add(qc_checklist)
            print(f"  ✓ Created sample delivery QC checklist")
        
        db.session.flush()
        
        # ============================
        # FOOD SAFETY LOGS
        # ============================
        print("\n3. Creating Food Safety Logs...")
        
        food_safety_entries = [
            {
                "category": "Temperature",
                "item_description": "Main Refrigerator - Food Storage",
                "temperature": Decimal("4.2"),
                "status": "Normal",
                "action_taken": None,
                "notes": "Temperature within safe range"
            },
            {
                "category": "Temperature",
                "item_description": "Freezer Unit",
                "temperature": Decimal("-18.5"),
                "status": "Normal",
                "action_taken": None,
                "notes": "Freezer operating correctly"
            },
            {
                "category": "Temperature",
                "item_description": "Hot Holding Unit",
                "temperature": Decimal("63.0"),
                "status": "Warning",
                "action_taken": "Increased heating element, rechecked after 15 minutes",
                "notes": "Temperature slightly below safe minimum, corrected"
            },
            {
                "category": "Storage",
                "item_description": "Dry Storage Area",
                "temperature": None,
                "status": "Normal",
                "action_taken": None,
                "notes": "Properly organized, no pest activity detected"
            },
            {
                "category": "Handling",
                "item_description": "Food Prep Area",
                "temperature": None,
                "status": "Normal",
                "action_taken": None,
                "notes": "All surfaces sanitized, staff following proper procedures"
            },
            {
                "category": "Cleaning",
                "item_description": "Dishwashing Station",
                "temperature": None,
                "status": "Normal",
                "action_taken": None,
                "notes": "Sanitizer concentration verified at 50ppm"
            },
            {
                "category": "Training",
                "item_description": "Food Safety Training Session",
                "temperature": None,
                "status": "Normal",
                "action_taken": None,
                "notes": "All kitchen staff attended HACCP refresher training"
            },
            {
                "category": "Pest Control",
                "item_description": "Kitchen Area Inspection",
                "temperature": None,
                "status": "Normal",
                "action_taken": None,
                "notes": "No signs of pests, traps checked and reset"
            }
        ]
        
        for i, entry in enumerate(food_safety_entries):
            log_date = date.today() - timedelta(days=i % 3)
            log_time = time(9 + i % 8, 0)  # Spread across 8 hours
            event_id = events[0].id if events and i < len(events) else None
            
            log = FoodSafetyLog(
                log_date=log_date,
                log_time=log_time,
                event_id=event_id,
                logged_by=kitchen_staff.id if kitchen_staff else admin.id,
                category=entry["category"],
                item_description=entry["item_description"],
                temperature=entry["temperature"],
                action_taken=entry["action_taken"],
                status=entry["status"],
                notes=entry["notes"]
            )
            db.session.add(log)
            print(f"  ✓ Created food safety log: {entry['category']} - {entry['item_description'][:30]}...")
        
        db.session.flush()
        
        # ============================
        # HYGIENE REPORTS
        # ============================
        print("\n4. Creating Hygiene Reports...")
        
        hygiene_areas = ["Kitchen", "Storage", "Prep Area", "Delivery Vehicle", "Dishwashing Area"]
        
        default_hygiene_items = [
            {"name": "Floors clean and dry", "checked": True},
            {"name": "Walls and ceilings clean", "checked": True},
            {"name": "Equipment clean and sanitized", "checked": True},
            {"name": "Proper waste disposal", "checked": True},
            {"name": "Pest control measures in place", "checked": True},
            {"name": "Staff wearing proper attire", "checked": True},
            {"name": "Handwashing facilities functional", "checked": True},
            {"name": "Temperature controls working", "checked": True}
        ]
        
        for i, area in enumerate(hygiene_areas):
            report_date = date.today() - timedelta(days=i % 3)
            report_time = time(10 + i, 0)
            event_id = events[0].id if events and i < len(events) else None
            
            # Make one report have issues
            has_issues = (i == 2)
            overall_rating = "Good" if not has_issues else "Fair"
            status = "Completed" if not has_issues else "Action Required"
            
            # Modify checklist items - one unchecked item if there are issues
            items = default_hygiene_items.copy()
            if has_issues:
                items[3]["checked"] = False  # Waste disposal issue
            
            report = HygieneReport(
                report_date=report_date,
                report_time=report_time,
                event_id=event_id,
                inspected_by=kitchen_staff.id if kitchen_staff else admin.id,
                area=area,
                checklist_items=json.dumps(items),
                overall_rating=overall_rating,
                issues_found="Waste disposal area needs immediate attention" if has_issues else None,
                corrective_actions="Scheduled deep cleaning and waste bin replacement" if has_issues else None,
                status=status,
                follow_up_date=report_date + timedelta(days=1) if has_issues else None
            )
            db.session.add(report)
            print(f"  ✓ Created hygiene report for {area} (Rating: {overall_rating})")
        
        db.session.flush()
        
        # Commit all data
        try:
            db.session.commit()
            print("\n" + "=" * 60)
            print("✅ Sample Production Quality Control Data Created Successfully!")
            print("=" * 60)
            print(f"\nSummary:")
            print(f"  ✓ Kitchen Checklists: {KitchenChecklist.query.count()}")
            print(f"  ✓ Delivery QC Checklists: {DeliveryQCChecklist.query.count()}")
            print(f"  ✓ Food Safety Logs: {FoodSafetyLog.query.count()}")
            print(f"  ✓ Hygiene Reports: {HygieneReport.query.count()}")
            print("\nYou can now view this data in the Production Department module.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error seeding data: {str(e)}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    seed_production_quality_control_data()




