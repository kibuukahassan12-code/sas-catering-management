"""CRM Blueprint - Enhanced Client Management, Sales Pipeline, and Communication Center."""
from datetime import datetime, date
import os

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from sas_management.models import (
    Client, ClientNote, ClientDocument, ClientActivity, ClientCommunication,
    Event, IncomingLead, Invoice, Task, User, UserRole, db
)
from sas_management.utils import role_required, permission_required

crm_bp = Blueprint("crm", __name__, url_prefix="/crm")


@crm_bp.route("/pipeline/seed", methods=["POST"])
@login_required
# @permission_required("crm")
def seed_pipeline_data():
    """Seed professional sample leads data for the pipeline."""
    try:
        from datetime import timedelta
        
        # Check if leads already exist
        existing_count = IncomingLead.query.count()
        if existing_count > 0:
            # Option to clear existing leads
            clear_existing = request.form.get("clear_existing", "false").lower() == "true"
            if not clear_existing:
                flash(f"Pipeline already has {existing_count} leads. Use 'Clear & Seed' to replace with sample data.", "info")
                return redirect(url_for("crm.pipeline"))
            else:
                # Clear existing leads
                IncomingLead.query.delete()
                db.session.commit()
                flash("Existing leads cleared.", "info")
        
        # Get users for assignment
        users = User.query.filter(User.role.in_([UserRole.Admin, UserRole.SalesManager])).all()
        user_ids = [u.id for u in users] if users else [None]
        
        # Professional sample leads data with realistic scenarios
        sample_leads = [
            {
                "client_name": "Sarah Nakato",
                "email": "sarah.nakato@email.com",
                "phone": "+256 700 123 456",
                "inquiry_type": "Wedding",
                "message": "Looking for catering services for my wedding in March. Need full service for 200 guests.",
                "pipeline_stage": "New Lead",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=2)
            },
            {
                "client_name": "John Mukasa",
                "email": "john.mukasa@email.com",
                "phone": "+256 701 234 567",
                "inquiry_type": "Corporate Event",
                "message": "Corporate team building event for 50 people. Need catering and venue setup.",
                "pipeline_stage": "New Lead",
                "assigned_user_id": None,
                "timestamp": datetime.utcnow() - timedelta(days=1)
            },
            {
                "client_name": "Grace Achieng",
                "email": "grace.achieng@email.com",
                "phone": "+256 702 345 678",
                "inquiry_type": "Birthday Party",
                "message": "Planning a 30th birthday party. Need catering for 80 guests with special dietary requirements.",
                "pipeline_stage": "New Lead",
                "assigned_user_id": None,
                "timestamp": datetime.utcnow() - timedelta(hours=5)
            },
            {
                "client_name": "Michael Ochieng",
                "email": "michael.ochieng@email.com",
                "phone": "+256 703 456 789",
                "inquiry_type": "Conference",
                "message": "Annual company conference. Need full catering service for 300 attendees over 2 days.",
                "pipeline_stage": "Qualified",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=5)
            },
            {
                "client_name": "Patience Namukasa",
                "email": "patience.namukasa@email.com",
                "phone": "+256 704 567 890",
                "inquiry_type": "Graduation Party",
                "message": "Graduation celebration for 150 guests. Looking for buffet service and dessert table.",
                "pipeline_stage": "Qualified",
                "assigned_user_id": user_ids[-1] if len(user_ids) > 1 else user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=4)
            },
            {
                "client_name": "David Kato",
                "email": "david.kato@email.com",
                "phone": "+256 705 678 901",
                "inquiry_type": "Wedding",
                "message": "Wedding reception for 250 guests. Full service including bar and dessert station.",
                "pipeline_stage": "Proposal Sent",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=7)
            },
            {
                "client_name": "Ruth Nakiyemba",
                "email": "ruth.nakiyemba@email.com",
                "phone": "+256 706 789 012",
                "inquiry_type": "Corporate Event",
                "message": "Product launch event. Need premium catering for 100 VIP guests.",
                "pipeline_stage": "Proposal Sent",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=6)
            },
            {
                "client_name": "James Ssemwogerere",
                "email": "james.ssemwogerere@email.com",
                "phone": "+256 707 890 123",
                "inquiry_type": "Wedding",
                "message": "Large wedding celebration for 400 guests. Negotiating package details and pricing.",
                "pipeline_stage": "Negotiation",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=10)
            },
            {
                "client_name": "Mary Nalubega",
                "email": "mary.nalubega@email.com",
                "phone": "+256 708 901 234",
                "inquiry_type": "Corporate Event",
                "message": "Annual gala dinner for 200 guests. Deposit payment pending.",
                "pipeline_stage": "Awaiting Payment",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=12)
            },
            {
                "client_name": "Peter Okello",
                "email": "peter.okello@email.com",
                "phone": "+256 709 012 345",
                "inquiry_type": "Conference",
                "message": "Tech conference catering for 500 attendees. Finalizing payment terms.",
                "pipeline_stage": "Awaiting Payment",
                "assigned_user_id": user_ids[-1] if len(user_ids) > 1 else user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=11)
            },
            {
                "client_name": "Esther Nakawunde",
                "email": "esther.nakawunde@email.com",
                "phone": "+256 710 123 456",
                "inquiry_type": "Wedding",
                "message": "Wedding reception confirmed. Full service package for 180 guests.",
                "pipeline_stage": "Confirmed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=15)
            },
            {
                "client_name": "Robert Mutebi",
                "email": "robert.mutebi@email.com",
                "phone": "+256 711 234 567",
                "inquiry_type": "Corporate Event",
                "message": "Company anniversary celebration. Event confirmed and scheduled.",
                "pipeline_stage": "Confirmed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=14)
            },
            {
                "client_name": "Florence Nalubowa",
                "email": "florence.nalubowa@email.com",
                "phone": "+256 712 345 678",
                "inquiry_type": "Wedding",
                "message": "Successfully completed wedding reception. Excellent service!",
                "pipeline_stage": "Completed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=30)
            },
            {
                "client_name": "Andrew Kigozi",
                "email": "andrew.kigozi@email.com",
                "phone": "+256 713 456 789",
                "inquiry_type": "Corporate Event",
                "message": "Corporate event completed successfully. Client very satisfied.",
                "pipeline_stage": "Completed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=25)
            },
            {
                "client_name": "Betty Namukasa",
                "email": "betty.namukasa@email.com",
                "phone": "+256 714 567 890",
                "inquiry_type": "Birthday Party",
                "message": "Client chose another vendor due to budget constraints. Follow-up scheduled for future events.",
                "pipeline_stage": "Lost",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=20)
            },
            # Additional professional leads
            {
                "client_name": "Charles Ouma",
                "email": "charles.ouma@email.com",
                "phone": "+256 715 678 901",
                "inquiry_type": "Corporate Event",
                "message": "Company anniversary celebration confirmed. Premium package selected. All payments received.",
                "pipeline_stage": "Confirmed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=12)
            },
            {
                "client_name": "Dorothy Akello",
                "email": "dorothy.akello@email.com",
                "phone": "+256 716 789 012",
                "inquiry_type": "Birthday Party",
                "message": "50th birthday celebration confirmed. Special dietary requirements accommodated.",
                "pipeline_stage": "Confirmed",
                "assigned_user_id": user_ids[-1] if len(user_ids) > 1 else user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=14)
            },
            {
                "client_name": "Francis Lubega",
                "email": "francis.lubega@email.com",
                "phone": "+256 717 890 123",
                "inquiry_type": "Wedding",
                "message": "Successfully completed wedding reception. Excellent service! Client very satisfied.",
                "pipeline_stage": "Completed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=30)
            },
            {
                "client_name": "Hellen Nalubega",
                "email": "hellen.nalubega@email.com",
                "phone": "+256 718 901 234",
                "inquiry_type": "Corporate Event",
                "message": "Corporate event completed successfully. Client very satisfied. Excellent feedback.",
                "pipeline_stage": "Completed",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=25)
            },
            {
                "client_name": "Ivan Ssebunya",
                "email": "ivan.ssebunya@email.com",
                "phone": "+256 719 012 345",
                "inquiry_type": "Conference",
                "message": "Tech conference completed. All attendees satisfied. Client requesting quote for next year.",
                "pipeline_stage": "Completed",
                "assigned_user_id": user_ids[-1] if len(user_ids) > 1 else user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=20)
            },
            {
                "client_name": "Jennifer Nakato",
                "email": "jennifer.nakato@email.com",
                "phone": "+256 720 123 456",
                "inquiry_type": "Birthday Party",
                "message": "Client chose another vendor due to budget constraints. Follow-up scheduled.",
                "pipeline_stage": "Lost",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=18)
            },
            {
                "client_name": "Kenneth Mubiru",
                "email": "kenneth.mubiru@email.com",
                "phone": "+256 721 234 567",
                "inquiry_type": "Wedding",
                "message": "Client postponed event indefinitely. Maintaining relationship for future opportunities.",
                "pipeline_stage": "Lost",
                "assigned_user_id": user_ids[0] if user_ids else None,
                "timestamp": datetime.utcnow() - timedelta(days=22)
            }
        ]
        
        # Create leads - model uses 'email' field
        created_count = 0
        for lead_data in sample_leads:
            # The model uses 'email' field, so ensure it's set correctly
            lead_dict = {
                'client_name': lead_data.get('client_name', ''),
                'email': lead_data.get('email', lead_data.get('client_email', '')),
                'phone': lead_data.get('phone', ''),
                'inquiry_type': lead_data.get('inquiry_type', ''),
                'message': lead_data.get('message', ''),
                'pipeline_stage': lead_data.get('pipeline_stage', 'New Lead'),
                'assigned_user_id': lead_data.get('assigned_user_id'),
                'timestamp': lead_data.get('timestamp', datetime.utcnow())
            }
            
            lead = IncomingLead(**lead_dict)
            db.session.add(lead)
            created_count += 1
        
        db.session.commit()
        flash(f"✅ Successfully created {created_count} professional sample leads across all pipeline stages! The pipeline is now ready to use.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error seeding pipeline data: {e}")
        flash(f"Error creating sample data: {str(e)}", "danger")
    
    return redirect(url_for("crm.pipeline"))


