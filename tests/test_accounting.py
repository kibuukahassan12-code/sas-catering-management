"""Unit tests for Accounting module."""
import os
import sys
from datetime import date, datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import (
    Account,
    AccountingPayment,
    AccountingReceipt,
    Invoice,
    InvoiceStatus,
    Journal,
    JournalEntry,
    JournalEntryLine,
    User,
    UserRole,
    Event,
    Client,
)
from services.accounting_service import (
    create_invoice,
    create_journal_entry,
    generate_receipt,
    record_payment,
    compute_trial_balance,
)


def test_create_invoice():
    """Test invoice creation."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test client and event
        client = Client(name="Test Client", email="test@example.com", phone="1234567890")
        db.session.add(client)
        db.session.flush()
        
        event = Event(
            event_name="Test Event",
            event_date=date.today(),
            client_id=client.id,
            guest_count=50,
        )
        db.session.add(event)
        db.session.flush()
        
        # Create invoice
        payload = {
            "event_id": event.id,
            "reference": "INV-TEST-001",
            "date": date.today().isoformat(),
            "due_date": date.today().isoformat(),
            "total_amount": "1000000.00",
            "post_to_ledger": True,
        }
        
        invoice = create_invoice(payload)
        
        assert invoice is not None
        assert invoice.invoice_number == "INV-TEST-001"
        assert invoice.total_amount_ugx == Decimal("1000000.00")
        assert invoice.status == InvoiceStatus.Draft
        
        # Check journal entry was created
        entries = JournalEntry.query.filter_by(reference=invoice.invoice_number).all()
        assert len(entries) > 0
        
        # Check journal lines balance
        entry = entries[0]
        total_debits = sum(line.debit for line in entry.lines)
        total_credits = sum(line.credit for line in entry.lines)
        assert total_debits == total_credits
        
        print("✓ test_create_invoice passed")


def test_record_payment_and_receipt():
    """Test payment recording and receipt generation."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test user
        from werkzeug.security import generate_password_hash
        user = User(
            email="cashier@test.com",
            password_hash=generate_password_hash("test"),
            role=UserRole.Admin,
        )
        db.session.add(user)
        db.session.flush()
        
        # Create test client and event
        client = Client(name="Test Client", email="test@example.com", phone="1234567890")
        db.session.add(client)
        db.session.flush()
        
        event = Event(
            event_name="Test Event",
            event_date=date.today(),
            client_id=client.id,
            guest_count=50,
        )
        db.session.add(event)
        db.session.flush()
        
        # Create invoice
        invoice = Invoice(
            event_id=event.id,
            invoice_number="INV-TEST-002",
            issue_date=date.today(),
            due_date=date.today(),
            total_amount_ugx=Decimal("1000000.00"),
            status=InvoiceStatus.Issued,
        )
        db.session.add(invoice)
        db.session.flush()
        
        # Create cash account
        cash_account = Account(
            code="1000",
            name="Cash",
            type="Asset",
            currency="UGX",
        )
        db.session.add(cash_account)
        db.session.flush()
        
        # Record payment
        payment, receipt = record_payment(
            invoice_id=invoice.id,
            amount="500000.00",
            method="cash",
            account_id=cash_account.id,
            received_by=user.id,
        )
        
        assert payment is not None
        assert receipt is not None
        assert payment.amount == Decimal("500000.00")
        assert receipt.reference is not None
        assert receipt.payment_id == payment.id
        
        # Check invoice status updated
        db.session.refresh(invoice)
        assert invoice.status in [InvoiceStatus.Issued, InvoiceStatus.Paid]
        
        print("✓ test_record_payment_and_receipt passed")


def test_journal_balances():
    """Test journal entry double-entry balancing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test user
        from werkzeug.security import generate_password_hash
        user = User(
            email="accountant@test.com",
            password_hash=generate_password_hash("test"),
            role=UserRole.Admin,
        )
        db.session.add(user)
        db.session.flush()
        
        # Create accounts
        cash_account = Account(code="1000", name="Cash", type="Asset", currency="UGX")
        expense_account = Account(code="5000", name="Office Expenses", type="Expense", currency="UGX")
        db.session.add_all([cash_account, expense_account])
        db.session.flush()
        
        # Create balanced journal entry
        lines = [
            {"account_id": expense_account.id, "debit": "100000.00", "credit": "0.00"},
            {"account_id": cash_account.id, "debit": "0.00", "credit": "100000.00"},
        ]
        
        entry = create_journal_entry(
            lines=lines,
            journal_name="General Journal",
            entry_date=date.today().isoformat(),
            reference="JE-TEST-001",
            narration="Test journal entry",
            created_by=user.id,
        )
        
        assert entry is not None
        
        # Verify balances
        total_debits = sum(line.debit for line in entry.lines)
        total_credits = sum(line.credit for line in entry.lines)
        assert total_debits == total_credits
        assert total_debits == Decimal("100000.00")
        
        print("✓ test_journal_balances passed")


def test_unbalanced_journal_entry():
    """Test that unbalanced journal entries are rejected."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        
        # Create test user
        from werkzeug.security import generate_password_hash
        user = User(
            email="accountant@test.com",
            password_hash=generate_password_hash("test"),
            role=UserRole.Admin,
        )
        db.session.add(user)
        db.session.flush()
        
        # Create accounts
        cash_account = Account(code="1000", name="Cash", type="Asset", currency="UGX")
        expense_account = Account(code="5000", name="Office Expenses", type="Expense", currency="UGX")
        db.session.add_all([cash_account, expense_account])
        db.session.flush()
        
        # Create unbalanced journal entry (should fail)
        lines = [
            {"account_id": expense_account.id, "debit": "100000.00", "credit": "0.00"},
            {"account_id": cash_account.id, "debit": "0.00", "credit": "50000.00"},  # Mismatch!
        ]
        
        try:
            entry = create_journal_entry(
                lines=lines,
                journal_name="General Journal",
                entry_date=date.today().isoformat(),
                reference="JE-TEST-002",
                narration="Unbalanced test entry",
                created_by=user.id,
            )
            assert False, "Unbalanced journal entry should have raised ValueError"
        except ValueError as e:
            assert "must balance" in str(e).lower() or "debits" in str(e).lower()
            print("✓ test_unbalanced_journal_entry passed (correctly rejected)")


if __name__ == "__main__":
    print("Running Accounting Module Tests...\n")
    
    try:
        test_create_invoice()
        test_record_payment_and_receipt()
        test_journal_balances()
        test_unbalanced_journal_entry()
        
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

