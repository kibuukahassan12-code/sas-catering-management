from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sas_management.models import User, Role, db

admin_users = Blueprint("admin_users", __name__)

@admin_users.route("/users/assign", methods=["GET", "POST"], endpoint="users_assign")
@login_required
def users_assign():
    """
    Legacy Assign User Roles endpoint.

    To retire this page safely without breaking existing links,
    all requests are redirected to the main Admin dashboard.
    """
    return redirect(url_for("admin.dashboard"))

