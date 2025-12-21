from decimal import Decimal

from flask import (
    Blueprint,
    render_template,
    request,
    url_for,
)
from flask_login import login_required

from sas_management.models import Ingredient, UserRole, db
from sas_management.utils import get_decimal, paginate_query, role_required, permission_required

inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@inventory_bp.route("/ingredients")
@login_required
# @permission_required("inventory")
def ingredients_list():
    pagination = paginate_query(Ingredient.query.order_by(Ingredient.name.asc()))
    return render_template(
        "inventory/ingredients_list.html",
        ingredients=pagination.items,
        pagination=pagination,
    )


@inventory_bp.route("/ingredients/add", methods=["GET", "POST"])
@login_required
# @permission_required("inventory")
def ingredients_add():
    units = ["kg", "liter", "g", "ml", "piece", "box", "pack"]
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        unit_of_measure = request.form.get("unit_of_measure", "kg")
        stock_count = get_decimal(request.form.get("stock_count"))
        unit_cost = get_decimal(request.form.get("unit_cost"))

        if not name:
            flash("Ingredient name is required.", "danger")
            return render_template(
                "inventory/ingredient_form.html",
                action="Add",
                ingredient=None,
                units=units,
            )

        db.session.add(
            Ingredient(
                name=name,
                unit_of_measure=unit_of_measure,
                stock_count=stock_count,
                unit_cost_ugx=unit_cost,
            )
        )
        db.session.commit()
        flash("Ingredient added.", "success")
        return redirect(url_for("inventory.ingredients_list"))

    return render_template(
        "inventory/ingredient_form.html", action="Add", ingredient=None, units=units
    )


@inventory_bp.route("/ingredients/edit/<int:ingredient_id>", methods=["GET", "POST"])
@login_required
# @permission_required("inventory")
def ingredients_edit(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    units = ["kg", "liter", "g", "ml", "piece", "box", "pack"]

    if request.method == "POST":
        ingredient.name = request.form.get("name", ingredient.name).strip()
        ingredient.unit_of_measure = request.form.get(
            "unit_of_measure", ingredient.unit_of_measure
        )
        stock_count_raw = request.form.get("stock_count")
        if stock_count_raw:
            ingredient.stock_count = get_decimal(
                stock_count_raw, fallback=str(ingredient.stock_count)
            )
        unit_cost_raw = request.form.get("unit_cost")
        if unit_cost_raw:
            ingredient.unit_cost_ugx = get_decimal(
                unit_cost_raw, fallback=str(ingredient.unit_cost_ugx)
            )
        db.session.commit()
        flash("Ingredient updated.", "success")
        return redirect(url_for("inventory.ingredients_list"))

    return render_template(
        "inventory/ingredient_form.html",
        action="Edit",
        ingredient=ingredient,
        units=units,
    )


@inventory_bp.route("/ingredients/delete/<int:ingredient_id>", methods=["POST"])
@login_required
@role_required("Admin", "InventoryManager")
def ingredients_delete(ingredient_id):
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    if ingredient.recipe_items:
        flash(
            "This ingredient is used in recipes. Remove it from recipes first.",
            "warning",
        )
        return redirect(url_for("inventory.ingredients_list"))

    db.session.delete(ingredient)
    db.session.commit()
    flash("Ingredient removed.", "info")
    return redirect(url_for("inventory.ingredients_list"))

