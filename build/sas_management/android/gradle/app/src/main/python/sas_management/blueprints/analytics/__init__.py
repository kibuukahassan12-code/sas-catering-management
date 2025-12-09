from flask import Blueprint, render_template
from flask_login import login_required

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics", template_folder="templates")

@analytics_bp.route("/dashboard")
@login_required
def dashboard():
    """Analytics dashboard - skeleton implementation."""
    # Minimal skeleton: real metrics later
    metrics = {
        "revenue": 0,
        "orders": 0,
        "events": 0,
        "clients": 0
    }
    return render_template("analytics/dashboard.html", metrics=metrics)

