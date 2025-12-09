"""Seed script for CRM Sales Pipeline sample data."""
import sys
from datetime import datetime, timedelta
from random import choice, randint

# Add project root to path
sys.path.insert(0, '.')

from app import create_app
from models import db, IncomingLead, User, UserRole

# Sample lead data
SAMPLE_LEADS = [
    {
        "client_name": "Sarah Mwangi",
        "client_email": "sarah.mwangi@example.com",
        "phone": "+256 700 123456",
        "inquiry_type": "Wedding Catering",
        "message": "Looking for full-service catering for my wedding on June 15th. Expected 150 guests. Please provide a quote with menu options.",
        "pipeline_stage": "New Lead"
    },
    {
        "client_name": "John Okello",
        "client_email": "john.okello@corporation.ug",
        "phone": "+256 701 234567",
        "inquiry_type": "Corporate Event",
        "message": "Annual company dinner for 200 employees. Need buffet style catering with vegetarian options.",
        "pipeline_stage": "Qualified"
    },
    {
        "client_name": "Grace Nakato",
        "client_email": "grace.nakato@gmail.com",
        "phone": "+256 702 345678",
        "inquiry_type": "Birthday Party",
        "message": "Planning a 50th birthday celebration for my mother. Need catering for about 80 people, preferably finger foods and desserts.",
        "pipeline_stage": "Proposal Sent"
    },
    {
        "client_name": "David Kipchoge",
        "client_email": "d.kipchoge@enterprise.co.ke",
        "phone": "+254 720 456789",
        "inquiry_type": "Corporate Event",
        "message": "Product launch event in Kampala. Need premium catering service for 100 VIP guests. Budget flexible.",
        "pipeline_stage": "Negotiation"
    },
    {
        "client_name": "Mary Kamau",
        "client_email": "mary.kamau@events.ug",
        "phone": "+256 703 567890",
        "inquiry_type": "Wedding Catering",
        "message": "Full wedding package needed: ceremony, cocktail hour, and reception. 250 guests. Looking for elegant presentation.",
        "pipeline_stage": "Awaiting Payment"
    },
    {
        "client_name": "Robert Ssemwogerere",
        "client_email": "r.semwogerere@business.ug",
        "phone": "+256 704 678901",
        "inquiry_type": "Corporate Event",
        "message": "Board meeting lunch for 30 executives. Need high-end catering with presentation and service staff.",
        "pipeline_stage": "Confirmed"
    },
    {
        "client_name": "Jennifer Atim",
        "client_email": "j.atim@email.com",
        "phone": "+256 705 789012",
        "inquiry_type": "Graduation Party",
        "message": "Celebrating my son's graduation. Need catering for outdoor event, 120 guests. Looking for BBQ options.",
        "pipeline_stage": "New Lead"
    },
    {
        "client_name": "Michael Ochieng",
        "client_email": "m.ochieng@startup.io",
        "phone": "+256 706 890123",
        "inquiry_type": "Corporate Event",
        "message": "Office opening ceremony. Need cocktail reception catering for 60 guests with canapes and drinks.",
        "pipeline_stage": "Qualified"
    },
    {
        "client_name": "Lucy Nalubega",
        "client_email": "lucy.nalubega@gmail.com",
        "phone": "+256 707 901234",
        "inquiry_type": "Baby Shower",
        "message": "Baby shower celebration for my friend. Need light refreshments, cakes, and finger foods for 50 people.",
        "pipeline_stage": "Proposal Sent"
    },
    {
        "client_name": "James Mutumba",
        "client_email": "j.mutumba@construction.ug",
        "phone": "+256 708 012345",
        "inquiry_type": "Corporate Event",
        "message": "Annual staff appreciation dinner. 150 employees. Need full meal service with dessert options.",
        "pipeline_stage": "Negotiation"
    },
    {
        "client_name": "Patricia Achieng",
        "client_email": "p.achieng@email.com",
        "phone": "+256 709 123456",
        "inquiry_type": "Wedding Catering",
        "message": "Looking for complete wedding catering including appetizers, main course, and dessert buffet. 180 guests.",
        "pipeline_stage": "Qualified"
    },
    {
        "client_name": "Peter Mukasa",
        "client_email": "peter.mukasa@ngo.org",
        "phone": "+256 710 234567",
        "inquiry_type": "Fundraising Event",
        "message": "Charity fundraising gala. Need elegant catering for 200 attendees with premium menu options.",
        "pipeline_stage": "New Lead"
    },
    {
        "client_name": "Esther Namukasa",
        "client_email": "esther.namukasa@gmail.com",
        "phone": "+256 711 345678",
        "inquiry_type": "Anniversary Party",
        "message": "25th wedding anniversary celebration. Looking for special menu with traditional and modern options. 100 guests.",
        "pipeline_stage": "Proposal Sent"
    },
    {
        "client_name": "Samuel Kiwanuka",
        "client_email": "s.kiwanuka@techstartup.ug",
        "phone": "+256 712 456789",
        "inquiry_type": "Product Launch",
        "message": "Tech product launch event. Need modern, Instagram-worthy food presentation for 80 attendees.",
        "pipeline_stage": "Confirmed"
    },
    {
        "client_name": "Ruth Nakibuuka",
        "client_email": "ruth.nakibuuka@hospital.ug",
        "phone": "+256 713 567890",
        "inquiry_type": "Corporate Event",
        "message": "Medical conference catering. Need breakfast, lunch, and coffee breaks for 300 attendees over 2 days.",
        "pipeline_stage": "Completed"
    },
    {
        "client_name": "Thomas Wamala",
        "client_email": "t.wamala@university.ac.ug",
        "phone": "+256 714 678901",
        "inquiry_type": "Graduation Ceremony",
        "message": "University graduation reception. Need buffet-style catering for 500 graduates and families.",
        "pipeline_stage": "Completed"
    },
    {
        "client_name": "Agnes Nakato",
        "client_email": "agnes.nakato@email.com",
        "phone": "+256 715 789012",
        "inquiry_type": "Birthday Party",
        "message": "Children's birthday party. Need kid-friendly menu, birthday cake, and entertainment snacks for 40 children.",
        "pipeline_stage": "New Lead"
    },
    {
        "client_name": "Francis Muleme",
        "client_email": "f.muleme@bank.co.ug",
        "phone": "+256 716 890123",
        "inquiry_type": "Corporate Event",
        "message": "Client appreciation event. Need premium catering with wine pairing options for 120 VIP clients.",
        "pipeline_stage": "Awaiting Payment"
    },
    {
        "client_name": "Betty Nsubuga",
        "client_email": "betty.nsubuga@gmail.com",
        "phone": "+256 717 901234",
        "inquiry_type": "Bridal Shower",
        "message": "Bridal shower brunch. Need elegant brunch menu with mimosas and pastries for 35 guests.",
        "pipeline_stage": "Qualified"
    },
    {
        "client_name": "Kenneth Ssekamwa",
        "client_email": "k.sekamwa@agency.gov.ug",
        "phone": "+256 718 012345",
        "inquiry_type": "Government Event",
        "message": "Ministry event catering. Need formal catering service for 250 government officials and guests.",
        "pipeline_stage": "Lost"
    }
]

