"""Migration script to create operational service management tables."""
from sas_management import create_app
from sas_management.models import db
from sas_management.service.models import (
    ServiceChecklist,
    ServiceChecklistItemNew,
    ServiceItemMovement,
    ServiceTeamLeader,
    PartTimeServiceStaff,
    ServiceTeamAssignment,
)

app = create_app()

with app.app_context():
    print("Creating operational service management tables...")
    
    try:
        # Create all new tables
        db.create_all()
        
        print("✓ Created service_checklists table")
        print("✓ Created service_checklist_items_new table")
        print("✓ Created service_item_movements table")
        print("✓ Created service_team_leaders table")
        print("✓ Created part_time_service_staff table")
        print("✓ Created service_team_assignments_new table")
        
        print("\n✅ All operational tables created successfully!")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        db.session.rollback()
        raise

