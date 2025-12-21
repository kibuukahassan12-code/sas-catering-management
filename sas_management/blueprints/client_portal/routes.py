"""Client Portal routes."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime

from sas_management.models import Client, Event, Quotation, QuotationLine, db
from services.client_portal_service import authenticate_client, create_shareable_link

client_portal_bp = Blueprint("client_portal", __name__, url_prefix="/client")


@client_portal_bp.route("/login", methods=["GET", "POST"])
def login():
    """Client portal login."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        
        result = authenticate_client(email, password)
        if result['success']:
            session['client_user_id'] = result['user'].id
            session['client_id'] = result['user'].client_id
            flash("Login successful!", "success")
            return redirect(url_for("client_portal.dashboard"))
        else:
            flash(result.get('error', 'Invalid credentials'), "danger")
    
    return render_template("client_portal/login.html")


@client_portal_bp.route("/logout")
def logout():
    """Client portal logout."""
    session.pop('client_user_id', None)
    session.pop('client_id', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("client_portal.login"))


@client_portal_bp.route("/dashboard")
def dashboard():
    """Client dashboard."""
    client_id = session.get('client_id')
    if not client_id:
        flash("Please log in to access your dashboard.", "warning")
        return redirect(url_for("client_portal.login"))
    
    try:
        client = db.session.get(Client, client_id)
        if not client:
            flash("Client not found.", "danger")
            return redirect(url_for("client_portal.login"))
        
        # Get client's events
        events = Event.query.filter_by(client_id=client_id).order_by(Event.event_date.desc()).limit(10).all()
        
        # Get recent quotations
        quotations = Quotation.query.filter_by(client_id=client_id).order_by(Quotation.created_at.desc()).limit(10).all()
        
        return render_template("client_portal/client_dashboard.html",
            client=client,
            events=events,
            quotations=quotations
        )
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return render_template("client_portal/client_dashboard.html", client=None, events=[], quotations=[])


@client_portal_bp.route("/quotes")
def quotes():
    """View client quotations."""
    client_id = session.get('client_id')
    if not client_id:
        flash("Please log in.", "warning")
        return redirect(url_for("client_portal.login"))
    
    quotations = Quotation.query.filter_by(client_id=client_id).order_by(Quotation.created_at.desc()).all()
    return render_template("client_portal/client_quotes.html", quotations=quotations)


@client_portal_bp.route("/quote/<int:quote_id>/view")
def view_quote(quote_id):
    """View quotation details."""
    client_id = session.get('client_id')
    if not client_id:
        flash("Please log in.", "warning")
        return redirect(url_for("client_portal.login"))
    
    quotation = Quotation.query.filter_by(id=quote_id, client_id=client_id).first_or_404()
    lines = QuotationLine.query.filter_by(quotation_id=quote_id).all()
    
    return render_template("client_portal/client_view_quote.html",
        quotation=quotation,
        lines=lines
    )


@client_portal_bp.route("/quote/<int:quote_id>/approve", methods=["POST"])
def approve_quote(quote_id):
    """Approve quotation."""
    client_id = session.get('client_id')
    if not client_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        quotation = Quotation.query.filter_by(id=quote_id, client_id=client_id).first_or_404()
        quotation.status = "Approved"
        quotation.approved_at = datetime.utcnow()
        db.session.commit()
        
        flash("Quotation approved successfully!", "success")
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@client_portal_bp.route("/contracts")
def contracts():
    """View client contracts."""
    client_id = session.get('client_id')
    if not client_id:
        flash("Please log in.", "warning")
        return redirect(url_for("client_portal.login"))
    
    # Get contracts linked to client's events
    from sas_management.models import Contract
    events = Event.query.filter_by(client_id=client_id).all()
    event_ids = [e.id for e in events]
    contracts = Contract.query.filter(Contract.event_id.in_(event_ids)).all() if event_ids else []
    
    return render_template("client_portal/client_contracts.html", contracts=contracts)