def seed_pipeline_data():
    """Seed the database with sample pipeline leads."""
    app = create_app()
    
    with app.app_context():
        # Check if leads already exist
        existing_count = IncomingLead.query.count()
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing leads in database.")
            response = input("Do you want to add more sample leads? (y/n): ").strip().lower()
            if response != 'y':
                print("Skipping seed data creation.")
                return
        
        # Get admin/sales manager users for assignment
        users = User.query.filter(User.role.in_([UserRole.Admin, UserRole.SalesManager])).all()
        
        if not users:
            print("⚠️  No admin or sales manager users found. Creating leads without assignments.")
            users = [None]
        
        # Create leads
        created_count = 0
        base_date = datetime.now() - timedelta(days=30)
        
        for i, lead_data in enumerate(SAMPLE_LEADS):
            # Vary timestamps to make data more realistic
            days_ago = randint(0, 30)
            timestamp = base_date + timedelta(days=days_ago, hours=randint(0, 23))
            
            # Randomly assign some leads
            assigned_user = choice(users) if users and randint(0, 3) > 0 else None
            
            lead = IncomingLead(
                client_name=lead_data["client_name"],
                client_email=lead_data["client_email"],
                phone=lead_data["phone"],
                inquiry_type=lead_data["inquiry_type"],
                message=lead_data["message"],
                pipeline_stage=lead_data["pipeline_stage"],
                assigned_user_id=assigned_user.id if assigned_user else None,
                timestamp=timestamp,
                updated_at=timestamp
            )
            
            db.session.add(lead)
            created_count += 1
        
        try:
            db.session.commit()
            print(f"✅ Successfully created {created_count} sample leads in the pipeline!")
            print("\nPipeline stages distribution:")
            
            # Show distribution
            stages = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", 
                     "Awaiting Payment", "Confirmed", "Completed", "Lost"]
            for stage in stages:
                count = IncomingLead.query.filter_by(pipeline_stage=stage).count()
                print(f"  • {stage}: {count} leads")
            
            print(f"\n📊 Total leads in pipeline: {IncomingLead.query.count()}")
            print("\n✨ Visit /crm/pipeline to view the Kanban board!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating leads: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    seed_pipeline_data()

