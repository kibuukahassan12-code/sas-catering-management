"""
SAS AI Routes

Routes for the SAS AI hub dashboard and feature management.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from sas_management.models import UserRole
from sas_management.utils import role_required
from sas_management.ai.dashboard import get_dashboard_data
from sas_management.ai.registry import get_feature_by_key, is_feature_enabled
from sas_management.ai.permissions import check_ai_access

sas_ai_bp = Blueprint("sas_ai", __name__, url_prefix="/sas-ai")


@sas_ai_bp.before_request
def check_ai_module_enabled():
    """Check if AI module is enabled before processing any request."""
    if not current_app.config.get("AI_MODULE_ENABLED", False):
        from flask import abort
        abort(404)


@sas_ai_bp.route("/")
@sas_ai_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """AI Hub Dashboard - main entry point."""
    try:
        if not check_ai_access():
            from flask import abort
            abort(403)
        
        dashboard_data = get_dashboard_data()
        
        return render_template(
            "ai/dashboard.html",
            **dashboard_data,
        )
    except Exception as e:
        current_app.logger.error(f"Error loading AI dashboard: {e}")
        from flask import flash
        flash("An error occurred loading the AI dashboard.", "danger")
        return render_template(
            "ai/dashboard.html",
            module_enabled=False,
            features=[],
            enabled_count=0,
            total_count=0,
            features_by_category={},
        )


@sas_ai_bp.route("/features")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def feature_list():
    """List all AI features."""
    try:
        if not check_ai_access():
            from flask import abort
            abort(403)
        
        from sas_management.ai.registry import get_feature_registry, get_features_by_category
        
        registry = get_feature_registry()
        features_by_category = get_features_by_category()
        
        return render_template(
            "ai/feature_list.html",
            features=list(registry.values()),
            features_by_category=features_by_category,
        )
    except Exception as e:
        current_app.logger.error(f"Error loading AI feature list: {e}")
        from flask import flash
        flash("An error occurred loading features.", "danger")
        return render_template(
            "ai/feature_list.html",
            features=[],
            features_by_category={},
        )


@sas_ai_bp.route("/features/<feature_key>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def feature_detail(feature_key):
    """View details of a specific AI feature."""
    try:
        if not check_ai_access():
            from flask import abort
            abort(403)
        
        feature = get_feature_by_key(feature_key)
        
        if not feature:
            from flask import abort
            abort(404)
        
        # Log feature access
        current_app.logger.info(
            f"AI feature '{feature_key}' accessed by user {current_user.email}"
        )
        
        enabled = is_feature_enabled(feature_key)
        
        return render_template(
            "ai/feature_detail.html",
            feature=feature,
            enabled=enabled,
        )
    except Exception as e:
        current_app.logger.error(f"Error loading AI feature detail: {e}")
        from flask import flash, abort
        flash("An error occurred loading the feature.", "danger")
        abort(404)


# ============================================================================
# API ENDPOINTS FOR EACH FEATURE
# ============================================================================

@sas_ai_bp.route("/api/features/<feature_key>/use", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_feature_use(feature_key):
    """API endpoint to use a specific AI feature."""
    try:
        if not check_ai_access():
            return jsonify({"success": False, "error": "Access denied"}), 403
        
        if not is_feature_enabled(feature_key):
            return jsonify({
                "success": False,
                "error": "Feature is disabled",
                "enabled": False,
            }), 200
        
        data = request.get_json() or {}
        
        # Route to appropriate service based on feature_key
        result = None
        
        if feature_key == "event_planner":
            from sas_management.ai.services.event_planner import get_event_planning_suggestions
            result = get_event_planning_suggestions(
                event_type=data.get("event_type"),
                guest_count=data.get("guest_count"),
            )
        elif feature_key == "quotation_ai":
            from sas_management.ai.services.quotation_ai import generate_quotation_suggestions
            result = generate_quotation_suggestions(
                client_id=data.get("client_id"),
                event_type=data.get("event_type"),
            )
        elif feature_key == "profit_analyzer":
            from sas_management.ai.services.profit_analyzer import analyze_profit_opportunities
            result = analyze_profit_opportunities(
                timeframe=data.get("timeframe", "30d"),
            )
        elif feature_key == "pricing_advisor":
            from sas_management.ai.services.pricing_advisor import get_pricing_recommendations
            result = get_pricing_recommendations(
                item_id=data.get("item_id"),
                category=data.get("category"),
            )
        elif feature_key == "staff_coach":
            from sas_management.ai.services.staff_coach import get_staff_coaching_recommendations
            result = get_staff_coaching_recommendations(
                staff_id=data.get("staff_id"),
            )
        elif feature_key == "inventory_predictor":
            from sas_management.ai.services.inventory_predictor import predict_inventory_needs
            result = predict_inventory_needs(
                horizon_days=data.get("horizon_days", 30),
            )
        elif feature_key == "client_analyzer":
            from sas_management.ai.services.client_analyzer import analyze_client
            result = analyze_client(
                client_id=data.get("client_id"),
            )
        elif feature_key == "compliance_monitor":
            from sas_management.ai.services.compliance_monitor import check_compliance_status
            result = check_compliance_status(
                area=data.get("area", "all"),
            )
        elif feature_key == "ops_chat":
            from sas_management.ai.services.ops_chat import chat_with_assistant
            result = chat_with_assistant(
                message=data.get("message", ""),
                context=data.get("context"),
            )
        elif feature_key == "business_forecaster":
            from sas_management.ai.services.business_forecaster import forecast_business_metrics
            result = forecast_business_metrics(
                horizon_days=data.get("horizon_days", 90),
                metrics=data.get("metrics"),
            )
        else:
            return jsonify({"success": False, "error": "Unknown feature"}), 404
        
        # Log feature usage
        current_app.logger.info(
            f"AI feature '{feature_key}' used by user {current_user.email}"
        )
        
        return jsonify({
            "success": True,
            "feature": feature_key,
            "result": result,
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error using AI feature '{feature_key}': {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


@sas_ai_bp.route("/api/features/<feature_key>/status")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_feature_status(feature_key):
    """Get status of a specific AI feature."""
    try:
        if not check_ai_access():
            return jsonify({"success": False, "error": "Access denied"}), 403
        
        feature = get_feature_by_key(feature_key)
        if not feature:
            return jsonify({"success": False, "error": "Feature not found"}), 404
        
        enabled = is_feature_enabled(feature_key)
        
        return jsonify({
            "success": True,
            "feature": feature_key,
            "enabled": enabled,
            "name": feature.get("name"),
            "description": feature.get("description"),
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting feature status '{feature_key}': {e}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500

