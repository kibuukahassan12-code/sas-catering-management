"""
SAS AI Blueprint

Single consolidated blueprint for all AI features.
Routes are guarded by feature enable/disable status.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from sas_management.ai.feature_guard import ai_features_state, log_if_disabled
from sas_management.ai.memory import conversation_memory

from sas_management.models import UserRole, db
from sas_management.utils import role_required
from sas_management.ai.dashboard import get_dashboard_data
from sas_management.ai.registry import (
    get_feature_registry,
    get_feature_by_key,
    get_features_by_category,
)
from sas_management.ai.guards import require_ai_module, require_ai_feature
from sas_management.ai.state import is_enabled, enable, disable, get_all_features_state
from sas_management.ai.feature_model import is_ai_feature_enabled
from sas_management.ai.branding import get_value_color, get_feature_icon
from sas_management.ai.scheduler import ai_scheduler

# Create blueprint - using "sas_ai" name to avoid conflict with legacy ai_bp
# Canonical route: /sas-ai/chat (premium ChatGPT-style UI)
sas_ai_bp = Blueprint("sas_ai", __name__, url_prefix="/sas-ai")


@sas_ai_bp.before_request
@require_ai_module
def check_ai_module():
    """Ensure AI module is enabled before processing any request."""
    pass


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@sas_ai_bp.route("/")
@sas_ai_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def dashboard():
    """AI Hub Dashboard - main entry point."""
    try:
        log_if_disabled("ai_enabled", request.path)

        dashboard_data = get_dashboard_data()
        
        # Log dashboard access
        current_app.logger.info(
            f"SAS AI dashboard accessed by user {current_user.email}"
        )
        
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
        log_if_disabled("ai_enabled", request.path)

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


@sas_ai_bp.route("/chat")
@login_required
def chat_ui():
    """SAS AI Chat interface - Canonical ChatGPT-style UI route."""
    try:
        log_if_disabled("ai_enabled", request.path)

        # Auto-enable AI module and ai_chat feature if not already enabled
        if not current_app.config.get("AI_MODULE_ENABLED", False):
            current_app.config["AI_MODULE_ENABLED"] = True
            current_app.logger.info("AI module auto-enabled")
        
        # Enforce DB-backed feature flag for SAS AI Chat
        if not is_ai_feature_enabled("sas_ai_chat"):
            current_app.logger.warning("SAS AI Chat accessed while disabled in DB")
            return render_template(
                "ai/feature_disabled.html",
                feature={"name": "SAS AI Chat", "key": "sas_ai_chat"},
                feature_key="sas_ai_chat",
            ), 403

        current_app.logger.info(
            f"SAS AI Chat accessed by user {current_user.email}"
        )

        # Pass feature state into canonical chat UI (observation-only in Phase 2)
        return render_template("ai/chat.html", features=ai_features_state())
    except Exception as e:
        current_app.logger.error(f"Error loading AI Chat: {e}")
        from flask import flash
        flash("An error occurred loading AI Chat.", "danger")
        from flask import abort
        abort(404)


@sas_ai_bp.route("/features/<feature_key>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def feature_detail(feature_key):
    """View details of a specific AI feature."""
    try:
        log_if_disabled("ai_enabled", request.path)

        feature = get_feature_by_key(feature_key)
        
        if not feature:
            from flask import abort
            abort(404)
        
        # Log feature access
        current_app.logger.info(
            f"SAS AI feature '{feature_key}' accessed by user {current_user.email}"
        )
        
        # Legacy state-based enabled remains for backward compatibility,
        # but primary enforcement now comes from DB-backed feature codes.
        enabled = is_enabled(feature_key)
        
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
# API ENDPOINTS
# ============================================================================

@sas_ai_bp.route("/api/features/<feature_key>/status")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_feature_status(feature_key):
    """Get status of a specific AI feature."""
    try:
        log_if_disabled("ai_enabled", request.path)

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


@sas_ai_bp.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    """
    Dedicated SAS AI Chat endpoint for ChatGPT-style UI.

    - Enforces DB-backed feature toggle (sas_ai_chat)
    - Uses SASAIAssistant via ai.services.ai_chat.process_chat_message
    - Available to all authenticated users (role-based visibility handled inside assistant)
    """
    from flask import request
    from sas_management.ai.services.ai_chat import process_chat_message

    log_if_disabled("ai_enabled", request.path)

    if not is_ai_feature_enabled("sas_ai_chat"):
        return jsonify({
            "success": False,
            "error": "SAS AI Chat is disabled by admin",
        }), 403

    payload = request.get_json() or {}
    message = payload.get("message", "") or ""
    context = payload.get("context", {}) or {}

    try:
        result = process_chat_message(message=message, user_id=current_user.id, context=context)
        return jsonify(result), (200 if result.get("success", False) else 400)
    except Exception as e:
        current_app.logger.error(f"SAS AI Chat API error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "reply": "I encountered an error processing your request. Please try again.",
        }), 500


@sas_ai_bp.route("/api/chat/clear", methods=["POST"])
@login_required
def api_chat_clear():
    """
    Clear the current user's SAS AI conversation memory.
    """
    log_if_disabled("ai_enabled", request.path)

    try:
        # Phase 1: clear in-memory conversation state for this user.
        try:
            conversation_memory.clear(current_user.id)
        except Exception as e:  # pragma: no cover - defensive
            current_app.logger.warning(
                "Error clearing in-memory SAS AI conversation for user %s: %s",
                current_user.id,
                e,
            )

        return jsonify({"success": True}), 200
    except Exception as e:
        current_app.logger.error(f"SAS AI Chat clear error: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Unable to clear conversation"}), 500


@sas_ai_bp.route("/api/scheduler/run-due", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def api_run_scheduler_due():
    """
    Manually trigger execution of due scheduled AI actions.

    Phase 1: admin-only, in-memory, logs only.
    """
    from sas_management.ai.engine import SASAIEngine
    from sas_management.ai.actions import get_actions

    log_if_disabled("ai_enabled", request.path)

    try:
        engine = SASAIEngine()
        actions = get_actions()
        ai_scheduler.run_due(engine=engine, actions=actions)
        return jsonify({"success": True}), 200
    except Exception as e:
        current_app.logger.warning(f"SAS AI scheduler run error (non-fatal): {e}")
        return jsonify({"success": False, "error": "Unable to run scheduler"}), 500


@sas_ai_bp.route("/api/features/<feature_key>/use", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_feature_use(feature_key):
    """API endpoint to use a specific AI feature."""
    try:
        log_if_disabled("ai_enabled", request.path)

        # Respect DB-backed SAS AI Chat toggle for ai_chat feature
        if feature_key == "ai_chat" and not is_ai_feature_enabled("sas_ai_chat"):
            return jsonify({
                "success": False,
                "error": "SAS AI Chat is disabled by admin",
            }), 403
        
        data = request.get_json() or {}
        
        # Get feature definition
        feature = get_feature_by_key(feature_key)
        if not feature:
            return jsonify({"success": False, "error": "Feature not found"}), 404
        
        # Import and call service handler
        service_handler_path = feature.get("service_handler")
        if not service_handler_path:
            return jsonify({"success": False, "error": "Service handler not defined"}), 500
        
        # Dynamically import service handler
        try:
            module_path, function_name = service_handler_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[function_name])
            handler = getattr(module, function_name)
        except (ImportError, AttributeError) as e:
            current_app.logger.error(f"Error importing handler '{service_handler_path}': {e}")
            return jsonify({
                "success": False,
                "error": f"Service handler import error: {str(e)}"
            }), 500
        
        # Special handling for ai_chat - pass user_id for logging
        if feature_key == "ai_chat":
            message = data.get("message", "")
            if not message or not message.strip():
                return jsonify({
                    "success": False,
                    "error": "Message is required",
                    "result": {
                        "reply": "Please enter a message.",
                        "intent": "general_knowledge",
                        "source": "general_knowledge",
                        "suggested_actions": []
                    }
                }), 400
            
            try:
                result = handler(message=message, user_id=current_user.id, context=data)
            except Exception as e:
                current_app.logger.error(f"Error in AI chat handler: {e}", exc_info=True)
                result = {
                    "success": False,
                    "error": str(e),
                    "reply": "I encountered an error processing your request. Please try again.",
                    "intent": "general_knowledge",
                    "source": "general_knowledge",
                    "suggested_actions": ["Try again", "Ask about events"],
                }
        else:
            # Call handler with data for other features
            try:
                result = handler(**data)
            except Exception as e:
                current_app.logger.error(f"Error in handler for '{feature_key}': {e}", exc_info=True)
                return jsonify({
                    "success": False,
                    "error": str(e),
                }), 500
        
        # Ensure result has success flag
        if not isinstance(result, dict) or "success" not in result:
            result = {"success": True, **result}
        
        # Log feature usage
        current_app.logger.info(
            f"SAS AI used: {feature_key} by user {current_user.email}"
        )
        
        return jsonify({
            "success": True,
            "feature": feature_key,
            "result": result,
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error using AI feature '{feature_key}': {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred. Please try again."
        }), 500

