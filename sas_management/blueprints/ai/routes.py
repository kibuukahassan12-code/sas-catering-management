"""
AI Chat Blueprint - ChatGPT-like interface.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from markupsafe import Markup
from sas_management.ai.service import ai_service

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

# Rate limiting will be applied via app-level limiter if available
# Check if limiter is initialized in app context


@ai_bp.route("/chat")
@login_required
def chat():
    """Render the chat interface."""
    try:
        return render_template("ai/chat.html")
    except Exception as e:
        current_app.logger.error(f"Error rendering chat page: {e}", exc_info=True)
        # Return minimal HTML even if template fails
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>SAS AI Chat</title></head>
        <body>
            <h1>SAS AI Chat</h1>
            <p>Chat interface is loading...</p>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """, 200


@ai_bp.route("/chat/send", methods=["POST"])
@login_required
def chat_send():
    """Handle chat message and return AI response with extended format.
    
    Rate limiting: Applied via app-level limiter (20 per minute default).
    """
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "")
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Process through intelligent chat engine with user context
        result = ai_service.chat(message, user_id=user_id)
        
        # Ensure result is a dict
        if isinstance(result, str):
            result = {
                "reply": result,
                "chart": None,
                "prediction": None,
                "report_url": None
            }
        
        # Return extended response format with HTML-safe markdown
        reply_text = result.get("message", result.get("reply", ""))
        return jsonify({
            "reply": str(Markup(reply_text)),
            "chart": result.get("chart"),
            "prediction": result.get("prediction"),
            "report_url": result.get("report_url")
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error in chat_send: {e}", exc_info=True)
        error_msg = f"⚠️ An error occurred while processing this request: {str(e)}"
        return jsonify({
            "reply": str(Markup(error_msg)),
            "chart": None,
            "prediction": None,
            "report_url": None
        }), 200


@ai_bp.route("/reports/<filename>")
@login_required
def serve_report(filename):
    """Serve generated AI reports."""
    try:
        import os
        from flask import send_from_directory
        
        # Security: only allow HTML files
        if not filename.endswith('.html'):
            return "Invalid file type", 400
        
        reports_dir = os.path.join(current_app.instance_path, "reports")
        return send_from_directory(reports_dir, filename)
    except Exception as e:
        current_app.logger.error(f"Error serving report: {e}", exc_info=True)
        return "Report not found", 404
