"""Equipment Maintenance routes for Hire Department."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from decimal import Decimal

from sas_management.models import db, InventoryItem, UserRole, EquipmentMaintenance, EquipmentConditionReport, EquipmentDepreciation
from sas_management.utils import role_required

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/hire/maintenance")

@maintenance_bp.route("/")
@login_required
@role_required(UserRole.Admin, UserRole.HireManager)
def dashboard():
    """Maintenance dashboard."""
    try:
        # Get upcoming maintenance (next 30 days)
        upcoming_date = date.today() + timedelta(days=30)
        upcoming_maintenance = EquipmentMaintenance.query.filter(
            EquipmentMaintenance.scheduled_date >= date.today()
        ).filter(
            EquipmentMaintenance.scheduled_date <= upcoming_date
        ).filter(
            EquipmentMaintenance.status.in_(['scheduled', 'in_progress'])
        ).order_by(EquipmentMaintenance.scheduled_date.asc()).limit(20).all()
        
        # Get recent condition reports
        recent_reports = EquipmentConditionReport.query.order_by(
            EquipmentConditionReport.report_date.desc()
        ).limit(10).all()
        
        # Get items needing attention (low condition ratings)
        critical_items = EquipmentConditionReport.query.filter(
            EquipmentConditionReport.condition_rating < 5
        ).order_by(EquipmentConditionReport.condition_rating.asc()).limit(10).all()
        
        # Statistics
        stats = {
            'upcoming_count': len(upcoming_maintenance),
            'in_progress_count': EquipmentMaintenance.query.filter_by(status='in_progress').count(),
            'completed_this_month': EquipmentMaintenance.query.filter(
                EquipmentMaintenance.status == 'completed'
            ).filter(
                EquipmentMaintenance.completed_date >= date.today().replace(day=1)
            ).count(),
            'items_need_attention': len(critical_items)
        }
        
        return render_template("hire/maintenance/dashboard.html",
            upcoming_maintenance=upcoming_maintenance,
            recent_reports=recent_reports,
            critical_items=critical_items,
            stats=stats
        )
    except Exception as e:
        flash(f"Error loading maintenance dashboard: {str(e)}", "danger")
        return render_template("hire/maintenance/dashboard.html",
            upcoming_maintenance=[],
            recent_reports=[],
            critical_items=[],
            stats={'upcoming_count': 0, 'in_progress_count': 0, 'completed_this_month': 0, 'items_need_attention': 0}
        )

@maintenance_bp.route("/schedule", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.HireManager)
def schedule():
    """Schedule new maintenance."""
    if request.method == "POST":
        try:
            maintenance = EquipmentMaintenance(
                hire_item_id=int(request.form["hire_item_id"]),
                maintenance_type=request.form["maintenance_type"],
                scheduled_date=datetime.strptime(request.form["scheduled_date"], "%Y-%m-%d").date(),
                technician_name=request.form.get("technician_name", "").strip(),
                notes=request.form.get("notes", "").strip(),
                cost=Decimal(request.form.get("cost", 0) or 0),
                status="scheduled"
            )
            db.session.add(maintenance)
            db.session.commit()
            flash("Maintenance scheduled successfully!", "success")
            return redirect(url_for("maintenance.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error scheduling maintenance: {str(e)}", "danger")
    
    items = InventoryItem.query.order_by(InventoryItem.name.asc()).all()
    return render_template("hire/maintenance/schedule.html", items=items)

@maintenance_bp.route("/update-status/<int:maintenance_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.HireManager)
def update_status(maintenance_id):
    """Update maintenance status."""
    try:
        maintenance = EquipmentMaintenance.query.get_or_404(maintenance_id)
        new_status = request.form.get("status")
        
        if new_status in ['scheduled', 'in_progress', 'completed', 'cancelled']:
            maintenance.status = new_status
            
            if new_status == 'completed':
                maintenance.completed_date = date.today()
            
            db.session.commit()
            flash(f"Maintenance status updated to {new_status}.", "success")
        else:
            flash("Invalid status.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating status: {str(e)}", "danger")
    
    return redirect(url_for("maintenance.dashboard"))

@maintenance_bp.route("/list")
@login_required
@role_required(UserRole.Admin, UserRole.HireManager)
def maintenance_list():
    """List all maintenance records."""
    try:
        status_filter = request.args.get("status", "all")
        query = EquipmentMaintenance.query
        
        if status_filter != "all":
            query = query.filter_by(status=status_filter)
        
        maintenance_records = query.order_by(EquipmentMaintenance.scheduled_date.desc()).limit(100).all()
        
        return render_template("hire/maintenance/list.html",
            maintenance_records=maintenance_records,
            status_filter=status_filter
        )
    except Exception as e:
        flash(f"Error loading maintenance list: {str(e)}", "danger")
        return render_template("hire/maintenance/list.html", maintenance_records=[])

@maintenance_bp.route("/condition-report", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.HireManager)
def condition_report():
    """Create condition report."""
    if request.method == "POST":
        try:
            report = EquipmentConditionReport(
                hire_item_id=int(request.form["hire_item_id"]),
                condition_rating=int(request.form["condition_rating"]),
                report_date=datetime.strptime(request.form.get("report_date", date.today().isoformat()), "%Y-%m-%d").date(),
                issues_found=request.form.get("issues_found", "").strip(),
                recommended_action=request.form.get("recommended_action", "").strip(),
                created_by=current_user.id
            )
            db.session.add(report)
            
            # Update item condition based on rating
            item = db.session.get(InventoryItem, report.hire_item_id)
            if item:
                if report.condition_rating <= 3:
                    item.condition = "Poor"
                elif report.condition_rating <= 5:
                    item.condition = "Fair"
                elif report.condition_rating <= 7:
                    item.condition = "Good"
                else:
                    item.condition = "Excellent"
            
            db.session.commit()
            flash("Condition report logged successfully!", "success")
            return redirect(url_for("maintenance.dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating condition report: {str(e)}", "danger")
    
    items = InventoryItem.query.order_by(InventoryItem.name.asc()).all()
    return render_template("hire/maintenance/condition_report.html", items=items)

@maintenance_bp.route("/depreciation/<int:item_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.HireManager)
def depreciation(item_id):
    """Calculate and track equipment depreciation."""
    item = InventoryItem.query.get_or_404(item_id)
    
    if request.method == "POST":
        try:
            purchase_price = Decimal(request.form["purchase_price"])
            salvage_value = Decimal(request.form.get("salvage_value", 0) or 0)
            life_years = int(request.form["life_years"])
            purchase_date_str = request.form.get("purchase_date")
            
            if purchase_date_str:
                purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date()
            else:
                purchase_date = date.today()
            
            # Calculate years since purchase
            years_owned = (date.today() - purchase_date).days / 365.25
            
            # Straight-line depreciation
            yearly_depreciation = (purchase_price - salvage_value) / life_years
            calculated_value = max(purchase_price - (yearly_depreciation * years_owned), salvage_value)
            
            # Check if depreciation record exists
            depreciation = EquipmentDepreciation.query.filter_by(hire_item_id=item_id).first()
            if depreciation:
                depreciation.purchase_price = purchase_price
                depreciation.salvage_value = salvage_value
                depreciation.useful_life_years = life_years
                depreciation.calculated_value = calculated_value
                depreciation.purchase_date = purchase_date
                depreciation.last_updated = date.today()
            else:
                depreciation = EquipmentDepreciation(
                    hire_item_id=item_id,
                    purchase_price=purchase_price,
                    salvage_value=salvage_value,
                    useful_life_years=life_years,
                    calculated_value=calculated_value,
                    purchase_date=purchase_date,
                    last_updated=date.today()
                )
                db.session.add(depreciation)
            
            db.session.commit()
            flash("Depreciation calculated and saved!", "success")
            return redirect(url_for("maintenance.depreciation", item_id=item_id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error calculating depreciation: {str(e)}", "danger")
    
    depreciation_record = EquipmentDepreciation.query.filter_by(hire_item_id=item_id).first()
    return render_template("hire/maintenance/depreciation.html",
        item=item,
        depreciation=depreciation_record
    )

@maintenance_bp.route("/view/<int:maintenance_id>")
@login_required
@role_required(UserRole.Admin, UserRole.HireManager)
def view_maintenance(maintenance_id):
    """View maintenance details."""
    maintenance = EquipmentMaintenance.query.get_or_404(maintenance_id)
    return render_template("hire/maintenance/view.html", maintenance=maintenance)

