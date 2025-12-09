"""Accounting service layer for business logic."""
import json
import os
from datetime import date, datetime
from decimal import Decimal
from flask import current_app, render_template, url_for
from io import BytesIO

# Try to import ReportLab - use simple canvas if available
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Fallback if reportlab is not installed
    pass

from sqlalchemy.exc import SQLAlchemyError

from models import (
    Account,
    AccountingPayment,
    AccountingReceipt,
    BankStatement,
    Client,
    Invoice,
    InvoiceStatus,
    Journal,
    JournalEntry,
    JournalEntryLine,
    User,
    db,
)
from sqlalchemy import func


# ============================
# TRIAL BALANCE FUNCTION
# ============================
def compute_trial_balance(start_date=None, end_date=None):
    """
    Computes a simplified trial balance.
    Returns a list of dicts with account name, debit, credit.
    """
    accounts = Account.query.all()
    result = []
    for acc in accounts:
        # Simplified: just return account structure
        result.append({
            "code": acc.code,
            "name": acc.name,
            "debit": 0.0,
            "credit": 0.0,
        })
    return result


# ============================
# PAYMENT RECORDING
# ============================
def record_payment(invoice_id=None, amount=None, method="cash", account_id=None, received_by=None, payment_date=None, reference=None):
    """
    Record a payment for an invoice and generate a receipt.

    Args:
        invoice_id: Optional Invoice ID to link the payment to.
        amount: Amount of the payment.
        method: Payment method (e.g., "cash", "bank", "mobile_money").
        account_id: Optional Account ID where the payment is received.
        received_by: User ID who received the payment.
        payment_date: Date of the payment.
        reference: Optional payment reference.

    Returns:
        Tuple of (AccountingPayment, AccountingReceipt)
    """
    try:
        if not amount or amount <= 0:
            raise ValueError("Payment amount must be positive.")
        amount_decimal = Decimal(str(amount))

        if payment_date:
            if isinstance(payment_date, str):
                payment_date = datetime.strptime(payment_date, "%Y-%m-%d").date()
        else:
            payment_date = date.today()

        invoice = None
        if invoice_id:
            invoice = Invoice.query.get(invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found.")

        # Generate unique payment reference if not provided
        if not reference:
            payment_count = AccountingPayment.query.count()
            reference = f"PAY-{payment_date.strftime('%Y%m%d')}-{payment_count + 1:04d}"
            existing_ref = AccountingPayment.query.filter_by(reference=reference).first()
            if existing_ref:
                reference = f"{reference}-{datetime.utcnow().strftime('%H%M%S')}"

        payment = AccountingPayment(
            invoice_id=invoice_id,
            reference=reference,
            date=payment_date,
            amount=amount_decimal,
            method=method,
            account_id=account_id,
            received_by=received_by
        )
        db.session.add(payment)
        db.session.flush()  # Get payment.id

        # Update invoice status if fully paid
        if invoice_id:
            total_paid = (
                db.session.query(func.coalesce(func.sum(AccountingPayment.amount), Decimal("0.00")))
                .filter(AccountingPayment.invoice_id == invoice_id)
                .scalar()
            )
            if total_paid >= (invoice.total_amount_ugx or Decimal("0.00")):
                invoice.status = InvoiceStatus.Paid

        # Generate receipt
        receipt = generate_receipt(payment.id, issued_by=received_by)

        db.session.commit()

        return payment, receipt

    except Exception as e:
        db.session.rollback()
        try:
            current_app.logger.exception(f"Error recording payment: {e}")
        except:
            pass
        raise


def generate_receipt(payment_id=None, issued_by=None, amount=None, client_id=None, method=None, receipt_date=None, notes=None):
    """
    Generate a receipt for a payment or create a standalone receipt.
    
    Args:
        payment_id: Payment ID (optional - if None, creates standalone receipt)
        issued_by: User ID who issued receipt (optional)
        amount: Amount for standalone receipt (required if payment_id is None)
        client_id: Client ID for standalone receipt (required if payment_id is None)
        method: Payment method for standalone receipt (optional)
        receipt_date: Receipt date (defaults to today)
        notes: Receipt notes (optional)
    
    Returns:
        AccountingReceipt object
    """
    try:
        # If payment_id is provided, use existing payment
        if payment_id:
            payment = AccountingPayment.query.get(payment_id)
            if not payment:
                raise ValueError(f"Payment {payment_id} not found")
        
            # Check if receipt already exists for this payment
            existing_receipt = AccountingReceipt.query.filter_by(payment_id=payment_id).first()
            if existing_receipt:
                return existing_receipt
            
            # Use payment data
            receipt_date = payment.date or date.today()
            receipt_amount = payment.amount
            receipt_method = payment.method
            issued_to = None
            
            # Get client from invoice if available
            if payment.invoice_id:
                invoice = Invoice.query.get(payment.invoice_id)
                if invoice and invoice.event_id:
                    from models import Event
                    event = Event.query.get(invoice.event_id)
                    if event and event.client_id:
                        issued_to = event.client_id
            
            receipt_notes = f"Payment for invoice {payment.invoice_id}" if payment.invoice_id else None
        else:
            # Standalone receipt - validate required fields
            if not amount:
                raise ValueError("amount is required for standalone receipt")
            if not client_id:
                raise ValueError("client_id is required for standalone receipt")
            
            receipt_date = receipt_date or date.today()
            receipt_amount = Decimal(str(amount))
            receipt_method = method or "cash"
            issued_to = client_id
            receipt_notes = notes
            
            # Create a payment record for the standalone receipt
            # (AccountingReceipt requires payment_id)
            from sqlalchemy import func
            payment_count = AccountingPayment.query.count()
            payment_reference = f"PAY-{receipt_date.strftime('%Y%m%d')}-{payment_count + 1:04d}"
            
            # Check if reference already exists
            existing_pay_ref = AccountingPayment.query.filter_by(reference=payment_reference).first()
            if existing_pay_ref:
                payment_reference = f"{payment_reference}-{datetime.utcnow().strftime('%H%M%S')}"
            
            payment = AccountingPayment(
                invoice_id=None,
                reference=payment_reference,
                date=receipt_date,
                amount=receipt_amount,
                method=receipt_method,
                received_by=issued_by
            )
            db.session.add(payment)
            db.session.flush()
            payment_id = payment.id
        
        # Generate unique receipt reference
        receipt_count = AccountingReceipt.query.count()
        reference = f"RCP-{receipt_date.strftime('%Y%m%d')}-{receipt_count + 1:04d}"
        
        # Check if reference already exists
        existing_ref = AccountingReceipt.query.filter_by(reference=reference).first()
        if existing_ref:
            reference = f"{reference}-{datetime.utcnow().strftime('%H%M%S')}"
        
        # Create receipt
        receipt = AccountingReceipt(
            payment_id=payment.id,
            reference=reference,
            issued_by=issued_by or payment.received_by,
            issued_to=issued_to,
            date=receipt_date,
            amount=receipt_amount,
            currency="UGX",
            method=receipt_method,
            notes=receipt_notes
        )
        db.session.add(receipt)
        db.session.flush()
        
        # Generate PDF if ReportLab is available
        if REPORTLAB_AVAILABLE:
            try:
                _generate_pdf_receipt_for_payment(receipt.id)
            except Exception as e:
                try:
                    current_app.logger.warning(f"Could not generate PDF for receipt {receipt.id}: {e}")
                    # Don't fail receipt creation if PDF generation fails
                except:
                    pass
        else:
            try:
                current_app.logger.warning("ReportLab is not installed. PDF receipt will not be generated.")
            except:
                pass
        
        db.session.commit()
        return receipt
        
    except Exception as e:
        db.session.rollback()
        try:
            current_app.logger.exception(f"Error generating receipt: {e}")
        except:
            pass
        raise


def _generate_pdf_receipt_for_payment(receipt_id):
    """Generate PDF for a receipt (internal helper)."""
    receipt = AccountingReceipt.query.get(receipt_id)
    if not receipt:
        raise ValueError(f"Receipt {receipt_id} not found")
    
    payment = receipt.payment
    invoice = payment.invoice if payment.invoice_id else None
    
    client = None
    if receipt.issued_to:
        client = Client.query.get(receipt.issued_to)
    elif invoice and invoice.event_id:
        from models import Event
        event = Event.query.get(invoice.event_id)
        if event and event.client_id:
            client = Client.query.get(event.client_id)
    
    issuer = None
    if receipt.issued_by:
        issuer = User.query.get(receipt.issued_by)
    
    # Generate PDF path
    receipts_folder = os.path.join(current_app.instance_path, "receipts")
    os.makedirs(receipts_folder, exist_ok=True)
    
    pdf_relative_path = f"receipts/receipt_{receipt.reference}.pdf"
    full_path = os.path.join(current_app.instance_path, pdf_relative_path)
    full_path = os.path.abspath(full_path)
    
    _generate_pdf_receipt(
        pdf_path=full_path,
        receipt=receipt,
        payment=payment,
        invoice=invoice,
        client=client,
        issuer=issuer
    )
    
    # Update receipt with PDF path
    receipt.pdf_path = pdf_relative_path
    db.session.commit()


def _generate_pdf_receipt(pdf_path, receipt, payment=None, invoice=None, client=None, issuer=None):
    """
    Generate professional single-page PDF receipt with SAS Best Foods branding.
    
    Args:
        pdf_path: Full path where PDF should be saved
        receipt: AccountingReceipt object
        payment: AccountingPayment object (optional)
        invoice: Invoice object (optional)
        client: Client object (optional)
        issuer: User object (optional)
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is not installed. Install it with: pip install reportlab")
    
    try:
        # SAS Brand Colors
        SAS_ORANGE = colors.HexColor('#F26822')
        SAS_GREEN = colors.HexColor('#2d5016')
        SAS_LIGHT_GRAY = colors.HexColor('#f8f9fa')
        SAS_DARK_GRAY = colors.HexColor('#6c757d')
        SAS_BORDER = colors.HexColor('#e0e0e0')
        
        # Page setup - optimized margins for single page
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                                leftMargin=0.6*inch, rightMargin=0.6*inch,
                                topMargin=0.5*inch, bottomMargin=0.4*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Try to load logo - make it optional so receipt can still generate
        logo_img = None
        try:
            logo_path = os.path.join(current_app.static_folder, 'images', 'sas_logo.png')
            if os.path.exists(logo_path):
                try:
                    # Use PIL to properly load and validate the image first
                    try:
                        from PIL import Image as PILImage
                        # Open and verify the image
                        pil_img = PILImage.open(logo_path)
                        # Convert to RGB if necessary (for PNG with transparency)
                        if pil_img.mode in ('RGBA', 'LA', 'P'):
                            # Create a white background
                            rgb_img = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                            if pil_img.mode == 'P':
                                pil_img = pil_img.convert('RGBA')
                            rgb_img.paste(pil_img, mask=pil_img.split()[-1] if pil_img.mode == 'RGBA' else None)
                            pil_img = rgb_img
                        # Save to a temporary BytesIO for ReportLab
                        from io import BytesIO
                        img_buffer = BytesIO()
                        pil_img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        # Now create ReportLab Image from the buffer
                        logo_img = Image(img_buffer, width=1.2*inch, height=1.2*inch)
                    except ImportError:
                        # PIL not available, try direct loading
                        logo_img = Image(logo_path, width=1.2*inch, height=1.2*inch)
                except Exception as img_error:
                    # If image loading fails, just continue without logo
                    try:
                        current_app.logger.warning(f"Could not load logo image: {img_error}")
                    except:
                        pass
                    logo_img = None
        except Exception as e:
            # If any error occurs, just continue without logo
            try:
                current_app.logger.warning(f"Error checking for logo: {e}")
            except:
                pass
            logo_img = None
        
        # ========== HEADER SECTION ==========
        # Create header table with logo and company info
        header_data = []
        if logo_img:
            header_data.append([logo_img, ''])
        else:
            header_data.append(['', ''])
        
        # Company info column
        company_name_style = ParagraphStyle(
            'CompanyName',
            parent=styles['Normal'],
            fontSize=24,
            textColor=SAS_ORANGE,
            fontName='Helvetica-Bold',
            leading=28,
            spaceAfter=4
        )
        company_tagline_style = ParagraphStyle(
            'CompanyTagline',
            parent=styles['Normal'],
            fontSize=11,
            textColor=SAS_GREEN,
            fontName='Helvetica',
            leading=13,
            spaceAfter=2
        )
        company_address_style = ParagraphStyle(
            'CompanyAddress',
            parent=styles['Normal'],
            fontSize=9,
            textColor=SAS_DARK_GRAY,
            fontName='Helvetica',
            leading=11,
            spaceAfter=1
        )
        
        company_info = [
            Paragraph("SAS BEST FOODS", company_name_style),
            Paragraph("Catering & Event Management", company_tagline_style),
            Paragraph("Near Akamwesi Mall, Gayaza Rd, Opp Electoral Commission", company_address_style),
            Paragraph("Kawempe, Kampala, Uganda", company_address_style),
            Paragraph("Tel: 0702060778 / 0745705088 | www.sasbestfoods.com", company_address_style),
        ]
        
        # Combine logo and company info
        header_cell = Table([[item] for item in company_info], colWidths=[5.5*inch])
        header_cell.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        header_data[0][1] = header_cell
        
        header_table = Table(header_data, colWidths=[1.5*inch, 5.5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Receipt title with decorative border
        title_style = ParagraphStyle(
            'ReceiptTitle',
            parent=styles['Normal'],
            fontSize=20,
            textColor=SAS_ORANGE,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=8
        )
        story.append(Paragraph("OFFICIAL RECEIPT", title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=SAS_ORANGE, spaceAfter=0.2*inch))
        story.append(Spacer(1, 0.15*inch))
        
        # ========== MAIN CONTENT SECTION ==========
        # Define styles
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=SAS_GREEN,
            fontName='Helvetica-Bold',
            spaceAfter=6,
            spaceBefore=8
        )
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=9,
            textColor=SAS_DARK_GRAY,
            fontName='Helvetica-Bold',
            spaceAfter=2
        )
        value_style = ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            fontName='Helvetica',
            spaceAfter=8
        )
        amount_style = ParagraphStyle(
            'Amount',
            parent=styles['Normal'],
            fontSize=18,
            textColor=SAS_ORANGE,
            fontName='Helvetica-Bold',
            spaceAfter=8
        )
        
        # Build left column data (Receipt & Payment Info)
        left_data = []
        left_data.append([Paragraph("RECEIPT DETAILS", section_title_style), ''])
        left_data.append([Paragraph("Receipt Number:", label_style), Paragraph(receipt.reference, value_style)])
        left_data.append([Paragraph("Date:", label_style), Paragraph(receipt.date.strftime('%B %d, %Y') if receipt.date else 'N/A', value_style)])
        left_data.append(['', ''])  # Spacer
        
        # Amount - highlighted box (span both columns)
        amount_text = Paragraph(f"UGX {receipt.amount:,.2f}", amount_style)
        amount_box_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), SAS_LIGHT_GRAY),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -1), 2, SAS_ORANGE),
            ('LINEABOVE', (0, 0), (-1, -1), 2, SAS_ORANGE),
            ('LINELEFT', (0, 0), (-1, -1), 2, SAS_ORANGE),
            ('LINERIGHT', (0, 0), (-1, -1), 2, SAS_ORANGE),
        ])
        amount_table = Table([[amount_text]], colWidths=[2.8*inch])
        amount_table.setStyle(amount_box_style)
        left_data.append([amount_table, ''])
        left_data.append(['', ''])  # Spacer
        
        # Payment details
        if payment:
            left_data.append([Paragraph("PAYMENT INFORMATION", section_title_style), ''])
            payment_method = payment.method or 'N/A'
            method_display = payment_method.replace('_', ' ').title()
            left_data.append([Paragraph("Payment Method:", label_style), Paragraph(method_display, value_style)])
            if payment.reference:
                left_data.append([Paragraph("Payment Reference:", label_style), Paragraph(payment.reference, value_style)])
            left_data.append(['', ''])  # Spacer
        
        # Invoice link
        if invoice:
            left_data.append([Paragraph("INVOICE INFORMATION", section_title_style), ''])
            left_data.append([Paragraph("Invoice Number:", label_style), Paragraph(invoice.invoice_number or f"INV-{invoice.id}", value_style)])
            if invoice.total_amount_ugx:
                left_data.append([Paragraph("Invoice Amount:", label_style), Paragraph(f"UGX {invoice.total_amount_ugx:,.2f}", value_style)])
            left_data.append(['', ''])  # Spacer
        
        # Build right column data (Client Info)
        right_data = []
        
        if client:
            right_data.append([Paragraph("CLIENT INFORMATION", section_title_style), ''])
            right_data.append([Paragraph("Name:", label_style), Paragraph(client.name or 'N/A', value_style)])
            if client.contact_person:
                right_data.append([Paragraph("Contact Person:", label_style), Paragraph(client.contact_person, value_style)])
            if client.company:
                right_data.append([Paragraph("Company:", label_style), Paragraph(client.company, value_style)])
            if client.email:
                right_data.append([Paragraph("Email:", label_style), Paragraph(client.email, value_style)])
            if client.phone:
                right_data.append([Paragraph("Phone:", label_style), Paragraph(client.phone, value_style)])
            if client.address:
                right_data.append([Paragraph("Address:", label_style), Paragraph(client.address, value_style)])
            right_data.append(['', ''])  # Spacer
        
        # Issued by
        if issuer:
            right_data.append([Paragraph("ISSUED BY", section_title_style), ''])
            issuer_name = issuer.email or (issuer.name if hasattr(issuer, 'name') else 'N/A')
            right_data.append([Paragraph("Name:", label_style), Paragraph(issuer_name, value_style)])
            right_data.append(['', ''])  # Spacer
        
        # Notes section
        if receipt.notes:
            notes_style = ParagraphStyle(
                'Notes',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.black,
                fontName='Helvetica',
                spaceAfter=8
            )
            right_data.append([Paragraph("NOTES", section_title_style), ''])
            right_data.append([Paragraph(receipt.notes, notes_style), ''])
        
        # Create two-column layout tables
        left_table = Table(left_data, colWidths=[1.2*inch, 1.8*inch])
        right_table = Table(right_data, colWidths=[1.2*inch, 1.8*inch])
        
        # Style the tables
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ])
        left_table.setStyle(table_style)
        right_table.setStyle(table_style)
        
        # Combine into main two-column layout
        main_data = [[left_table, right_table]]
        main_table = Table(main_data, colWidths=[3.2*inch, 3.2*inch])
        main_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(main_table)
        story.append(Spacer(1, 0.25*inch))
        
        # ========== FOOTER SECTION ==========
        story.append(HRFlowable(width="100%", thickness=1, color=SAS_BORDER, spaceAfter=0.15*inch))
        
        thank_you_style = ParagraphStyle(
            'ThankYou',
            parent=styles['Normal'],
            fontSize=12,
            textColor=SAS_GREEN,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=6
        )
        story.append(Paragraph("Thank you for your business!", thank_you_style))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=SAS_DARK_GRAY,
            alignment=TA_CENTER,
            spaceAfter=2
        )
        story.append(Paragraph("This is an official receipt. Please keep for your records.", footer_style))
        story.append(Paragraph("SAS Best Foods - Catering & Event Management", footer_style))
        
        doc.build(story)
        
    except Exception as e:
        try:
            current_app.logger.exception(f"Error generating PDF receipt: {e}")
        except:
            pass
        raise


def create_journal_entry(*args, **kwargs):
    """Create journal entry - placeholder implementation."""
    raise NotImplementedError("create_journal_entry() not implemented yet.")


def reconcile_bank_statement(*args, **kwargs):
    """Reconcile bank statement - placeholder implementation."""
    raise NotImplementedError("reconcile_bank_statement() not implemented yet.")


def compute_profit_and_loss(*args, **kwargs):
    """Compute profit and loss statement - placeholder implementation."""
    return {"income": 0, "expenses": 0, "profit": 0}


def compute_balance_sheet(*args, **kwargs):
    """Compute balance sheet - placeholder implementation."""
    return {"assets": 0, "liabilities": 0, "equity": 0}
