"""Seed Communication Hub with sample data."""
from app import create_app
from models import (
    db, Announcement, BulletinPost, DirectMessageThread, DirectMessage,
    EventMessageThread, EventMessage, StaffTask, User, Event
)
from datetime import datetime, date, timedelta

def seed_communication_data():
    """Seed communication hub sample data."""
    app = create_app()
    
    with app.app_context():
        try:
            print("Seeding Communication Hub sample data...")
            
            # Get first admin user
            admin_user = User.query.filter_by(role='Admin').first()
            if not admin_user:
                print("  ⚠️  No admin user found - skipping seed")
                return
            
            # Get second user for direct messaging
            other_user = User.query.filter(User.id != admin_user.id).first()
            
            # 1. Create Welcome Announcement
            existing_announcement = Announcement.query.filter_by(title="Welcome to SAS Internal Hub").first()
            if not existing_announcement:
                announcement = Announcement(
                    title="Welcome to SAS Internal Hub",
                    message="This is your new communication center. Use announcements for company-wide updates, the bulletin board for general posts, and direct messages for private conversations.",
                    image_url="comm_uploads/sample_banner.jpg",  # Will be set if file exists
                    created_by=admin_user.id
                )
                db.session.add(announcement)
                print("    ✓ Welcome announcement created")
            else:
                print("    ✓ Welcome announcement already exists")
            
            # 2. Create Bulletin Post
            existing_bulletin = BulletinPost.query.first()
            if not existing_bulletin:
                bulletin = BulletinPost(
                    message="System update deployed successfully. All features are now operational!",
                    created_by=admin_user.id
                )
                db.session.add(bulletin)
                print("    ✓ Sample bulletin post created")
            else:
                print("    ✓ Bulletin posts already exist")
            
            # 3. Create Direct Message Thread (if we have two users)
            if other_user:
                # Check if thread already exists
                thread = DirectMessageThread.query.filter(
                    ((DirectMessageThread.user_a == admin_user.id) & (DirectMessageThread.user_b == other_user.id)) |
                    ((DirectMessageThread.user_a == other_user.id) & (DirectMessageThread.user_b == admin_user.id))
                ).first()
                
                if not thread:
                    # Ensure user_a < user_b for consistency
                    user_a_id = min(admin_user.id, other_user.id)
                    user_b_id = max(admin_user.id, other_user.id)
                    
                    thread = DirectMessageThread(
                        user_a=user_a_id,
                        user_b=user_b_id
                    )
                    db.session.add(thread)
                    db.session.flush()
                    
                    # Add welcome message
                    message = DirectMessage(
                        thread_id=thread.id,
                        sender_id=admin_user.id,
                        message="Welcome to the new messaging center! You can now send direct messages to team members."
                    )
                    db.session.add(message)
                    print("    ✓ Direct message thread created with welcome message")
                else:
                    print("    ✓ Direct message thread already exists")
            
            # 4. Create Event Message Thread (if events exist)
            first_event = Event.query.first()
            if first_event:
                existing_thread = EventMessageThread.query.filter_by(event_id=first_event.id).first()
                if not existing_thread:
                    thread = EventMessageThread(event_id=first_event.id)
                    db.session.add(thread)
                    db.session.flush()
                    
                    # Add initial message
                    message = EventMessage(
                        thread_id=thread.id,
                        sender_id=admin_user.id,
                        message=f"Discussion thread for event: {first_event.event_name}"
                    )
                    db.session.add(message)
                    print(f"    ✓ Event message thread created for event #{first_event.id}")
                else:
                    print(f"    ✓ Event message thread already exists for event #{first_event.id}")
            
            # 5. Create Sample Task
            existing_task = StaffTask.query.filter_by(title="Sample Task: Review Communication Hub").first()
            if not existing_task and other_user:
                task = StaffTask(
                    assigned_to=other_user.id,
                    assigned_by=admin_user.id,
                    title="Sample Task: Review Communication Hub",
                    details="Please familiarize yourself with the new communication hub features.",
                    priority="medium",
                    due_date=date.today() + timedelta(days=7),
                    status="pending"
                )
                db.session.add(task)
                print("    ✓ Sample task created")
            else:
                print("    ✓ Sample task already exists")
            
            db.session.commit()
            print("\n✅ Communication Hub sample data seeded successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding communication data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    seed_communication_data()

