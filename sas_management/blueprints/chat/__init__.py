from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from sas_management.models import Message, db

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

# Available channels with descriptions
AVAILABLE_CHANNELS = {
    "General": "General discussion and announcements",
    "Kitchen_Ops": "Kitchen operations and coordination",
    "Hire_Logistics": "Hire department logistics and scheduling",
    "Production": "Production planning and updates",
    "Sales": "Sales team coordination",
    "Support": "Technical support and help",
}


@chat_bp.route("")
@login_required
def index():
    """Main chat page - accessible to all logged-in users."""
    channel = request.args.get("channel", "General")
    if channel not in AVAILABLE_CHANNELS:
        channel = "General"

    # Fetch messages for the selected channel (last 100 messages)
    messages = (
        Message.query.filter_by(channel=channel)
        .order_by(Message.timestamp.desc())
        .limit(100)
        .all()
    )
    messages.reverse()  # Show oldest first

    # Get channel info
    channel_description = AVAILABLE_CHANNELS.get(channel, "Chat channel")

    return render_template(
        "chat/index.html",
        channels=AVAILABLE_CHANNELS,
        current_channel=channel,
        channel_description=channel_description,
        messages=messages,
    )


@chat_bp.route("/send", methods=["POST"])
@login_required
def send_message():
    """Handle message submission."""
    channel = request.form.get("channel", "General")
    content = request.form.get("content", "").strip()

    if not content:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"status": "error", "message": "Message cannot be empty"}), 400
        flash("Message cannot be empty.", "warning")
        return redirect(url_for("chat.index", channel=channel))

    if channel not in AVAILABLE_CHANNELS:
        channel = "General"

    message = Message(
        user_id=current_user.id,
        channel=channel,
        content=content,
        timestamp=datetime.utcnow(),
    )
    db.session.add(message)
    db.session.commit()

    # Return JSON for AJAX requests, otherwise redirect
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message_id": message.id}), 200

    return redirect(url_for("chat.index", channel=channel))


@chat_bp.route("/api/messages/<channel_name>")
@login_required
def api_get_messages(channel_name):
    """API endpoint to fetch messages for a specific channel as JSON."""
    if channel_name not in AVAILABLE_CHANNELS:
        return jsonify({"error": "Invalid channel"}), 400

    # Query messages for the channel (last 100 messages)
    messages = (
        Message.query.filter_by(channel=channel_name)
        .order_by(Message.timestamp.desc())
        .limit(100)
        .all()
    )
    messages.reverse()  # Show oldest first

    # Serialize messages to JSON
    messages_data = [
        {
            "id": msg.id,
            "user_id": msg.user.id,
            "user_email": msg.user.email,
            "user_name": msg.user.email.split("@")[0] if msg.user.email else "User",
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
            "formatted_time": msg.timestamp.strftime("%H:%M"),
            "formatted_date": msg.timestamp.strftime("%b %d, %Y"),
            "is_own_message": msg.user.id == current_user.id,
        }
        for msg in messages
    ]

    return jsonify(messages_data)

