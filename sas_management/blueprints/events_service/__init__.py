from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from sas_management.models import db
from sas_management.blueprints.events_service.models import Service, ServiceItem, ServiceTask
from sas_management.blueprints.events_service.forms import ServiceForm, ServiceItemForm, ServiceTaskForm
from flask_login import login_required, current_user

bp = Blueprint('events_service', __name__, url_prefix='/events-service', template_folder='../../templates/events_service', static_folder='static')

@bp.route('/')
@login_required
def index():
    return redirect(url_for('events_service.dashboard'))

@bp.route('/dashboard')
@login_required
def dashboard():
    """Event Service dashboard with overview statistics."""
    try:
        services = Service.query.order_by(Service.created_at.desc()).all()
        total_services = Service.query.count()
        total_items = ServiceItem.query.count()
        total_tasks = ServiceTask.query.count()
        pending_tasks = ServiceTask.query.filter_by(status='Pending').count()
        
        # Recent services
        recent_services = Service.query.order_by(Service.created_at.desc()).limit(10).all()
        
        return render_template(
            'events_service/list.html',
            services=services,
            total_services=total_services,
            total_items=total_items,
            total_tasks=total_tasks,
            pending_tasks=pending_tasks,
            recent_services=recent_services
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading events service dashboard: {e}")
        flash("Error loading dashboard. Please try again.", "danger")
        return render_template(
            'events_service/list.html',
            services=[],
            total_services=0,
            total_items=0,
            total_tasks=0,
            pending_tasks=0,
            recent_services=[]
        )

@bp.route('/service/add', methods=['GET','POST'])
@login_required
def service_add():
    """Add a new event service."""
    try:
        if request.method == 'POST':
            # Get form data
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip() or None
            price_str = request.form.get('price', '0')
            
            # Validate required fields
            if not title:
                flash('Service title is required.', 'danger')
                return render_template('events_service/service_form.html', action='Add', service=None)
            
            # Parse price
            try:
                price = float(price_str) if price_str else 0.0
                if price < 0:
                    price = 0.0
            except (ValueError, TypeError):
                price = 0.0
            
            # Check for duplicate title
            existing = Service.query.filter_by(title=title).first()
            if existing:
                flash('A service with this title already exists.', 'danger')
                return render_template('events_service/service_form.html', action='Add', service=None)
            
            try:
                # Create service
                s = Service(
                    title=title,
                    description=description,
                    price=price,
                    created_by=current_user.id
                )
                db.session.add(s)
                db.session.commit()
                flash('Service added successfully.', 'success')
                return redirect(url_for('events_service.dashboard'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error creating service: {e}")
                flash(f'Error creating service: {str(e)}', 'danger')
        
        # GET request - show form
        return render_template('events_service/service_form.html', action='Add', service=None)
    except Exception as e:
        current_app.logger.exception(f"Error in service_add route: {e}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return render_template('events_service/service_form.html', action='Add', service=None)

@bp.route('/service/<int:service_id>/edit', methods=['GET','POST'])
@login_required
def service_edit(service_id):
    """Edit an existing event service."""
    try:
        s = Service.query.get_or_404(service_id)
        
        if request.method == 'POST':
            # Get form data
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip() or None
            price_str = request.form.get('price', '0')
            
            # Validate required fields
            if not title:
                flash('Service title is required.', 'danger')
                return render_template('events_service/service_form.html', action='Edit', service=s)
            
            # Parse price
            try:
                price = float(price_str) if price_str else s.price
                if price < 0:
                    price = 0.0
            except (ValueError, TypeError):
                price = s.price
            
            # Check for duplicate title (excluding current service)
            existing = Service.query.filter_by(title=title).filter(Service.id != service_id).first()
            if existing:
                flash('A service with this title already exists.', 'danger')
                return render_template('events_service/service_form.html', action='Edit', service=s)
            
            try:
                # Update service
                s.title = title
                s.description = description
                s.price = price
                db.session.commit()
                flash('Service updated successfully.', 'success')
                return redirect(url_for('events_service.dashboard'))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error updating service: {e}")
                flash(f'Error updating service: {str(e)}', 'danger')
        
        # GET request - show form with existing data
        return render_template('events_service/service_form.html', action='Edit', service=s)
    except Exception as e:
        current_app.logger.exception(f"Error in service_edit route: {e}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('events_service.dashboard'))

@bp.route('/service/<int:service_id>/delete', methods=['POST'])
@login_required
def service_delete(service_id):
    """Delete an event service."""
    try:
        s = Service.query.get_or_404(service_id)
        db.session.delete(s)
        db.session.commit()
        flash('Service removed successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error deleting service: {e}")
        flash(f'Error removing service: {str(e)}', 'danger')
    return redirect(url_for('events_service.dashboard'))

# API endpoints for cursor/automation
@bp.route('/api/services')
@login_required
def api_services():
    services = Service.query.all()
    return jsonify([s.to_dict() for s in services])

@bp.route('/api/service/<int:service_id>')
@login_required
def api_service(service_id):
    s = Service.query.get_or_404(service_id)
    return jsonify(s.to_dict())

