"""Migration script to add Accounting Department tables."""
import sqlite3
import os

# Get the database path
db_path = os.path.join("instance", "site.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}. Creating new database structure...")
    print("Please run the app once to create the database, then run this migration.")
    exit(1)

print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Starting Accounting Department module migration...")

# Create account table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            parent_id INTEGER,
            type VARCHAR(50) NOT NULL,
            currency VARCHAR(10) DEFAULT 'UGX',
            created_at DATETIME,
            FOREIGN KEY (parent_id) REFERENCES account(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'account'")
except Exception as e:
    print(f"  Error creating 'account' table: {e}")
    conn.rollback()

# Create journal table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            created_at DATETIME
        )
    """)
    conn.commit()
    print("[OK] Created table 'journal'")
except Exception as e:
    print(f"  Error creating 'journal' table: {e}")
    conn.rollback()

# Create journal_entry table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_id INTEGER NOT NULL,
            reference VARCHAR(120),
            date DATE NOT NULL,
            narration TEXT,
            created_at DATETIME,
            created_by INTEGER,
            FOREIGN KEY (journal_id) REFERENCES journal(id),
            FOREIGN KEY (created_by) REFERENCES user(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'journal_entry'")
except Exception as e:
    print(f"  Error creating 'journal_entry' table: {e}")
    conn.rollback()

# Create journal_entry_line table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entry_line (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            debit NUMERIC(14,2) DEFAULT 0.0,
            credit NUMERIC(14,2) DEFAULT 0.0,
            created_at DATETIME,
            FOREIGN KEY (entry_id) REFERENCES journal_entry(id),
            FOREIGN KEY (account_id) REFERENCES account(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'journal_entry_line'")
except Exception as e:
    print(f"  Error creating 'journal_entry_line' table: {e}")
    conn.rollback()

# Create accounting_payment table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounting_payment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            reference VARCHAR(120) UNIQUE,
            date DATE NOT NULL,
            amount NUMERIC(14,2) DEFAULT 0.0,
            method VARCHAR(50) NOT NULL,
            account_id INTEGER,
            received_by INTEGER,
            created_at DATETIME,
            FOREIGN KEY (invoice_id) REFERENCES invoice(id),
            FOREIGN KEY (account_id) REFERENCES account(id),
            FOREIGN KEY (received_by) REFERENCES user(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'accounting_payment'")
except Exception as e:
    print(f"  Error creating 'accounting_payment' table: {e}")
    conn.rollback()

# Create accounting_receipt table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounting_receipt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id INTEGER NOT NULL,
            reference VARCHAR(120) UNIQUE NOT NULL,
            issued_by INTEGER,
            issued_to INTEGER,
            date DATE NOT NULL,
            amount NUMERIC(14,2) DEFAULT 0.0,
            currency VARCHAR(10) DEFAULT 'UGX',
            method VARCHAR(50),
            notes TEXT,
            pdf_path VARCHAR(255),
            created_at DATETIME,
            FOREIGN KEY (payment_id) REFERENCES accounting_payment(id),
            FOREIGN KEY (issued_by) REFERENCES user(id),
            FOREIGN KEY (issued_to) REFERENCES client(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'accounting_receipt'")
except Exception as e:
    print(f"  Error creating 'accounting_receipt' table: {e}")
    conn.rollback()

# Create bank_statement table
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_statement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            date DATE NOT NULL,
            description VARCHAR(255),
            amount NUMERIC(14,2) DEFAULT 0.0,
            txn_type VARCHAR(10) NOT NULL,
            reconciled BOOLEAN DEFAULT 0,
            journal_entry_id INTEGER,
            created_at DATETIME,
            FOREIGN KEY (account_id) REFERENCES account(id),
            FOREIGN KEY (journal_entry_id) REFERENCES journal_entry(id)
        )
    """)
    conn.commit()
    print("[OK] Created table 'bank_statement'")
except Exception as e:
    print(f"  Error creating 'bank_statement' table: {e}")
    conn.rollback()

# Check if tables already exist
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('account', 'journal', 'journal_entry', 'journal_entry_line', 'accounting_payment', 'accounting_receipt', 'bank_statement')")
    existing_tables = [row[0] for row in cursor.fetchall()]
    if existing_tables:
        print(f"  Note: Tables already exist: {', '.join(existing_tables)}")
except Exception as e:
    print(f"  Note: {e}")

conn.close()
print("\nMigration completed! Accounting Department module tables are now available.")
print("You may need to restart the application for changes to take full effect.")

