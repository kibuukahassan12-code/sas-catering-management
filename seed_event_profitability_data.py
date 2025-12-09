"""
Seed script to generate sample data for Event Profitability Analysis.

This script creates:
- Completed events with revenue and COGS
- Staff assignments for those events
- Ready for profitability analysis
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

from models import (
    db, Event, Client, EventStaffAssignment, User, UserRole
)


def seed_event_profitability_data():
    """Generate sample events with profitability data."""
    
    # Check if we already have completed events
    existing_completed = Event.query.filter_by(status="Completed").count()
    if existing_completed >= 10:
        print(f"✓ Already have {existing_completed} completed events. Skipping seed.")
        return
    
    # Get or create clients
    clients = Client.query.limit(5).all()
    if not clients:
        print("⚠️  No clients found. Please create clients first.")
        return
    
    # Get users for staff assignments
    users = User.query.filter(User.role.in_([UserRole.Admin, UserRole.KitchenStaff, UserRole.SalesManager])).all()
    if not users:
        print("⚠️  No users found for staff assignments. Please create users first.")
        return
    
    # Event types and names
    event_types = ["Wedding", "Corporate", "Birthday", "Conference", "Graduation", "Anniversary"]
    event_names = [
        "Grand Wedding Reception",
        "Corporate Annual Dinner",
        "Birthday Celebration",
        "Business Conference",
        "Graduation Party",
        "Anniversary Gala",
        "Product Launch Event",
        "Charity Fundraiser",
        "Holiday Celebration",
        "Team Building Event",
        "Awards Ceremony",
        "Networking Mixer",
        "Cultural Festival",
        "Sports Event Catering",
        "Religious Ceremony"
    ]
    
    # Generate 15 completed events
    events_created = 0
    today = date.today()
    
    for i in range(15):
        # Random date in the past 6 months
        days_ago = random.randint(30, 180)
        event_date = today - timedelta(days=days_ago)
        
        # Random client
        client = random.choice(clients)
        
        # Random event type and name
        event_type = random.choice(event_types)
        event_name = random.choice(event_names)
        
        # Generate realistic revenue (500k to 10M UGX)
        revenue = Decimal(random.randint(500000, 10000000))
        
        # Generate COGS (30% to 60% of revenue for realistic margins)
        cogs_percentage = random.uniform(0.30, 0.60)
        cogs = revenue * Decimal(str(cogs_percentage))
        
        # Guest count (50 to 500)
        guest_count = random.randint(50, 500)
        
        # Create event
        event = Event(
            client_id=client.id,
            event_name=f"{event_name} - {client.name}",
            event_type=event_type,
            event_date=event_date,
            event_time=f"{random.randint(10, 18)}:00",
            guest_count=guest_count,
            venue=f"Venue {random.randint(1, 20)}",
            status="Completed",
            quoted_value=revenue,
            actual_cogs_ugx=cogs,
            notes=f"Sample completed event for profitability analysis. Event type: {event_type}",
            created_at=datetime.utcnow() - timedelta(days=days_ago + 10),
            updated_at=datetime.utcnow() - timedelta(days=days_ago)
        )
        
        db.session.add(event)
        db.session.flush()
        
        # Create staff assignments (3 to 8 staff members per event)
        num_staff = random.randint(3, 8)
        assigned_users = random.sample(users, min(num_staff, len(users)))
        
        roles = ["Chef", "Waiter", "Logistics", "Supervisor", "Cleaner", "Decorator"]
        
        for user in assigned_users:
            role = random.choice(roles)
            assignment = EventStaffAssignment(
                event_id=event.id,
                user_id=user.id,
                role=role,
                notes=f"Assigned for {event_name}"
            )
            db.session.add(assignment)
        
        events_created += 1
        print(f"✓ Created event: {event_name} - Revenue: UGX {revenue:,.0f}, COGS: UGX {cogs:,.0f}, Staff: {num_staff}")
    
    try:
        db.session.commit()
        print(f"\n✅ Successfully created {events_created} completed events with staff assignments!")
        print(f"   You can now generate profitability analysis for these events.")
        print(f"   Go to: Business Intelligence > Event Profitability")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error creating events: {e}")
        raise


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    
    with app.app_context():
        seed_event_profitability_data()

