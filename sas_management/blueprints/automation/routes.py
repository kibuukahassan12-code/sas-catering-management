"""Experience Automation routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import json

from sas_management.models import db, Workflow, ActionLog, UserRole
from sas_management.utils import role_required

automation_bp = Blueprint("automation", __name__, url_prefix="/automation")

@automation_bp.route("/")
@login_required
@role_required(UserRole.Admin)
def dashboard():
    """Automation dashboard."""
    workflows = Workflow.query.all()
    recent_logs = ActionLog.query.order_by(ActionLog.run_at.desc()).limit(20).all()
    return render_template("automation/automation_dashboard.html", workflows=workflows, logs=recent_logs)

@automation_bp.route("/trigger-test", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def trigger_test():
    """Test workflow trigger."""
    try:
        workflow_id = request.json.get('workflow_id')
        workflow = Workflow.query.get_or_404(workflow_id)
        
        # Execute workflow
        from services.automation_service import execute_workflow
        result = execute_workflow(workflow.id, {'test': True})
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

