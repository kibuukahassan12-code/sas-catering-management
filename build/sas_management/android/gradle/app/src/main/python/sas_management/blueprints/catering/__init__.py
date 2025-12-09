from collections import defaultdict
from datetime import date
from decimal import Decimal

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from models import (
    CateringItem,
    Ingredient,
    PriceHistory,
    RecipeItem,
    UserRole,
    db,
)
from utils import get_decimal, paginate_query, role_required

catering_bp = Blueprint("catering", __name__, url_prefix="/catering")


@catering_bp.route("/")
@login_required
def index():
    return render_template(
        "module_placeholder.html",
        module_title="Catering Workspace",
        description="Catering workflows will live here, including menu design, staffing, and on-site logistics.",
    )


@catering_bp.route("/menu")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def menu_list():
    pagination = paginate_query(
        CateringItem.query.order_by(CateringItem.name.asc())
    )
    return render_template(
        "catering/menu_list.html", 
        items=pagination.items, 
        pagination=pagination,
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
    )


@catering_bp.route("/menu/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def menu_add():
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            selling_price_str = request.form.get("selling_price", "").strip()
            estimated_cogs_str = request.form.get("estimated_cogs", "").strip()
            
            if not name:
                flash("Menu item name is required.", "danger")
                return render_template(
                    "catering/menu_form.html", 
                    action="Add", 
                    item=None,
                    CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
                )
            
            selling_price = get_decimal(selling_price_str) if selling_price_str else Decimal('0.00')
            estimated_cogs_decimal = get_decimal(estimated_cogs_str) if estimated_cogs_str else None

            # Create the catering item
            new_item = CateringItem(
                name=name,
                selling_price_ugx=selling_price,
                price_ugx=selling_price,  # Keep for backward compatibility
                estimated_cogs_ugx=estimated_cogs_decimal,
            )
            db.session.add(new_item)
            db.session.flush()  # Get the ID

            # Create initial price history record
            try:
                price_history = PriceHistory(
                    item_id=new_item.id,
                    item_type="CATERING",
                    price_ugx=selling_price,
                    effective_date=date.today(),
                    user_id=current_user.id if current_user.is_authenticated else None,
                )
                db.session.add(price_history)
            except Exception as e:
                current_app.logger.warning(f"Could not create price history: {e}")
            
            db.session.commit()
            flash("Catering menu item added successfully.", "success")
            return redirect(url_for("catering.menu_list"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Error adding catering menu item: {e}")
            flash(f"Error adding menu item: {str(e)}", "danger")
            return render_template(
                "catering/menu_form.html", 
                action="Add", 
                item=None,
                CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
            )

    return render_template(
        "catering/menu_form.html", 
        action="Add", 
        item=None,
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
    )


@catering_bp.route("/menu/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def menu_edit(item_id):
    item = CateringItem.query.get_or_404(item_id)

    if request.method == "POST":
        try:
            item.name = request.form.get("name", item.name).strip()
            selling_price_raw = request.form.get("selling_price", "").strip()
            estimated_cogs_raw = request.form.get("estimated_cogs", "").strip()
            
            if selling_price_raw:
                new_price = get_decimal(selling_price_raw)
                item.selling_price_ugx = new_price
                item.price_ugx = new_price  # Keep for backward compatibility
            else:
                # Keep existing price if not provided
                if not item.selling_price_ugx:
                    item.selling_price_ugx = item.price_ugx or Decimal('0.00')
            
            if estimated_cogs_raw:
                item.estimated_cogs_ugx = get_decimal(estimated_cogs_raw)
            else:
                item.estimated_cogs_ugx = None
            
            # Handle price change - create new PriceHistory record if price changed
            if selling_price_raw:
                try:
                    current_price = item.get_current_price()
                    new_price = get_decimal(selling_price_raw)
                    if new_price != current_price:
                        price_history = PriceHistory(
                            item_id=item.id,
                            item_type="CATERING",
                            price_ugx=new_price,
                            effective_date=date.today(),
                            user_id=current_user.id if current_user.is_authenticated else None,
                        )
                        db.session.add(price_history)
                except Exception as e:
                    current_app.logger.warning(f"Could not update price history: {e}")
            
            db.session.commit()
            flash("Catering menu item updated successfully.", "success")
            return redirect(url_for("catering.menu_list"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Error updating catering menu item: {e}")
            flash(f"Error updating menu item: {str(e)}", "danger")
            return render_template(
                "catering/menu_form.html", 
                action="Edit", 
                item=item,
                CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
            )

    return render_template(
        "catering/menu_form.html", 
        action="Edit", 
        item=item,
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
    )


@catering_bp.route("/menu/delete/<int:item_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def menu_delete(item_id):
    try:
        item = CateringItem.query.get_or_404(item_id)
        
        # Check if item has recipe items
        recipe_items_count = RecipeItem.query.filter_by(catering_item_id=item_id).count()
        if recipe_items_count > 0:
            flash(
                f"This item has {recipe_items_count} recipe item(s). Delete recipes first or use the recipe builder to remove them.",
                "warning",
            )
            return redirect(url_for("catering.menu_list"))

        # Delete associated price history
        try:
            PriceHistory.query.filter_by(item_id=item_id, item_type="CATERING").delete()
        except Exception as e:
            current_app.logger.warning(f"Could not delete price history: {e}")

        db.session.delete(item)
        db.session.commit()
        flash("Catering menu item removed successfully.", "info")
        return redirect(url_for("catering.menu_list"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error deleting catering menu item: {e}")
        flash(f"Error deleting menu item: {str(e)}", "danger")
        return redirect(url_for("catering.menu_list"))


@catering_bp.route("/menu/recipe/<int:item_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def recipe_builder(item_id):
    try:
        item = CateringItem.query.get_or_404(item_id)
        ingredients = Ingredient.query.order_by(Ingredient.name.asc()).all()

        if request.method == "POST":
            try:
                # Parse form data for recipe items
                ingredient_ids = request.form.getlist("ingredient_id[]")
                quantities = request.form.getlist("quantity[]")

                # Clear existing recipe items
                RecipeItem.query.filter_by(catering_item_id=item_id).delete()

                # Add new recipe items
                total_cogs = Decimal("0.00")
                added_items = 0
                
                for ing_id, qty_str in zip(ingredient_ids, quantities):
                    if not ing_id or not ing_id.strip():
                        continue
                    try:
                        ing_id_int = int(ing_id)
                        qty = get_decimal(qty_str) if qty_str else Decimal('0.00')
                        if qty <= 0:
                            continue

                        ingredient = Ingredient.query.get(ing_id_int)
                        if not ingredient:
                            continue

                        db.session.add(
                            RecipeItem(
                                catering_item_id=item_id,
                                ingredient_id=ing_id_int,
                                quantity_required=qty,
                            )
                        )
                        # Calculate COGS contribution
                        unit_cost = ingredient.unit_cost_ugx or Decimal('0.00')
                        total_cogs += unit_cost * qty
                        added_items += 1
                    except (ValueError, TypeError) as e:
                        current_app.logger.warning(f"Error processing ingredient {ing_id}: {e}")
                        continue

                # Update estimated COGS
                item.estimated_cogs_ugx = total_cogs
                db.session.commit()
                
                if added_items > 0:
                    flash(f"Recipe updated successfully. {added_items} ingredient(s) added. COGS: {current_app.config.get('CURRENCY_PREFIX', 'UGX ')}{total_cogs:,.2f}", "success")
                else:
                    flash("Recipe cleared. No ingredients added.", "info")
                    
                return redirect(url_for("catering.recipe_builder", item_id=item_id))
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error updating recipe: {e}")
                flash(f"Error updating recipe: {str(e)}", "danger")

        # Load existing recipe items
        existing_recipe = {}
        try:
            recipe_items = RecipeItem.query.filter_by(catering_item_id=item_id).all()
            for ri in recipe_items:
                existing_recipe[ri.ingredient_id] = float(ri.quantity_required) if ri.quantity_required else 0.0
        except Exception as e:
            current_app.logger.warning(f"Error loading recipe items: {e}")
            existing_recipe = {}

        return render_template(
            "catering/recipe_builder.html",
            item=item,
            ingredients=ingredients,
            existing_recipe=existing_recipe,
            CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
        )
        
    except Exception as e:
        current_app.logger.exception(f"Error in recipe builder: {e}")
        flash(f"Error loading recipe builder: {str(e)}", "danger")
        return redirect(url_for("catering.menu_list"))
