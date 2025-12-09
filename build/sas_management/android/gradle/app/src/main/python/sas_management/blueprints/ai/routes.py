"""AI Suite routes."""
import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user

from models import UserRole

from utils import role_required

# Safe import of AI service
try:
    from services.ai_service import (
        auto_cost_optimization, menu_engine_recommendations,
        run_sales_forecast, forecast_accuracy_score,
        kitchen_planner, predictive_staffing, predict_item_shortages
    )
    AI_SERVICE_AVAILABLE = True
except Exception as e:
    current_app.logger.warning(f"AI service not available: {e}") if 'current_app' in globals() else None
    AI_SERVICE_AVAILABLE = False

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

@ai_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """AI Suite dashboard."""
    try:
        from models import (
            AIPredictionRun, MenuRecommendation, ForecastResult,
            StaffingSuggestion, ShortageAlert, CostOptimization
        )
        
        # Get recent activity
        recent_runs = AIPredictionRun.query.order_by(AIPredictionRun.created_at.desc()).limit(10).all()
        recent_recommendations = MenuRecommendation.query.order_by(MenuRecommendation.created_at.desc()).limit(5).all()
        active_alerts = ShortageAlert.query.filter(ShortageAlert.status == 'active').count()
        
        status = {
            'ai_service_available': AI_SERVICE_AVAILABLE,
            'mock_mode': os.getenv('AI_MOCK', 'false').lower() == 'true'
        }
        
        return render_template("ai/ai_dashboard.html",
            recent_runs=recent_runs,
            recent_recommendations=recent_recommendations,
            active_alerts=active_alerts,
            status=status
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading AI dashboard: {e}")
        return render_template("ai/ai_dashboard.html",
            recent_runs=[],
            recent_recommendations=[],
            active_alerts=0,
            status={'ai_service_available': False}
        )

@ai_bp.route("/menu-recommendations")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def menu_recommendations():
    """Menu AI recommendations page."""
    try:
        from models import MenuRecommendation
        
        recommendations = MenuRecommendation.query.order_by(
            MenuRecommendation.score.desc()
        ).limit(50).all()
        
        return render_template("ai/menu_recommendations.html",
            recommendations=recommendations
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading menu recommendations: {e}")
        flash("An error occurred loading recommendations.", "danger")
        return render_template("ai/menu_recommendations.html", recommendations=[])

@ai_bp.route("/cost-optimizations")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def cost_optimizations():
    """Cost optimization suggestions page."""
    try:
        from models import CostOptimization
        
        optimizations = CostOptimization.query.order_by(
            CostOptimization.savings.desc()
        ).limit(50).all()
        
        return render_template("ai/cost_optimization.html",
            optimizations=optimizations
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading cost optimizations: {e}")
        flash("An error occurred loading optimizations.", "danger")
        return render_template("ai/cost_optimization.html", optimizations=[])

@ai_bp.route("/forecast/<source>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def forecast_view(source):
    """Forecast visualization page."""
    try:
        from models import ForecastResult
        
        forecasts = ForecastResult.query.filter(
            ForecastResult.source == source
        ).order_by(ForecastResult.date.desc()).limit(30).all()
        
        return render_template("ai/forecast_view.html",
            source=source,
            forecasts=forecasts
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading forecast: {e}")
        flash("An error occurred loading forecast.", "danger")
        return render_template("ai/forecast_view.html", source=source, forecasts=[])

@ai_bp.route("/kitchen-assistant/<int:event_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager, UserRole.KitchenStaff)
def kitchen_assistant(event_id):
    """Kitchen assistant page for event."""
    try:
        if not AI_SERVICE_AVAILABLE:
            flash("AI service not available.", "warning")
            return redirect(url_for("events.event_view", event_id=event_id))
        
        result = kitchen_planner(event_id)
        
        return render_template("ai/kitchen_assistant.html",
            event_id=event_id,
            schedule=result.get('schedule', []),
            success=result.get('success', False)
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading kitchen assistant: {e}")
        flash("An error occurred loading kitchen assistant.", "danger")
        return render_template("ai/kitchen_assistant.html", event_id=event_id, schedule=[])

@ai_bp.route("/staffing/<int:event_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def staffing_recommendations(event_id):
    """Staffing recommendations page."""
    try:
        from models import StaffingSuggestion
        
        suggestions = StaffingSuggestion.query.filter(
            StaffingSuggestion.event_id == event_id
        ).order_by(StaffingSuggestion.created_at.desc()).limit(5).all()
        
        return render_template("ai/staffing_recommendations.html",
            event_id=event_id,
            suggestions=suggestions
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading staffing recommendations: {e}")
        flash("An error occurred loading staffing recommendations.", "danger")
        return render_template("ai/staffing_recommendations.html", event_id=event_id, suggestions=[])

@ai_bp.route("/shortages")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def shortages():
    """Shortage alerts page."""
    try:
        from models import ShortageAlert, InventoryItem
        
        alerts = ShortageAlert.query.filter(
            ShortageAlert.status == 'active'
        ).order_by(ShortageAlert.severity.desc(), ShortageAlert.predicted_shortage_date.asc()).all()
        
        return render_template("ai/shortages.html",
            alerts=alerts
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading shortages: {e}")
        flash("An error occurred loading shortage alerts.", "danger")
        return render_template("ai/shortages.html", alerts=[])

# ============================================================
# API ROUTES
# ============================================================

@ai_bp.route("/api/menu/recommend", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_menu_recommend():
    """API: Generate menu recommendations."""
    try:
        if not AI_SERVICE_AVAILABLE:
            return jsonify({'success': False, 'error': 'AI service not available'}), 503
        
        data = request.get_json() or {}
        top_k = int(data.get('top_k', 10))
        constraints = data.get('constraints', {})
        
        result = menu_engine_recommendations(top_k=top_k, constraints=constraints)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(f"Error in menu recommend API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route("/api/cost/optimize", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_cost_optimize():
    """API: Run cost optimization."""
    try:
        if not AI_SERVICE_AVAILABLE:
            return jsonify({'success': False, 'error': 'AI service not available'}), 503
        
        data = request.get_json() or {}
        event_id = data.get('event_id')
        menu_items = data.get('menu_items')
        
        result = auto_cost_optimization(event_id=event_id, menu_items_list=menu_items)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(f"Error in cost optimize API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route("/api/forecast/run", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_forecast_run():
    """API: Run sales forecast."""
    try:
        if not AI_SERVICE_AVAILABLE:
            return jsonify({'success': False, 'error': 'AI service not available'}), 503
        
        data = request.get_json() or {}
        source = data.get('source', 'POS')
        horizon = int(data.get('horizon', 14))
        
        result = run_sales_forecast(source=source, horizon=horizon)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(f"Error in forecast run API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route("/api/forecast/result/<int:result_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_forecast_result(result_id):
    """API: Get forecast result."""
    try:
        from models import ForecastResult
        
        result = ForecastResult.query.get_or_404(result_id)
        return jsonify({
            'success': True,
            'result': {
                'id': result.id,
                'source': result.source,
                'date': result.date.isoformat() if result.date else None,
                'predicted': float(result.predicted) if result.predicted else None,
                'actual': float(result.actual) if result.actual else None,
                'model_name': result.model_name
            }
        })
    except Exception as e:
        current_app.logger.exception(f"Error in forecast result API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route("/api/staffing/run", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_staffing_run():
    """API: Run predictive staffing."""
    try:
        if not AI_SERVICE_AVAILABLE:
            return jsonify({'success': False, 'error': 'AI service not available'}), 503
        
        data = request.get_json() or {}
        event_id = data.get('event_id')
        date_range = data.get('date_range')  # Would need parsing
        
        result = predictive_staffing(event_id=event_id, date_range=date_range)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(f"Error in staffing run API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ai_bp.route("/api/shortages/run", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_shortages_run():
    """API: Run shortage prediction."""
    try:
        if not AI_SERVICE_AVAILABLE:
            return jsonify({'success': False, 'error': 'AI service not available'}), 503
        
        data = request.get_json() or {}
        horizon_days = int(data.get('horizon_days', 30))
        
        result = predict_item_shortages(horizon_days=horizon_days)
        return jsonify(result)
    except Exception as e:
        current_app.logger.exception(f"Error in shortages run API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

