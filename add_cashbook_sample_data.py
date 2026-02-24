"""
Add sample cashbook transactions (income and expenditure) to the system.

Usage:
    python add_cashbook_sample_data.py

This script will create a variety of sample transactions including:
- Income from various sources (catering events, hire services, etc.)
- Expenses (salaries, supplies, utilities, etc.)
"""

import sys
import os
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

# Add the parent directory to the path to import sas_management
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sas_management.app import create_app
from sas_management.models import Transaction, TransactionType, db

def add_sample_transactions():
    """Add sample cashbook transactions."""
    app = create_app()
    
    with app.app_context():
        # Check if transactions already exist
        existing_count = Transaction.query.count()
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing transactions.")
            response = input("Do you want to add sample data anyway? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return
        
        print("Creating sample cashbook transactions...")
        
        # Sample income transactions
        income_categories = [
            "Catering Services",
            "Event Management",
            "Hire Services",
            "Bakery Sales",
            "Consulting Fees",
            "Additional Services",
            "Deposits Received",
            "Final Payments",
        ]
        
        income_descriptions = [
            "Corporate event catering for 200 guests",
            "Wedding reception catering services",
            "Equipment hire for outdoor event",
            "Bakery order delivery",
            "Event planning consultation",
            "Additional staffing services",
            "Deposit payment for upcoming event",
            "Final payment received for completed event",
            "Holiday party catering package",
            "Conference catering services",
            "Birthday celebration package",
            "Anniversary dinner service",
            "Bridal shower catering",
            "Graduation party services",
            "Charity event catering",
        ]
        
        # Sample expense transactions
        expense_categories = [
            "Salaries & Wages",
            "Supplies & Ingredients",
            "Utilities",
            "Rent & Facilities",
            "Transportation",
            "Marketing & Advertising",
            "Equipment Maintenance",
            "Insurance",
            "Professional Services",
            "Office Supplies",
            "Training & Development",
            "Communication",
            "Taxes & Fees",
            "Miscellaneous Expenses",
        ]
        
        expense_descriptions = [
            "Monthly payroll for kitchen staff",
            "Fresh produce purchase from supplier",
            "Electricity bill payment",
            "Monthly rent for kitchen facility",
            "Fuel expenses for delivery vehicles",
            "Social media advertising campaign",
            "Kitchen equipment repair and maintenance",
            "Business insurance premium",
            "Accounting services fee",
            "Office stationery and supplies",
            "Staff training workshop",
            "Internet and phone bills",
            "Business license renewal fee",
            "Miscellaneous office expenses",
            "Cleaning supplies purchase",
            "Uniforms for staff",
            "Equipment rental fees",
            "Event permit fees",
            "Bank charges and fees",
            "Legal consultation fee",
        ]
        
        transactions = []
        
        # Generate income transactions (last 6 months)
        print("Generating income transactions...")
        start_date = date.today() - timedelta(days=180)
        
        for i in range(30):  # 30 income transactions
            tx_date = start_date + timedelta(days=random.randint(0, 180))
            category = random.choice(income_categories)
            description = random.choice(income_descriptions)
            amount = Decimal(str(random.randint(500000, 10000000)))  # 500k to 10M
            
            transaction = Transaction(
                type=TransactionType.Income,
                category=category,
                description=description,
                amount=amount,
                date=tx_date,
                related_event_id=None,
                created_at=datetime.now() - timedelta(days=random.randint(0, 180))
            )
            transactions.append(transaction)
        
        # Generate expense transactions (last 6 months)
        print("Generating expense transactions...")
        
        for i in range(40):  # 40 expense transactions
            tx_date = start_date + timedelta(days=random.randint(0, 180))
            category = random.choice(expense_categories)
            description = random.choice(expense_descriptions)
            amount = Decimal(str(random.randint(50000, 5000000)))  # 50k to 5M
            
            transaction = Transaction(
                type=TransactionType.Expense,
                category=category,
                description=description,
                amount=amount,
                date=tx_date,
                related_event_id=None,
                created_at=datetime.now() - timedelta(days=random.randint(0, 180))
            )
            transactions.append(transaction)
        
        # Add some recent transactions (last 30 days)
        print("Adding recent transactions...")
        for i in range(10):  # 10 recent transactions (mix of income and expense)
            tx_date = date.today() - timedelta(days=random.randint(0, 30))
            is_income = random.choice([True, False])
            
            if is_income:
                category = random.choice(income_categories)
                description = random.choice(income_descriptions)
                amount = Decimal(str(random.randint(1000000, 8000000)))  # 1M to 8M
                tx_type = TransactionType.Income
            else:
                category = random.choice(expense_categories)
                description = random.choice(expense_descriptions)
                amount = Decimal(str(random.randint(100000, 3000000)))  # 100k to 3M
                tx_type = TransactionType.Expense
            
            transaction = Transaction(
                type=tx_type,
                category=category,
                description=description,
                amount=amount,
                date=tx_date,
                related_event_id=None,
                created_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            transactions.append(transaction)
        
        # Bulk insert transactions
        print(f"Adding {len(transactions)} transactions to database...")
        try:
            db.session.add_all(transactions)
            db.session.commit()
            print(f"✅ Successfully added {len(transactions)} sample transactions!")
            
            # Show summary
            total_income = sum(tx.amount for tx in transactions if tx.type == TransactionType.Income)
            total_expense = sum(tx.amount for tx in transactions if tx.type == TransactionType.Expense)
            net = total_income - total_expense
            
            print("\n📊 Summary:")
            print(f"   Income transactions: {len([t for t in transactions if t.type == TransactionType.Income])}")
            print(f"   Expense transactions: {len([t for t in transactions if t.type == TransactionType.Expense])}")
            print(f"   Total Income: UGX {total_income:,.2f}")
            print(f"   Total Expenses: UGX {total_expense:,.2f}")
            print(f"   Net Profit: UGX {net:,.2f}")
            print("\n✅ Sample data generation complete!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding transactions: {str(e)}")
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("Cashbook Sample Data Generator")
    print("=" * 60)
    print()
    add_sample_transactions()
