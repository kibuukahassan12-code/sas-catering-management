# Accounting Department Module - Implementation Guide

## Overview

The Accounting Department module provides comprehensive financial management capabilities for SAS Best Foods, including:
- Chart of Accounts management
- Double-entry bookkeeping (Journals and Journal Entries)
- Invoice creation and management
- Payment processing
- Receipt generation (PDF)
- Bank reconciliation
- Trial Balance and Financial Reports

---

## Features

### 1. Chart of Accounts
- Hierarchical account structure
- Account types: Asset, Liability, Income, Expense, Equity
- Account codes for easy organization (e.g., 1000-1999: Assets)

### 2. Journals & Journal Entries
- Multiple journal types (Sales Journal, Cash Receipts Journal, General Journal, etc.)
- Double-entry validation (debits must equal credits)
- Automatic journal posting for invoices and payments
- Manual journal entry creation

### 3. Invoices
- Create invoices linked to events/clients
- Automatic journal entry posting (Debit AR, Credit Revenue)
- Invoice status tracking: Draft → Issued → Paid/Partially Paid
- Support for tax calculations

### 4. Payments
- Record payments against invoices
- Multiple payment methods: Cash, Bank Transfer, Mobile Money, POS/Card
- Automatic receipt generation
- Journal entry posting (Debit Cash/Bank, Credit AR)

### 5. Receipts
- Automatic PDF receipt generation using ReportLab
- Receipts include:
  - Business details (SAS Best Foods)
  - Invoice and payment references
  - Client information
  - Payment details and method
  - Amount in numbers and words
- PDFs saved to `instance/receipts/` directory
- Download/print receipts via web interface

### 6. Bank Reconciliation
- Import bank statements
- Match bank transactions with journal entries
- Reconcile accounts for accurate cash tracking

### 7. Financial Reports
- Trial Balance
- Profit & Loss Statement (planned)
- Balance Sheet (planned)

---

## Database Models

### Account
- `code`: Account code (e.g., "4000")
- `name`: Account name (e.g., "Sales Revenue")
- `type`: Account type (Asset/Liability/Income/Expense/Equity)
- `parent_id`: Parent account for hierarchical structure
- `currency`: Currency code (default: UGX)

### Journal
- `name`: Journal name (e.g., "Sales Journal", "General Journal")

### JournalEntry
- `journal_id`: Reference to Journal
- `reference`: Reference number (e.g., invoice number)
- `date`: Transaction date
- `narration`: Description of the entry
- `created_by`: User who created the entry

### JournalEntryLine
- `entry_id`: Reference to JournalEntry
- `account_id`: Reference to Account
- `debit`: Debit amount
- `credit`: Credit amount

### AccountingPayment
- `invoice_id`: Reference to Invoice
- `reference`: Payment reference number
- `date`: Payment date
- `amount`: Payment amount
- `method`: Payment method (cash/bank/mobile_money/pos)
- `account_id`: Bank/Cash account
- `received_by`: User who received payment

### AccountingReceipt
- `payment_id`: Reference to AccountingPayment
- `reference`: Receipt reference number
- `date`: Receipt date
- `amount`: Receipt amount
- `method`: Payment method
- `pdf_path`: Path to generated PDF
- `issued_by`: User who issued receipt
- `issued_to`: Client ID

### BankStatement
- `account_id`: Bank account
- `date`: Transaction date
- `description`: Transaction description
- `amount`: Transaction amount
- `txn_type`: credit/debit
- `reconciled`: Reconciliation status
- `journal_entry_id`: Matched journal entry

---

## API Endpoints

### Accounts

#### GET `/api/accounting/accounts`
List all chart of accounts.

**Response:**
```json
{
  "status": "success",
  "accounts": [
    {
      "id": 1,
      "code": "4000",
      "name": "Sales Revenue",
      "type": "Income",
      "parent_id": null,
      "currency": "UGX"
    }
  ]
}
```

#### POST `/api/accounting/accounts`
Create a new account.

