"""Enhanced Sales Pipeline with professional UI and comprehensive sample data."""
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from sas_management.models import (
    Client, Event, IncomingLead, Invoice, User, UserRole, db
)
from sas_management.utils import role_required

crm_bp = Blueprint("crm", __name__, url_prefix="/crm")

# Professional sample data with realistic scenarios
PROFESSIONAL_SAMPLE_LEADS = [
    # New Leads
    {
        "client_name": "Sarah Nakato",
        "email": "sarah.nakato@email.com",
        "phone": "+256 700 123 456",
        "inquiry_type": "Wedding",
        "message": "Planning a grand wedding reception for 200 guests in March. Need full-service catering including bar service, dessert station, and waitstaff. Budget: 15M UGX.",
        "pipeline_stage": "New Lead",
        "timestamp": datetime.utcnow() - timedelta(hours=3)
    },
    {
        "client_name": "John Mukasa",
        "email": "john.mukasa@email.com",
        "phone": "+256 701 234 567",
        "inquiry_type": "Corporate Event",
        "message": "Corporate team building event for 50 executives. Need premium catering, venue setup, and AV equipment. Date: Next month.",
        "pipeline_stage": "New Lead",
        "timestamp": datetime.utcnow() - timedelta(hours=12)
    },
    {
        "client_name": "Grace Achieng",
        "email": "grace.achieng@email.com",
        "phone": "+256 702 345 678",
        "inquiry_type": "Birthday Party",
        "message": "30th birthday celebration for 80 guests. Special dietary requirements: vegetarian, gluten-free options needed.",
        "pipeline_stage": "New Lead",
        "timestamp": datetime.utcnow() - timedelta(hours=6)
    },
    {
        "client_name": "David Kigozi",
        "email": "david.kigozi@email.com",
        "phone": "+256 703 456 789",
        "inquiry_type": "Graduation Party",
        "message": "University graduation party for 120 guests. Need buffet service and dessert table. Looking for competitive pricing.",
        "pipeline_stage": "New Lead",
        "timestamp": datetime.utcnow() - timedelta(hours=1)
    },
    
    # Qualified Leads
    {
        "client_name": "Michael Ochieng",
        "email": "michael.ochieng@email.com",
        "phone": "+256 704 567 890",
        "inquiry_type": "Conference",
        "message": "Annual company conference for 300 attendees over 2 days. Full catering service including breakfast, lunch, and coffee breaks.",
        "pipeline_stage": "Qualified",
        "timestamp": datetime.utcnow() - timedelta(days=2)
    },
    {
        "client_name": "Patience Namukasa",
        "email": "patience.namukasa@email.com",
        "phone": "+256 705 678 901",
        "inquiry_type": "Wedding",
        "message": "Wedding reception for 150 guests. Interested in premium package. Budget confirmed: 12M UGX.",
        "pipeline_stage": "Qualified",
        "timestamp": datetime.utcnow() - timedelta(days=1)
    },
    {
        "client_name": "Robert Mutebi",
        "email": "robert.mutebi@email.com",
        "phone": "+256 706 789 012",
        "inquiry_type": "Corporate Event",
        "message": "Product launch event for 100 VIP guests. Need high-end catering and professional service. Budget: 8M UGX.",
        "pipeline_stage": "Qualified",
        "timestamp": datetime.utcnow() - timedelta(days=3)
    },
    
    # Proposal Sent
    {
        "client_name": "Ruth Nakiyemba",
        "email": "ruth.nakiyemba@email.com",
        "phone": "+256 707 890 123",
        "inquiry_type": "Corporate Event",
        "message": "Annual gala dinner for 200 guests. Premium proposal sent. Awaiting client feedback.",
        "pipeline_stage": "Proposal Sent",
        "timestamp": datetime.utcnow() - timedelta(days=5)
    },
    {
        "client_name": "James Ssemwogerere",
        "email": "james.ssemwogerere@email.com",
        "phone": "+256 708 901 234",
        "inquiry_type": "Wedding",
        "message": "Large wedding celebration for 400 guests. Comprehensive proposal delivered. Client reviewing options.",
        "pipeline_stage": "Proposal Sent",
        "timestamp": datetime.utcnow() - timedelta(days=4)
    },
    {
        "client_name": "Florence Nalubowa",
        "email": "florence.nalubowa@email.com",
        "phone": "+256 709 012 345",
        "inquiry_type": "Conference",
        "message": "Tech conference catering for 500 attendees. Detailed proposal with multiple package options sent.",
        "pipeline_stage": "Proposal Sent",
        "timestamp": datetime.utcnow() - timedelta(days=6)
    },
    
    # Negotiation
    {
        "client_name": "Peter Okello",
        "email": "peter.okello@email.com",
        "phone": "+256 710 123 456",
        "inquiry_type": "Wedding",
        "message": "Wedding reception for 250 guests. Negotiating package details, pricing, and payment terms. Very interested.",
        "pipeline_stage": "Negotiation",
        "timestamp": datetime.utcnow() - timedelta(days=8)
    },
    {
        "client_name": "Esther Nakawunde",
        "email": "esther.nakawunde@email.com",
        "phone": "+256 711 234 567",
        "inquiry_type": "Corporate Event",
        "message": "Company anniversary celebration. Discussing custom menu options and final pricing. Close to agreement.",
        "pipeline_stage": "Negotiation",
        "timestamp": datetime.utcnow() - timedelta(days=7)
    },
    
    # Awaiting Payment
    {
        "client_name": "Mary Nalubega",
        "email": "mary.nalubega@email.com",
        "phone": "+256 712 345 678",
        "inquiry_type": "Corporate Event",
        "message": "Annual gala dinner for 200 guests. Contract signed. Deposit payment of 3M UGX pending. Expected within 2 days.",
        "pipeline_stage": "Awaiting Payment",
        "timestamp": datetime.utcnow() - timedelta(days=10)
    },
    {
        "client_name": "Andrew Kigozi",
        "email": "andrew.kigozi@email.com",
        "phone": "+256 713 456 789",
        "inquiry_type": "Conference",
        "message": "Tech conference for 500 attendees. Agreement reached. Awaiting 50% deposit payment (5M UGX).",
        "pipeline_stage": "Awaiting Payment",
        "timestamp": datetime.utcnow() - timedelta(days=9)
    },
    
    # Confirmed
    {
        "client_name": "Betty Namukasa",
        "email": "betty.namukasa@email.com",
        "phone": "+256 714 567 890",
        "inquiry_type": "Wedding",
        "message": "Wedding reception confirmed. Full service package for 180 guests. Deposit received. Event scheduled for next month.",
        "pipeline_stage": "Confirmed",
        "timestamp": datetime.utcnow() - timedelta(days=15)
    },
    {
        "client_name": "Charles Ouma",
        "email": "charles.ouma@email.com",
        "phone": "+256 715 678 901",
        "inquiry_type": "Corporate Event",
        "message": "Company anniversary celebration confirmed. Premium package selected. All payments received. Ready for execution.",
        "pipeline_stage": "Confirmed",
        "timestamp": datetime.utcnow() - timedelta(days=12)
    },
    {
        "client_name": "Dorothy Akello",
        "email": "dorothy.akello@email.com",
        "phone": "+256 716 789 012",
        "inquiry_type": "Birthday Party",
        "message": "50th birthday celebration confirmed. Special dietary requirements accommodated. Event date confirmed.",
        "pipeline_stage": "Confirmed",
        "timestamp": datetime.utcnow() - timedelta(days=14)
    },
    
    # Completed
    {
        "client_name": "Francis Lubega",
        "email": "francis.lubega@email.com",
        "phone": "+256 717 890 123",
        "inquiry_type": "Wedding",
        "message": "Successfully completed wedding reception. Excellent service! Client very satisfied. Potential for referrals.",
        "pipeline_stage": "Completed",
        "timestamp": datetime.utcnow() - timedelta(days=30)
    },
    {
        "client_name": "Hellen Nalubega",
        "email": "hellen.nalubega@email.com",
        "phone": "+256 718 901 234",
        "inquiry_type": "Corporate Event",
        "message": "Corporate event completed successfully. Client very satisfied. Excellent feedback received.",
        "pipeline_stage": "Completed",
        "timestamp": datetime.utcnow() - timedelta(days=25)
    },
    {
        "client_name": "Ivan Ssebunya",
        "email": "ivan.ssebunya@email.com",
        "phone": "+256 719 012 345",
        "inquiry_type": "Conference",
        "message": "Tech conference completed. All attendees satisfied. Client requesting quote for next year's event.",
        "pipeline_stage": "Completed",
        "timestamp": datetime.utcnow() - timedelta(days=20)
    },
    
    # Lost
    {
        "client_name": "Jennifer Nakato",
        "email": "jennifer.nakato@email.com",
        "phone": "+256 720 123 456",
        "inquiry_type": "Birthday Party",
        "message": "Client chose another vendor due to budget constraints. Follow-up scheduled for future events.",
        "pipeline_stage": "Lost",
        "timestamp": datetime.utcnow() - timedelta(days=18)
    },
    {
        "client_name": "Kenneth Mubiru",
        "email": "kenneth.mubiru@email.com",
        "phone": "+256 721 234 567",
        "inquiry_type": "Wedding",
        "message": "Client postponed event indefinitely. Marked as lost but maintaining relationship for future opportunities.",
        "pipeline_stage": "Lost",
        "timestamp": datetime.utcnow() - timedelta(days=22)
    }
]

