#!/usr/bin/env python3
"""
Seed Food Safety Sample Data
Creates sample temperature logs and safety incidents for testing.
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import (
    TemperatureLog,
    SafetyIncident,
    User,
    Event,
    UserRole
)

def seed_food_safety_data():
    """Seed food safety sample data."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("FOOD SAFETY SAMPLE DATA SEEDING")
        print("=" * 60)
        print()
        
        # Get users (preferably kitchen staff or admin)
        users = User.query.filter(
            db.or_(
                User.role == UserRole.KitchenStaff,
                User.role == UserRole.Admin
            )
        ).all()
        
        if not users:
            # Fallback to any user
            users = User.query.limit(3).all()
        
        if not users:
            print("⚠️  No users found. Please create users first.")
            return False
        
        # Get some events (optional)
        events = Event.query.limit(5).all()
        
        # Sample food items for temperature logging
        food_items = [
            "Chicken Breast (Raw)",
            "Beef Steak (Raw)",
            "Fish Fillet (Raw)",
            "Cooked Rice",
            "Soup (Hot)",
            "Salad (Cold)",
            "Dessert (Chilled)",
            "Beverages (Cold)",
            "Bread (Room Temp)",
            "Pasta (Hot)",
            "Vegetables (Fresh)",
            "Dairy Products (Cold)",
            "Frozen Items",
            "Hot Food Holding",
            "Cold Food Holding"
        ]
        
        locations = [
            "Main Refrigerator",
            "Freezer Unit 1",
            "Freezer Unit 2",
            "Hot Holding Station",
            "Cold Holding Station",
            "Prep Area",
            "Kitchen Counter",
            "Storage Room",
            "Delivery Vehicle",
            "Event Site"
        ]
        
        # Create Temperature Logs (last 30 days)
        print("1. Creating Temperature Logs...")
        temp_logs_created = 0
        
        for i in range(50):  # Create 50 temperature logs
            days_ago = random.randint(0, 30)
            log_date = date.today() - timedelta(days=days_ago)
            recorded_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            item = random.choice(food_items)
            location = random.choice(locations)
            user = random.choice(users)
            
            # Generate realistic temperatures based on item type
            if "Raw" in item or "Frozen" in item:
                temp = Decimal(str(random.uniform(-18, 4)))  # Frozen/raw: -18 to 4°C
            elif "Hot" in item or "Cooked" in item or "Soup" in item or "Pasta" in item:
                temp = Decimal(str(random.uniform(60, 85)))  # Hot: 60-85°C
            elif "Cold" in item or "Chilled" in item or "Dairy" in item:
                temp = Decimal(str(random.uniform(1, 5)))  # Cold: 1-5°C
            else:
                temp = Decimal(str(random.uniform(15, 25)))  # Room temp: 15-25°C
            
            # Check if log already exists (avoid duplicates)
            existing = TemperatureLog.query.filter_by(
                log_date=log_date,
                temperature=temp,
                location=location
            ).first()
            
            if not existing:
                log = TemperatureLog(
                    event_id=random.choice(events).id if events else None,
                    log_date=log_date,
                    temperature=temp,
                    location=location,
                    recorded_by=user.id,
                    recorded_at=recorded_at,
                    created_at=recorded_at
                )
                db.session.add(log)
                temp_logs_created += 1
        
        db.session.commit()
        print(f"   ✓ Created {temp_logs_created} temperature logs")
        
        # Create Safety Incidents
        print("\n2. Creating Safety Incidents...")
        incident_types = [
            "Temperature Violation",
            "Cross Contamination",
            "Improper Storage",
            "Expired Food",
            "Equipment Malfunction",
            "Personal Hygiene",
            "Cleaning Issue",
            "Pest Sighting",
            "Food Spoilage",
            "Allergen Contamination"
        ]
        
        severities = ["Low", "Medium", "High", "Critical"]
        statuses = ["open", "investigating", "resolved", "closed"]
        
        incident_descriptions = [
            "Refrigerator temperature exceeded safe limit for 2+ hours",
            "Raw meat stored above ready-to-eat items in refrigerator",
            "Food items found stored at incorrect temperature zone",
            "Expired products discovered in storage area",
            "Temperature monitoring equipment malfunction detected",
            "Staff member observed not following handwashing protocol",
            "Food preparation surface not properly sanitized",
            "Rodent activity observed in storage area",
            "Food items showing signs of spoilage before expiration",
            "Potential allergen cross-contamination during preparation"
        ]
        
        incidents_created = 0
        
        for i in range(15):  # Create 15 safety incidents
            days_ago = random.randint(0, 60)
            created_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            incident_type = random.choice(incident_types)
            severity = random.choice(severities)
            status = random.choice(statuses)
            description = random.choice(incident_descriptions)
            user = random.choice(users)
            
            # Check if similar incident exists
            existing = SafetyIncident.query.filter_by(
                incident_type=incident_type,
                description=description,
                created_at=created_at.date()
            ).first()
            
            if not existing:
                incident = SafetyIncident(
                    event_id=random.choice(events).id if events else None,
                    incident_type=incident_type,
                    description=description,
                    severity=severity,
                    reported_by=user.id,
                    status=status,
                    created_at=created_at
                )
                db.session.add(incident)
                incidents_created += 1
        
        db.session.commit()
        print(f"   ✓ Created {incidents_created} safety incidents")
        
        print("\n" + "=" * 60)
        print("✅ FOOD SAFETY SAMPLE DATA SEEDING COMPLETE")
        print("=" * 60)
        print(f"\nCreated:")
        print(f"  - {temp_logs_created} temperature logs")
        print(f"  - {incidents_created} safety incidents")
        print("\nYou can now view the data at:")
        print("  - /food-safety/reports")
        print("  - /food-safety/dashboard")
        print()
        
        return True

if __name__ == "__main__":
    success = seed_food_safety_data()
    sys.exit(0 if success else 1)