**Request Body:**
```json
{
  "code": "4100",
  "name": "Catering Revenue",
  "type": "Income",
  "parent_id": null,
  "currency": "UGX"
}
```

### Invoices

#### GET `/api/accounting/invoices`
List invoices with pagination.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10)

**Response:**
```json
{
  "status": "success",
  "invoices": [
    {
      "id": 1,
      "invoice_number": "INV-20251130-001",
      "issue_date": "2025-11-30",
      "due_date": "2025-12-07",
      "total_amount_ugx": 1000000.00,
      "status": "Issued"
    }
  ],
  "pagination": {
    "page": 1,
    "pages": 5,
    "per_page": 10,
    "total": 50
  }
}
```

#### POST `/api/accounting/invoices`
Create a new invoice.

**Request Body:**
```json
{
  "event_id": 12,
  "reference": "INV-20251130-001",
  "date": "2025-11-30",
  "due_date": "2025-12-07",
  "total_amount": "1000000.00",
  "post_to_ledger": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Invoice created",
  "invoice_id": 1,
  "invoice_number": "INV-20251130-001"
}
```

#### POST `/api/accounting/invoices/<invoice_id>/send`
Send invoice (change status from Draft to Issued).

**Response:**
```json
{
  "status": "success",
  "message": "Invoice sent",
  "invoice_id": 1,
  "invoice_number": "INV-20251130-001"
}
```

### Payments

#### POST `/api/accounting/invoices/<invoice_id>/payments`
Record a payment for an invoice.

**Request Body:**
```json
{
  "amount": "500000.00",
  "method": "cash",
  "account_id": 2,
  "reference": "MOMO-12345"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Payment recorded and receipt generated",
  "payment_id": 1,
  "receipt_id": 1,
  "receipt_reference": "RCP-20251130-0001",
  "pdf_path": "/path/to/receipt.pdf"
}
```

#### POST `/api/accounting/payments/<payment_id>/receipt`
Generate or regenerate receipt for a payment.

**Response:**
```json
{
  "status": "success",
  "message": "Receipt generated",
  "receipt_id": 1,
  "receipt_reference": "RCP-20251130-0001",
  "pdf_path": "/path/to/receipt.pdf"
}
```

### Receipts

#### GET `/api/accounting/receipts/<receipt_id>`
Get receipt details.

**Response:**
```json
{
  "status": "success",
  "receipt": {
    "id": 1,
    "reference": "RCP-20251130-0001",
    "date": "2025-11-30",
    "amount": 500000.00,
    "currency": "UGX",
    "method": "cash",
    "notes": "Payment for invoice INV-20251130-001",
    "pdf_path": "/path/to/receipt.pdf",
    "payment": {
      "id": 1,
      "reference": "PAY-20251130-0001",
      "amount": 500000.00
    },
    "invoice": {
      "id": 1,
      "invoice_number": "INV-20251130-001"
    }
  }
}
```

#### GET `/accounting/receipts/<receipt_id>/pdf`
Download PDF receipt.

### Journal Entries

#### GET `/api/accounting/journal-entries`
List journal entries.

**Response:**
```json
{
  "status": "success",
  "entries": [
    {
      "id": 1,
      "reference": "INV-20251130-001",
      "date": "2025-11-30",
      "narration": "Invoice INV-20251130-001",
      "journal_name": "Sales Journal",
      "lines_count": 2
    }
  ]
}
```

#### POST `/api/accounting/journal-entries`
Create a manual journal entry.

**Request Body:**
```json
{
  "journal_name": "General Journal",
  "date": "2025-11-30",
  "reference": "JE-20251130-001",
  "narration": "Office supplies purchase",
  "lines": [
    {
      "account_id": 5,
      "debit": "100000.00",
      "credit": "0.00"
    },
    {
      "account_id": 1,
      "debit": "0.00",
      "credit": "100000.00"
    }
  ]
}
```

**Note:** Debits must equal credits. The system will validate this.

### Reports

#### GET `/api/accounting/trial-balance`
Get trial balance.

**Query Parameters:**
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)

