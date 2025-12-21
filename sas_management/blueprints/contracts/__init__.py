"""Contracts Blueprint - Contract and legal document management."""
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for, send_from_directory
from flask_login import current_user, login_required
from datetime import datetime

from sas_management.models import db, Contract, ContractTemplate, Event, Client, UserRole
from sas_management.utils import role_required
from sas_management.services.contracts_service import (
    create_contract, get_contract, list_contracts, mark_as_signed,
    load_contract_template, list_contract_templates, create_contract_template,
    apply_template_variables, generate_contract_pdf, get_pdf_folder
)

contracts_bp = Blueprint("contracts", __name__, url_prefix="/contracts")

@contracts_bp.route("/dashboard")
@login_required
def dashboard():
    """Contracts dashboard."""
    try:
        # Get statistics
        total_contracts = Contract.query.count()
        draft_contracts = Contract.query.filter_by(status='draft').count()
        signed_contracts = Contract.query.filter_by(status='signed').count()
        sent_contracts = Contract.query.filter_by(status='sent').count()
        
        # Get recent contracts
        recent_contracts = Contract.query.order_by(Contract.created_at.desc()).limit(10).all()
        
        # Get upcoming events without contracts
        from datetime import date
        upcoming_events = Event.query.filter(
            Event.event_date >= date.today(),
            Event.status.in_(['Confirmed', 'Awaiting Payment'])
        ).order_by(Event.event_date.asc()).limit(10).all()
        
        return render_template("contracts/contracts_dashboard.html",
            total_contracts=total_contracts,
            draft_contracts=draft_contracts,
            signed_contracts=signed_contracts,
            sent_contracts=sent_contracts,
            recent_contracts=recent_contracts,
            upcoming_events=upcoming_events
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading contracts dashboard: {e}")
        return render_template("contracts/contracts_dashboard.html",
            total_contracts=0, draft_contracts=0, signed_contracts=0, sent_contracts=0,
            recent_contracts=[], upcoming_events=[]
        )

@contracts_bp.route("/list")
@login_required
def contract_list():
    """List all contracts."""
    try:
        status_filter = request.args.get('status')
        client_filter = request.args.get('client_id', type=int)
        event_filter = request.args.get('event_id', type=int)
        
        result = list_contracts(status=status_filter, client_id=client_filter, event_id=event_filter)
        contracts = result.get('contracts', [])
        
        return render_template("contracts/contract_list.html",
            contracts=contracts,
            status_filter=status_filter,
            client_filter=client_filter,
            event_filter=event_filter
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading contract list: {e}")
        return render_template("contracts/contract_list.html",
            contracts=[], status_filter=None, client_filter=None, event_filter=None
        )

@contracts_bp.route("/view/<int:contract_id>")
@login_required
def contract_view(contract_id):
    """View a contract."""
    try:
        result = get_contract(contract_id)
        if not result['success']:
            flash(result.get('error', 'Contract not found'), "danger")
            return redirect(url_for("contracts.contract_list"))
        
        contract = result['contract']
        return render_template("contracts/contract_view.html", contract=contract)
    except Exception as e:
        current_app.logger.exception(f"Error viewing contract: {e}")
        return redirect(url_for("contracts.contract_list"))

@contracts_bp.route("/new/<int:event_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def contract_new(event_id):
    """Create a new contract for an event."""
    try:
        event = Event.query.get_or_404(event_id)
        client = Client.query.get_or_404(event.client_id)
        
        if request.method == "POST":
            contract_body = request.form.get('contract_body', '').strip()
            template_id = request.form.get('template_id', type=int)
            
            if template_id:
                # Load and apply template
                template_result = load_contract_template(template_id)
                if template_result['success']:
                    template = template_result['template']
                    # Prepare event and client data
                    event_data = {
                        'event_name': event.event_name,
                        'event_date': str(event.event_date) if event.event_date else 'N/A',
                        'event_time': str(event.event_time) if event.event_time else 'N/A',
                        'venue': event.venue or 'N/A',
                        'guest_count': event.guest_count or 0,
                        'quoted_value': float(event.quoted_value or 0)
                    }
                    client_data = {
                        'name': client.name,
                        'email': client.email or 'N/A',
                        'phone': client.phone or 'N/A'
                    }
                    # Apply variables
                    var_result = apply_template_variables(template.body, event_data, client_data)
                    if var_result['success']:
                        contract_body = var_result['body']
            
            if not contract_body:
                flash("Contract body is required.", "danger")
                return redirect(url_for("contracts.contract_new", event_id=event_id))
            
            result = create_contract(event_id, event.client_id, contract_body, current_user.id, template_id)
            
            if result['success']:
                flash("Contract created successfully!", "success")
                return redirect(url_for("contracts.contract_view", contract_id=result['contract'].id))
            else:
                flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        
        # Get templates
        templates_result = list_contract_templates()
        templates = templates_result.get('templates', [])
        
        # Get default template
        default_template = ContractTemplate.query.filter_by(is_default=True).first()
        
        return render_template("contracts/contract_editor.html",
            event=event,
            client=client,
            contract=None,
            templates=templates,
            default_template=default_template
        )
    except Exception as e:
        current_app.logger.exception(f"Error creating contract: {e}")
        return redirect(url_for("contracts.dashboard"))

@contracts_bp.route("/create", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def contract_create():
    """Create contract (API endpoint)."""
    try:
        event_id = request.form.get('event_id', type=int)
        client_id = request.form.get('client_id', type=int)
        contract_body = request.form.get('contract_body', '').strip()
        
        if not contract_body:
            return jsonify({"success": False, "error": "Contract body is required"}), 400
        
        result = create_contract(event_id, client_id, contract_body, current_user.id)
        
        if result['success']:
            return jsonify({"success": True, "contract_id": result['contract'].id})
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error creating contract: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@contracts_bp.route("/<int:contract_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def contract_edit(contract_id):
    """Edit a contract."""
    try:
        result = get_contract(contract_id)
        if not result['success']:
            flash(result.get('error', 'Contract not found'), "danger")
            return redirect(url_for("contracts.contract_list"))
        
        contract = result['contract']
        
        if request.method == "POST":
            contract_body = request.form.get('contract_body', '').strip()
            status = request.form.get('status')
            
            from sas_management.services.contracts_service import update_contract as update_contract_service
            result = update_contract_service(contract_id, contract_body, status)
            
            if result['success']:
                flash("Contract updated successfully!", "success")
                return redirect(url_for("contracts.contract_view", contract_id=contract_id))
            else:
                flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        
        return render_template("contracts/contract_editor.html",
            event=contract.event,
            client=contract.client,
            contract=contract,
            templates=[],
            default_template=None
        )
    except Exception as e:
        current_app.logger.exception(f"Error editing contract: {e}")
        return redirect(url_for("contracts.contract_list"))

@contracts_bp.route("/generate-pdf/<int:contract_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def generate_pdf(contract_id):
    """Generate PDF for contract."""
    try:
        result = generate_contract_pdf(contract_id)
        
        if result['success']:
            flash("PDF generation initiated. " + result.get('message', ''), "info")
        else:
            flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        
        return redirect(url_for("contracts.contract_view", contract_id=contract_id))
    except Exception as e:
        current_app.logger.exception(f"Error generating PDF: {e}")
        return redirect(url_for("contracts.contract_list"))

@contracts_bp.route("/mark-signed/<int:contract_id>", methods=["POST"])
@login_required
def mark_signed(contract_id):
    """Mark contract as signed."""
    try:
        signed_by = request.form.get('signed_by', '').strip()
        
        result = mark_as_signed(contract_id, signed_by if signed_by else None)
        
        if result['success']:
            flash("Contract marked as signed!", "success")
        else:
            flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        
        return redirect(url_for("contracts.contract_view", contract_id=contract_id))
    except Exception as e:
        current_app.logger.exception(f"Error marking contract as signed: {e}")
        return redirect(url_for("contracts.contract_list"))

@contracts_bp.route("/download/<int:contract_id>")
@login_required
def download_pdf(contract_id):
    """Download contract PDF."""
    try:
        result = get_contract(contract_id)
        if not result['success']:
            flash("Contract not found.", "danger")
            return redirect(url_for("contracts.contract_list"))
        
        contract = result['contract']
        
        if not contract.pdf_path:
            flash("PDF not generated yet. Please generate it first.", "warning")
            return redirect(url_for("contracts.contract_view", contract_id=contract_id))
        
        pdf_folder = get_pdf_folder()
        filename = contract.pdf_path.split('/')[-1]
        
        return send_from_directory(pdf_folder, filename, as_attachment=True)
    except Exception as e:
        current_app.logger.exception(f"Error downloading PDF: {e}")
        return redirect(url_for("contracts.contract_list"))

