"""Business Intelligence Blueprint - Analytics, predictions, and dashboards."""
import os
from datetime import datetime, date, timedelta
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from models import (
    db, BIEventProfitability, BIIngredientPriceTrend, BISalesForecast,
    BIStaffPerformance, BIBakeryDemand, BICustomerBehavior, BIPOSHeatmap,
    Event, Ingredient, Employee, Client, BakeryItem, UserRole
)
from utils import role_required
from services.bi_service import (
    calculate_event_profitability, ingest_ingredient_price,
    generate_price_trend_history, run_sales_forecasting,
    generate_staff_performance, generate_bakery_demand_forecast,
    calculate_customer_behavior, generate_pos_heatmap,
    get_bi_dashboard_metrics
)

bi_bp = Blueprint("bi", __name__, url_prefix="/bi")

@bi_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """Main BI dashboard."""
    try:
        metrics_result = get_bi_dashboard_metrics()
        metrics = metrics_result.get('metrics', {}) if metrics_result['success'] else {}
        
        # Get recent profitability records
        recent_profitability = BIEventProfitability.query.order_by(
            BIEventProfitability.generated_at.desc()
        ).limit(10).all()
        
        # Get upcoming forecasts
        upcoming_forecasts = BISalesForecast.query.filter(
            BISalesForecast.date >= date.today()
        ).order_by(BISalesForecast.date.asc()).limit(30).all()
        
        return render_template("bi/bi_dashboard.html",
            metrics=metrics,
            recent_profitability=recent_profitability,
            upcoming_forecasts=upcoming_forecasts
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading BI dashboard: {e}")
        return render_template("bi/bi_dashboard.html",
            metrics={},
            recent_profitability=[],
            upcoming_forecasts=[]
        )

@bi_bp.route("/event-profitability")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_profitability():
    """Event profitability analysis page."""
    try:
        # Get all profitability records
        profitability_records = BIEventProfitability.query.order_by(
            BIEventProfitability.generated_at.desc()
        ).all()
        
        # Get events without profitability data
        all_events = Event.query.filter_by(status="Completed").all()
        event_ids_with_profit = {r.event_id for r in profitability_records if r.event_id}
        events_needing_analysis = [e for e in all_events if e.id not in event_ids_with_profit]
        
        # Count completed events for seed button visibility
        completed_events_count = len(all_events)
        
        CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")
        return render_template("bi/event_profitability.html",
            profitability_records=profitability_records,
            events_needing_analysis=events_needing_analysis,
            completed_events_count=completed_events_count,
            CURRENCY=CURRENCY
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading event profitability: {e}")
        CURRENCY = current_app.config.get("CURRENCY_PREFIX", "UGX ")
        return render_template("bi/event_profitability.html",
            profitability_records=[],
            events_needing_analysis=[],
            completed_events_count=0,
            CURRENCY=CURRENCY
        )

@bi_bp.route("/event-profitability/seed", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def seed_profitability_data():
    """Generate sample data for event profitability analysis."""
    try:
        from seed_event_profitability_data import seed_event_profitability_data
        seed_event_profitability_data()
        flash("Sample event profitability data generated successfully!", "success")
    except Exception as e:
        current_app.logger.exception(f"Error seeding profitability data: {e}")
        flash(f"Error generating sample data: {str(e)}", "danger")
    return redirect(url_for("bi.event_profitability"))

@bi_bp.route("/ingredient-trends")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def ingredient_trends():
    """Ingredient price trend analysis."""
    try:
        # Get all ingredients
        ingredients = Ingredient.query.order_by(Ingredient.name.asc()).all()
        
        # Get price trend items with ingredients eagerly loaded
        trend_items = BIIngredientPriceTrend.query.options(
            joinedload(BIIngredientPriceTrend.inventory_item)
        ).order_by(
            BIIngredientPriceTrend.date.desc()
        ).limit(100).all()
        
        return render_template("bi/ingredient_trends.html",
            ingredients=ingredients,
            trend_items=trend_items,
            today_date=date.today().isoformat()
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading ingredient trends: {e}")
        return render_template("bi/ingredient_trends.html",
            ingredients=[],
            trend_items=[],
            today_date=date.today().isoformat()
        )

@bi_bp.route("/sales-forecast")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def sales_forecast():
    """Sales forecasting page."""
    try:
        # Get upcoming forecasts
        upcoming_forecasts = BISalesForecast.query.filter(
            BISalesForecast.date >= date.today()
        ).order_by(BISalesForecast.date.asc(), BISalesForecast.source.asc()).all()
        
        # Get historical forecasts (last 30 days)
        historical_start = date.today() - timedelta(days=30)
        historical_forecasts = BISalesForecast.query.filter(
            BISalesForecast.date >= historical_start,
            BISalesForecast.date < date.today()
        ).order_by(BISalesForecast.date.desc()).limit(100).all()
        
        return render_template("bi/sales_forecast.html",
            upcoming_forecasts=upcoming_forecasts,
            historical_forecasts=historical_forecasts
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading sales forecast: {e}")
        return render_template("bi/sales_forecast.html",
            upcoming_forecasts=[],
            historical_forecasts=[]
        )

@bi_bp.route("/staff-performance")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def staff_performance():
    """Staff performance analytics."""
    try:
        # Get all performance records
        performance_records = BIStaffPerformance.query.order_by(
            BIStaffPerformance.created_at.desc()
        ).limit(100).all()
        
        # Get employees
        employees = Employee.query.filter_by(status='active').all()
        
        return render_template("bi/staff_performance.html",
            performance_records=performance_records,
            employees=employees
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading staff performance: {e}")
        return render_template("bi/staff_performance.html",
            performance_records=[],
            employees=[]
        )

@bi_bp.route("/bakery-demand")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def bakery_demand():
    """Bakery demand forecasting."""
    try:
        # Get bakery items
        bakery_items = BakeryItem.query.filter_by(status="Active").all()
        
        # Get upcoming demand forecasts
        upcoming_demands = BIBakeryDemand.query.filter(
            BIBakeryDemand.date >= date.today()
        ).order_by(BIBakeryDemand.date.asc()).limit(100).all()
        
        return render_template("bi/bakery_demand.html",
            bakery_items=bakery_items,
            upcoming_demands=upcoming_demands
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading bakery demand: {e}")
        return render_template("bi/bakery_demand.html",
            bakery_items=[],
            upcoming_demands=[]
        )

@bi_bp.route("/customer-behavior")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def customer_behavior():
    """Customer behavior analytics."""
    try:
        # Get behavior records
        behavior_records = BICustomerBehavior.query.order_by(
            BICustomerBehavior.generated_at.desc()
        ).limit(200).all()
        
        # Group by customer
        behaviors_by_customer = {}
        for record in behavior_records:
            customer_id = record.client_id or record.customer_id
            if customer_id not in behaviors_by_customer:
                behaviors_by_customer[customer_id] = []
            behaviors_by_customer[customer_id].append(record)
        
        return render_template("bi/customer_behavior.html",
            behaviors_by_customer=behaviors_by_customer,
            total_records=len(behavior_records)
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading customer behavior: {e}")
        return render_template("bi/customer_behavior.html",
            behaviors_by_customer={},
            total_records=0
        )

@bi_bp.route("/pos-heatmap")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def pos_heatmap():
    """POS sales heatmap page."""
    try:
        # Get heatmap data
        heatmap_data = BIPOSHeatmap.query.order_by(
            BIPOSHeatmap.day, BIPOSHeatmap.hour
        ).all()
        
        # Generate heatmap matrix
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hours = list(range(24))
        
        heatmap_matrix = {}
        for day in days:
            heatmap_matrix[day] = {}
            for hour in hours:
                data = next((h for h in heatmap_data if h.day == day and h.hour == hour), None)
                heatmap_matrix[day][hour] = {
                    "sales": float(data.sales) if data else 0,
                    "orders": int(data.transaction_count) if data else 0
                }
        
        return render_template("bi/pos_heatmap.html",
            heatmap_matrix=heatmap_matrix,
            days=days,
            hours=hours
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading POS heatmap: {e}")
        return render_template("bi/pos_heatmap.html",
            heatmap_matrix={},
            days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            hours=list(range(24))
        )

# ============================
# API ENDPOINTS
# ============================

@bi_bp.route("/api/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_dashboard():
    """API: Get dashboard metrics."""
    try:
        result = get_bi_dashboard_metrics()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({"success": False, "error": result.get('error')}), 500
    except Exception as e:
        current_app.logger.exception(f"Error in API dashboard: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/api/event-profitability/generate", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_generate_event_profitability():
    """API: Generate event profitability analysis."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        event_id = data.get('event_id', type=int)
        
        if not event_id:
            return jsonify({"success": False, "error": "event_id is required"}), 400
        
        result = calculate_event_profitability(event_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error generating event profitability: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/event-profitability/pdf")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def event_profitability_pdf():
    """Generate and download Event Profitability Analysis PDF report."""
    from flask import send_file, flash, redirect
    from services.bi_service import generate_profitability_pdf_report
    from datetime import datetime
    
    try:
        # Generate PDF
        pdf_path = generate_profitability_pdf_report()
        
        if not pdf_path or not os.path.exists(pdf_path):
            flash("PDF file was not generated successfully.", "danger")
            return redirect(url_for("bi.event_profitability"))
        
        # Send file
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"event_profitability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype='application/pdf'
        )
    except ValueError as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("bi.event_profitability"))
    except ImportError as e:
        flash(f"PDF generation library not available: {str(e)}", "danger")
        return redirect(url_for("bi.event_profitability"))
    except Exception as e:
        current_app.logger.exception(f"Error generating profitability PDF: {e}")
        flash(f"Error generating PDF report: {str(e)}", "danger")
        return redirect(url_for("bi.event_profitability"))

@bi_bp.route("/api/ingredient-price/add", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_add_ingredient_price():
    """API: Add ingredient price data."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        item_id = data.get('item_id', type=int)
        price = data.get('price', type=float)
        price_date = data.get('date')
        
        if not item_id or not price:
            return jsonify({"success": False, "error": "item_id and price are required"}), 400
        
        # Parse date if provided
        parsed_date = None
        if price_date:
            try:
                parsed_date = datetime.strptime(price_date, '%Y-%m-%d').date()
            except:
                pass
        
        result = ingest_ingredient_price(item_id, price, parsed_date)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error adding ingredient price: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/api/ingredient-price/trend/<int:item_id>")
@login_required
def api_ingredient_price_trend(item_id):
    """API: Get ingredient price trend."""
    try:
        days = request.args.get('days', 30, type=int)
        result = generate_price_trend_history(item_id, days)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error getting price trend: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/api/sales-forecast/run", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_run_sales_forecast():
    """API: Run sales forecasting."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        source = data.get('source', 'all')
        model = data.get('model', 'simple')
        days = data.get('days', 14, type=int)
        
        result = run_sales_forecasting(source=source, model=model, days=days)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error running sales forecast: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/api/sales-forecast")
@login_required
def api_sales_forecast():
    """API: Get sales forecasts."""
    try:
        source = request.args.get('source', 'all')
        days = request.args.get('days', 30, type=int)
        
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        
        query = BISalesForecast.query.filter(
            BISalesForecast.date >= start_date,
            BISalesForecast.date <= end_date
        )
        
        if source != 'all':
            query = query.filter_by(source=source)
        
        forecasts = query.order_by(BISalesForecast.date.asc()).all()
        
        forecast_data = [{
            "source": f.source,
            "date": f.date.isoformat(),
            "predicted_sales": float(f.predicted_sales),
            "model": f.model_name,
            "confidence": float(f.confidence) if f.confidence else None
        } for f in forecasts]
        
        return jsonify({
            "success": True,
            "forecasts": forecast_data
        }), 200
    except Exception as e:
        current_app.logger.exception(f"Error getting sales forecast: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/api/staff-performance/add", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_add_staff_performance():
    """API: Add staff performance metric."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        employee_id = data.get('employee_id', type=int)
        metric = data.get('metric')
        value = data.get('value', type=float)
        period = data.get('period', 'daily')
        
        if not employee_id or not metric or value is None:
            return jsonify({"success": False, "error": "employee_id, metric, and value are required"}), 400
        
        result = generate_staff_performance(employee_id, metric, value, period)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error adding staff performance: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/api/bakery-demand/forecast", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_bakery_demand_forecast():
    """API: Generate bakery demand forecast."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        item_id = data.get('item_id', type=int)
        days = data.get('days', 14, type=int)
        
        if not item_id:
            return jsonify({"success": False, "error": "item_id is required"}), 400
        
        result = generate_bakery_demand_forecast(item_id, days)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error generating bakery demand forecast: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/api/customer-behavior/analyze", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_analyze_customer_behavior():
    """API: Analyze customer behavior."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        customer_id = data.get('customer_id', type=int)
        
        if not customer_id:
            return jsonify({"success": False, "error": "customer_id is required"}), 400
        
        result = calculate_customer_behavior(customer_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error analyzing customer behavior: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@bi_bp.route("/api/pos/heatmap")
@login_required
def api_pos_heatmap():
    """API: Get POS heatmap data."""
    try:
        days = request.args.get('days', 7, type=int)
        
        # Generate heatmap if not exists
        result = generate_pos_heatmap(days=days)
        
        if not result['success']:
            return jsonify({"success": False, "error": result.get('error')}), 500
        
        # Get heatmap data from database
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        
        heatmap_data = BIPOSHeatmap.query.filter(
            BIPOSHeatmap.period_start >= start_date,
            BIPOSHeatmap.period_end <= end_date
        ).order_by(BIPOSHeatmap.day, BIPOSHeatmap.hour).all()
        
        # Format for frontend
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        heatmap_matrix = {}
        
        for day in days:
            heatmap_matrix[day] = {}
            for hour in range(24):
                data = next((h for h in heatmap_data if h.day == day and h.hour == hour), None)
                heatmap_matrix[day][hour] = {
                    "sales": float(data.sales) if data else 0,
                    "orders": int(data.transaction_count) if data else 0
                }
        
        return jsonify({
            "success": True,
            "heatmap": heatmap_matrix,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }), 200
    except Exception as e:
        current_app.logger.exception(f"Error getting POS heatmap: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

