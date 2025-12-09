# Quality Control Routes - This file contains routes to be added to production blueprint
# Imported at the end of __init__.py

from datetime import datetime, date
from decimal import Decimal
import json
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from models import (
    Event, UserRole, db,
    KitchenChecklist, DeliveryQCChecklist, FoodSafetyLog, HygieneReport
)

def add_quality_control_routes(production_bp, role_required_decorator, paginate_helper):
    """Add quality control routes to production blueprint."""
    
    # ============================
    # KITCHEN CHECKLIST
    # ============================
    
    @production_bp.route("/kitchen-checklist")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def kitchen_checklist_list():
        """List all kitchen checklists."""
        date_filter = request.args.get("date")
        status_filter = request.args.get("status")
        query = KitchenChecklist.query.order_by(KitchenChecklist.checklist_date.desc())
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                query = query.filter(KitchenChecklist.checklist_date == filter_date)
            except ValueError:
                pass
        
        if status_filter:
            query = query.filter(KitchenChecklist.status == status_filter)
        
        pagination = paginate_helper(query)
        # Pre-calculate item counts for each checklist
        for checklist in pagination.items:
            try:
                # Try JSON items first, then fall back to relationship items
                if hasattr(checklist, 'items') and checklist.items:
                    try:
                        items = json.loads(checklist.items) if isinstance(checklist.items, str) else checklist.items
                        checklist._item_count = len(items) if isinstance(items, list) else 0
                    except (json.JSONDecodeError, TypeError):
                        checklist._item_count = 0
                elif hasattr(checklist, 'checklist_items') and checklist.checklist_items:
                    checklist._item_count = len(checklist.checklist_items)
                else:
                    checklist._item_count = 0
            except Exception:
                checklist._item_count = 0
        return render_template("production/kitchen_checklist_list.html", checklists=pagination.items, pagination=pagination)
    
    @production_bp.route("/kitchen-checklist/new", methods=["GET", "POST"])
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def kitchen_checklist_new():
        """Create new kitchen checklist."""
        events = Event.query.filter(Event.status.in_(["Confirmed", "In Progress"])).order_by(Event.event_date.desc()).all()
        
        if request.method == "POST":
            try:
                checklist_date_str = request.form.get("checklist_date")
                checklist_date = datetime.strptime(checklist_date_str, "%Y-%m-%d").date() if checklist_date_str else date.today()
                event_id = request.form.get("event_id", type=int) or None
                status = request.form.get("status", "Pending")
                notes = request.form.get("notes", "").strip()
                title = request.form.get("title", "").strip() or None
                checklist_type = request.form.get("checklist_type", "").strip() or None
                
                # Get checklist items from form
                items = []
                item_names = request.form.getlist("item_name[]")
                item_statuses = request.form.getlist("item_status[]")
                item_notes = request.form.getlist("item_note[]")
                item_checked = request.form.getlist("item_checked[]")
                
                for idx, name in enumerate(item_names):
                    if name:
                        # If checkbox is checked, override status to "Checked"
                        item_status = "Checked" if idx < len(item_checked) and item_checked[idx] == "on" else (item_statuses[idx] if idx < len(item_statuses) else "Pending")
                        items.append({
                            "name": name,
                            "status": item_status or "Pending",
                            "note": item_notes[idx] if idx < len(item_notes) else ""
                        })
                
                checklist = KitchenChecklist(
                    checklist_date=checklist_date,
                    event_id=event_id,
                    title=title,
                    checklist_type=checklist_type,
                    checked_by=current_user.id,
                    created_by=current_user.id,
                    items=json.dumps(items),
                    status=status,
                    notes=notes
                )
                db.session.add(checklist)
                db.session.commit()
                flash("Kitchen checklist created successfully.", "success")
                return redirect(url_for("production.kitchen_checklist_list"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error creating kitchen checklist: {e}")
                flash(f"Error creating checklist: {str(e)}", "danger")
        
        # Default checklist items
        default_items = [
            "Equipment cleaned and sanitized",
            "Food storage temperatures checked",
            "Personal hygiene verified",
            "Handwashing stations functional",
            "Food prep surfaces sanitized",
            "Waste disposal checked",
            "Ingredient inventory verified",
            "Allergen information displayed"
        ]
        
        return render_template("production/kitchen_checklist_form.html", checklist=None, events=events, default_items=default_items)
    
    @production_bp.route("/kitchen-checklist/<int:checklist_id>")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def kitchen_checklist_view(checklist_id):
        """View kitchen checklist details."""
        checklist = KitchenChecklist.query.get_or_404(checklist_id)
        items = []
        try:
            # Try JSON items first
            if hasattr(checklist, 'items') and checklist.items:
                if isinstance(checklist.items, str):
                    items = json.loads(checklist.items)
                elif isinstance(checklist.items, list):
                    items = checklist.items
            # Fall back to relationship items
            elif hasattr(checklist, 'checklist_items') and checklist.checklist_items:
                items = [{"name": item.description, "status": "Checked" if item.is_completed else "Pending", "note": ""} 
                        for item in checklist.checklist_items]
        except (json.JSONDecodeError, TypeError, AttributeError) as e:
            current_app.logger.warning(f"Error loading checklist items: {e}")
            items = []
        return render_template("production/kitchen_checklist_view.html", checklist=checklist, items=items)
    
    # ============================
    # DELIVERY QC CHECKLIST
    # ============================
    
    @production_bp.route("/delivery-qc")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def delivery_qc_list():
        """List all delivery QC checklists."""
        date_filter = request.args.get("date")
        query = DeliveryQCChecklist.query.order_by(DeliveryQCChecklist.delivery_date.desc())
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                query = query.filter(DeliveryQCChecklist.delivery_date == filter_date)
            except ValueError:
                pass
        
        pagination = paginate_helper(query)
        return render_template("production/delivery_qc_list.html", checklists=pagination.items, pagination=pagination)
    
    @production_bp.route("/delivery-qc/new", methods=["GET", "POST"])
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def delivery_qc_new():
        """Create new delivery QC checklist."""
        events = Event.query.filter(Event.status.in_(["Confirmed", "In Progress"])).order_by(Event.event_date.desc()).all()
        
        if request.method == "POST":
            try:
                event_id = request.form.get("event_id", type=int)
                if not event_id:
                    flash("Event is required.", "danger")
                    return render_template("production/delivery_qc_form.html", checklist=None, events=events)
                
                delivery_date_str = request.form.get("delivery_date")
                delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date() if delivery_date_str else date.today()
                delivery_time_str = request.form.get("delivery_time")
                delivery_time = datetime.strptime(delivery_time_str, "%H:%M").time() if delivery_time_str else None
                
                checklist = DeliveryQCChecklist(
                    event_id=event_id,
                    delivery_date=delivery_date,
                    delivery_time=delivery_time,
                    checked_by=current_user.id,
                    temperature_check=request.form.get("temperature_check", "").strip(),
                    packaging_integrity=request.form.get("packaging_integrity", "Good"),
                    presentation=request.form.get("presentation", "Acceptable"),
                    quantity_verified=request.form.get("quantity_verified") == "on",
                    customer_satisfaction=request.form.get("customer_satisfaction", "").strip() or None,
                    issues=request.form.get("issues", "").strip() or None,
                    notes=request.form.get("notes", "").strip() or None
                )
                db.session.add(checklist)
                db.session.commit()
                flash("Delivery QC checklist created successfully.", "success")
                return redirect(url_for("production.delivery_qc_list"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error creating delivery QC checklist: {e}")
                flash(f"Error creating checklist: {str(e)}", "danger")
        
        return render_template("production/delivery_qc_form.html", checklist=None, events=events)
    
    @production_bp.route("/delivery-qc/<int:checklist_id>")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def delivery_qc_view(checklist_id):
        """View delivery QC checklist details."""
        checklist = DeliveryQCChecklist.query.get_or_404(checklist_id)
        return render_template("production/delivery_qc_view.html", checklist=checklist)
    
    # ============================
    # FOOD SAFETY LOGS
    # ============================
    
    @production_bp.route("/food-safety")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def food_safety_list():
        """List all food safety logs."""
        date_filter = request.args.get("date")
        category_filter = request.args.get("category")
        query = FoodSafetyLog.query.order_by(FoodSafetyLog.log_date.desc(), FoodSafetyLog.log_time.desc())
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                query = query.filter(FoodSafetyLog.log_date == filter_date)
            except ValueError:
                pass
        
        if category_filter:
            query = query.filter(FoodSafetyLog.category == category_filter)
        
        pagination = paginate_helper(query)
        categories = db.session.query(FoodSafetyLog.category).distinct().all()
        return render_template("production/food_safety_list.html", logs=pagination.items, pagination=pagination, categories=[c[0] for c in categories if c[0]])
    
    @production_bp.route("/food-safety/new", methods=["GET", "POST"])
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def food_safety_new():
        """Create new food safety log."""
        events = Event.query.filter(Event.status.in_(["Confirmed", "In Progress"])).order_by(Event.event_date.desc()).all()
        categories = ["Temperature", "Storage", "Handling", "Cleaning", "Training", "Pest Control", "Allergen", "Other"]
        
        if request.method == "POST":
            try:
                log_date_str = request.form.get("log_date")
                log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date() if log_date_str else date.today()
                log_time_str = request.form.get("log_time")
                log_time = datetime.strptime(log_time_str, "%H:%M").time() if log_time_str else None
                event_id = request.form.get("event_id", type=int) or None
                category = request.form.get("category", "").strip()
                item_description = request.form.get("item_description", "").strip()
                temperature_str = request.form.get("temperature")
                temperature = Decimal(temperature_str) if temperature_str else None
                action_taken = request.form.get("action_taken", "").strip() or None
                status = request.form.get("status", "Normal")
                notes = request.form.get("notes", "").strip() or None
                
                if not category or not item_description:
                    flash("Category and item description are required.", "danger")
                    return render_template("production/food_safety_form.html", log=None, events=events, categories=categories)
                
                log = FoodSafetyLog(
                    log_date=log_date,
                    log_time=log_time,
                    event_id=event_id,
                    logged_by=current_user.id,
                    category=category,
                    item_description=item_description,
                    temperature=temperature,
                    action_taken=action_taken,
                    status=status,
                    notes=notes
                )
                db.session.add(log)
                db.session.commit()
                flash("Food safety log created successfully.", "success")
                return redirect(url_for("production.food_safety_list"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error creating food safety log: {e}")
                flash(f"Error creating log: {str(e)}", "danger")
        
        return render_template("production/food_safety_form.html", log=None, events=events, categories=categories)
    
    @production_bp.route("/food-safety/<int:log_id>")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def food_safety_view(log_id):
        """View food safety log details."""
        log = FoodSafetyLog.query.get_or_404(log_id)
        return render_template("production/food_safety_view.html", log=log)
    
    # ============================
    # HYGIENE REPORTS
    # ============================
    
    @production_bp.route("/hygiene-reports")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def hygiene_reports_list():
        """List all hygiene reports."""
        date_filter = request.args.get("date")
        area_filter = request.args.get("area")
        query = HygieneReport.query.order_by(HygieneReport.report_date.desc(), HygieneReport.report_time.desc())
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                query = query.filter(HygieneReport.report_date == filter_date)
            except ValueError:
                pass
        
        if area_filter:
            query = query.filter(HygieneReport.area == area_filter)
        
        pagination = paginate_helper(query)
        areas = db.session.query(HygieneReport.area).distinct().all()
        return render_template("production/hygiene_reports_list.html", reports=pagination.items, pagination=pagination, areas=[a[0] for a in areas if a[0]])
    
    @production_bp.route("/hygiene-reports/new", methods=["GET", "POST"])
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def hygiene_reports_new():
        """Create new hygiene report."""
        events = Event.query.filter(Event.status.in_(["Confirmed", "In Progress"])).order_by(Event.event_date.desc()).all()
        areas = ["Kitchen", "Storage", "Prep Area", "Delivery Vehicle", "Dishwashing Area", "Staff Facilities", "Other"]
        
        if request.method == "POST":
            try:
                report_date_str = request.form.get("report_date")
                report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date() if report_date_str else date.today()
                report_time_str = request.form.get("report_time")
                report_time = datetime.strptime(report_time_str, "%H:%M").time() if report_time_str else None
                event_id = request.form.get("event_id", type=int) or None
                area = request.form.get("area", "").strip()
                overall_rating = request.form.get("overall_rating", "Good")
                issues_found = request.form.get("issues_found", "").strip() or None
                corrective_actions = request.form.get("corrective_actions", "").strip() or None
                status = request.form.get("status", "Completed")
                follow_up_date_str = request.form.get("follow_up_date")
                follow_up_date = datetime.strptime(follow_up_date_str, "%Y-%m-%d").date() if follow_up_date_str else None
                
                # Get checklist items
                items = []
                item_names = request.form.getlist("item_name[]")
                item_checked = request.form.getlist("item_checked[]")
                
                for name, checked in zip(item_names, item_checked):
                    if name:
                        items.append({
                            "name": name,
                            "checked": checked == "on"
                        })
                
                if not area:
                    flash("Area is required.", "danger")
                    return render_template("production/hygiene_reports_form.html", report=None, events=events, areas=areas)
                
                report = HygieneReport(
                    report_date=report_date,
                    report_time=report_time,
                    event_id=event_id,
                    inspected_by=current_user.id,
                    area=area,
                    checklist_items=json.dumps(items),
                    overall_rating=overall_rating,
                    issues_found=issues_found,
                    corrective_actions=corrective_actions,
                    status=status,
                    follow_up_date=follow_up_date
                )
                db.session.add(report)
                db.session.commit()
                flash("Hygiene report created successfully.", "success")
                return redirect(url_for("production.hygiene_reports_list"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error creating hygiene report: {e}")
                flash(f"Error creating report: {str(e)}", "danger")
        
        default_items = [
            "Floors clean and dry",
            "Walls and ceilings clean",
            "Equipment clean and sanitized",
            "Proper waste disposal",
            "Pest control measures in place",
            "Staff wearing proper attire",
            "Handwashing facilities functional",
            "Temperature controls working"
        ]
        
        return render_template("production/hygiene_reports_form.html", report=None, events=events, areas=areas, default_items=default_items)
    
    @production_bp.route("/hygiene-reports/<int:report_id>")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def hygiene_reports_view(report_id):
        """View hygiene report details."""
        report = HygieneReport.query.get_or_404(report_id)
        items = json.loads(report.checklist_items) if report.checklist_items else []
        return render_template("production/hygiene_reports_view.html", report=report, items=items)

