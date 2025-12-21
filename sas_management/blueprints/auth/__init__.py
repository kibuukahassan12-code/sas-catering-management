"""Authentication Blueprint - Password Management."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from sas_management.models import User, db
from sas_management.utils import permission_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/change-password", methods=["GET", "POST"])
@auth_bp.route("/set-new-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change password route - required for first login."""
    # Admin is exempt from first login password change requirement
    is_admin = hasattr(current_user, 'is_admin') and current_user.is_admin
    if is_admin and not (getattr(current_user, 'must_change_password', False) or getattr(current_user, 'force_password_change', False)):
        return redirect(url_for("core.dashboard"))
    
    # Check if user is forced to change password
    must_change = getattr(current_user, 'must_change_password', False) or getattr(current_user, 'force_password_change', False)
    is_first_login = getattr(current_user, 'first_login', True)
    
    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        old_password = request.form.get("old_password", "").strip()
        
        # Validate new password
        if not new_password or len(new_password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/change_password.html", must_change=must_change, is_first_login=is_first_login)
        
        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return render_template("auth/change_password.html", must_change=must_change, is_first_login=is_first_login)
        
        # For first login, always require old password. For voluntary changes, also require old password.
        if is_first_login or not must_change:
            if not old_password:
                flash("Please provide your current password.", "danger")
                return render_template("auth/change_password.html", must_change=must_change, is_first_login=is_first_login)
            
            if not current_user.check_password(old_password):
                flash("Current password is incorrect.", "danger")
                return render_template("auth/change_password.html", must_change=must_change, is_first_login=is_first_login)
        
        # Update password
        current_user.set_password(new_password)
        current_user.first_login = False
        current_user.must_change_password = False
        current_user.force_password_change = False
        db.session.commit()
        
        flash("Password changed successfully!", "success")
        return redirect(url_for("core.dashboard"))
    
    return render_template("auth/change_password.html", must_change=must_change, is_first_login=is_first_login)

