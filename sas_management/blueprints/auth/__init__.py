"""Authentication Blueprint - Password Management."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from models import User, db
from utils import permission_required

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/change-password", methods=["GET", "POST"])
@auth_bp.route("/set-new-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change password route - required for first login."""
    # Check if user is forced to change password
    must_change = getattr(current_user, 'must_change_password', False) or getattr(current_user, 'force_password_change', False)
    
    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        old_password = request.form.get("old_password", "").strip()
        
        # Validate new password
        if not new_password or len(new_password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("auth/change_password.html", must_change=must_change)
        
        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return render_template("auth/change_password.html", must_change=must_change)
        
        # Check old password only if not forced to change (i.e., user is changing voluntarily)
        if not must_change:
            if not old_password:
                flash("Please provide your current password.", "danger")
                return render_template("auth/change_password.html", must_change=must_change)
            
            if not current_user.check_password(old_password):
                flash("Current password is incorrect.", "danger")
                return render_template("auth/change_password.html", must_change=must_change)
        
        # Update password
        current_user.set_password(new_password)
        current_user.must_change_password = False
        current_user.force_password_change = False
        db.session.commit()
        
        flash("Password changed successfully!", "success")
        return redirect(url_for("core.dashboard"))
    
    return render_template("auth/change_password.html", must_change=must_change)