@crm_bp.route("/pipeline")
@login_required
# @permission_required("crm")
def pipeline():
    """Sales Pipeline Kanban Board."""
    try:
        from sqlalchemy.orm import joinedload
        from decimal import Decimal
        
        stages = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Awaiting Payment", "Confirmed", "Completed", "Lost"]
        
        # Eager load assigned_user relationship to avoid N+1 queries
        leads_by_stage = {}
        for stage in stages:
            try:
                leads_by_stage[stage] = (
                    IncomingLead.query
                    .options(joinedload(IncomingLead.assigned_user))
                    .filter_by(pipeline_stage=stage)
                    .order_by(IncomingLead.timestamp.desc())
                    .all()
                )
            except Exception as e:
                current_app.logger.error(f"Error loading leads for stage {stage}: {e}")
                leads_by_stage[stage] = []
        
        # Get all users for assignment dropdown
        try:
            users = User.query.filter(User.role.in_([UserRole.Admin, UserRole.SalesManager])).all()
        except Exception as e:
            current_app.logger.error(f"Error loading users: {e}")
            users = []
        
        # Calculate pipeline statistics
        try:
            total_leads = IncomingLead.query.count()
        except Exception as e:
            current_app.logger.error(f"Error counting leads: {e}")
            total_leads = 0
        
        # Calculate pipeline value from converted events
        total_value = Decimal('0.00')
        try:
            from sqlalchemy import func
            result = (
                db.session.query(func.coalesce(func.sum(Event.quoted_value), 0))
                .join(IncomingLead, IncomingLead.converted_event_id == Event.id)
                .filter(IncomingLead.pipeline_stage.in_(["Qualified", "Proposal Sent", "Negotiation", "Awaiting Payment", "Confirmed"]))
                .scalar()
            )
            if result:
                total_value = Decimal(str(result))
        except Exception as e:
            current_app.logger.warning(f"Error calculating pipeline value: {e}")
            total_value = Decimal('0.00')
        
        # Ensure all variables are properly initialized and serializable
        return render_template(
            "crm/pipeline.html",
            stages=stages,
            leads_by_stage=leads_by_stage,
            users=users,
            total_leads=int(total_leads),
            total_value=float(total_value)
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading pipeline: {e}")
        flash(f"Error loading sales pipeline: {str(e)}", "danger")
        # Return a safe fallback
        return render_template(
            "crm/pipeline.html",
            stages=["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Awaiting Payment", "Confirmed", "Completed", "Lost"],
            leads_by_stage={},
            users=[],
            total_leads=0,
            total_value=0.0
        )


@crm_bp.route("/api/pipeline/update/<int:lead_id>", methods=["POST"])
@login_required
# @permission_required("crm")
def api_update_pipeline_stage(lead_id):
    """API endpoint to update lead pipeline stage."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        lead = IncomingLead.query.get_or_404(lead_id)
        new_stage = data.get("stage", "")
        
        # Validate stage
        valid_stages = ["New Lead", "Qualified", "Proposal Sent", "Negotiation", "Awaiting Payment", "Confirmed", "Completed", "Lost"]
        if new_stage and new_stage in valid_stages:
            old_stage = lead.pipeline_stage
            lead.pipeline_stage = new_stage
            lead.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": f"Lead moved from {old_stage} to {new_stage}",
                "lead_id": lead_id,
                "new_stage": new_stage
            })
        
        return jsonify({"status": "error", "message": "Invalid stage"}), 400
    except Exception as e:
        current_app.logger.exception(f"Error updating pipeline stage: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@crm_bp.route("/api/pipeline/assign/<int:lead_id>", methods=["POST"])
@login_required
# @permission_required("crm")
def api_assign_lead(lead_id):
    """API endpoint to assign lead to a user."""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        lead = IncomingLead.query.get_or_404(lead_id)
        user_id = data.get("user_id")
        
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                lead.assigned_user_id = user_id
                lead.updated_at = datetime.utcnow()
                db.session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": f"Lead assigned to {user.email}",
                    "lead_id": lead_id,
                    "user_id": user_id
                })
            else:
                return jsonify({"status": "error", "message": "User not found"}), 404
        else:
            # Unassign lead
            lead.assigned_user_id = None
            lead.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Lead unassigned",
                "lead_id": lead_id,
                "user_id": None
            })
    except Exception as e:
        current_app.logger.exception(f"Error assigning lead: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@crm_bp.route("/clients/<int:client_id>")
@login_required
# @permission_required("crm")
def client_profile(client_id):
    """Comprehensive Client Profile View."""
    try:
        client = Client.query.get_or_404(client_id)
        
        # Get all related data with safe error handling
        events = []
        invoices = []
        tasks = []
        
        try:
            events = Event.query.filter_by(client_id=client_id).order_by(Event.event_date.desc()).all()
        except Exception as e:
            current_app.logger.warning(f"Error fetching events for client {client_id}: {e}")
        
        try:
            # Get invoices through events - safer approach
            event_ids = [e.id for e in events] if events else []
            if event_ids:
                invoices = Invoice.query.filter(Invoice.event_id.in_(event_ids)).order_by(Invoice.issue_date.desc()).all()
            else:
                # Try direct relationship if invoice has client_id
                if hasattr(Invoice, 'client_id'):
                    invoices = Invoice.query.filter_by(client_id=client_id).order_by(Invoice.issue_date.desc()).all()
        except Exception as e:
            current_app.logger.warning(f"Error fetching invoices for client {client_id}: {e}")
        
        try:
            # Get tasks through events
            event_ids = [e.id for e in events] if events else []
            if event_ids:
                tasks = Task.query.filter(Task.event_id.in_(event_ids)).order_by(Task.due_date.desc()).all()
            else:
                tasks = []
        except Exception as e:
            current_app.logger.warning(f"Error fetching tasks for client {client_id}: {e}")
            tasks = []
        
        # Calculate open tasks count (not Complete)
        try:
            from sas_management.models import TaskStatus
            open_tasks_count = sum(1 for t in tasks if hasattr(t, 'status') and t.status != TaskStatus.Complete)
        except Exception:
            open_tasks_count = 0
        
        # Get users for assignment
        users = User.query.filter(User.role.in_([UserRole.Admin, UserRole.SalesManager])).all()
        
        # Get notes, documents, communications, and activities with safe handling
        notes = []
        documents = []
        communications = []
        activities = []
        
        try:
            notes = client.notes if hasattr(client, 'notes') else []
        except Exception as e:
            current_app.logger.warning(f"Error fetching notes: {e}")
        
        try:
            documents = client.documents if hasattr(client, 'documents') else []
        except Exception as e:
            current_app.logger.warning(f"Error fetching documents: {e}")
        
        try:
            communications = client.communications if hasattr(client, 'communications') else []
        except Exception as e:
            current_app.logger.warning(f"Error fetching communications: {e}")
        
        try:
            activities = client.activities if hasattr(client, 'activities') else []
        except Exception as e:
            current_app.logger.warning(f"Error fetching activities: {e}")
        
        return render_template(
            "crm/client_profile.html",
            client=client,
            events=events,
            invoices=invoices,
            tasks=tasks,
            open_tasks_count=open_tasks_count,
            users=users,
            notes=notes,
            documents=documents,
            communications=communications,
            activities=activities
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading client profile {client_id}: {e}")
        flash(f"Error loading client profile: {str(e)}", "danger")
        return redirect(url_for("core.clients_list"))


@crm_bp.route("/clients/<int:client_id>/notes", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def add_client_note(client_id):
    """Add a note to a client."""
    client = Client.query.get_or_404(client_id)
    content = request.form.get("content", "").strip()
    
    if not content:
        flash("Note content cannot be empty.", "warning")
        return redirect(url_for("crm.client_profile", client_id=client_id))
    
    note = ClientNote(
        client_id=client_id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(note)
    
    # Create activity log
    activity = ClientActivity(
        client_id=client_id,
        user_id=current_user.id,
        activity_type="Note Added",
        description=f"Added note: {content[:50]}..."
    )
    db.session.add(activity)
    
    db.session.commit()
    flash("Note added successfully.", "success")
    return redirect(url_for("crm.client_profile", client_id=client_id))


@crm_bp.route("/clients/<int:client_id>/notes/<int:note_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def delete_client_note(client_id, note_id):
    """Delete a client note."""
    note = ClientNote.query.get_or_404(note_id)
    if note.client_id != client_id:
        flash("Invalid note.", "danger")
        return redirect(url_for("crm.client_profile", client_id=client_id))
    
    db.session.delete(note)
    db.session.commit()
    flash("Note deleted.", "info")
    return redirect(url_for("crm.client_profile", client_id=client_id))


@crm_bp.route("/clients/<int:client_id>/documents", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def upload_client_document(client_id):
    """Upload a document for a client."""
    client = Client.query.get_or_404(client_id)
    
    if 'file' not in request.files:
        flash("No file provided.", "warning")
        return redirect(url_for("crm.client_profile", client_id=client_id))
    
    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "warning")
        return redirect(url_for("crm.client_profile", client_id=client_id))
    
    if file and file.filename and '.' in file.filename:
        filename = secure_filename(file.filename)
        # Create unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{client_id}_{timestamp}_{filename}"
        
        # Ensure upload directory exists
        upload_folder = os.path.join(current_app.instance_path, "..", current_app.config.get("UPLOAD_FOLDER", "files"))
        upload_folder = os.path.abspath(upload_folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Store relative path
        relative_path = os.path.join(current_app.config.get("UPLOAD_FOLDER", "files"), unique_filename)
        
        document = ClientDocument(
            client_id=client_id,
            user_id=current_user.id,
            title=request.form.get("title", filename),
            file_path=relative_path,
            file_size=os.path.getsize(file_path),
            file_type=filename.rsplit('.', 1)[1].lower() if '.' in filename else None
        )
        db.session.add(document)
        
        # Create activity log
        activity = ClientActivity(
            client_id=client_id,
            user_id=current_user.id,
            activity_type="Document Uploaded",
            description=f"Uploaded document: {document.title}"
        )
        db.session.add(activity)
        
        db.session.commit()
        flash("Document uploaded successfully.", "success")
    else:
        flash("Invalid file type.", "danger")
    
    return redirect(url_for("crm.client_profile", client_id=client_id))


@crm_bp.route("/clients/<int:client_id>/documents/<int:doc_id>/download")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def download_client_document(client_id, doc_id):
    """Download a client document."""
    document = ClientDocument.query.get_or_404(doc_id)
    if document.client_id != client_id:
        flash("Invalid document.", "danger")
        return redirect(url_for("crm.client_profile", client_id=client_id))
    
    file_dir = os.path.join(current_app.instance_path, "..", current_app.config.get("UPLOAD_FOLDER", "files"))
    file_dir = os.path.abspath(file_dir)
    filename = os.path.basename(document.file_path)
    
    return send_from_directory(file_dir, filename, as_attachment=True)


@crm_bp.route("/clients/<int:client_id>/documents/<int:doc_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def delete_client_document(client_id, doc_id):
    """Delete a client document."""
    document = ClientDocument.query.get_or_404(doc_id)
    if document.client_id != client_id:
        flash("Invalid document.", "danger")
        return redirect(url_for("crm.client_profile", client_id=client_id))
    
    # Delete physical file
    file_path = os.path.join(current_app.instance_path, "..", document.file_path)
    file_path = os.path.abspath(file_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    
    db.session.delete(document)
    db.session.commit()
    flash("Document deleted.", "info")
    return redirect(url_for("crm.client_profile", client_id=client_id))


@crm_bp.route("/clients/<int:client_id>/tags", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def update_client_tags(client_id):
    """Update client tags."""
    client = Client.query.get_or_404(client_id)
    tags = request.form.get("tags", "").strip()
    
    old_tags = client.tags
    client.tags = tags
    client.updated_at = datetime.utcnow()
    
    # Create activity log
    activity = ClientActivity(
        client_id=client_id,
        user_id=current_user.id,
        activity_type="Tags Updated",
        description=f"Tags changed from '{old_tags}' to '{tags}'"
    )
    db.session.add(activity)
    
    db.session.commit()
    flash("Tags updated successfully.", "success")
    return redirect(url_for("crm.client_profile", client_id=client_id))


@crm_bp.route("/clients/<int:client_id>/communication", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def add_client_communication(client_id):
    """Add a communication record to client timeline."""
    client = Client.query.get_or_404(client_id)
    
    communication = ClientCommunication(
        client_id=client_id,
        user_id=current_user.id,
        communication_type=request.form.get("communication_type", "Email"),
        subject=request.form.get("subject", "").strip(),
        content=request.form.get("content", "").strip(),
        direction=request.form.get("direction", "Outbound"),
        event_id=request.form.get("event_id", type=int) or None
    )
    db.session.add(communication)
    
    # Create activity log
    activity = ClientActivity(
        client_id=client_id,
        user_id=current_user.id,
        activity_type="Communication Recorded",
        description=f"{communication.communication_type} communication: {communication.subject or 'No subject'}"
    )
    db.session.add(activity)
    
    db.session.commit()
    flash("Communication recorded successfully.", "success")
    return redirect(url_for("crm.client_profile", client_id=client_id))


@crm_bp.route("/clients/<int:client_id>/archive", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def archive_client(client_id):
    """Archive or unarchive a client."""
    client = Client.query.get_or_404(client_id)
    action = request.form.get("action", "archive")
    
    client.is_archived = (action == "archive")
    client.updated_at = datetime.utcnow()
    
    # Create activity log
    activity = ClientActivity(
        client_id=client_id,
        user_id=current_user.id,
        activity_type="Archived" if client.is_archived else "Unarchived",
        description=f"Client {action}d"
    )
    db.session.add(activity)
    
    db.session.commit()
    flash(f"Client {action}d successfully.", "success")
    if action == "unarchive":
        return redirect(url_for("crm.client_profile", client_id=client_id))
    return redirect(url_for("core.clients_list"))


@crm_bp.route("/leads/<int:lead_id>/convert", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def convert_lead(lead_id):
    """Convert a lead to a client and optionally an event."""
    lead = IncomingLead.query.get_or_404(lead_id)
    
    if request.method == "POST":
        try:
            # Get email from lead (model uses 'email' field)
            lead_email = lead.email or ''
            
            # Check if client already exists with this email
            existing_client = None
            if lead_email:
                existing_client = Client.query.filter_by(email=lead_email).first()
            
            if existing_client:
                client = existing_client
                flash("Client with this email already exists. Using existing client record.", "info")
            else:
                # Create new client
                client = Client(
                    name=lead.client_name,
                    contact_person=lead.client_name,
                    phone=lead.phone or "N/A",
                    email=lead_email,
                    tags="Converted Lead"
                )
                db.session.add(client)
                db.session.flush()
                
                # Create activity
                activity = ClientActivity(
                    client_id=client.id,
                    user_id=current_user.id,
                    activity_type="Created",
                    description=f"Client created from lead #{lead_id}"
                )
                db.session.add(activity)
            
            # Create event if requested
            event = None
            if request.form.get("create_event") == "yes":
                event_name = request.form.get("event_name", "").strip()
                event_date_str = request.form.get("event_date", "")
                guest_count = request.form.get("guest_count", "0")
                
                if not event_name:
                    flash("Event name is required when creating an event.", "warning")
                    return render_template("crm/convert_lead.html", lead=lead)
                
                try:
                    if event_date_str:
                        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
                    else:
                        event_date = date.today()
                    
                    event = Event(
                        client_id=client.id,
                        event_name=event_name,
                        event_date=event_date,
                        guest_count=int(guest_count) if guest_count else 0,
                        status="Draft",
                        quoted_value=Decimal('0.00')
                    )
                    db.session.add(event)
                    db.session.flush()
                except ValueError as e:
                    flash(f"Invalid date format. Please use YYYY-MM-DD format.", "danger")
                    return render_template("crm/convert_lead.html", lead=lead)
            
            # Update lead
            lead.pipeline_stage = "Completed"
            lead.converted_client_id = client.id
            if event:
                lead.converted_event_id = event.id
            lead.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            success_msg = f"Lead converted successfully! Client created: {client.name}."
            if event:
                success_msg += f" Event created: {event.event_name}."
            flash(success_msg, "success")
            
            if event:
                return redirect(url_for("core.events_edit", event_id=event.id))
            return redirect(url_for("crm.client_profile", client_id=client.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Error converting lead: {e}")
            flash(f"Error converting lead: {str(e)}", "danger")
            return render_template("crm/convert_lead.html", lead=lead)
    
    return render_template("crm/convert_lead.html", lead=lead)
