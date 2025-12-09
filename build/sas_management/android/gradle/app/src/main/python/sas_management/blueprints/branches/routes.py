"""Multi-branch routes."""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

from models import db, Branch, UserRole
from utils import role_required

branches_bp = Blueprint("branches", __name__, url_prefix="/branches")

@branches_bp.route("/")
@login_required
@role_required(UserRole.Admin)
def branches_list():
    """List all branches."""
    branches = Branch.query.all()
    return render_template("branches/branches_list.html", branches=branches)

@branches_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin)
def create():
    """Create new branch."""
    if request.method == "POST":
        try:
            branch = Branch(
                name=request.form.get('name', ''),
                address=request.form.get('address', ''),
                phone=request.form.get('phone', ''),
                email=request.form.get('email', ''),
                timezone=request.form.get('timezone', 'Africa/Kampala'),
                is_active=True
            )
            db.session.add(branch)
            db.session.commit()
            flash("Branch created successfully!", "success")
            return redirect(url_for("branches.branches_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating branch: {str(e)}", "danger")
    
    return render_template("branches/create.html")

