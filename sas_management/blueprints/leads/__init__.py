
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from sas_management.models import IncomingLead, UserRole, db
from sas_management.utils import role_required, paginate_query

leads_bp = Blueprint("leads", __name__, url_prefix="/leads")

@leads_bp.route("/")
@leads_bp.route("/list")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def index():
    """Leads dashboard - accessible only by Admin and SalesManager."""
    query = IncomingLead.query.order_by(IncomingLead.timestamp.desc())
    pagination = paginate_query(query)
    return render_template(
        "leads/index.html",
        leads=pagination.items,
        pagination=pagination,
    )

@leads_bp.route("/convert/<int:lead_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def convert_lead(lead_id):
    """Placeholder for converting a lead to Client/Event."""
    lead = IncomingLead.query.get_or_404(lead_id)
    flash(
        f"Convert lead functionality coming soon. Lead: {lead.client_name} ({lead.inquiry_type})",
        "info",
    )
    return redirect(url_for("leads.index"))

