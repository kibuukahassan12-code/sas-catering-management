"""Simple PDF receipt generation using canvas."""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os


def _generate_pdf_receipt_simple(pdf_path, receipt, payment, invoice, client, issuer):
    """
    Generate PDF receipt using ReportLab Canvas (simple version).
    
    Args:
        pdf_path: Full path to save PDF
        receipt: AccountingReceipt instance
        payment: AccountingPayment instance
        invoice: Invoice instance (optional)
        client: Client instance (optional)
        issuer: User instance (optional)
    """
    # Create PDF canvas
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "SAS BEST FOODS - OFFICIAL RECEIPT")
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "For all your Catering Solutions")
    c.drawString(50, height - 85, "Near Akamwesi Mall, Gayaza Rd")
    c.drawString(50, height - 100, "Opp Electoral Commission Kawempe Offices")
    c.drawString(50, height - 115, "Kawempe, Kampala, Uganda")
    c.drawString(50, height - 130, "Tel: 0702060778 / 0745705088")
    c.drawString(50, height - 145, "Website: www.sasbestfoods.com")
    
    # Receipt details
    y_pos = height - 200
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, "RECEIPT")
    
    y_pos -= 30
    c.setFont("Helvetica", 11)
    c.drawString(50, y_pos, f"Receipt Number: {receipt.reference}")
    
    y_pos -= 20
    c.drawString(50, y_pos, f"Date: {receipt.date.strftime('%B %d, %Y')}")
    
    if invoice:
        y_pos -= 20
        c.drawString(50, y_pos, f"Invoice Number: {invoice.invoice_number}")
    
    if payment.reference:
        y_pos -= 20
        c.drawString(50, y_pos, f"Payment Reference: {payment.reference}")
    
    # Client info
    if client:
        y_pos -= 40
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y_pos, "Received From:")
        y_pos -= 20
        c.setFont("Helvetica", 10)
        c.drawString(50, y_pos, client.name or "N/A")
        if client.email:
            y_pos -= 15
            c.drawString(50, y_pos, client.email)
        if client.phone:
            y_pos -= 15
            c.drawString(50, y_pos, client.phone)
    
    # Payment details
    y_pos -= 40
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y_pos, "Payment Details:")
    y_pos -= 20
    c.setFont("Helvetica", 10)
    amount = float(receipt.amount if receipt.amount else (payment.amount if payment else 0))
    c.drawString(50, y_pos, f"Amount Paid: UGX {amount:,.2f}")
    
    y_pos -= 20
    method = receipt.method or payment.method or "N/A"
    c.drawString(50, y_pos, f"Payment Method: {method.title()}")
    
    # Footer
    y_pos = 100
    c.setFont("Helvetica", 9)
    c.drawString(50, y_pos, "Thank you for your business!")
    y_pos -= 15
    c.drawString(50, y_pos, "This is a computer-generated receipt.")
    
    # Save PDF
    c.showPage()
    c.save()

