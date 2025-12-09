#!/usr/bin/env python3
"""
Add sample chat messages to the system
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from models import Message, User

def add_chat_sample_data():
    """Add sample chat messages."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("ADDING CHAT SAMPLE DATA")
        print("=" * 60)
        print()
        
        # Get users
        users = User.query.limit(5).all()
        if not users:
            print("❌ No users found. Please create users first.")
            return False
        
        print(f"Found {len(users)} users")
        
        # Sample messages for different channels
        sample_messages = {
            "General": [
                "Good morning team! Let's have a great day today.",
                "Reminder: Team meeting at 2 PM today in the conference room.",
                "Thanks everyone for the hard work yesterday!",
                "Has anyone seen the event checklist for tomorrow?",
                "Great job on the weekend event everyone!",
            ],
            "Kitchen_Ops": [
                "Prep list for today is ready. Check the production sheet.",
                "We need more ingredients for the evening service.",
                "Kitchen inspection completed. All good!",
                "New recipe cards are available in the kitchen.",
                "Reminder: Temperature logs need to be updated every 2 hours.",
            ],
            "Hire_Logistics": [
                "Delivery truck scheduled for 3 PM pickup.",
                "All equipment for tomorrow's event is ready.",
                "Need to confirm delivery address with client.",
                "Equipment maintenance completed on all items.",
                "New inventory items added to the system.",
            ],
            "Production": [
                "Production order #123 is ready for pickup.",
                "All ingredients reserved for today's orders.",
                "Kitchen checklist completed for event #456.",
                "Production sheet updated with latest changes.",
            ],
            "Sales": [
                "New quotation created for client ABC Corp.",
                "Follow up needed on proposal sent last week.",
                "Client meeting scheduled for tomorrow at 10 AM.",
                "Quotation #789 has been approved!",
            ],
            "Support": [
                "System update completed successfully.",
                "If anyone needs help with the new features, let me know!",
                "Password reset requests can be handled through the admin panel.",
            ],
        }
        
        messages_created = 0
        
        for channel, messages in sample_messages.items():
            # Check if channel already has messages
            existing_count = Message.query.filter_by(channel=channel).count()
            if existing_count > 0:
                print(f"   - Channel '{channel}' already has {existing_count} messages, skipping...")
                continue
            
            # Create messages spread over the past week
            today = datetime.now()
            for i, msg_text in enumerate(messages):
                # Spread messages over the past 7 days
                days_ago = random.randint(0, 7)
                hours_ago = random.randint(0, 23)
                message_time = today - timedelta(days=days_ago, hours=hours_ago)
                
                user = random.choice(users)
                
                message = Message(
                    user_id=user.id,
                    channel=channel,
                    content=msg_text,
                    timestamp=message_time,
                )
                db.session.add(message)
                messages_created += 1
        
        try:
            db.session.commit()
            print(f"\n✅ Created {messages_created} sample messages")
            print("\n" + "=" * 60)
            print("✅ CHAT SAMPLE DATA ADDED SUCCESSFULLY")
            print("=" * 60)
            print("\nSample messages added to:")
            for channel in sample_messages.keys():
                count = Message.query.filter_by(channel=channel).count()
                print(f"  - {channel}: {count} messages")
            print()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = add_chat_sample_data()
    sys.exit(0 if success else 1)