**Response:**
```json
{
  "status": "success",
  "trial_balance": [
    {
      "account_id": 1,
      "code": "4000",
      "name": "Sales Revenue",
      "type": "Income",
      "debits": 0.0,
      "credits": 5000000.00,
      "balance": -5000000.00
    }
  ]
}
```

---

## HTML Views

### Dashboard
**Route:** `GET /accounting/dashboard`

Shows financial summary including:
- Total invoices
- Paid invoices
- Pending invoices
- Total receipts
- Total payments

### Journal View
**Route:** `GET /accounting/journal`

View all journal entries (Admin only).

### Receipt View
**Route:** `GET /accounting/receipts/<receipt_id>/view`

View receipt details and download PDF.

---

## Sample cURL Commands

### 1. Create Invoice
```bash
curl -X POST http://localhost:5000/api/accounting/invoices \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<session_cookie>" \
  -d '{
    "event_id": 12,
    "reference": "INV-20251130-001",
    "date": "2025-11-30",
    "due_date": "2025-12-07",
    "total_amount": "1000000.00",
    "post_to_ledger": true
  }'
```

### 2. Record Payment
```bash
curl -X POST http://localhost:5000/api/accounting/invoices/1/payments \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<session_cookie>" \
  -d '{
    "amount": "500000.00",
    "method": "cash",
    "account_id": 2,
    "reference": "MOMO-12345"
  }'
```

### 3. Generate Receipt
```bash
curl -X POST http://localhost:5000/api/accounting/payments/1/receipt \
  -H "Cookie: session=<session_cookie>"
```

### 4. List Accounts
```bash
curl -X GET http://localhost:5000/api/accounting/accounts \
  -H "Cookie: session=<session_cookie>"
```

### 5. Create Journal Entry
```bash
curl -X POST http://localhost:5000/api/accounting/journal-entries \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<session_cookie>" \
  -d '{
    "journal_name": "General Journal",
    "date": "2025-11-30",
    "reference": "JE-20251130-001",
    "narration": "Office supplies purchase",
    "lines": [
      {
        "account_id": 5,
        "debit": "100000.00",
        "credit": "0.00"
      },
      {
        "account_id": 1,
        "debit": "0.00",
        "credit": "100000.00"
      }
    ]
  }'
```

### 6. Get Trial Balance
```bash
curl -X GET "http://localhost:5000/api/accounting/trial-balance?date_from=2025-01-01&date_to=2025-12-31" \
  -H "Cookie: session=<session_cookie>"
```

---

## Installation & Setup

### 1. Install Dependencies
```bash
pip install Flask Flask-SQLAlchemy Flask-Login Flask-Migrate reportlab python-dateutil
```

### 2. Initialize Database (if not already done)
The tables are already created via `migrate_accounting_module.py`. However, for Flask-Migrate:

```bash
python -m flask db init          # Only if migrations folder doesn't exist
python -m flask db migrate -m "Add accounting tables"
python -m flask db upgrade
```

### 3. Seed Chart of Accounts
```bash
python seed_chart_of_accounts.py
```

This will create standard accounts including:
- Assets (1000-1999): Cash, Bank, Accounts Receivable, Inventory, Equipment
- Liabilities (2000-2999): Accounts Payable, Tax Payable, Loans
- Equity (3000-3999): Capital, Retained Earnings
- Income (4000-4999): Sales Revenue, Catering Revenue, Bakery Revenue
- Expenses (5000-5999): COGS, Salaries, Rent, Utilities, etc.

### 4. Ensure Receipts Directory Exists
The receipts directory is automatically created at `instance/receipts/` on app startup.

---

## Running Tests

```bash
python tests/test_accounting.py
```

Tests include:
- `test_create_invoice`: Verify invoice creation and journal entry posting
- `test_record_payment_and_receipt`: Verify payment recording and PDF receipt generation
- `test_journal_balances`: Verify double-entry bookkeeping validation
- `test_unbalanced_journal_entry`: Verify unbalanced entries are rejected

---

