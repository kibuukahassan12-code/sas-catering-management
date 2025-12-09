from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import User, Role, db

admin_users = Blueprint("admin_users", __name__)

@admin_users.route("/users/assign", methods=["GET", "POST"], endpoint="users_assign")
@login_required
def users_assign():
    users = User.query.all()
    roles = Role.query.all()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        role_id = request.form.get("role_id")

        user = User.query.get(user_id)
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("admin_users.users_assign"))

        user.role_id = role_id
        db.session.commit()
        flash("Role updated successfully!", "success")
        return redirect(url_for("admin_users.users_assign"))

    return render_template("admin/users_assign.html", users=users, roles=roles)

