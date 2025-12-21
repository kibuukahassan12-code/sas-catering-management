"""Production Department Blueprint."""
from datetime import datetime, date, time
from decimal import Decimal
import json

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from sas_management.models import (
    Event, ProductionOrder, Recipe, UserRole, User, db,
    KitchenChecklist, DeliveryQCChecklist, FoodSafetyLog, HygieneReport
)
from sas_management.services.production_service import (
    compute_cogs_for_order,
    create_production_order,
    generate_production_reference,
    generate_production_sheet,
    release_reservations,
    reserve_ingredients,
    scale_recipe,
)
from sas_management.utils import paginate_query, role_required

production_bp = Blueprint("production", __name__, url_prefix="/production")


# HTML Views

@production_bp.route("/")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def index():
    """Production dashboard."""
    today = datetime.now().date()
    active_orders = (
        ProductionOrder.query.filter(ProductionOrder.status.in_(["Planned", "In Prep", "Cooking", "Packed"]))
        .order_by(ProductionOrder.scheduled_prep.asc())
        .limit(10)
        .all()
    )
    
    summary = {
        "total_orders": ProductionOrder.query.count(),
        "active_orders": ProductionOrder.query.filter(
            ProductionOrder.status.in_(["Planned", "In Prep", "Cooking", "Packed"])
        ).count(),
        "completed_today": ProductionOrder.query.filter(
            ProductionOrder.status == "Completed",
            db.func.date(ProductionOrder.updated_at) == today,
        ).count(),
    }
    
    return render_template(
        "production/production_index.html",
        summary=summary,
        active_orders=active_orders,
    )


