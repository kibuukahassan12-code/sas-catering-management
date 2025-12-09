"""Seed sample accounting data for SAS Best Foods."""
from app import create_app, db
from models import (
    Account,
    Invoice,
    InvoiceStatus,
    AccountingPayment,
    AccountingReceipt,
    Event,
    Client,
    User,
    UserRole,
    Journal,
    JournalEntry,
    JournalEntryLine,
)
from datetime import date, datetime, timedelta
from decimal import Decimal
from werkzeug.security import generate_password_hash


def seed_accounting_sample_data():
    """Seed sample invoices, payments, and receipts."""
    app = create_app()
    
    with app.app_context():
        print("Seeding Accounting Sample Data...")
        
        # Check if sample data already exists
        if Invoice.query.count() > 0 or AccountingPayment.query.count() > 0:
            print("Sample accounting data already exists. Skipping...")
            print(f"  Current invoices: {Invoice.query.count()}")
            print(f"  Current payments: {AccountingPayment.query.count()}")
            print(f"  Current receipts: {AccountingReceipt.query.count()}")
            return
        
        # Get or create test client
        client = Client.query.filter_by(email="sample_client@sasbestfoods.com").first()
        if not client:
            client = Client(
                name="Sample Corporate Client",
                email="sample_client@sasbestfoods.com",
                phone="0701234567",
                contact_person="John Doe",
                company="ABC Corporation",
            )
            db.session.add(client)
            db.session.flush()
            print(f"  ✓ Created sample client: {client.name}")
        
        # Get or create test user (cashier)
        user = User.query.filter_by(email="cashier@sasbestfoods.com").first()
        if not user:
            user = User(
                email="cashier@sasbestfoods.com",
                password_hash=generate_password_hash("password123"),
                role=UserRole.SalesManager,
            )
            db.session.add(user)
            db.session.flush()
            print(f"  ✓ Created sample user: {user.email}")
        
        # Get accounts
        cash_account = Account.query.filter_by(code="1000").first()
        bank_account = Account.query.filter_by(code="1100").first()
        ar_account = Account.query.filter_by(code="1200").first()
        sales_account = Account.query.filter_by(code="4000").first()
        
        if not all([cash_account, ar_account, sales_account]):
            print("  ⚠ Warning: Some accounts missing. Please run seed_chart_of_accounts.py first.")
            return
        
        # Get or create journals
        sales_journal = Journal.query.filter_by(name="Sales Journal").first()
        if not sales_journal:
            sales_journal = Journal(name="Sales Journal")
            db.session.add(sales_journal)
            db.session.flush()
        
        cash_journal = Journal.query.filter_by(name="Cash Receipts Journal").first()
        if not cash_journal:
            cash_journal = Journal(name="Cash Receipts Journal")
            db.session.add(cash_journal)
            db.session.flush()
        
        # Create sample events for invoices
        events = []
        event_names = [
            "Corporate Lunch Event",
            "Wedding Reception",
            "Birthday Party",
            "Annual Gala Dinner",
            "Product Launch Event",
        ]
        
        for i, event_name in enumerate(event_names):
            event = Event(
                event_name=event_name,
                event_date=date.today() + timedelta(days=30 + i*10),
                client_id=client.id,
                guest_count=50 + i*20,
                status="Confirmed",
            )
            db.session.add(event)
            events.append(event)
        db.session.flush()
        print(f"  ✓ Created {len(events)} sample events")
        
        # Create sample invoices
        invoices = []
        invoice_data = [
            {"amount": 2500000, "status": InvoiceStatus.Paid, "days_ago": 60},
            {"amount": 1500000, "status": InvoiceStatus.Paid, "days_ago": 45},
            {"amount": 3200000, "status": InvoiceStatus.Issued, "days_ago": 30},
            {"amount": 1800000, "status": InvoiceStatus.Draft, "days_ago": 15},
            {"amount": 2800000, "status": InvoiceStatus.Paid, "days_ago": 90},
            {"amount": 1200000, "status": InvoiceStatus.Issued, "days_ago": 20},
            {"amount": 2100000, "status": InvoiceStatus.Paid, "days_ago": 75},
        ]
        
        for i, inv_data in enumerate(invoice_data):
            invoice_date = date.today() - timedelta(days=inv_data["days_ago"])
            invoice = Invoice(
                invoice_number=f"INV-{invoice_date.strftime('%Y%m%d')}-{i+1:03d}",
                issue_date=invoice_date,
                due_date=invoice_date + timedelta(days=30),
                total_amount_ugx=Decimal(str(inv_data["amount"])),
                status=inv_data["status"],
                event_id=events[i % len(events)].id if i < len(events) else events[0].id,
            )
            db.session.add(invoice)
            invoices.append(invoice)
        db.session.flush()
        print(f"  ✓ Created {len(invoices)} sample invoices")
        
        # Create journal entries for invoices
        for invoice in invoices:
            entry = JournalEntry(
                journal_id=sales_journal.id,
                reference=invoice.invoice_number,
                date=invoice.issue_date,
                narration=f"Invoice {invoice.invoice_number}",
            )
            db.session.add(entry)
            db.session.flush()
            
            # Debit AR, Credit Revenue
            db.session.add(JournalEntryLine(
                entry_id=entry.id,
                account_id=ar_account.id,
                debit=invoice.total_amount_ugx,
                credit=Decimal("0.00"),
            ))
            db.session.add(JournalEntryLine(
                entry_id=entry.id,
                account_id=sales_account.id,
                debit=Decimal("0.00"),
                credit=invoice.total_amount_ugx,
            ))
        db.session.flush()
        print(f"  ✓ Created journal entries for invoices")
        
        # Create payments for paid invoices
        payments = []
        receipts = []
        
        paid_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.Paid]
        payment_methods = ["cash", "bank_transfer", "mobile_money", "pos", "cash"]
        
        for i, invoice in enumerate(paid_invoices):
            payment_date = invoice.issue_date + timedelta(days=5 + i*2)
            
            # Create payment
            payment = AccountingPayment(
                invoice_id=invoice.id,
                reference=f"PAY-{payment_date.strftime('%Y%m%d')}-{i+1:04d}",
                date=payment_date,
                amount=invoice.total_amount_ugx,
                method=payment_methods[i % len(payment_methods)],
                account_id=cash_account.id if i % 2 == 0 else (bank_account.id if bank_account else cash_account.id),
                received_by=user.id,
            )
            db.session.add(payment)
            payments.append(payment)
        db.session.flush()
        print(f"  ✓ Created {len(payments)} sample payments")
        
        # Create journal entries for payments
        for payment in payments:
            entry = JournalEntry(
                journal_id=cash_journal.id,
                reference=payment.reference,
                date=payment.date,
                narration=f"Payment for invoice {payment.invoice.invoice_number}",
            )
            db.session.add(entry)
            db.session.flush()
            
            # Debit Cash/Bank, Credit AR
            db.session.add(JournalEntryLine(
                entry_id=entry.id,
                account_id=payment.account_id,
                debit=payment.amount,
                credit=Decimal("0.00"),
            ))
            db.session.add(JournalEntryLine(
                entry_id=entry.id,
                account_id=ar_account.id,
                debit=Decimal("0.00"),
                credit=payment.amount,
            ))
        db.session.flush()
        print(f"  ✓ Created journal entries for payments")
        
        # Create receipts for payments
        for i, payment in enumerate(payments):
            receipt = AccountingReceipt(
                payment_id=payment.id,
                reference=f"RCP-{payment.date.strftime('%Y%m%d')}-{i+1:04d}",
                issued_by=user.id,
                issued_to=client.id,
                date=payment.date,
                amount=payment.amount,
                currency="UGX",
                method=payment.method,
                notes=f"Payment for invoice {payment.invoice.invoice_number}",
            )
            db.session.add(receipt)
            receipts.append(receipt)
        db.session.flush()
        print(f"  ✓ Created {len(receipts)} sample receipts")
        
        # Create a partial payment for one issued invoice
        issued_invoice = next((inv for inv in invoices if inv.status == InvoiceStatus.Issued), None)
        if issued_invoice:
            partial_payment = AccountingPayment(
                invoice_id=issued_invoice.id,
                reference=f"PAY-{date.today().strftime('%Y%m%d')}-PARTIAL-001",
                date=date.today() - timedelta(days=5),
                amount=issued_invoice.total_amount_ugx * Decimal("0.5"),  # 50% payment
                method="mobile_money",
                account_id=cash_account.id,
                received_by=user.id,
            )
            db.session.add(partial_payment)
            db.session.flush()
            
            # Create receipt for partial payment
            partial_receipt = AccountingReceipt(
                payment_id=partial_payment.id,
                reference=f"RCP-{partial_payment.date.strftime('%Y%m%d')}-PARTIAL-001",
                issued_by=user.id,
                issued_to=client.id,
                date=partial_payment.date,
                amount=partial_payment.amount,
                currency="UGX",
                method=partial_payment.method,
                notes=f"Partial payment for invoice {issued_invoice.invoice_number}",
            )
            db.session.add(partial_receipt)
            db.session.flush()
            print(f"  ✓ Created partial payment and receipt")
        
        db.session.commit()
        
        # Print summary
        total_invoices = Invoice.query.count()
        paid_invoices = Invoice.query.filter_by(status=InvoiceStatus.Paid).count()
        pending_invoices = Invoice.query.filter(Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft])).count()
        total_payments = AccountingPayment.query.count()
        total_receipts = AccountingReceipt.query.count()
        total_revenue = db.session.query(db.func.sum(Invoice.total_amount_ugx)).filter_by(status=InvoiceStatus.Paid).scalar() or 0
        pending_amount = db.session.query(db.func.sum(Invoice.total_amount_ugx)).filter(
            Invoice.status.in_([InvoiceStatus.Issued, InvoiceStatus.Draft])
        ).scalar() or 0
        
        print("\n✓ Sample Accounting Data Seeded Successfully!")
        print("\nSummary:")
        print(f"  Total Invoices: {total_invoices}")
        print(f"  Paid Invoices: {paid_invoices}")
        print(f"  Pending Invoices: {pending_invoices}")
        print(f"  Total Payments: {total_payments}")
        print(f"  Total Receipts: {total_receipts}")
        print(f"  Total Revenue: {float(total_revenue):,.2f} UGX")
        print(f"  Pending Amount: {float(pending_amount):,.2f} UGX")


if __name__ == "__main__":
    seed_accounting_sample_data()

