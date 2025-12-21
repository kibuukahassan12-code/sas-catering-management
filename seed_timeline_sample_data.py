"""Seed Event Timeline sample data."""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import db, Event, EventTimeline
from datetime import datetime, timedelta, date, timezone

def seed_timeline_data():
    """Add comprehensive timeline phases to all existing events."""
    app = create_app()
    with app.app_context():
        try:
            # Get all events
            events = Event.query.all()
            
            if not events:
                print("[WARNING] No events found. Please create events first.")
                return
            
            print(f"Found {len(events)} events. Adding timeline phases...")
            
            timeline_phases_added = 0
            
            for event in events:
                # Check if event already has timeline phases
                existing_phases = EventTimeline.query.filter_by(event_id=event.id).count()
                if existing_phases > 0:
                    print(f"  Event '{event.title}' already has {existing_phases} timeline phases. Skipping...")
                    continue
                
                # Get event date (use date or event_date, fallback to today + 30 days)
                event_date = event.date if event.date else (event.event_date if event.event_date else date.today() + timedelta(days=30))
                
                # Define timeline phases with due dates relative to event date
                phases = [
                    {
                        "phase": "Planning",
                        "description": "Initial event planning and client consultation",
                        "days_before_event": 30,
                        "completed": True
                    },
                    {
                        "phase": "Planning",
                        "description": "Menu selection and finalization",
                        "days_before_event": 25,
                        "completed": True
                    },
                    {
                        "phase": "Planning",
                        "description": "Venue confirmation and site visit",
                        "days_before_event": 20,
                        "completed": True
                    },
                    {
                        "phase": "Prep",
                        "description": "Staff assignment and briefing",
                        "days_before_event": 14,
                        "completed": True
                    },
                    {
                        "phase": "Prep",
                        "description": "Equipment and inventory preparation",
                        "days_before_event": 7,
                        "completed": False
                    },
                    {
                        "phase": "Prep",
                        "description": "Final menu prep and quality check",
                        "days_before_event": 3,
                        "completed": False
                    },
                    {
                        "phase": "Prep",
                        "description": "Pre-event setup and logistics coordination",
                        "days_before_event": 1,
                        "completed": False
                    },
                    {
                        "phase": "Execution",
                        "description": "Event day - Setup and preparation",
                        "days_before_event": 0,
                        "completed": False
                    },
                    {
                        "phase": "Execution",
                        "description": "Event execution - Service delivery",
                        "days_before_event": 0,
                        "completed": False
                    },
                    {
                        "phase": "Post-Event",
                        "description": "Equipment breakdown and cleanup",
                        "days_before_event": -1,
                        "completed": False
                    },
                    {
                        "phase": "Post-Event",
                        "description": "Client feedback collection",
                        "days_before_event": -3,
                        "completed": False
                    },
                    {
                        "phase": "Post-Event",
                        "description": "Final invoicing and payment processing",
                        "days_before_event": -7,
                        "completed": False
                    },
                    {
                        "phase": "Post-Event",
                        "description": "Post-event review and documentation",
                        "days_before_event": -14,
                        "completed": False
                    }
                ]
                
                # Create timeline phases for this event
                for phase_data in phases:
                    due_date = event_date - timedelta(days=phase_data["days_before_event"])
                    
                    # Only create if due date is not in the past (for future events)
                    # For past events, create all phases anyway
                    timeline = EventTimeline(
                        event_id=event.id,
                        phase=phase_data["phase"],
                        description=phase_data["description"],
                        due_date=due_date,
                        completed=phase_data["completed"],
                        completed_at=datetime.now(timezone.utc) if phase_data["completed"] else None
                    )
                    db.session.add(timeline)
                    timeline_phases_added += 1
                
                print(f"  [OK] Added {len(phases)} timeline phases to event '{event.title}'")
            
            db.session.commit()
            print(f"\n[SUCCESS] Successfully added {timeline_phases_added} timeline phases across {len(events)} events!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERROR] Error seeding timeline data: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

if __name__ == "__main__":
    seed_timeline_data()

