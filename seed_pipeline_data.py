"""Script to seed sample leads data for the sales pipeline."""
from datetime import datetime, timedelta
from app import create_app
from models import db, IncomingLead, User, UserRole

def seed_pipeline_data():
    """Add sample leads across all pipeline stages."""
    app = create_app()
    
    with app.app_context():
        # Get admin/sales manager users for assignment
        users = User.query.filter(User.role.in_([UserRole.Admin, UserRole.SalesManager])).all()
        if not users:
            print("⚠️  No Admin or SalesManager users found. Creating sample leads without assignments.")
            user_ids = [None]
        else:
            user_ids = [u.id for u in users]
        
        # Sample leads data
        sample_leads = [
            # New Leads
            {
                "client_name": "Sarah Nakato",
                "client_email": "sarah.nakato@email.com",
                "phone": "+256 700 123 456",
                "inquiry_type": "Wedding",
                "message": "Looking for catering services for my wedding in March. Need full service for 200 guests.",
                "pipeline_stage": "New Lead",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=2)
            },
            {
                "client_name": "John Mukasa",
                "client_email": "john.mukasa@email.com",
                "phone": "+256 701 234 567",
                "inquiry_type": "Corporate Event",
                "message": "Corporate team building event for 50 people. Need catering and venue setup.",
                "pipeline_stage": "New Lead",
                "assigned_user_id": None,
                "timestamp": datetime.utcnow() - timedelta(days=1)
            },
            {
                "client_name": "Grace Achieng",
                "client_email": "grace.achieng@email.com",
                "phone": "+256 702 345 678",
                "inquiry_type": "Birthday Party",
                "message": "Planning a 30th birthday party. Need catering for 80 guests with special dietary requirements.",
                "pipeline_stage": "New Lead",
                "assigned_user_id": None,
                "timestamp": datetime.utcnow() - timedelta(hours=5)
            },
            
            # Qualified Leads
            {
                "client_name": "Michael Ochieng",
                "client_email": "michael.ochieng@email.com",
                "phone": "+256 703 456 789",
                "inquiry_type": "Conference",
                "message": "Annual company conference. Need full catering service for 300 attendees over 2 days.",
                "pipeline_stage": "Qualified",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=5)
            },
            {
                "client_name": "Patience Namukasa",
                "client_email": "patience.namukasa@email.com",
                "phone": "+256 704 567 890",
                "inquiry_type": "Graduation Party",
                "message": "Graduation celebration for 150 guests. Looking for buffet service and dessert table.",
                "pipeline_stage": "Qualified",
                "assigned_user_id": user_ids[-1] if len(user_ids) > 1 else user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=4)
            },
            
            # Proposal Sent
            {
                "client_name": "David Kato",
                "client_email": "david.kato@email.com",
                "phone": "+256 705 678 901",
                "inquiry_type": "Wedding",
                "message": "Wedding reception for 250 guests. Full service including bar and dessert station.",
                "pipeline_stage": "Proposal Sent",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=7)
            },
            {
                "client_name": "Ruth Nakiyemba",
                "client_email": "ruth.nakiyemba@email.com",
                "phone": "+256 706 789 012",
                "inquiry_type": "Corporate Event",
                "message": "Product launch event. Need premium catering for 100 VIP guests.",
                "pipeline_stage": "Proposal Sent",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=6)
            },
            
            # Negotiation
            {
                "client_name": "James Ssemwogerere",
                "client_email": "james.ssemwogerere@email.com",
                "phone": "+256 707 890 123",
                "inquiry_type": "Wedding",
                "message": "Large wedding celebration for 400 guests. Negotiating package details and pricing.",
                "pipeline_stage": "Negotiation",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=10)
            },
            
            # Awaiting Payment
            {
                "client_name": "Mary Nalubega",
                "client_email": "mary.nalubega@email.com",
                "phone": "+256 708 901 234",
                "inquiry_type": "Corporate Event",
                "message": "Annual gala dinner for 200 guests. Deposit payment pending.",
                "pipeline_stage": "Awaiting Payment",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=12)
            },
            {
                "client_name": "Peter Okello",
                "client_email": "peter.okello@email.com",
                "phone": "+256 709 012 345",
                "inquiry_type": "Conference",
                "message": "Tech conference catering for 500 attendees. Finalizing payment terms.",
                "pipeline_stage": "Awaiting Payment",
                "assigned_user_id": user_ids[-1] if len(user_ids) > 1 else user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=11)
            },
            
            # Confirmed
            {
                "client_name": "Esther Nakawunde",
                "client_email": "esther.nakawunde@email.com",
                "phone": "+256 710 123 456",
                "inquiry_type": "Wedding",
                "message": "Wedding reception confirmed. Full service package for 180 guests.",
                "pipeline_stage": "Confirmed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=15)
            },
            {
                "client_name": "Robert Mutebi",
                "client_email": "robert.mutebi@email.com",
                "phone": "+256 711 234 567",
                "inquiry_type": "Corporate Event",
                "message": "Company anniversary celebration. Event confirmed and scheduled.",
                "pipeline_stage": "Confirmed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=14)
            },
            
            # Completed
            {
                "client_name": "Florence Nalubowa",
                "client_email": "florence.nalubowa@email.com",
                "phone": "+256 712 345 678",
                "inquiry_type": "Wedding",
                "message": "Successfully completed wedding reception. Excellent service!",
                "pipeline_stage": "Completed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=30)
            },
            {
                "client_name": "Andrew Kigozi",
                "client_email": "andrew.kigozi@email.com",
                "phone": "+256 713 456 789",
                "inquiry_type": "Corporate Event",
                "message": "Corporate event completed successfully. Client very satisfied.",
                "pipeline_stage": "Completed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=25)
            },
            
            # Lost
            {
                "client_name": "Betty Namukasa",
                "client_email": "betty.namukasa@email.com",
                "phone": "+256 714 567 890",
                "inquiry_type": "Birthday Party",
                "message": "Client chose another vendor due to budget constraints.",
                "pipeline_stage": "Lost",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=20)
            }
        ]
        
        # Check if leads already exist
        existing_count = IncomingLead.query.count()
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing leads. Skipping seed to avoid duplicates.")
            print("   To reset, delete existing leads first.")
            return
        
        # Create sample leads
        created_count = 0
        for lead_data in sample_leads:
            lead = IncomingLead(**lead_data)
            db.session.add(lead)
            created_count += 1
        
        try:
            db.session.commit()
            print(f"✅ Successfully created {created_count} sample leads across all pipeline stages!")
            print(f"   - New Lead: {sum(1 for l in sample_leads if l['pipeline_stage'] == 'New Lead')}")
            print(f"   - Qualified: {sum(1 for l in sample_leads if l['pipeline_stage'] == 'Qualified')}")
            print(f"   - Proposal Sent: {sum(1 for l in sample_leads if l['pipeline_stage'] == 'Proposal Sent')}")
            print(f"   - Negotiation: {sum(1 for l in sample_leads if l['pipeline_stage'] == 'Negotiation')}")
            print(f"   - Awaiting Payment: {sum(1 for l in sample_leads if l['pipeline_stage'] == 'Awaiting Payment')}")
            print(f"   - Confirmed: {sum(1 for l in sample_leads if l['pipeline_stage'] == 'Confirmed')}")
            print(f"   - Completed: {sum(1 for l in sample_leads if l['pipeline_stage'] == 'Completed')}")
            print(f"   - Lost: {sum(1 for l in sample_leads if l['pipeline_stage'] == 'Lost')}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating sample leads: {e}")

if __name__ == "__main__":
    seed_pipeline_data()

