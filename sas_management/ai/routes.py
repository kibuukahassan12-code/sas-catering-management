from flask import Blueprint, render_template
from flask_login import login_required

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

@ai_bp.route("/chat")
@login_required
def chat():
    return render_template("ai/chat.html")
