"""
PDF Generator Utility for Event Briefs
Generates professional PDF documents for events with SAS Best Foods branding.
"""
import os
from datetime import datetime
from flask import current_app, url_for
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    try:
        import pdfkit
        PDFKIT_AVAILABLE = True
    except ImportError:
        PDFKIT_AVAILABLE = False


def generate_event_brief_pdf(event):
    """
    Generate a PDF event brief for the given event.
    
    Returns:
        str: Path to the generated PDF file
    """
    if not WEASYPRINT_AVAILABLE and not PDFKIT_AVAILABLE:
        raise Exception("No PDF library available. Install weasyprint or pdfkit.")
    
    # Generate HTML content
    html_content = _generate_event_brief_html(event)
    
    # Create output directory
    output_dir = os.path.join(current_app.instance_path, "..", "static", "pdfs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    filename = f"event_brief_{event.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Generate PDF
    if WEASYPRINT_AVAILABLE:
        HTML(string=html_content).write_pdf(filepath)
    elif PDFKIT_AVAILABLE:
        pdfkit.from_string(html_content, filepath)
    
    return filepath


def _generate_event_brief_html(event):
    """Generate HTML content for event brief."""
    
    # Format dates
    event_date = event.date.strftime("%B %d, %Y") if event.date else "N/A"
    start_time = event.start_time or "N/A"
    end_time = event.end_time or "N/A"
    
    # Venue info
    venue_name = event.venue_obj.name if event.venue_obj else "Not specified"
    venue_address = event.venue_obj.address if event.venue_obj else "N/A"
    
    # Menu package
    menu_package_name = event.menu_package_obj.name if event.menu_package_obj else "Not specified"
    menu_items = event.menu_package_obj.items if (event.menu_package_obj and event.menu_package_obj.items) else []
    
    # Staff assignments
    staff_list = []
    for assignment in event.staff_assignments:
        staff_list.append(f"{assignment.staff_name} - {assignment.role}")
    
    # Timeline
    timeline_items = []
    for timeline in event.timelines:
        status = "✓ Completed" if timeline.completed else "○ Pending"
        timeline_items.append(f"{timeline.phase}: {timeline.description} - {status}")
    
    # Vendors
    vendor_list = []
    for assignment in event.vendor_assignments:
        vendor_name = assignment.vendor.name if assignment.vendor else "Unknown"
        vendor_list.append(f"{vendor_name} ({assignment.role_in_event or 'N/A'})")
    
    # Checklist progress
    checklist_progress = event.get_checklist_progress()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Event Brief - {event.title}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: 'Arial', sans-serif;
                color: #263238;
                line-height: 1.6;
            }}
            .header {{
                background-color: #BF360C;
                color: white;
                padding: 20px;
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .header p {{
                margin: 5px 0 0 0;
                font-size: 14px;
            }}
            .section {{
                margin-bottom: 25px;
                page-break-inside: avoid;
            }}
            .section-title {{
                background-color: #FF7043;
                color: white;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .info-grid {{
                display: table;
                width: 100%;
                border-collapse: collapse;
            }}
            .info-row {{
                display: table-row;
            }}
            .info-label {{
                display: table-cell;
                font-weight: bold;
                padding: 8px;
                width: 30%;
                background-color: #F5F5F5;
            }}
            .info-value {{
                display: table-cell;
                padding: 8px;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #BF360C;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
            ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            li {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SAS Best Foods</h1>
            <p>Event Brief Document</p>
        </div>
        
        <div class="section">
            <div class="section-title">Event Information</div>
            <div class="info-grid">
                <div class="info-row">
                    <div class="info-label">Event Title:</div>
                    <div class="info-value">{event.title}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Client Name:</div>
                    <div class="info-value">{event.client_name}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Client Email:</div>
                    <div class="info-value">{event.client_email or 'N/A'}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Client Phone:</div>
                    <div class="info-value">{event.client_phone or 'N/A'}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Event Type:</div>
                    <div class="info-value">{event.event_type or 'N/A'}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Date:</div>
                    <div class="info-value">{event_date}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Time:</div>
                    <div class="info-value">{start_time} - {end_time}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Guest Count:</div>
                    <div class="info-value">{event.guest_count}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Status:</div>
                    <div class="info-value">{event.status.value}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Venue Details</div>
            <div class="info-grid">
                <div class="info-row">
                    <div class="info-label">Venue Name:</div>
                    <div class="info-value">{venue_name}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Address:</div>
                    <div class="info-value">{venue_address}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Menu Package</div>
            <div class="info-grid">
                <div class="info-row">
                    <div class="info-label">Package Name:</div>
                    <div class="info-value">{menu_package_name}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Price per Guest:</div>
                    <div class="info-value">UGX {event.menu_package_obj.price_per_guest if event.menu_package_obj else 0:,.2f}</div>
                </div>
            </div>
            {f'<ul>{"".join([f"<li>{item}</li>" for item in menu_items])}</ul>' if menu_items else '<p>No menu items specified.</p>'}
        </div>
        
        <div class="section">
            <div class="section-title">Staff Assignments</div>
            {f'<ul>{"".join([f"<li>{staff}</li>" for staff in staff_list])}</ul>' if staff_list else '<p>No staff assigned.</p>'}
        </div>
        
        <div class="section">
            <div class="section-title">Timeline & Milestones</div>
            {f'<ul>{"".join([f"<li>{item}</li>" for item in timeline_items])}</ul>' if timeline_items else '<p>No timeline items.</p>'}
        </div>
        
        <div class="section">
            <div class="section-title">Vendor Assignments</div>
            {f'<ul>{"".join([f"<li>{vendor}</li>" for vendor in vendor_list])}</ul>' if vendor_list else '<p>No vendors assigned.</p>'}
        </div>
        
        <div class="section">
            <div class="section-title">Checklist Progress</div>
            <p>Completion: {checklist_progress}%</p>
        </div>
        
        <div class="section">
            <div class="section-title">Budget Information</div>
            <div class="info-grid">
                <div class="info-row">
                    <div class="info-label">Budget Estimate:</div>
                    <div class="info-value">UGX {event.budget_estimate:,.2f}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Actual Cost:</div>
                    <div class="info-value">UGX {event.actual_cost or 0:,.2f}</div>
                </div>
            </div>
        </div>
        
        {f'<div class="section"><div class="section-title">Notes</div><p>{event.notes}</p></div>' if event.notes else ''}
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
            <p>SAS Best Foods Management System</p>
        </div>
    </body>
    </html>
    """
    
    return html

