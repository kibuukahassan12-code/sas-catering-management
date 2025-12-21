"""Proposal Builder routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from datetime import datetime, date
import json
import uuid

from sas_management.models import db, Proposal, Client, Event, UserRole
from sas_management.utils import role_required

proposals_bp = Blueprint("proposals", __name__, url_prefix="/proposals")

@proposals_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def new_proposal():
    """Create a new proposal - select client and event."""
    if request.method == "POST":
        client_id = request.form.get("client_id")
        event_id = request.form.get("event_id") or None
        
        if not client_id:
            flash("Please select a client.", "danger")
            return redirect(url_for("proposals.new_proposal"))
        
        # Generate unique proposal number
        max_attempts = 10
        for attempt in range(max_attempts):
            proposal_number = f"PROP-{date.today().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            existing = Proposal.query.filter_by(proposal_number=proposal_number).first()
            if not existing:
                break
        else:
            # Fallback if all attempts failed (very unlikely)
            proposal_number = f"PROP-{date.today().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
        
        # Create new proposal
        proposal = Proposal(
            client_id=int(client_id),
            event_id=int(event_id) if event_id else None,
            proposal_number=proposal_number,
            content=json.dumps({"blocks": []}),
            total_value=0.00,
            status="Draft"
        )
        db.session.add(proposal)
        db.session.commit()
        
        flash("Proposal created successfully. You can now build your proposal.", "success")
        return redirect(url_for("proposals.builder", proposal_id=proposal.id))
    
    # GET request - show form
    clients = Client.query.filter_by(is_archived=False).order_by(Client.name.asc()).all()
    events = Event.query.order_by(Event.event_date.desc()).limit(50).all()
    return render_template("proposals/new.html", clients=clients, events=events)

@proposals_bp.route("/builder/<int:proposal_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def builder(proposal_id):
    """Proposal builder interface."""
    proposal = Proposal.query.get_or_404(proposal_id)
    client = proposal.client
    event = proposal.event
    
    # Parse existing content
    try:
        content_data = json.loads(proposal.content) if proposal.content else {"blocks": []}
    except:
        content_data = {"blocks": []}
    
    return render_template("proposals/builder.html", proposal=proposal, client=client, event=event, blocks=content_data.get("blocks", []))

@proposals_bp.route("/save", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def save():
    """Save proposal."""
    try:
        data = request.get_json()
        proposal_id = data.get('proposal_id')
        
        if not proposal_id:
            return jsonify({'success': False, 'error': 'Proposal ID required'}), 400
        
        proposal = Proposal.query.get_or_404(proposal_id)
        
        # Calculate total from blocks
        blocks = data.get('blocks', [])
        total_value = 0.0
        for block in blocks:
            if block.get('type') == 'pricing':
                total_value += float(block.get('price', 0))
        
        # Update proposal
        proposal.content = json.dumps({"blocks": blocks})
        proposal.total_value = total_value
        proposal.status = data.get('status', proposal.status)
        
        db.session.commit()
        return jsonify({'success': True, 'id': proposal.id, 'total_value': float(total_value)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@proposals_bp.route("/list")
@proposals_bp.route("")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def proposal_list():
    """List all proposals."""
    proposals = Proposal.query.order_by(Proposal.created_at.desc()).limit(50).all()
    return render_template("proposals/proposal_list.html", proposals=proposals)

@proposals_bp.route("/generate-pdf/<int:proposal_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def generate_pdf(proposal_id):
    """Generate PDF for proposal."""
    proposal = Proposal.query.get_or_404(proposal_id)
    
    # TODO: Implement PDF generation with ReportLab
    # For now, return JSON
    return jsonify({'success': False, 'error': 'PDF generation not yet implemented'})

