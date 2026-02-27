"""Production Department Blueprint."""
from datetime import datetime, date, time
from decimal import Decimal
import json

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user

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


# ============================
# PRODUCTION BUDGET ROUTES
# ============================
from sas_management.models import ProductionBudget, ProductionBudgetItem, BudgetItemCategory, ProductionBudgetStatus
from sas_management.models import Event, User, UserRole
from decimal import Decimal


@production_bp.route("/budgets")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budgets_list():
    """List all production budgets."""
    page = request.args.get("page", 1, type=int)
    per_page = 20
    status_filter = request.args.get("status", "")

    budgets_query = ProductionBudget.query
    if status_filter:
        try:
            status_enum = ProductionBudgetStatus(status_filter)
            budgets_query = budgets_query.filter(ProductionBudget.status == status_enum)
        except ValueError:
            pass
    budgets_query = budgets_query.order_by(ProductionBudget.created_at.desc())
    pagination = budgets_query.paginate(page=page, per_page=per_page, error_out=False)
    budgets = pagination.items

    return render_template(
        "production/budgets_list.html",
        budgets=budgets,
        pagination=pagination,
    )


@production_bp.route("/budgets/export")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budgets_export():
    """Export budgets to CSV."""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        from datetime import datetime
        
        budgets = ProductionBudget.query.order_by(ProductionBudget.created_at.desc()).all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'ID', 'Event', 'Client', 'Status', 'Total Cost (UGX)', 
            'Created', 'Submitted', 'Approved/Rejected'
        ])
        
        for budget in budgets:
            event_title = budget.event.title if budget.event else 'N/A'
            client_name = budget.event.client.name if budget.event and budget.event.client else 'N/A'
            
            writer.writerow([
                budget.id,
                event_title,
                client_name,
                budget.status.value if budget.status else 'N/A',
                budget.total_cost_ugx or 0,
                budget.created_at.strftime('%Y-%m-%d') if budget.created_at else '',
                budget.submitted_at.strftime('%Y-%m-%d') if budget.submitted_at else '',
                budget.reviewed_at.strftime('%Y-%m-%d') if budget.reviewed_at else ''
            ])
        
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=production_budgets_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        
        return response
    except Exception as e:
        flash(f"Error exporting budgets: {str(e)}", "danger")
        return redirect(url_for("production.budgets_list"))


