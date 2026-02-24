"""
Seed CRM sample data (clients + leads + a few events).

Idempotent by default:
- If the database already has clients or leads, it will NOT create duplicates.
- Pass --force to clear CRM data first.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import argparse

from sas_management.app import app, db
from sas_management.models import (
    Client,
    ClientActivity,
    ClientCommunication,
    ClientNote,
    Event,
    EventStatus,
    IncomingLead,
)


def seed(force: bool = False) -> None:
    with app.app_context():
        sample_emails = {
            "acme@example.com",
            "sarah.nakato@email.com",
            "john.mukasa@email.com",
            "peter.okello@email.com",
            "mary.nalubega@email.com",
            "grace.achieng@email.com",
        }

        if force:
            # Clear only sample-tagged records to avoid wiping real data.
            sample_clients = (
                Client.query.filter(
                    (Client.email.in_(sample_emails))
                    | (Client.tags.ilike("%Sample Data%"))
                ).all()
            )
            sample_client_ids = [c.id for c in sample_clients]

            if sample_client_ids:
                try:
                    Event.query.filter(Event.client_id.in_(sample_client_ids)).delete(synchronize_session=False)
                except Exception:
                    pass
                ClientCommunication.query.filter(ClientCommunication.client_id.in_(sample_client_ids)).delete(synchronize_session=False)
                ClientNote.query.filter(ClientNote.client_id.in_(sample_client_ids)).delete(synchronize_session=False)
                ClientActivity.query.filter(ClientActivity.client_id.in_(sample_client_ids)).delete(synchronize_session=False)
                Client.query.filter(Client.id.in_(sample_client_ids)).delete(synchronize_session=False)

            IncomingLead.query.filter(IncomingLead.email.in_(sample_emails)).delete(synchronize_session=False)
            db.session.commit()

        existing_clients = Client.query.count()
        existing_leads = IncomingLead.query.count()
        if not force and (existing_clients > 0 or existing_leads > 0):
            print(
                f"CRM already has data (clients: {existing_clients}, leads: {existing_leads}). "
                f"Run with --force to replace."
            )
            return

        sample_clients = [
            {"name": "Acme Holdings Ltd", "contact_person": "Daniel Kato", "phone": "+256 700 111 222", "email": "acme@example.com", "tags": "Corporate,VIP"},
            {"name": "Nakato Family", "contact_person": "Sarah Nakato", "phone": "+256 700 123 456", "email": "sarah.nakato@email.com", "tags": "Wedding"},
            {"name": "Mukasa Group", "contact_person": "John Mukasa", "phone": "+256 701 234 567", "email": "john.mukasa@email.com", "tags": "Corporate"},
            {"name": "Okello Events", "contact_person": "Peter Okello", "phone": "+256 709 012 345", "email": "peter.okello@email.com", "tags": "Conference"},
            {"name": "Nalubega Celebrations", "contact_person": "Mary Nalubega", "phone": "+256 708 901 234", "email": "mary.nalubega@email.com", "tags": "Gala"},
        ]

        created_clients: list[Client] = []
        for c in sample_clients:
            existing = Client.query.filter_by(email=c["email"]).first() if c.get("email") else None
            client = existing or Client(
                name=c["name"],
                contact_person=c.get("contact_person"),
                phone=c.get("phone"),
                email=c.get("email"),
                preferred_channel="Phone",
                tags=(c.get("tags") or "") + ",Sample Data",
                is_archived=False,
            )
            db.session.add(client)
            db.session.flush()
            if client not in created_clients:
                created_clients.append(client)

            db.session.add(
                ClientActivity(
                    client_id=client.id,
                    user_id=1,  # system owner
                    activity_type="Created",
                    description="Sample client created",
                )
            )
            db.session.add(
                ClientCommunication(
                    client_id=client.id,
                    user_id=1,
                    communication_type="Email",
                    subject="Welcome to SAS CRM",
                    content="This is a sample communication record created for demonstration.",
                    direction="Outbound",
                )
            )
            db.session.add(
                ClientNote(
                    client_id=client.id,
                    user_id=1,
                    note="Sample note: client prefers timely updates and clear quotations.",
                )
            )

        now = datetime.utcnow()
        leads = [
            ("Sarah Nakato", "sarah.nakato@email.com", "+256 700 123 456", "Wedding", "[SAMPLE] Need full service for 200 guests.", "Qualified", now - timedelta(days=2)),
            ("John Mukasa", "john.mukasa@email.com", "+256 701 234 567", "Corporate Event", "[SAMPLE] Corporate team building for 50 people.", "Proposal Sent", now - timedelta(days=4)),
            ("Grace Achieng", "grace.achieng@email.com", "+256 702 345 678", "Birthday Party", "[SAMPLE] Catering for 80 guests.", "New Lead", now - timedelta(hours=6)),
            ("Peter Okello", "peter.okello@email.com", "+256 709 012 345", "Conference", "[SAMPLE] Tech conference catering for 500 attendees.", "Awaiting Payment", now - timedelta(days=7)),
            ("Acme Holdings Ltd", "acme@example.com", "+256 700 111 222", "Corporate Event", "[SAMPLE] VIP product launch for 120 guests.", "Confirmed", now - timedelta(days=8)),
        ]
        for name, email, phone, inquiry, msg, stage, ts in leads:
            if email and IncomingLead.query.filter_by(email=email).first():
                continue
            db.session.add(
                IncomingLead(
                    client_name=name,
                    email=email,
                    phone=phone,
                    inquiry_type=inquiry,
                    message=msg,
                    pipeline_stage=stage,
                    assigned_user_id=1,
                    timestamp=ts,
                )
            )

        future_1 = (date.today() + timedelta(days=10))
        future_2 = (date.today() + timedelta(days=20))
        if created_clients:
            for idx, (client, when, title) in enumerate(
                [
                    (created_clients[0], future_1, "Acme Product Launch"),
                    (created_clients[1], future_2, "Nakato Wedding Reception"),
                ]
            ):
                db.session.add(
                    Event(
                        title=title,
                        client_id=client.id,
                        client_name=client.contact_person or client.name,
                        client_phone=client.phone,
                        client_email=client.email,
                        date=when,
                        event_date=when,
                        guest_count=120 if idx == 0 else 200,
                        budget_estimate=Decimal("0.00"),
                        quoted_value=0.0,
                        status=EventStatus.NotStarted,
                    )
                )

        db.session.commit()
        print(f"Seeded CRM sample data: clients={len(created_clients)}, leads={len(leads)}, events=2")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Clear CRM data before seeding.")
    args = parser.parse_args()
    seed(force=args.force)

