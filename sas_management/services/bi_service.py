"""Business Intelligence Service - Analytics, predictions, and data warehouse operations."""
from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import current_app
from sqlalchemy import func, and_, or_
import statistics
from collections import defaultdict

from sas_management.models import (
    db, BIEventProfitability, BIIngredientPriceTrend, BISalesForecast,
    BIStaffPerformance, BIBakeryDemand, BICustomerBehavior, BIPOSHeatmap,
    Event, EventMenuSelection, EventStaffAssignment, Ingredient, Employee,
    Client, BakeryItem, Transaction, TransactionType
)


def calculate_event_profitability(event_id):
    """Calculate and store event profitability metrics."""
    try:
        db.session.begin()
        
        event = db.session.get(Event, event_id)
        if not event:
            raise ValueError("Event not found")
        
        # Calculate revenue (quoted value or actual)
        revenue = float(event.quoted_value or 0)
        # If event completed, use actual revenue if available
        # For now, use quoted value
        
        # Calculate COGS
        cost_of_goods = float(event.actual_cogs_ugx or 0)
        
        # Estimate labor cost (simplified - based on staff assignments)
        labor_cost = 0.0
        staff_assignments = EventStaffAssignment.query.filter_by(event_id=event_id).all()
        # Simple estimation: 50k UGX per staff hour (adjustable)
        labor_cost = len(staff_assignments) * 50000 * 8  # 8 hour estimate
        
        # Overhead cost (10% of revenue as estimate)
        overhead_cost = revenue * 0.10
        
        # Calculate profit
        profit = revenue - cost_of_goods - labor_cost - overhead_cost
        
        # Calculate margin
        margin_percent = (profit / revenue * 100) if revenue > 0 else 0
        
        # Store or update profitability record
        existing = BIEventProfitability.query.filter_by(event_id=event_id).first()
        if existing:
            existing.revenue = revenue
            existing.cost_of_goods = cost_of_goods
            existing.labor_cost = labor_cost
            existing.overhead_cost = overhead_cost
            existing.profit = profit
            existing.margin_percent = margin_percent
            existing.generated_at = datetime.utcnow()
        else:
            profitability = BIEventProfitability(
                event_id=event_id,
                revenue=revenue,
                cost_of_goods=cost_of_goods,
                labor_cost=labor_cost,
                overhead_cost=overhead_cost,
                profit=profit,
                margin_percent=margin_percent
            )
            db.session.add(profitability)
        
        db.session.commit()
        
        return {
            "success": True,
            "event_id": event_id,
            "revenue": revenue,
            "cost_of_goods": cost_of_goods,
            "labor_cost": labor_cost,
            "overhead_cost": overhead_cost,
            "profit": profit,
            "margin_percent": round(margin_percent, 2)
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error calculating event profitability: {e}")
        return {"success": False, "error": str(e)}


def generate_profitability_pdf_report():
    """
    Generate a comprehensive PDF report for all Event Profitability Analysis records.
    
    Returns:
        Full path to the generated PDF file
    """
    # Try to import ReportLab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
        REPORTLAB_AVAILABLE = True
    except ImportError:
        raise ImportError("ReportLab is not installed. Install it with: pip install reportlab")
    
    import os
    
    # Get all profitability records with event data
    from sqlalchemy.orm import joinedload
    profitability_records = BIEventProfitability.query.options(
        joinedload(BIEventProfitability.event).joinedload(Event.client)
    ).order_by(BIEventProfitability.generated_at.desc()).all()
    
    if not profitability_records:
        raise ValueError("No profitability records found. Generate analysis for events first.")
    
    # Generate PDF path
    try:
        reports_folder = os.path.join(current_app.instance_path, "reports")
        os.makedirs(reports_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_relative_path = f"reports/event_profitability_report_{timestamp}.pdf"
        full_path = os.path.join(current_app.instance_path, pdf_relative_path)
        full_path = os.path.abspath(full_path)
        
        # Generate PDF
        _generate_pdf_profitability_report(
            pdf_path=full_path,
            profitability_records=profitability_records
        )
        
        # Verify file was created
        if not os.path.exists(full_path):
            raise IOError(f"PDF file was not created at {full_path}")
        
        return full_path
    except Exception as e:
        current_app.logger.exception(f"Error in generate_profitability_pdf_report: {e}")
        raise


def _generate_pdf_profitability_report(pdf_path, profitability_records):
    """
    Generate professional PDF report for Event Profitability Analysis.
    
    Args:
        pdf_path: Full path where PDF should be saved
        profitability_records: List of BIEventProfitability records
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    except ImportError:
        raise ImportError("ReportLab is not installed. Install it with: pip install reportlab")
    
    import os
    from flask import current_app
    
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
    story.append(Paragraph("EVENT PROFITABILITY ANALYSIS REPORT", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=SAS_ORANGE, spaceAfter=0.2*inch))
    
    # Report metadata
    meta_style = ParagraphStyle(
        'Meta',
        parent=styles['Normal'],
        fontSize=9,
        textColor=SAS_DARK_GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER,
        spaceAfter=0.15*inch
    )
    report_date = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    story.append(Paragraph(f"Generated on {report_date}", meta_style))
    story.append(Paragraph(f"Total Events Analyzed: {len(profitability_records)}", meta_style))
    story.append(Spacer(1, 0.2*inch))
    
    # ========== SUMMARY STATISTICS ==========
    total_revenue = sum(float(r.revenue) for r in profitability_records)
    total_cogs = sum(float(r.cost_of_goods) for r in profitability_records)
    total_labor = sum(float(r.labor_cost) for r in profitability_records)
    total_overhead = sum(float(r.overhead_cost) for r in profitability_records)
    total_profit = sum(float(r.profit) for r in profitability_records)
    avg_margin = sum(float(r.margin_percent) for r in profitability_records) / len(profitability_records) if profitability_records else 0
    
    summary_title_style = ParagraphStyle(
        'SummaryTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=SAS_GREEN,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    story.append(Paragraph("SUMMARY STATISTICS", summary_title_style))
    
    summary_data = [
        ['Metric', 'Amount (UGX)'],
        ['Total Revenue', f"{total_revenue:,.2f}"],
        ['Total COGS', f"{total_cogs:,.2f}"],
        ['Total Labor Cost', f"{total_labor:,.2f}"],
        ['Total Overhead', f"{total_overhead:,.2f}"],
        ['Total Profit', f"{total_profit:,.2f}"],
        ['Average Margin %', f"{avg_margin:.2f}%"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SAS_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), SAS_LIGHT_GRAY),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
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
    
    # ========== DETAILED EVENT PROFITABILITY TABLE ==========
    detail_title_style = ParagraphStyle(
        'DetailTitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=SAS_GREEN,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    story.append(Paragraph("DETAILED EVENT PROFITABILITY", detail_title_style))
    
    # Table headers
    table_data = [['Event ID', 'Event Name', 'Revenue', 'COGS', 'Labor', 'Overhead', 'Profit', 'Margin %']]
    
    # Add data rows
    for record in profitability_records:
        event = record.event if hasattr(record, 'event') and record.event else None
        event_name = event.event_name if event else f"Event #{record.event_id or 'N/A'}"
        if event and event.client:
            event_name = f"{event_name} - {event.client.name}"
        
        # Truncate long names
        if len(event_name) > 30:
            event_name = event_name[:27] + "..."
        
        profit_color = colors.black
        if float(record.profit) > 0:
            profit_color = SAS_GREEN
        elif float(record.profit) < 0:
            profit_color = colors.red
        
        margin_color = colors.black
        if float(record.margin_percent) > 30:
            margin_color = SAS_GREEN
        elif float(record.margin_percent) < 15:
            margin_color = colors.red
        
        table_data.append([
            f"#{record.event_id or 'N/A'}",
            event_name,
            f"{float(record.revenue):,.0f}",
            f"{float(record.cost_of_goods):,.0f}",
            f"{float(record.labor_cost):,.0f}",
            f"{float(record.overhead_cost):,.0f}",
            f"{float(record.profit):,.0f}",
            f"{float(record.margin_percent):.1f}%"
        ])
    
    # Create table with appropriate column widths
    col_widths = [0.6*inch, 2.2*inch, 0.9*inch, 0.9*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.7*inch]
    detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    detail_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), SAS_GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, SAS_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, SAS_LIGHT_GRAY]),
    ]))
    
    story.append(detail_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ========== FOOTER SECTION ==========
    story.append(HRFlowable(width="100%", thickness=1, color=SAS_BORDER, spaceAfter=0.15*inch))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=SAS_DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=2
    )
    story.append(Paragraph("This report was generated automatically by SAS Best Foods Management System", footer_style))
    story.append(Paragraph("For questions or clarifications, please contact the management team.", footer_style))
    
    try:
        doc.build(story)
    except Exception as e:
        current_app.logger.exception(f"Error building PDF document: {e}")
        raise


def ingest_ingredient_price(inventory_item_id, price, price_date=None):
    """Ingest ingredient price data for trend analysis."""
    try:
        if not price_date:
            price_date = date.today()
        
        # Check if record exists for this date
        existing = BIIngredientPriceTrend.query.filter_by(
            inventory_item_id=inventory_item_id,
            date=price_date
        ).first()
        
        if existing:
            existing.price = price
        else:
            trend = BIIngredientPriceTrend(
                inventory_item_id=inventory_item_id,  # This references ingredient.id
                date=price_date,
                price=price
            )
            db.session.add(trend)
        
        db.session.commit()
        
        return {"success": True, "message": "Price ingested successfully"}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error ingesting ingredient price: {e}")
        return {"success": False, "error": str(e)}


def generate_price_trend_history(inventory_item_id, days=30):
    """Generate price trend history for an ingredient."""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        trends = BIIngredientPriceTrend.query.filter(
            and_(
                BIIngredientPriceTrend.inventory_item_id == inventory_item_id,
                BIIngredientPriceTrend.date >= start_date,
                BIIngredientPriceTrend.date <= end_date
            )
        ).order_by(BIIngredientPriceTrend.date.asc()).all()
        
        # Calculate moving averages (7-day)
        data_points = []
        prices = [float(t.price) for t in trends]
        
        for i, trend in enumerate(trends):
            price = float(trend.price)
            # Calculate 7-day moving average
            start_idx = max(0, i - 6)
            window = prices[start_idx:i+1]
            moving_avg = statistics.mean(window) if window else price
            
            data_points.append({
                "date": trend.date.isoformat(),
                "price": price,
                "moving_average": round(moving_avg, 2)
            })
        
        # Calculate trend direction
        trend_direction = "stable"
        if len(prices) >= 2:
            first_half = statistics.mean(prices[:len(prices)//2])
            second_half = statistics.mean(prices[len(prices)//2:])
            if second_half > first_half * 1.05:
                trend_direction = "increasing"
            elif second_half < first_half * 0.95:
                trend_direction = "decreasing"
        
        return {
            "success": True,
            "item_id": inventory_item_id,
            "data_points": data_points,
            "trend_direction": trend_direction,
            "current_price": float(trends[-1].price) if trends else None,
            "average_price": round(statistics.mean(prices), 2) if prices else None
        }
    except Exception as e:
        current_app.logger.exception(f"Error generating price trend: {e}")
        return {"success": False, "error": str(e), "data_points": []}


def run_sales_forecasting(source="all", model="simple", days=14):
    """Generate sales forecasts for POS, Catering, or Bakery."""
    try:
        db.session.begin()
        
        forecast_date = date.today() + timedelta(days=1)
        end_date = forecast_date + timedelta(days=days - 1)
        
        sources = ["POS", "Catering", "Bakery"] if source == "all" else [source]
        forecasts = []
        
        for src in sources:
            # Get historical sales data (last 30 days)
            historical_start = date.today() - timedelta(days=30)
            
            # Simple linear regression based on historical averages
            # In production, use ML models (scikit-learn, etc.)
            if src == "POS":
                # Get POS transactions
                historical_txns = Transaction.query.filter(
                    and_(
                        Transaction.type == TransactionType.Revenue,
                        Transaction.date >= historical_start,
                        Transaction.category.ilike("%POS%")
                    )
                ).all()
                
                daily_avg = statistics.mean([float(t.amount) for t in historical_txns]) / 30 if historical_txns else 50000
                
            elif src == "Catering":
                # Get catering revenue (from events)
                historical_events = Event.query.filter(
                    Event.event_date >= historical_start
                ).all()
                
                event_revenue = [float(e.quoted_value or 0) for e in historical_events]
                daily_avg = statistics.mean(event_revenue) / 30 if event_revenue else 100000
                
            elif src == "Bakery":
                # Get bakery transactions
                historical_txns = Transaction.query.filter(
                    and_(
                        Transaction.type == TransactionType.Revenue,
                        Transaction.date >= historical_start,
                        Transaction.category.ilike("%Bakery%")
                    )
                ).all()
                
                daily_avg = statistics.mean([float(t.amount) for t in historical_txns]) / 30 if historical_txns else 30000
            
            # Generate forecasts
            current_date = forecast_date
            while current_date <= end_date:
                # Simple model: daily average with day-of-week adjustment
                day_of_week = current_date.weekday()
                # Weekend boost (Saturday=5, Sunday=6)
                multiplier = 1.5 if day_of_week >= 5 else 1.0
                
                predicted = daily_avg * multiplier
                
                # Check if forecast already exists
                existing = BISalesForecast.query.filter_by(
                    source=src,
                    date=current_date
                ).first()
                
                if existing:
                    existing.predicted_sales = predicted
                    existing.model_name = model
                else:
                    forecast = BISalesForecast(
                        source=src,
                        date=current_date,
                        predicted_sales=predicted,
                        model_name=model,
                        confidence=0.7  # Simple model confidence
                    )
                    db.session.add(forecast)
                    forecasts.append({
                        "source": src,
                        "date": current_date.isoformat(),
                        "predicted_sales": round(predicted, 2)
                    })
                
                current_date += timedelta(days=1)
        
        db.session.commit()
        
        return {
            "success": True,
            "model": model,
            "forecasts": forecasts,
            "forecast_period": {
                "start": forecast_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error running sales forecast: {e}")
        return {"success": False, "error": str(e)}


def generate_staff_performance(employee_id, metric, value, period="daily", period_start=None, period_end=None):
    """Generate staff performance metrics."""
    try:
        db.session.begin()
        
        if not period_start:
            period_start = date.today()
        if not period_end and period == "daily":
            period_end = period_start
        elif not period_end:
            period_end = period_start + timedelta(days=6) if period == "weekly" else period_start + timedelta(days=29)
        
        performance = BIStaffPerformance(
            employee_id=employee_id,
            metric=metric,
            value=float(value),
            period=period,
            period_start=period_start,
            period_end=period_end
        )
        
        db.session.add(performance)
        db.session.commit()
        
        return {"success": True, "performance_id": performance.id}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error generating staff performance: {e}")
        return {"success": False, "error": str(e)}


def generate_bakery_demand_forecast(item_id, days=14):
    """Generate bakery item demand forecast."""
    try:
        db.session.begin()
        
        # Get historical sales data (from POS or bakery orders)
        historical_start = date.today() - timedelta(days=30)
        
        # Simple average-based forecast
        # In production, use time series models (ARIMA, Prophet, etc.)
        avg_daily_qty = 5  # Default average
        
        forecast_date = date.today() + timedelta(days=1)
        end_date = forecast_date + timedelta(days=days - 1)
        
        forecasts = []
        current_date = forecast_date
        
        while current_date <= end_date:
            # Day-of-week adjustment
            day_of_week = current_date.weekday()
            multiplier = 1.8 if day_of_week >= 5 else 1.0  # Weekend boost
            
            predicted_qty = int(avg_daily_qty * multiplier)
            
            existing = BIBakeryDemand.query.filter_by(
                bakery_item_id=item_id,
                date=current_date
            ).first()
            
            if existing:
                existing.predicted_qty = predicted_qty
                existing.model_name = "simple"
            else:
                demand = BIBakeryDemand(
                    bakery_item_id=item_id,
                    date=current_date,
                    predicted_qty=predicted_qty,
                    model_name="simple",
                    confidence=0.65
                )
                db.session.add(demand)
                forecasts.append({
                    "date": current_date.isoformat(),
                    "predicted_qty": predicted_qty
                })
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        
        return {
            "success": True,
            "item_id": item_id,
            "forecasts": forecasts
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error generating bakery demand forecast: {e}")
        return {"success": False, "error": str(e)}


def calculate_customer_behavior(customer_id):
    """Calculate customer behavior metrics (frequency, AOV, LTV, churn risk)."""
    try:
        # Get customer events
        events = Event.query.filter_by(client_id=customer_id).all()
        
        # Frequency (events per month average)
        if events:
            first_event = min(e.event_date for e in events if e.event_date)
            last_event = max(e.event_date for e in events if e.event_date)
            months = max(1, (last_event - first_event).days / 30)
            frequency = len(events) / months if months > 0 else 0
        else:
            frequency = 0
        
        # Average Order Value (AOV)
        event_values = [float(e.quoted_value or 0) for e in events]
        aov = statistics.mean(event_values) if event_values else 0
        
        # Lifetime Value (LTV)
        ltv = sum(event_values)
        
        # Churn risk (based on last order date)
        churn_risk = 0.0
        if events:
            last_order = max(e.event_date for e in events if e.event_date)
            days_since_last = (date.today() - last_order).days
            if days_since_last > 90:
                churn_risk = 0.8
            elif days_since_last > 60:
                churn_risk = 0.5
            elif days_since_last > 30:
                churn_risk = 0.2
        
        # Store metrics
        db.session.begin()
        
        metrics = [
            ("frequency", frequency, "monthly"),
            ("aov", aov, "lifetime"),
            ("ltv", ltv, "lifetime"),
            ("churn_risk", churn_risk, "current")
        ]
        
        for metric_name, value, period in metrics:
            behavior = BICustomerBehavior(
                customer_id=customer_id,
                metric=metric_name,
                value=value,
                period=period
            )
            db.session.add(behavior)
        
        db.session.commit()
        
        return {
            "success": True,
            "customer_id": customer_id,
            "frequency": round(frequency, 2),
            "aov": round(aov, 2),
            "ltv": round(ltv, 2),
            "churn_risk": round(churn_risk, 2)
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error calculating customer behavior: {e}")
        return {"success": False, "error": str(e)}


def generate_pos_heatmap(days=7):
    """Generate POS sales heatmap data (hour × day matrix)."""
    try:
        db.session.begin()
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        # Get POS transactions (simulated for now - in production, query actual POS orders)
        # Group by hour and day of week
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # Initialize heatmap data
        heatmap_data = defaultdict(lambda: {"sales": 0.0, "count": 0})
        
        # Simulate data (in production, query actual POSOrder table)
        # For now, generate sample distribution
        for day_idx, day_name in enumerate(days_of_week):
            for hour in range(24):
                # Peak hours: 8-10, 12-14, 17-19
                if hour in [8, 9, 12, 13, 17, 18]:
                    sales = 15000.0
                    count = 3
                elif hour in [10, 11, 14, 15, 19, 20]:
                    sales = 10000.0
                    count = 2
                else:
                    sales = 3000.0
                    count = 1
                
                # Weekend boost
                if day_idx >= 5:
                    sales *= 1.5
                    count = int(count * 1.5)
                
                heatmap_data[(day_name, hour)]["sales"] += sales
                heatmap_data[(day_name, hour)]["count"] += count
        
        # Store heatmap data
        for (day_name, hour), data in heatmap_data.items():
            # Find existing record (may not have date field, check day and hour)
            existing = BIPOSHeatmap.query.filter_by(
                day=day_name,
                hour=hour
            ).first()
            
            if existing:
                existing.sales = data["sales"]
                existing.transaction_count = data["count"]
            else:
                heatmap = BIPOSHeatmap(
                    day=day_name,
                    hour=hour,
                    sales=data["sales"],
                    transaction_count=data["count"],
                    period_start=start_date,
                    period_end=end_date
                )
                db.session.add(heatmap)
        
        db.session.commit()
        
        return {
            "success": True,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "heatmap": dict(heatmap_data)
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error generating POS heatmap: {e}")
        return {"success": False, "error": str(e)}


def get_bi_dashboard_metrics():
    """Get aggregated metrics for BI dashboard."""
    try:
        metrics = {}
        
        # Total events profitability
        total_profitability = db.session.query(
            func.sum(BIEventProfitability.revenue).label("total_revenue"),
            func.sum(BIEventProfitability.profit).label("total_profit"),
            func.avg(BIEventProfitability.margin_percent).label("avg_margin")
        ).first()
        
        metrics["events"] = {
            "total_revenue": float(total_profitability.total_revenue or 0),
            "total_profit": float(total_profitability.total_profit or 0),
            "avg_margin": round(float(total_profitability.avg_margin or 0), 2)
        }
        
        # Sales forecast summary
        upcoming_forecasts = BISalesForecast.query.filter(
            BISalesForecast.date >= date.today()
        ).all()
        
        forecast_by_source = defaultdict(float)
        for f in upcoming_forecasts:
            forecast_by_source[f.source] += float(f.predicted_sales)
        
        metrics["sales_forecast"] = dict(forecast_by_source)
        
        # Staff performance summary
        staff_perf_count = BIStaffPerformance.query.count()
        metrics["staff_performance"] = {
            "records_count": staff_perf_count
        }
        
        # Ingredient price trends count
        price_trends_count = BIIngredientPriceTrend.query.count()
        metrics["price_trends"] = {
            "records_count": price_trends_count
        }
        
        # Customer behavior summary
        behavior_count = BICustomerBehavior.query.count()
        metrics["customer_behavior"] = {
            "records_count": behavior_count
        }
        
        return {"success": True, "metrics": metrics}
    except Exception as e:
        current_app.logger.exception(f"Error getting BI dashboard metrics: {e}")
        return {"success": False, "error": str(e), "metrics": {}}

