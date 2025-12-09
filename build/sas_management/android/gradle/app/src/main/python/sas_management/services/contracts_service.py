"""Contracts Service - Business logic for contract and legal document management."""
import os
import re
from datetime import datetime
from flask import current_app
from models import db, Contract, ContractTemplate, Event, Client
from decimal import Decimal


def get_pdf_folder():
    """Get the folder for PDF contracts."""
    pdf_folder = os.path.join(current_app.instance_path, 'premium_assets', 'contracts')
    os.makedirs(pdf_folder, exist_ok=True)
    return pdf_folder


# ============================
# CONTRACTS
# ============================

def create_contract(event_id, client_id, contract_body, created_by, template_id=None):
    """Create a new contract."""
    try:
        # Verify event and client exist
        event = Event.query.get(event_id)
        client = Client.query.get(client_id)
        
        if not event or not client:
            return {"success": False, "error": "Event or client not found"}
        
        contract = Contract(
            event_id=event_id,
            client_id=client_id,
            contract_body=contract_body,
            status="draft",
            created_by=created_by
        )
        
        db.session.add(contract)
        db.session.commit()
        db.session.refresh(contract)
        
        return {"success": True, "contract": contract}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating contract: {e}")
        return {"success": False, "error": str(e)}


def get_contract(contract_id):
    """Get a specific contract."""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return {"success": False, "error": "Contract not found"}
        return {"success": True, "contract": contract}
    except Exception as e:
        current_app.logger.exception(f"Error getting contract: {e}")
        return {"success": False, "error": str(e)}


def list_contracts(status=None, client_id=None, event_id=None):
    """List contracts with optional filters."""
    try:
        query = Contract.query
        if status:
            query = query.filter_by(status=status)
        if client_id:
            query = query.filter_by(client_id=client_id)
        if event_id:
            query = query.filter_by(event_id=event_id)
        
        contracts = query.order_by(Contract.created_at.desc()).all()
        return {"success": True, "contracts": contracts}
    except Exception as e:
        current_app.logger.exception(f"Error listing contracts: {e}")
        return {"success": False, "error": str(e), "contracts": []}


def update_contract(contract_id, contract_body=None, status=None):
    """Update a contract."""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return {"success": False, "error": "Contract not found"}
        
        if contract_body is not None:
            contract.contract_body = contract_body
        if status:
            contract.status = status
        
        contract.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "contract": contract}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating contract: {e}")
        return {"success": False, "error": str(e)}


def mark_as_signed(contract_id, signed_by=None):
    """Mark contract as signed."""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return {"success": False, "error": "Contract not found"}
        
        contract.status = "signed"
        contract.signed_at = datetime.utcnow()
        if signed_by:
            contract.signed_by = signed_by.strip()
        
        contract.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "contract": contract}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error marking contract as signed: {e}")
        return {"success": False, "error": str(e)}


# ============================
# CONTRACT TEMPLATES
# ============================

def load_contract_template(template_id):
    """Load a contract template."""
    try:
        template = ContractTemplate.query.get(template_id)
        if not template:
            return {"success": False, "error": "Template not found"}
        return {"success": True, "template": template}
    except Exception as e:
        current_app.logger.exception(f"Error loading template: {e}")
        return {"success": False, "error": str(e)}


def list_contract_templates():
    """List all contract templates."""
    try:
        templates = ContractTemplate.query.order_by(ContractTemplate.name.asc()).all()
        return {"success": True, "templates": templates}
    except Exception as e:
        current_app.logger.exception(f"Error listing templates: {e}")
        return {"success": False, "error": str(e), "templates": []}


def create_contract_template(name, body, description=None, is_default=False):
    """Create a contract template."""
    try:
        template = ContractTemplate(
            name=name.strip(),
            body=body,
            description=description.strip() if description else None,
            is_default=is_default
        )
        
        # If this is default, unset others
        if is_default:
            ContractTemplate.query.update({ContractTemplate.is_default: False})
        
        db.session.add(template)
        db.session.commit()
        db.session.refresh(template)
        
        return {"success": True, "template": template}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating template: {e}")
        return {"success": False, "error": str(e)}


# ============================
# TEMPLATE VARIABLE SUBSTITUTION
# ============================

def apply_template_variables(body, event_data=None, client_data=None):
    """Apply template variables to contract body."""
    try:
        result = body
        
        # Replace client variables
        if client_data:
            result = result.replace("{client_name}", client_data.get('name', 'N/A'))
            result = result.replace("{client_email}", client_data.get('email', 'N/A'))
            result = result.replace("{client_phone}", client_data.get('phone', 'N/A'))
        
        # Replace event variables
        if event_data:
            result = result.replace("{event_name}", event_data.get('event_name', 'N/A'))
            result = result.replace("{event_date}", str(event_data.get('event_date', 'N/A')))
            result = result.replace("{event_time}", str(event_data.get('event_time', 'N/A')))
            result = result.replace("{venue}", event_data.get('venue', 'N/A'))
            result = result.replace("{guest_count}", str(event_data.get('guest_count', 0)))
            result = result.replace("{quoted_value}", str(event_data.get('quoted_value', 0)))
        
        # Replace common placeholders
        result = result.replace("{package_name}", event_data.get('package_name', 'N/A') if event_data else 'N/A')
        result = result.replace("{today}", datetime.utcnow().strftime('%Y-%m-%d'))
        
        return {"success": True, "body": result}
    except Exception as e:
        current_app.logger.exception(f"Error applying template variables: {e}")
        return {"success": False, "error": str(e), "body": body}


# ============================
# PDF GENERATION
# ============================

def generate_contract_pdf(contract_id):
    """Generate PDF from contract (placeholder for ReportLab)."""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return {"success": False, "error": "Contract not found"}
        
        # TODO: Implement PDF generation using ReportLab
        # For now, return success with a message
        pdf_path = f"premium_assets/contracts/contract_{contract_id}.pdf"
        contract.pdf_path = pdf_path
        
        db.session.commit()
        
        return {
            "success": True,
            "message": "PDF generation will be implemented with ReportLab",
            "pdf_path": pdf_path,
            "contract_id": contract_id
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error generating contract PDF: {e}")
        return {"success": False, "error": str(e)}

