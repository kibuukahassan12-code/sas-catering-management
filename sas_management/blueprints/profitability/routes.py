"""Profitability Analysis Routes."""
import os
import io
import base64
from datetime import datetime
from decimal import Decimal

from flask import render_template, request, abort, send_file, current_app, flash, redirect, url_for
from flask_login import login_required, current_user

from sas_management.models import Event, EventCostItem, EventRevenueItem, UserRole, db
from blueprints.profitability import profitability_bp
from sas_management.utils import role_required

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None

# Try to import ReportLab for PDF
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


@profitability_bp.route("/event/<int:event_id>/report")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_report(event_id):
    """Generate event profitability report."""
    event = Event.query.get_or_404(event_id)
    
    # Pull cost and revenue items
    costs = EventCostItem.query.filter_by(event_id=event_id).all()
    revenue = EventRevenueItem.query.filter_by(event_id=event_id).all()
    
    # Calculate totals
    total_cost = sum(float(item.amount) for item in costs)
    total_revenue = sum(float(item.amount) for item in revenue)
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Create cost breakdown pie chart if matplotlib is available
    chart_data = None
    if MATPLOTLIB_AVAILABLE and costs:
        try:
            labels = [c.description[:20] + "..." if len(c.description) > 20 else c.description for c in costs]
            values = [float(c.amount) for c in costs]
            
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
            ax.set_title("Cost Breakdown", fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            img_bytes = io.BytesIO()
            plt.savefig(img_bytes, format="png", dpi=100, bbox_inches='tight')
            img_bytes.seek(0)
            chart_data = base64.b64encode(img_bytes.getvalue()).decode("utf-8")
            plt.close()
        except Exception as e:
            current_app.logger.warning(f"Error generating chart: {e}")
            chart_data = None
    
    CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")
    
    return render_template(
        "profitability/event_report.html",
        event=event,
        costs=costs,
        revenue=revenue,
        total_cost=total_cost,
        total_revenue=total_revenue,
        profit=profit,
        margin=margin,
        chart_data=chart_data,
        CURRENCY=CURRENCY
    )


@profitability_bp.route("/event/<int:event_id>/report/pdf")
@login_required
@role_required(UserRole.SalesManager, UserRole.Admin)
def event_report_pdf(event_id):
    """Generate and download event profitability report as PDF."""
    if not REPORTLAB_AVAILABLE:
        flash("PDF generation not available. ReportLab is not installed.", "danger")
        return redirect(url_for("profitability.event_report", event_id=event_id))
    
    event = Event.query.get_or_404(event_id)
    
    # Pull cost and revenue items
    costs = EventCostItem.query.filter_by(event_id=event_id).all()
    revenue = EventRevenueItem.query.filter_by(event_id=event_id).all()
    
    # Calculate totals
    total_cost = sum(float(item.amount) for item in costs)
    total_revenue = sum(float(item.amount) for item in revenue)
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Generate PDF
    try:
        pdf_path = _generate_profitability_pdf(event, costs, revenue, total_cost, total_revenue, profit, margin)
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"event_profitability_{event.id}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        current_app.logger.exception(f"Error generating PDF: {e}")
        flash(f"Error generating PDF: {str(e)}", "danger")
        return redirect(url_for("profitability.event_report", event_id=event_id))


def _generate_profitability_pdf(event, costs, revenue, total_cost, total_revenue, profit, margin):
    """Generate PDF report for event profitability."""
    import os
    
    # SAS Brand Colors
    SAS_ORANGE = colors.HexColor('#F26822')
    SAS_GREEN = colors.HexColor('#2d5016')
    SAS_LIGHT_GRAY = colors.HexColor('#f8f9fa')
    SAS_DARK_GRAY = colors.HexColor('#6c757d')
    SAS_BORDER = colors.HexColor('#e0e0e0')
    
    # Generate PDF path
    reports_folder = os.path.join(current_app.instance_path, "reports")
    os.makedirs(reports_folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(reports_folder, f"event_profitability_{event.id}_{timestamp}.pdf")
    pdf_path = os.path.abspath(pdf_path)
    
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
            except Exception:
                logo_img = None
    except Exception:
        logo_img = None
    
    # Header
    header_data = []
    if logo_img:
        header_data.append([logo_img, ''])
    else:
        header_data.append(['', ''])
    
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
    
    company_info = [
        Paragraph("SAS BEST FOODS", company_name_style),
        Paragraph("Catering & Event Management", company_tagline_style),
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
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 0.25*inch))
    
    # Report title
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Normal'],
        fontSize=20,
        textColor=SAS_ORANGE,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=8
    )
    story.append(Paragraph("EVENT PROFITABILITY REPORT", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SAS_ORANGE, spaceAfter=0.2*inch))
    
    # Event info
    event_info_style = ParagraphStyle(
        'EventInfo',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    event_date_str = event.event_date.strftime('%B %d, %Y') if event.event_date else 'N/A'
    story.append(Paragraph(f"Event: {event.event_name}", event_info_style))
    story.append(Paragraph(f"Date: {event_date_str}", styles['Normal']))
    if event.client:
        story.append(Paragraph(f"Client: {event.client.name}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Revenue section
    revenue_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=SAS_GREEN,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    story.append(Paragraph("REVENUE", revenue_title_style))
    
    revenue_data = [['Description', 'Amount (UGX)']]
    for r in revenue:
        revenue_data.append([r.description, f"{float(r.amount):,.2f}"])
    revenue_data.append(['TOTAL REVENUE', f"{total_revenue:,.2f}"])
    
    revenue_table = Table(revenue_data, colWidths=[4*inch, 2*inch])
    revenue_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SAS_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('BACKGROUND', (0, -1), (-1, -1), SAS_LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 1, SAS_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(revenue_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Costs section
    story.append(Paragraph("COSTS", revenue_title_style))
    
    cost_data = [['Description', 'Amount (UGX)']]
    for c in costs:
        cost_data.append([c.description, f"{float(c.amount):,.2f}"])
    cost_data.append(['TOTAL COSTS', f"{total_cost:,.2f}"])
    
    cost_table = Table(cost_data, colWidths=[4*inch, 2*inch])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('BACKGROUND', (0, -1), (-1, -1), SAS_LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 1, SAS_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(cost_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    summary_title_style = ParagraphStyle(
        'SummaryTitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=SAS_ORANGE,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    story.append(Paragraph("PROFITABILITY SUMMARY", summary_title_style))
    
    summary_data = [
        ['Metric', 'Amount (UGX)'],
        ['Total Revenue', f"{total_revenue:,.2f}"],
        ['Total Costs', f"{total_cost:,.2f}"],
        ['Profit', f"{profit:,.2f}"],
        ['Margin %', f"{margin:.2f}%"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SAS_ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, SAS_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=SAS_BORDER, spaceAfter=0.15*inch))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=SAS_DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=2
    )
    story.append(Paragraph("Generated by SAS Best Foods Management System", footer_style))
    story.append(Paragraph(f"Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    
    doc.build(story)
    
    return pdf_path