@production_bp.route("/order/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def order_create():
    """Create a new production order."""
    events = Event.query.filter(Event.status == "Confirmed").order_by(Event.event_date.asc()).all()
    recipes = Recipe.query.order_by(Recipe.name.asc()).all()
    
    if request.method == "POST":
        try:
            event_id = request.form.get("event_id", type=int) or None
            items_data = []
            
            # Parse form items
            recipe_ids = request.form.getlist("recipe_id[]")
            portions = request.form.getlist("portions[]")
            recipe_names = request.form.getlist("recipe_name[]")
            
            for recipe_id, portion, recipe_name in zip(recipe_ids, portions, recipe_names):
                if recipe_id and portion:
                    items_data.append({
                        "recipe_id": int(recipe_id),
                        "portions": int(portion),
                        "recipe_name": recipe_name or (lambda r: r.name if r else "Unknown")(db.session.get(Recipe, int(recipe_id))),
                    })
            
            if not items_data:
                flash("Please add at least one recipe to the order.", "danger")
                return render_template(
                    "production/production_order_create.html",
                    events=events,
                    recipes=recipes,
                )
            
            # Convert datetime-local format to ISO format
            def format_datetime_local(dt_str):
                if not dt_str:
                    return None
                # datetime-local format is YYYY-MM-DDTHH:MM, convert to ISO
                return dt_str.replace(' ', 'T') if dt_str else None
            
            schedule_times = {
                "prep": format_datetime_local(request.form.get("scheduled_prep")) or datetime.now().isoformat(),
                "cook": format_datetime_local(request.form.get("scheduled_cook")),
                "pack": format_datetime_local(request.form.get("scheduled_pack")),
                "load": format_datetime_local(request.form.get("scheduled_load")),
            }
            
            order = create_production_order(event_id, items_data, schedule_times)
            flash(f"Production order {order.reference} created successfully.", "success")
            return redirect(url_for("production.order_view", order_id=order.id))
            
        except Exception as e:
            flash(f"Error creating production order: {str(e)}", "danger")
            return render_template(
                "production/production_order_create.html",
                events=events,
                recipes=recipes,
            )
    
    return render_template(
        "production/production_order_create.html",
        events=events,
        recipes=recipes,
    )


@production_bp.route("/order/<int:order_id>")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def order_view(order_id):
    """View production order details."""
    order = ProductionOrder.query.get_or_404(order_id)
    sheet_data = generate_production_sheet(order_id)
    
    return render_template(
        "production/production_order_view.html",
        order=order,
        sheet_data=sheet_data,
    )


# REST API Endpoints

@production_bp.route("/api/orders")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_orders_list():
    """API: List production orders."""
    status_filter = request.args.get("status")
    date_filter = request.args.get("date")
    
    query = ProductionOrder.query
    
    if status_filter:
        query = query.filter(ProductionOrder.status == status_filter)
    
    if date_filter:
        try:
            filter_date = datetime.fromisoformat(date_filter).date()
            query = query.filter(db.func.date(ProductionOrder.scheduled_prep) == filter_date)
        except (ValueError, TypeError):
            pass
    
    query = query.order_by(ProductionOrder.scheduled_prep.desc())
    pagination = paginate_query(query)
    
    return jsonify({
        "status": "success",
        "orders": [
            {
                "id": order.id,
                "reference": order.reference,
                "event_id": order.event_id,
                "event_name": order.event.event_name if order.event else None,
                "scheduled_prep": order.scheduled_prep.isoformat() if order.scheduled_prep else None,
                "status": order.status,
                "total_portions": order.total_portions,
                "total_cost": float(order.total_cost),
            }
            for order in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "pages": pagination.pages,
            "per_page": pagination.per_page,
            "total": pagination.total,
        },
    })


@production_bp.route("/api/orders", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_order_create():
    """API: Create production order."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    try:
        items = data.get("items", [])
        if not items:
            return jsonify({"status": "error", "message": "At least one recipe item is required"}), 400
        
        schedule_times = data.get("schedule_times", {})
        if not schedule_times.get("prep"):
            schedule_times["prep"] = datetime.now().isoformat()
        else:
            # Ensure datetime strings are properly formatted
            prep = schedule_times.get("prep")
            if prep and isinstance(prep, str):
                schedule_times["prep"] = prep.replace(' ', 'T') if ' ' in prep else prep
        
        order = create_production_order(
            event_id=data.get("event_id"),
            items=items,
            schedule_times=schedule_times,
        )
        
        return jsonify({
            "status": "success",
            "message": "Production order created",
            "order_id": order.id,
            "reference": order.reference,
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@production_bp.route("/api/orders/<int:order_id>")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_order_detail(order_id):
    """API: Get production order details."""
    order = ProductionOrder.query.get_or_404(order_id)
    sheet_data = generate_production_sheet(order_id)
    
    return jsonify({
        "status": "success",
        "order": sheet_data["order"],
        "line_items": sheet_data["line_items"],
        "shopping_list": sheet_data["shopping_list"],
        "total_cogs": sheet_data["total_cogs"],
    })


@production_bp.route("/api/orders/<int:order_id>/status", methods=["PATCH", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_order_status(order_id):
    """API: Update production order status."""
    order = ProductionOrder.query.get_or_404(order_id)
    
    if request.is_json:
        data = request.get_json()
        new_status = data.get("status")
    else:
        new_status = request.form.get("status")
    
    if not new_status:
        return jsonify({"status": "error", "message": "Status is required"}), 400
    
    valid_statuses = ["Planned", "In Prep", "Cooking", "Packed", "Loaded", "Completed"]
    if new_status not in valid_statuses:
        return jsonify({"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
    
    order.status = new_status
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": f"Order status updated to {new_status}",
        "order_id": order.id,
        "new_status": new_status,
    })


@production_bp.route("/api/orders/<int:order_id>/reserve", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_order_reserve(order_id):
    """API: Reserve ingredients for production order."""
    order = ProductionOrder.query.get_or_404(order_id)
    
    try:
        # Get all ingredients needed
        all_ingredients = {}
        for line_item in order.items:
            recipe = db.session.get(Recipe, line_item.recipe_id)
            if recipe:
                scaled = scale_recipe(recipe.id, line_item.portions)
                for ing_id, qty in scaled.items():
                    if ing_id in all_ingredients:
                        all_ingredients[ing_id] += qty
                    else:
                        all_ingredients[ing_id] = qty
        
        reserved = reserve_ingredients(all_ingredients)
        
        return jsonify({
            "status": "success",
            "message": "Ingredients reserved successfully",
            "reserved": reserved,
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@production_bp.route("/api/orders/<int:order_id>/release", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_order_release(order_id):
    """API: Release reserved ingredients."""
    try:
        release_reservations(order_id)
        return jsonify({
            "status": "success",
            "message": "Reservations released successfully",
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@production_bp.route("/api/recipes")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_recipes_list():
    """API: List recipes."""
    recipes = Recipe.query.order_by(Recipe.name.asc()).all()
    
    return jsonify({
        "status": "success",
        "recipes": [
            {
                "id": recipe.id,
                "name": recipe.name,
                "description": recipe.description,
                "portions": recipe.portions,
                "prep_time_mins": recipe.prep_time_mins,
                "cook_time_mins": recipe.cook_time_mins,
                "cost_per_portion": float(recipe.cost_per_portion),
            }
            for recipe in recipes
        ],
    })


@production_bp.route("/api/recipes", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_recipe_create():
    """API: Create or update recipe."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    try:
        import json as json_lib
        
        recipe = Recipe(
            name=data.get("name"),
            description=data.get("description"),
            portions=data.get("portions", 1),
            ingredients=json_lib.dumps(data.get("ingredients", [])),
            prep_time_mins=data.get("prep_time_mins", 0),
            cook_time_mins=data.get("cook_time_mins", 0),
            cost_per_portion=Decimal(str(data.get("cost_per_portion", 0))),
        )
        db.session.add(recipe)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Recipe created",
            "recipe_id": recipe.id,
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400


@production_bp.route("/api/orders/<int:order_id>/sheet")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def api_order_sheet(order_id):
    """API: Generate production sheet."""
    sheet_data = generate_production_sheet(order_id)
    return jsonify({
        "status": "success",
        "sheet": sheet_data,
    })


# ============================
# QUALITY CONTROL ROUTES
# ============================
# Import and register quality control routes
from blueprints.production.quality_control import add_quality_control_routes
add_quality_control_routes(production_bp, role_required, paginate_query)
