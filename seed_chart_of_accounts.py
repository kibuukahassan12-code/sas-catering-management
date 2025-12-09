"""Seed initial Chart of Accounts for SAS Best Foods."""
from app import create_app, db
from models import Account


def seed_chart_of_accounts():
    """Seed the chart of accounts with standard accounts."""
    app = create_app()
    
    with app.app_context():
        print("Seeding Chart of Accounts...")
        
        # Check if accounts already exist
        if Account.query.count() > 0:
            print("Chart of Accounts already seeded. Skipping...")
            return
        
        # Asset accounts (1xxx)
        assets = [
            {"code": "1000", "name": "Cash on Hand", "type": "Asset"},
            {"code": "1100", "name": "Bank - Checking Account", "type": "Asset"},
            {"code": "1110", "name": "Bank - Savings Account", "type": "Asset"},
            {"code": "1200", "name": "Accounts Receivable", "type": "Asset"},
            {"code": "1300", "name": "Inventory - Raw Materials", "type": "Asset"},
            {"code": "1310", "name": "Inventory - Finished Goods", "type": "Asset"},
            {"code": "1400", "name": "Prepaid Expenses", "type": "Asset"},
            {"code": "1500", "name": "Equipment", "type": "Asset"},
            {"code": "1510", "name": "Accumulated Depreciation - Equipment", "type": "Asset"},
            {"code": "1600", "name": "Vehicles", "type": "Asset"},
            {"code": "1610", "name": "Accumulated Depreciation - Vehicles", "type": "Asset"},
        ]
        
        # Liability accounts (2xxx)
        liabilities = [
            {"code": "2000", "name": "Accounts Payable", "type": "Liability"},
            {"code": "2100", "name": "Salaries Payable", "type": "Liability"},
            {"code": "2200", "name": "Tax Payable - VAT", "type": "Liability"},
            {"code": "2210", "name": "Tax Payable - WHT", "type": "Liability"},
            {"code": "2300", "name": "Accrued Expenses", "type": "Liability"},
            {"code": "2400", "name": "Short-term Loans", "type": "Liability"},
            {"code": "2500", "name": "Long-term Loans", "type": "Liability"},
        ]
        
        # Equity accounts (3xxx)
        equity = [
            {"code": "3000", "name": "Capital", "type": "Equity"},
            {"code": "3100", "name": "Retained Earnings", "type": "Equity"},
            {"code": "3200", "name": "Current Year Earnings", "type": "Equity"},
        ]
        
        # Income accounts (4xxx)
        income = [
            {"code": "4000", "name": "Sales Revenue", "type": "Income"},
            {"code": "4100", "name": "Catering Revenue", "type": "Income"},
            {"code": "4110", "name": "Bakery Revenue", "type": "Income"},
            {"code": "4120", "name": "POS Revenue", "type": "Income"},
            {"code": "4200", "name": "Other Income", "type": "Income"},
        ]
        
        # Expense accounts (5xxx)
        expenses = [
            {"code": "5000", "name": "Cost of Goods Sold", "type": "Expense"},
            {"code": "5100", "name": "Cost of Goods Sold - Catering", "type": "Expense"},
            {"code": "5110", "name": "Cost of Goods Sold - Bakery", "type": "Expense"},
            {"code": "5200", "name": "Salaries and Wages", "type": "Expense"},
            {"code": "5210", "name": "Kitchen Staff Salaries", "type": "Expense"},
            {"code": "5220", "name": "Administrative Salaries", "type": "Expense"},
            {"code": "5300", "name": "Rent Expense", "type": "Expense"},
            {"code": "5400", "name": "Utilities", "type": "Expense"},
            {"code": "5410", "name": "Electricity", "type": "Expense"},
            {"code": "5420", "name": "Water", "type": "Expense"},
            {"code": "5430", "name": "Internet", "type": "Expense"},
            {"code": "5500", "name": "Marketing and Advertising", "type": "Expense"},
            {"code": "5600", "name": "Transportation", "type": "Expense"},
            {"code": "5700", "name": "Office Supplies", "type": "Expense"},
            {"code": "5800", "name": "Insurance", "type": "Expense"},
            {"code": "5900", "name": "Other Expenses", "type": "Expense"},
        ]
        
        all_accounts = assets + liabilities + equity + income + expenses
        
        for acc_data in all_accounts:
            account = Account(
                code=acc_data["code"],
                name=acc_data["name"],
                type=acc_data["type"],
                currency="UGX",
            )
            db.session.add(account)
        
        db.session.commit()
        print(f"✓ Seeded {len(all_accounts)} accounts to Chart of Accounts")
        print("\nAccount Categories:")
        print(f"  Assets: {len(assets)} accounts")
        print(f"  Liabilities: {len(liabilities)} accounts")
        print(f"  Equity: {len(equity)} accounts")
        print(f"  Income: {len(income)} accounts")
        print(f"  Expenses: {len(expenses)} accounts")


if __name__ == "__main__":
    seed_chart_of_accounts()