## Receipt Generation

Receipts are automatically generated when a payment is recorded. The PDF generation uses ReportLab library.

### Receipt Contents:
1. **Header**: SAS Best Foods logo and company details
2. **Receipt Number**: Unique reference (e.g., RCP-20251130-0001)
3. **Date**: Receipt date
4. **Invoice Reference**: Linked invoice number (if applicable)
5. **Client Information**: Name, email, phone
6. **Payment Details**: Description, amount
7. **Total Amount**: Amount in UGX
8. **Payment Method**: Cash, Bank, Mobile Money, POS/Card
9. **Received By**: Cashier/user who processed payment
10. **Footer**: Thank you message

### PDF Location:
Receipts are saved to `instance/receipts/receipt_<reference>.pdf`

### Download Receipt:
- Via API: `GET /accounting/receipts/<receipt_id>/pdf`
- Via Web: Click "Download PDF" button on receipt view page

---

## Manual for Finance Users

### Creating an Invoice

1. Navigate to the Invoice module (or use API)
2. Fill in invoice details:
   - Client/Event
   - Invoice number (or auto-generated)
   - Issue date
   - Due date
   - Total amount
3. Save invoice (status: Draft)
4. Send invoice (status: Issued)

**Journal Entry Created:**
- Debit: Accounts Receivable (1200)
- Credit: Sales Revenue (4000)

### Recording a Payment

1. Navigate to invoice details
2. Click "Record Payment"
3. Enter payment details:
   - Amount
   - Payment method
   - Bank/Cash account
   - Reference number (optional)
4. Submit payment

**Automatic Actions:**
- Payment record created
- Receipt generated (PDF)
- Invoice status updated
- Journal entry created:
  - Debit: Cash/Bank Account
  - Credit: Accounts Receivable

### Creating a Manual Journal Entry

1. Navigate to Journal Entries (Admin only)
2. Click "New Journal Entry"
3. Select journal type (e.g., General Journal)
4. Enter entry details:
   - Reference
   - Date
   - Narration
5. Add journal lines:
   - For each line: select account, enter debit or credit amount
   - **Important**: Total debits must equal total credits
6. Save entry

### Bank Reconciliation

1. Import bank statement (CSV or manual entry)
2. Match bank transactions with journal entries
3. Mark transactions as reconciled
4. Generate reconciliation report

### Viewing Financial Reports

1. Navigate to Accounting Dashboard
2. View Trial Balance:
   - Summary of all account balances
   - Filter by date range
3. View Journal Entries:
   - All transactions in chronological order
   - Filter by journal type

---

## Error Handling

All API endpoints return JSON responses with:
- `status`: "success" or "error"
- `message`: Human-readable message
- Additional data on success

**Common Errors:**
- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Not logged in
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error (check logs)

**Example Error Response:**
```json
{
  "status": "error",
  "message": "Journal entry must balance. Debits: 100000.00, Credits: 50000.00"
}
```

---

## Security & Permissions

- **Admin**: Full access to all accounting functions
- **SalesManager**: Can create invoices, record payments, view receipts
- **Other Roles**: Limited access (view-only in most cases)

All endpoints require authentication (`@login_required`) and role-based authorization (`@role_required`).

---

## Notes

- All monetary amounts are stored as `Decimal` to avoid floating-point rounding errors
- Currency defaults to UGX (Uganda Shillings)
- Receipt PDF generation requires `reportlab` library. If not installed, receipts are created without PDF paths.
- Journal entries are immutable once created (recommendation: create reversing entries for corrections)
- Bank reconciliation is manual; CSV import feature can be added

---

## Future Enhancements

- Automated invoice sending via email
- Automated receipt email to clients
- Profit & Loss statement generation
- Balance Sheet generation
- Cash flow statement
- Budget vs Actual reporting
- Multi-currency support
- Tax report generation (VAT/WHT returns)
- Integration with external accounting software
- Automated bank statement import from CSV/OFX

---

## Support

For issues or questions, contact the development team or refer to the main application documentation.

