"""SAS AI Routes - Flask Blueprint routes for chat functionality."""
from flask import request, jsonify, render_template, session, current_app, url_for
from flask_login import login_required, current_user
from . import sas_ai_bp
from .permissions import require_sas_ai_enabled, is_sas_ai_enabled
from .memory import add_message
from datetime import datetime

from sas_management.ai.compat.legacy_chat_adapter import legacy_chat_handler
from sas_management.ai.feature_guard import ai_features_state, log_if_disabled

# Import UserRole for role checking
try:
    from sas_management.models import UserRole
except ImportError:
    UserRole = None


@sas_ai_bp.route("/chat", methods=["POST"])
@login_required
@require_sas_ai_enabled
def chat():
    """Chat endpoint - accepts messages and returns AI replies via canonical engine adapter."""
    try:
        # Phase 2: observe-only feature flag logging (no blocking)
        log_if_disabled("ai_enabled", request.path)

        data = request.get_json() or {}

        if not data:
            return jsonify(
                {
                    "success": False,
                    "reply": "Invalid request data",
                }
            ), 400

        # Get message and session_id
        user_message = (data.get("message") or "").strip()
        session_id = data.get("session_id") or session.get("sas_ai_session_id")

        if not user_message:
            return jsonify(
                {
                    "success": False,
                    "reply": "Message is required",
                }
            ), 400

        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{current_user.id}_{datetime.utcnow().timestamp()}"
            session["sas_ai_session_id"] = session_id

        # Add user message to conversation (legacy behavior preserved)
        add_message(session_id, "user", user_message)

        # Delegate to canonical SASAIEngine via compat adapter
        engine_response = legacy_chat_handler(user_message, current_user)

        # Store assistant reply in conversation, if available
        try:
            add_message(
                session_id,
                "assistant",
                engine_response.get("text", ""),
                metadata={"source": engine_response.get("source")},
            )
        except Exception:
            # Conversation memory issues must not block the response
            current_app.logger.warning(
                "Failed to save SAS AI assistant message to memory", exc_info=True
            )

        # Log usage without assuming specific response fields
        current_app.logger.info(
            f"SAS AI Chat (legacy adapter): user_id={current_user.id}, "
            f"session_id={str(session_id)[:20]}, message_length={len(user_message)}"
        )

        # Transform engine response to match expected format
        # Engine returns: {"text": "...", "source": "..."}
        # JavaScript expects: {"success": true, "reply": "...", "session_id": "..."}
        response = {
            "success": True,
            "reply": engine_response.get("text", "I'm sorry, I couldn't process that request."),
            "session_id": session_id
        }
        
        # Add optional fields if present
        if "source" in engine_response:
            response["source"] = engine_response["source"]
        if "intent" in engine_response:
            response["intent"] = engine_response["intent"]
        if "suggested_actions" in engine_response:
            response["suggested_actions"] = engine_response["suggested_actions"]
        
        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Error in SAS AI chat endpoint: {e}", exc_info=True)
        return jsonify(
            {
                "success": False,
                "reply": "I encountered an error processing your request. Please try again.",
                "error": str(e) if current_app.config.get("DEBUG") else None,
            }
        ), 500


@sas_ai_bp.route("/chat", methods=["GET"])
@login_required
def chat_ui():
    """Render the chat UI with context."""
    # Phase 2: observe-only feature flag logging for legacy UI entrypoint
    log_if_disabled("ai_enabled", request.path)

    if not is_sas_ai_enabled(current_app):
        return render_template("sas_ai/offline.html"), 503
    
    # Determine current module from referrer or session
    current_module = session.get('current_module', 'general')
    referrer = request.referrer or ''
    
    # Auto-detect module from referrer
    if '/service' in referrer:
        current_module = 'service'
    elif '/finance' in referrer or '/financial' in referrer:
        current_module = 'finance'
    elif '/events' in referrer:
        current_module = 'events'
    elif '/staff' in referrer:
        current_module = 'staff'
    elif '/client' in referrer:
        current_module = 'client'
    
    # Get active event from session or referrer
    active_event = None
    if session.get('active_event_id'):
        try:
            from sas_management.service.models import ServiceEvent
            event_id = session.get('active_event_id')
            active_event = ServiceEvent.query.get(event_id)
            if active_event:
                active_event = {
                    'id': active_event.id,
                    'title': active_event.title or f'Event #{active_event.id}',
                    'event_date': active_event.event_date.isoformat() if active_event.event_date else None
                }
        except Exception:
            active_event = None
    
    # Get user role
    user_role = 'user'
    if hasattr(current_user, 'role') and current_user.role:
        if UserRole:
            # Map UserRole enum to string
            role_map = {
                UserRole.Admin: 'admin',
                UserRole.SalesManager: 'sales_manager',
                UserRole.ServiceManager: 'service_manager',
                UserRole.Staff: 'staff',
                UserRole.Client: 'client'
            }
            user_role = role_map.get(current_user.role, str(current_user.role).lower())
        else:
            user_role = str(current_user.role).lower()
    
    return render_template(
        "sas_ai/chat.html",
        current_module=current_module,
        active_event=active_event,
        user_role=user_role,
        features=ai_features_state(),
    )


@sas_ai_bp.route("/status", methods=["GET"])
@login_required
def status():
    """Check SAS AI status."""
    return jsonify({
        "enabled": is_sas_ai_enabled(current_app),
        "status": "online" if is_sas_ai_enabled(current_app) else "offline"
    }), 200

