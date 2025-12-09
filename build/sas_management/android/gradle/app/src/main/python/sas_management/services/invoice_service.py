"""Invoice service layer for PDF generation and business logic."""
import os
from datetime import date, datetime
from decimal import Decimal
from flask import current_app

# Try to import ReportLab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    pass

from models import Invoice, Event, Client, db


def generate_invoice_pdf(invoice_id):
    """
    Generate professional PDF invoice with SAS Best Foods branding.
    
    Args:
        invoice_id: Invoice ID to generate PDF for
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is not installed. Install it with: pip install reportlab")
    
    invoice = Invoice.query.options(
        db.joinedload(Invoice.event).joinedload(Event.client)
    ).get(invoice_id)
    
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")
    
    # Generate PDF path
    invoices_folder = os.path.join(current_app.instance_path, "invoices")
    os.makedirs(invoices_folder, exist_ok=True)
    
    pdf_relative_path = f"invoices/invoice_{invoice.invoice_number}.pdf"
    full_path = os.path.join(current_app.instance_path, pdf_relative_path)
    full_path = os.path.abspath(full_path)
    
    # Generate PDF
    _generate_pdf_invoice(
        pdf_path=full_path,
        invoice=invoice,
        event=invoice.event,
        client=invoice.event.client if invoice.event else None
    )
    
    # Update invoice with PDF path (if field exists)
    if hasattr(invoice, 'pdf_path'):
        invoice.pdf_path = pdf_relative_path
        db.session.commit()
    
    return full_path


def _generate_pdf_invoice(pdf_path, invoice, event=None, client=None):
    """
    Generate professional single-page PDF invoice with SAS Best Foods branding.
    
    Args:
        pdf_path: Full path where PDF should be saved
        invoice: Invoice object
        event: Event object (optional)
        client: Client object (optional)
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
        
        # Page setup
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                                leftMargin=0.6*inch, rightMargin=0.6*inch,
                                topMargin=0.5*inch, bottomMargin=0.4*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Try to load logo
        logo_img = None
        try:
            logo_path = os.path.join(current_app.static_folder, 'images', 'sas_logo.png')
            if os.path.exists(logo_path):
                try:
                    from PIL import Image as PILImage
                    from io import BytesIO
                    pil_img = PILImage.open(logo_path)
                    if pil_img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                        if pil_img.mode == 'P':
                            pil_img = pil_img.convert('RGBA')
                        rgb_img.paste(pil_img, mask=pil_img.split()[-1] if pil_img.mode == 'RGBA' else None)
                        pil_img = rgb_img
                    img_buffer = BytesIO()
                    pil_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    logo_img = Image(img_buffer, width=1.2*inch, height=1.2*inch)
                except ImportError:
                    logo_img = Image(logo_path, width=1.2*inch, height=1.2*inch)
                except Exception:
                    logo_img = None
        except Exception:
            logo_img = None
        
        # ========== HEADER SECTION ==========
        header_data = []
        if logo_img:
            header_data.append([logo_img, ''])
        else:
            header_data.append(['', ''])
        
        # Company info
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
        
        # Invoice title
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Normal'],
            fontSize=20,
            textColor=SAS_ORANGE,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=8
        )
        story.append(Paragraph("INVOICE", title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=SAS_ORANGE, spaceAfter=0.2*inch))
        story.append(Spacer(1, 0.15*inch))
        
        # ========== INVOICE DETAILS SECTION ==========
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
        
        # Left column - Invoice details
        left_data = []
        left_data.append([Paragraph("INVOICE DETAILS", section_title_style), ''])
        left_data.append([Paragraph("Invoice Number:", label_style), Paragraph(invoice.invoice_number, value_style)])
        left_data.append([Paragraph("Issue Date:", label_style), Paragraph(invoice.issue_date.strftime('%B %d, %Y') if invoice.issue_date else 'N/A', value_style)])
        left_data.append([Paragraph("Due Date:", label_style), Paragraph(invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else 'N/A', value_style)])
        left_data.append([Paragraph("Status:", label_style), Paragraph(invoice.status.value if hasattr(invoice.status, 'value') else str(invoice.status), value_style)])
        left_data.append(['', ''])  # Spacer
        
        # Amount - highlighted box
        amount_style = ParagraphStyle(
            'Amount',
            parent=styles['Normal'],
            fontSize=18,
            textColor=SAS_ORANGE,
            fontName='Helvetica-Bold',
            spaceAfter=8
        )
        amount_text = Paragraph(f"UGX {invoice.total_amount_ugx:,.2f}", amount_style)
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
        
        # Right column - Client & Event info
        right_data = []
        
        if client:
            right_data.append([Paragraph("BILL TO", section_title_style), ''])
            right_data.append([Paragraph("Name:", label_style), Paragraph(client.name or 'N/A', value_style)])
            if client.contact_person:
                right_data.append([Paragraph("Contact:", label_style), Paragraph(client.contact_person, value_style)])
            if client.email:
                right_data.append([Paragraph("Email:", label_style), Paragraph(client.email, value_style)])
            if client.phone:
                right_data.append([Paragraph("Phone:", label_style), Paragraph(client.phone, value_style)])
            if client.company:
                right_data.append([Paragraph("Company:", label_style), Paragraph(client.company, value_style)])
            if client.address:
                right_data.append([Paragraph("Address:", label_style), Paragraph(client.address, value_style)])
            right_data.append(['', ''])  # Spacer
        
        if event:
            right_data.append([Paragraph("EVENT DETAILS", section_title_style), ''])
            right_data.append([Paragraph("Event Name:", label_style), Paragraph(event.event_name or 'N/A', value_style)])
            if event.event_date:
                right_data.append([Paragraph("Event Date:", label_style), Paragraph(event.event_date.strftime('%B %d, %Y'), value_style)])
            if event.guest_count:
                right_data.append([Paragraph("Guests:", label_style), Paragraph(str(event.guest_count), value_style)])
            if event.venue:
                right_data.append([Paragraph("Venue:", label_style), Paragraph(event.venue, value_style)])
        
        # Create two-column layout
        left_table = Table(left_data, colWidths=[1.2*inch, 1.8*inch])
        right_table = Table(right_data, colWidths=[1.2*inch, 1.8*inch])
        
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
        
        payment_terms_style = ParagraphStyle(
            'PaymentTerms',
            parent=styles['Normal'],
            fontSize=10,
            textColor=SAS_DARK_GRAY,
            fontName='Helvetica',
            alignment=TA_CENTER,
            spaceAfter=4
        )
        story.append(Paragraph("Payment terms: 30 days from invoice date. Please make payment to the account details provided above.", payment_terms_style))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=SAS_DARK_GRAY,
            alignment=TA_CENTER,
            spaceAfter=2
        )
        story.append(Paragraph("Thank you for your business!", footer_style))
        story.append(Paragraph("SAS Best Foods - Catering & Event Management", footer_style))
        
        doc.build(story)
        
    except Exception as e:
        try:
            current_app.logger.exception(f"Error generating PDF invoice: {e}")
        except:
            pass
        raise

