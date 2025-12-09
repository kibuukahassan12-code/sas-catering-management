"""Floor Planner Service Layer - Business logic for floor plan management."""
import json
import base64
import io
from datetime import datetime
from typing import Optional, Dict, List

from sqlalchemy.exc import SQLAlchemyError
from PIL import Image

from models import FloorPlan, SeatingAssignment, Event, User, db


def create_floorplan(event_id: int, user_id: int, name: str = None) -> FloorPlan:
    """Create a new floor plan for an event."""
    try:
        event = Event.query.get_or_404(event_id)
        
        if not name:
            name = f"Floor Plan - {event.event_name}"
        
        floorplan = FloorPlan(
            event_id=event_id,
            name=name,
            layout_json='{"objects": [], "meta": {"zoom": 1, "pan": {"x": 0, "y": 0}, "grid": true}}',
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(floorplan)
        db.session.commit()
        return floorplan
    except SQLAlchemyError as e:
        db.session.rollback()
        raise Exception(f"Database error creating floor plan: {str(e)}")


def update_floorplan(id: int, json_data: str) -> FloorPlan:
    """Update floor plan layout JSON."""
    try:
        floorplan = FloorPlan.query.get_or_404(id)
        
        # Validate JSON
        try:
            json.loads(json_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON data")
        
        floorplan.layout_json = json_data
        floorplan.updated_at = datetime.utcnow()
        
        db.session.commit()
        return floorplan
    except SQLAlchemyError as e:
        db.session.rollback()
        raise Exception(f"Database error updating floor plan: {str(e)}")


def save_thumbnail(id: int, png_data: str) -> FloorPlan:
    """Save thumbnail from base64 PNG data."""
    try:
        floorplan = FloorPlan.query.get_or_404(id)
        
        # Decode base64 PNG data
        if png_data.startswith('data:image/png;base64,'):
            png_data = png_data.split(',')[1]
        
        thumbnail_bytes = base64.b64decode(png_data)
        
        # Optionally resize thumbnail
        try:
            img = Image.open(io.BytesIO(thumbnail_bytes))
            img.thumbnail((400, 300), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='PNG')
            thumbnail_bytes = output.getvalue()
        except Exception:
            pass  # Use original if resize fails
        
        floorplan.thumbnail = thumbnail_bytes
        floorplan.updated_at = datetime.utcnow()
        
        db.session.commit()
        return floorplan
    except SQLAlchemyError as e:
        db.session.rollback()
        raise Exception(f"Database error saving thumbnail: {str(e)}")


def get_floorplan(id: int) -> Optional[FloorPlan]:
    """Get floor plan by ID."""
    try:
        return FloorPlan.query.get(id)
    except SQLAlchemyError as e:
        raise Exception(f"Database error getting floor plan: {str(e)}")


def list_floorplans(event_id: int = None) -> List[FloorPlan]:
    """List all floor plans, optionally filtered by event."""
    try:
        query = FloorPlan.query
        if event_id:
            query = query.filter_by(event_id=event_id)
        return query.order_by(FloorPlan.updated_at.desc()).all()
    except SQLAlchemyError as e:
        raise Exception(f"Database error listing floor plans: {str(e)}")


def delete_floorplan(id: int) -> bool:
    """Delete a floor plan and all its seating assignments."""
    try:
        floorplan = FloorPlan.query.get_or_404(id)
        
        # Delete seating assignments (cascade should handle this, but explicit is safer)
        SeatingAssignment.query.filter_by(floorplan_id=id).delete()
        
        db.session.delete(floorplan)
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        raise Exception(f"Database error deleting floor plan: {str(e)}")


def export_png(id: int) -> bytes:
    """Export floor plan as PNG image."""
    try:
        floorplan = FloorPlan.query.get_or_404(id)
        
        # If we have a thumbnail, return it
        if floorplan.thumbnail:
            return floorplan.thumbnail
        
        # Otherwise, we'd need to render from JSON
        # For now, return a placeholder or the thumbnail
        raise ValueError("No thumbnail available. Please save the floor plan first.")
    except SQLAlchemyError as e:
        raise Exception(f"Database error exporting PNG: {str(e)}")


def export_pdf(id: int) -> bytes:
    """Export floor plan as PDF with event details and seating assignments."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        floorplan = FloorPlan.query.get_or_404(id)
        event = Event.query.get_or_404(floorplan.event_id)
        seating_assignments = SeatingAssignment.query.filter_by(floorplan_id=id).all()
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for the 'Flowable' objects
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#F26822'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"Floor Plan: {floorplan.name}", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Event Details
        event_style = ParagraphStyle(
            'EventStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        )
        elements.append(Paragraph(f"<b>Event:</b> {event.event_name}", event_style))
        elements.append(Paragraph(f"<b>Date:</b> {event.event_date.strftime('%B %d, %Y')}", event_style))
        if event.venue:
            elements.append(Paragraph(f"<b>Venue:</b> {event.venue}", event_style))
        elements.append(Paragraph(f"<b>Guest Count:</b> {event.guest_count}", event_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Floor Plan Image
        if floorplan.thumbnail:
            try:
                img = Image.open(io.BytesIO(floorplan.thumbnail))
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                rl_img = RLImage(img_buffer, width=6*inch, height=4.5*inch)
                elements.append(rl_img)
                elements.append(Spacer(1, 0.3*inch))
            except Exception as e:
                elements.append(Paragraph(f"<i>Image unavailable: {str(e)}</i>", styles['Normal']))
        
        # Seating Assignments Table
        if seating_assignments:
            elements.append(Paragraph("<b>Seating Assignments</b>", styles['Heading2']))
            elements.append(Spacer(1, 0.2*inch))
            
            # Table data
            table_data = [['Guest Name', 'Table', 'Seat', 'Special Requests']]
            for assignment in seating_assignments:
                table_data.append([
                    assignment.guest_name or 'Unassigned',
                    assignment.table_number or '-',
                    assignment.seat_number or '-',
                    assignment.special_requests or '-'
                ])
            
            # Create table
            table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 2.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F26822')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FCF1D6')])
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph("<i>No seating assignments yet.</i>", styles['Normal']))
        
        # Footer
        elements.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(f"Generated on {datetime.utcnow().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
        
    except ImportError:
        raise Exception("reportlab is required for PDF export. Install with: pip install reportlab")
    except Exception as e:
        raise Exception(f"Error generating PDF: {str(e)}")