@production_bp.route("/budget/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budget_new():
    """Create a new production budget."""
    if request.method == "POST":
        try:
            event_id = request.form.get("event_id", type=int)
            if not event_id:
                flash("Please select an event.", "danger")
                return redirect(url_for("production.budget_new"))
            
            budget = ProductionBudget(
                event_id=event_id,
                created_by=current_user.id,
                status=ProductionBudgetStatus.Draft,
            )
            db.session.add(budget)
            db.session.flush()
            
            # Read form arrays
            form_categories = request.form.getlist("category[]")
            form_descriptions = request.form.getlist("description[]")
            form_quantities = request.form.getlist("quantity[]")
            form_costs = request.form.getlist("unit_cost_ugx[]")
            form_notes = request.form.getlist("notes[]")
            
            if form_categories:
                for i, cat_val in enumerate(form_categories):
                    qty = Decimal(form_quantities[i]) if i < len(form_quantities) and form_quantities[i] else Decimal("1")
                    cost = Decimal(form_costs[i]) if i < len(form_costs) and form_costs[i] else Decimal("0")
                    desc = form_descriptions[i] if i < len(form_descriptions) else cat_val
                    notes = form_notes[i] if i < len(form_notes) else ""
                    item = ProductionBudgetItem(
                        budget_id=budget.id,
                        category=cat_val,
                        description=desc,
                        quantity=qty,
                        unit_cost_ugx=cost,
                        total_cost_ugx=qty * cost,
                        notes=notes,
                    )
                    db.session.add(item)
            else:
                # No form rows submitted - create one empty row per category
                default_cats = [
                    BudgetItemCategory.FoodItems, BudgetItemCategory.Sauces,
                    BudgetItemCategory.MarketAccessories, BudgetItemCategory.Spices,
                    BudgetItemCategory.Fruits, BudgetItemCategory.TeaBeverages,
                    BudgetItemCategory.Transport, BudgetItemCategory.Hire,
                    BudgetItemCategory.ProductionLabour, BudgetItemCategory.ServiceLabour,
                ]
                for cat in default_cats:
                    item = ProductionBudgetItem(
                        budget_id=budget.id,
                        category=cat.value,
                        description=f"{cat.value} - Initial item",
                        quantity=Decimal("1"),
                        unit_cost_ugx=Decimal("0"),
                        total_cost_ugx=Decimal("0"),
                    )
                    db.session.add(item)
            
            budget.recalc_totals()
            db.session.commit()
            flash("Budget created successfully.", "success")
            return redirect(url_for("production.budget_view", budget_id=budget.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating budget: {str(e)}", "danger")
    
    events = Event.query.filter(Event.status == "Confirmed").order_by(Event.event_date.desc()).all()
    from sas_management.models import BudgetItemCategory
    categories = list(BudgetItemCategory)
    return render_template("production/budget_form.html", events=events, categories=categories)


@production_bp.route("/budget/<int:budget_id>")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budget_view(budget_id):
    """View budget details."""
    budget = ProductionBudget.query.get_or_404(budget_id)
    budget_items = ProductionBudgetItem.query.filter_by(budget_id=budget_id).order_by(ProductionBudgetItem.category).all()
    
    is_admin = current_user.role == UserRole.Admin
    upcoming_events = Event.query.filter(Event.status == "Confirmed").order_by(Event.event_date.asc()).all()
    
    return render_template(
        "production/budget_view.html",
        budget=budget,
        budget_items=budget_items,
        is_admin=is_admin,
        upcoming_events=upcoming_events,
    )


@production_bp.route("/budget/<int:budget_id>/pdf")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budget_pdf(budget_id):
    budget = ProductionBudget.query.get_or_404(budget_id)

    if budget.status != ProductionBudgetStatus.Approved:
        flash("Only approved budgets can be downloaded as PDF.", "warning")
        return redirect(url_for("production.budget_view", budget_id=budget_id))

    from flask import make_response
    from sas_management.services.production_budget_pdf_service import (
        generate_production_budget_pdf_bytes,
    )

    pdf_bytes = generate_production_budget_pdf_bytes(budget)
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers[
        "Content-Disposition"
    ] = f"inline; filename=production_budget_{budget.id}.pdf"
    return response


@production_bp.route("/budget/<int:budget_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budget_edit(budget_id):
    """Edit budget."""
    budget = ProductionBudget.query.get_or_404(budget_id)
    
    if budget.status != ProductionBudgetStatus.Draft:
        flash("Only draft budgets can be edited.", "warning")
        return redirect(url_for("production.budget_view", budget_id=budget_id))
    
    if request.method == "POST":
        try:
            item_ids = request.form.getlist("item_id[]")
            quantities = request.form.getlist("quantity[]")
            unit_costs = request.form.getlist("unit_cost_ugx[]")
            descriptions = request.form.getlist("description[]")
            categories_form = request.form.getlist("category[]")
            notes_form = request.form.getlist("notes[]")
            
            # Update existing items
            for i, item_id in enumerate(item_ids):
                if not item_id:
                    continue
                item = ProductionBudgetItem.query.get(int(item_id))
                if item:
                    item.category = categories_form[i] if i < len(categories_form) else item.category
                    item.description = descriptions[i] if i < len(descriptions) else item.description
                    item.quantity = Decimal(quantities[i] or "0") if i < len(quantities) else item.quantity
                    item.unit_cost_ugx = Decimal(unit_costs[i] or "0") if i < len(unit_costs) else item.unit_cost_ugx
                    item.total_cost_ugx = item.quantity * item.unit_cost_ugx
                    item.notes = notes_form[i] if i < len(notes_form) else item.notes
            
            # Add any new rows (no item_id)
            new_cats = request.form.getlist("new_category[]")
            new_descs = request.form.getlist("new_description[]")
            new_qtys = request.form.getlist("new_quantity[]")
            new_costs = request.form.getlist("new_unit_cost_ugx[]")
            new_notes = request.form.getlist("new_notes[]")
            for i, cat_val in enumerate(new_cats):
                if not cat_val:
                    continue
                qty = Decimal(new_qtys[i] or "1") if i < len(new_qtys) else Decimal("1")
                cost = Decimal(new_costs[i] or "0") if i < len(new_costs) else Decimal("0")
                new_item = ProductionBudgetItem(
                    budget_id=budget_id,
                    category=cat_val,
                    description=new_descs[i] if i < len(new_descs) else cat_val,
                    quantity=qty,
                    unit_cost_ugx=cost,
                    total_cost_ugx=qty * cost,
                    notes=new_notes[i] if i < len(new_notes) else "",
                )
                db.session.add(new_item)
            
            budget.recalc_totals()
            db.session.commit()
            flash("Budget updated.", "success")
            return redirect(url_for("production.budget_view", budget_id=budget_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating budget: {str(e)}", "danger")
    
    budget_items = ProductionBudgetItem.query.filter_by(budget_id=budget_id).order_by(ProductionBudgetItem.category).all()
    from sas_management.models import BudgetItemCategory
    categories = list(BudgetItemCategory)
    events = Event.query.filter(Event.status == "Confirmed").order_by(Event.event_date.desc()).all()
    return render_template("production/budget_form.html", budget=budget, budget_items=budget_items, categories=categories, events=events)


@production_bp.route("/budget/<int:budget_id>/submit", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budget_submit(budget_id):
    """Submit budget for approval."""
    budget = ProductionBudget.query.get_or_404(budget_id)
    
    if budget.status != ProductionBudgetStatus.Draft:
        flash("Only draft budgets can be submitted.", "warning")
        return redirect(url_for("production.budget_view", budget_id=budget_id))
    
    budget.status = ProductionBudgetStatus.Submitted
    budget.submitted_at = datetime.utcnow()
    db.session.commit()
    
    flash("Budget submitted for approval.", "success")
    return redirect(url_for("production.budget_view", budget_id=budget_id))


@production_bp.route("/budget/<int:budget_id>/review", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def budget_review(budget_id):
    """Review and approve/reject budget."""
    budget = ProductionBudget.query.get_or_404(budget_id)
    
    if budget.status != ProductionBudgetStatus.Submitted:
        flash("Only submitted budgets can be reviewed.", "warning")
        return redirect(url_for("production.budget_view", budget_id=budget_id))
    
    action = request.form.get("action")
    recommendations = request.form.get("admin_recommendations", "")
    
    if action == "approve":
        budget.status = ProductionBudgetStatus.Approved
    elif action == "reject":
        budget.status = ProductionBudgetStatus.Rejected
    else:
        flash("Invalid action.", "danger")
        return redirect(url_for("production.budget_view", budget_id=budget_id))
    
    budget.reviewed_by = current_user.id
    budget.reviewed_at = datetime.utcnow()
    budget.admin_recommendations = recommendations
    db.session.commit()
    
    flash(f"Budget {action}d successfully.", "success")
    return redirect(url_for("production.budget_view", budget_id=budget_id))


@production_bp.route("/budget/<int:budget_id>/update-event", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budget_update_event(budget_id):
    """Update event associated with budget."""
    budget = ProductionBudget.query.get_or_404(budget_id)
    event_id = request.form.get("event_id", type=int)
    
    if event_id:
        budget.event_id = event_id
        db.session.commit()
        flash("Budget event updated.", "success")
    
    return redirect(url_for("production.budget_view", budget_id=budget_id))


@production_bp.route("/budget/<int:budget_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.Admin)
def budget_delete(budget_id):
    """Delete a budget."""
    budget = ProductionBudget.query.get_or_404(budget_id)
    
    if budget.status not in [ProductionBudgetStatus.Draft, ProductionBudgetStatus.Rejected]:
        flash("Only draft or rejected budgets can be deleted.", "warning")
        return redirect(url_for("production.budgets_list"))
    
    db.session.delete(budget)
    db.session.commit()
    
    flash("Budget deleted.", "success")
    return redirect(url_for("production.budgets_list"))


@production_bp.route("/budget/import-file-manager")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budget_import_file_manager():
    """Open file manager to select file for budget import."""
    return render_template("production/budget_import_file_manager.html")


@production_bp.route("/budget/<int:budget_id>/add-item", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def budget_add_item(budget_id):
    """Add item to budget."""
    budget = ProductionBudget.query.get_or_404(budget_id)
    
    if budget.status != ProductionBudgetStatus.Draft:
        flash("Only draft budgets can be edited.", "warning")
        return redirect(url_for("production.budget_view", budget_id=budget_id))
    
    category = request.form.get("category", BudgetItemCategory.FoodItems.value)
    description = request.form.get("description", "")
    quantity = Decimal(request.form.get("quantity", 1))
    unit_cost = Decimal(request.form.get("unit_cost", 0))
    
    item = ProductionBudgetItem(
        budget_id=budget_id,
        category=category,
        description=description,
        quantity=quantity,
        unit_cost_ugx=unit_cost,
        total_cost_ugx=quantity * unit_cost,
    )
    db.session.add(item)
    budget.recalc_totals()
    db.session.commit()
    
    flash("Item added.", "success")
    return redirect(url_for("production.budget_view", budget_id=budget_id))


# ============================
# DAILY INVENTORY ROUTES
# ============================
from sas_management.models import ProductionInventoryItem, ProductionInventoryMovement


@production_bp.route("/inventory")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def daily_inventory_list():
    """List daily inventory items."""
    page = request.args.get("page", 1, type=int)
    per_page = 20
    
    items_query = ProductionInventoryItem.query.order_by(ProductionInventoryItem.name.asc())
    pagination = items_query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items
    
    return render_template(
        "production/daily_inventory_list.html",
        items=items,
        pagination=pagination,
    )


@production_bp.route("/inventory/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def daily_inventory_new():
    """Create new inventory item."""
    if request.method == "POST":
        try:
            item = ProductionInventoryItem(
                name=request.form.get("name"),
                category=request.form.get("category"),
                unit=request.form.get("unit"),
                current_stock=Decimal(request.form.get("current_stock", 0)),
                min_stock_level=Decimal(request.form.get("min_stock_level", 0)),
                cost_per_unit=Decimal(request.form.get("cost_per_unit", 0)),
            )
            db.session.add(item)
            db.session.commit()
            flash("Inventory item created.", "success")
            return redirect(url_for("production.daily_inventory_list"))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
    
    return render_template("production/daily_inventory_form.html")


@production_bp.route("/inventory/<int:item_id>/movement", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def daily_inventory_movement(item_id):
    """Record inventory movement."""
    item = ProductionInventoryItem.query.get_or_404(item_id)
    
    movement_type = request.form.get("type")
    quantity = Decimal(request.form.get("quantity", 0))
    notes = request.form.get("notes", "")
    
    if movement_type == "in":
        item.current_stock += quantity
    elif movement_type == "out":
        item.current_stock -= quantity
    
    movement = ProductionInventoryMovement(
        item_id=item_id,
        movement_type=movement_type,
        quantity=quantity,
        notes=notes,
        performed_by=current_user.id,
    )
    db.session.add(movement)
    db.session.commit()
    
    flash("Movement recorded.", "success")
    return redirect(url_for("production.daily_inventory_list"))


@production_bp.route("/inventory/report")
@login_required
@role_required(UserRole.Admin, UserRole.KitchenStaff)
def daily_inventory_report():
    """View inventory report."""
    items = ProductionInventoryItem.query.all()
    return render_template("production/daily_inventory_report.html", items=items)
