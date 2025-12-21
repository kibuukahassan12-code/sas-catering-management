"""Production Recipes Blueprint - Advanced food costing and recipe management."""
from datetime import datetime
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for, jsonify, send_file
from flask_login import current_user, login_required

from sas_management.models import (
    db, RecipeAdvanced, RecipeIngredient, BatchProduction, WasteLog,
    Ingredient, Employee, User, UserRole
)
from sas_management.utils import role_required
from sas_management.services.recipe_service import (
    create_recipe, update_recipe, add_ingredient, calculate_recipe_cost,
    record_batch_production, log_waste, get_recipe, list_recipes
)

recipes_bp = Blueprint("recipes", __name__, url_prefix="/production/recipes")

@recipes_bp.route("/dashboard")
@login_required
def dashboard():
    """Recipe dashboard with KPIs."""
    try:
        from sqlalchemy import func
        
        total_recipes = RecipeAdvanced.query.filter_by(status='active').count()
        total_ingredients = RecipeIngredient.query.count()
        total_batches = BatchProduction.query.count()
        
        # Calculate total waste cost
        total_waste_cost = db.session.query(func.sum(WasteLog.cost_lost)).scalar() or 0
        
        # Recent recipes
        recent_recipes = RecipeAdvanced.query.order_by(RecipeAdvanced.created_at.desc()).limit(5).all()
        
        # Recipes with high costs
        recipes_with_costs = []
        for recipe in RecipeAdvanced.query.filter_by(status='active').limit(10).all():
            cost_result = calculate_recipe_cost(recipe.id)
            if cost_result['success']:
                recipes_with_costs.append({
                    'recipe': recipe,
                    'cost_per_serving': cost_result['cost_per_serving']
                })
        
        # Sort by cost
        recipes_with_costs.sort(key=lambda x: x['cost_per_serving'], reverse=True)
        
        CURRENCY = current_app.config.get('CURRENCY_PREFIX', 'UGX ')
        return render_template("production_recipes/recipe_dashboard.html",
            total_recipes=total_recipes,
            total_ingredients=total_ingredients,
            total_batches=total_batches,
            total_waste_cost=float(total_waste_cost),
            recent_recipes=recent_recipes,
            high_cost_recipes=recipes_with_costs[:5],
            CURRENCY=CURRENCY
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading recipe dashboard: {e}")
        return render_template("production_recipes/recipe_dashboard.html",
            total_recipes=0,
            total_ingredients=0,
            total_batches=0,
            total_waste_cost=0,
            recent_recipes=[],
            high_cost_recipes=[]
        )

@recipes_bp.route("")
@login_required
def recipe_list():
    """List all recipes."""
    try:
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '')
        status = request.args.get('status', 'active')
        
        filters = {}
        if search:
            filters['search'] = search
        if category:
            filters['category'] = category
        if status:
            filters['status'] = status
        
        result = list_recipes(filters)
        recipes_data = result.get('recipes', [])
        
        # Get unique categories
        categories = db.session.query(RecipeAdvanced.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        return render_template("production_recipes/recipe_list.html",
            recipes_data=recipes_data,
            categories=categories,
            search=search,
            category=category,
            status=status
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading recipe list: {e}")
        return render_template("production_recipes/recipe_list.html",
            recipes_data=[],
            categories=[],
            search="",
            category="",
            status="active"
        )

@recipes_bp.route("/new")
@login_required
def recipe_new():
    """New recipe form."""
    try:
        # Get categories
        categories = db.session.query(RecipeAdvanced.category).distinct().all()
        categories = [c[0] for c in categories if c[0]]
        
        # Get available ingredients
        ingredients = Ingredient.query.order_by(Ingredient.name.asc()).all()
        
        return render_template("production_recipes/recipe_form.html",
            recipe=None,
            categories=categories,
            ingredients=ingredients,
            mode='create'
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading recipe form: {e}")
        return redirect(url_for("recipes.recipe_list"))

@recipes_bp.route("/<int:recipe_id>")
@login_required
def recipe_view(recipe_id):
    """View recipe details."""
    try:
        result = get_recipe(recipe_id)
        if not result['success']:
            flash(result.get('error', 'Recipe not found'), "danger")
            return redirect(url_for("recipes.recipe_list"))
        
        recipe = result['recipe']
        costs = result.get('costs')
        
        # Get batches
        batches = BatchProduction.query.filter_by(recipe_id=recipe_id).order_by(BatchProduction.date.desc()).limit(10).all()
        
        # Get waste logs
        waste_logs = WasteLog.query.filter_by(recipe_id=recipe_id).order_by(WasteLog.timestamp.desc()).limit(10).all()
        
        # Get available ingredients for adding
        ingredients = Ingredient.query.order_by(Ingredient.name.asc()).all()
        
        return render_template("production_recipes/recipe_view.html",
            recipe=recipe,
            costs=costs,
            batches=batches,
            waste_logs=waste_logs,
            ingredients=ingredients
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading recipe view: {e}")
        return redirect(url_for("recipes.recipe_list"))

@recipes_bp.route("/<int:recipe_id>/batch")
@login_required
def batch_costing(recipe_id):
    """Batch costing calculator."""
    try:
        recipe = RecipeAdvanced.query.get_or_404(recipe_id)
        
        # Calculate base cost
        cost_result = calculate_recipe_cost(recipe_id)
        
        # Get recent batches
        batches = BatchProduction.query.filter_by(recipe_id=recipe_id).order_by(BatchProduction.date.desc()).limit(10).all()
        
        # Get employees for assignment
        employees = Employee.query.filter_by(status='active').all()
        
        return render_template("production_recipes/batch_costing.html",
            recipe=recipe,
            cost_result=cost_result,
            batches=batches,
            employees=employees
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading batch costing: {e}")
        return redirect(url_for("recipes.recipe_view", recipe_id=recipe_id))

@recipes_bp.route("/<int:recipe_id>/waste")
@login_required
def waste_log_page(recipe_id):
    """Waste logging page."""
    try:
        recipe = RecipeAdvanced.query.get_or_404(recipe_id)
        
        # Get waste logs
        waste_logs = WasteLog.query.filter_by(recipe_id=recipe_id).order_by(WasteLog.timestamp.desc()).all()
        
        # Get ingredients
        ingredients = Ingredient.query.order_by(Ingredient.name.asc()).all()
        
        # Calculate total waste cost
        from sqlalchemy import func
        total_waste = db.session.query(func.sum(WasteLog.cost_lost)).filter_by(recipe_id=recipe_id).scalar() or 0
        
        return render_template("production_recipes/waste_log.html",
            recipe=recipe,
            waste_logs=waste_logs,
            ingredients=ingredients,
            total_waste=float(total_waste)
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading waste log: {e}")
        return redirect(url_for("recipes.recipe_view", recipe_id=recipe_id))

# ============================
# FORM SUBMISSIONS
# ============================

@recipes_bp.route("/create", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def recipe_create():
    """Create new recipe."""
    try:
        data = request.form.to_dict()
        data['created_by'] = current_user.id
        
        # Handle image upload
        image_file = request.files.get('image')
        
        result = create_recipe(data, image_file)
        
        if result['success']:
            flash(f"Recipe '{result['recipe'].name}' created successfully!", "success")
            return redirect(url_for("recipes.recipe_view", recipe_id=result['recipe_id']))
        else:
            flash(result.get('error', 'Failed to create recipe'), "danger")
            return redirect(url_for("recipes.recipe_new"))
    except Exception as e:
        current_app.logger.exception(f"Error creating recipe: {e}")
        return redirect(url_for("recipes.recipe_new"))

@recipes_bp.route("/<int:recipe_id>/ingredient/add", methods=["POST"])
@login_required
def ingredient_add(recipe_id):
    """Add ingredient to recipe."""
    try:
        inventory_item_id = request.form.get('ingredient_id', type=int)
        ingredient_name = request.form.get('ingredient_name', '').strip()
        qty_required = request.form.get('qty_required')
        unit = request.form.get('unit', 'g')
        
        result = add_ingredient(
            recipe_id=recipe_id,
            inventory_item_id=inventory_item_id if inventory_item_id else None,
            ingredient_name=ingredient_name,
            qty_required=qty_required,
            unit=unit
        )
        
        if result['success']:
            flash("Ingredient added successfully!", "success")
        else:
            flash(result.get('error', 'Failed to add ingredient'), "danger")
        
        return redirect(url_for("recipes.recipe_view", recipe_id=recipe_id))
    except Exception as e:
        current_app.logger.exception(f"Error adding ingredient: {e}")
        return redirect(url_for("recipes.recipe_view", recipe_id=recipe_id))

@recipes_bp.route("/<int:recipe_id>/batch/run", methods=["POST"])
@login_required
def batch_run(recipe_id):
    """Record batch production."""
    try:
        batch_size = float(request.form.get('batch_size', 1))
        servings_produced = request.form.get('servings_produced', type=int)
        performed_by = request.form.get('performed_by', type=int)
        notes = request.form.get('notes', '').strip()
        
        result = record_batch_production(
            recipe_id=recipe_id,
            batch_size=batch_size,
            servings_produced=servings_produced,
            performed_by=performed_by,
            notes=notes
        )
        
        if result['success']:
            flash(f"Batch production recorded! Total cost: {result['total_cost']} UGX", "success")
        else:
            flash(result.get('error', 'Failed to record batch'), "danger")
        
        return redirect(url_for("recipes.batch_costing", recipe_id=recipe_id))
    except Exception as e:
        current_app.logger.exception(f"Error recording batch: {e}")
        return redirect(url_for("recipes.batch_costing", recipe_id=recipe_id))

@recipes_bp.route("/<int:recipe_id>/waste/log", methods=["POST"])
@login_required
def waste_log_submit(recipe_id):
    """Log waste."""
    try:
        ingredient_id = request.form.get('ingredient_id', type=int)
        ingredient_name = request.form.get('ingredient_name', '').strip()
        qty_lost = float(request.form.get('qty_lost', 0))
        unit = request.form.get('unit', 'g')
        reason = request.form.get('reason', '').strip()
        
        result = log_waste(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id if ingredient_id else None,
            ingredient_name=ingredient_name,
            qty_lost=qty_lost,
            unit=unit,
            reason=reason,
            logged_by=current_user.id
        )
        
        if result['success']:
            flash("Waste logged successfully!", "success")
        else:
            flash(result.get('error', 'Failed to log waste'), "danger")
        
        return redirect(url_for("recipes.waste_log_page", recipe_id=recipe_id))
    except Exception as e:
        current_app.logger.exception(f"Error logging waste: {e}")
        return redirect(url_for("recipes.waste_log_page", recipe_id=recipe_id))

# ============================
# REST API ENDPOINTS
# ============================

@recipes_bp.route("/api/recipes", methods=["GET"])
@login_required
def api_list_recipes():
    """API: List recipes."""
    try:
        filters = {}
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        result = list_recipes(filters)
        
        if result['success']:
            return jsonify({
                "success": True,
                "recipes": [{
                    "id": r['recipe'].id,
                    "name": r['recipe'].name,
                    "category": r['recipe'].category,
                    "cost_per_serving": r['cost_per_serving'],
                    "total_cost": r['total_cost']
                } for r in result['recipes']]
            }), 200
        else:
            return jsonify({"success": False, "error": result.get('error')}), 500
    except Exception as e:
        current_app.logger.exception(f"Error in API list recipes: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@recipes_bp.route("/api/recipes/<int:recipe_id>", methods=["GET"])
@login_required
def api_get_recipe(recipe_id):
    """API: Get recipe details."""
    try:
        result = get_recipe(recipe_id)
        
        if result['success']:
            recipe = result['recipe']
            return jsonify({
                "success": True,
                "recipe": {
                    "id": recipe.id,
                    "name": recipe.name,
                    "category": recipe.category,
                    "description": recipe.description,
                    "yield_percent": recipe.yield_percent,
                    "base_servings": recipe.base_servings,
                    "image_url": recipe.image_url,
                    "costs": result.get('costs')
                }
            }), 200
        else:
            return jsonify({"success": False, "error": result.get('error')}), 404
    except Exception as e:
        current_app.logger.exception(f"Error in API get recipe: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@recipes_bp.route("/api/recipes", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_create_recipe():
    """API: Create recipe."""
    try:
        if request.is_json:
            data = request.get_json()
            image_file = None
        else:
            data = request.form.to_dict()
            image_file = request.files.get('image')
        
        data['created_by'] = current_user.id
        result = create_recipe(data, image_file)
        
        if result['success']:
            return jsonify({
                "success": True,
                "recipe_id": result['recipe_id'],
                "message": "Recipe created successfully"
            }), 201
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error in API create recipe: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@recipes_bp.route("/api/recipes/<int:recipe_id>/ingredients", methods=["POST"])
@login_required
def api_add_ingredient(recipe_id):
    """API: Add ingredient to recipe."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        result = add_ingredient(
            recipe_id=recipe_id,
            inventory_item_id=data.get('ingredient_id'),
            ingredient_name=data.get('ingredient_name'),
            qty_required=data.get('qty_required'),
            unit=data.get('unit', 'g')
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "ingredient_id": result['ingredient_id'],
                "message": "Ingredient added successfully"
            }), 201
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error in API add ingredient: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@recipes_bp.route("/api/recipes/<int:recipe_id>/batch", methods=["POST"])
@login_required
def api_record_batch(recipe_id):
    """API: Record batch production."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        result = record_batch_production(
            recipe_id=recipe_id,
            batch_size=float(data.get('batch_size', 1)),
            servings_produced=data.get('servings_produced'),
            performed_by=data.get('performed_by'),
            notes=data.get('notes', '')
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "batch_id": result['batch_id'],
                "total_cost": result['total_cost'],
                "cost_per_serving": result['cost_per_serving'],
                "message": "Batch production recorded successfully"
            }), 201
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error in API record batch: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@recipes_bp.route("/api/recipes/<int:recipe_id>/waste", methods=["POST"])
@login_required
def api_log_waste(recipe_id):
    """API: Log waste."""
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400
        
        data = request.get_json()
        result = log_waste(
            recipe_id=recipe_id,
            ingredient_id=data.get('ingredient_id'),
            ingredient_name=data.get('ingredient_name'),
            qty_lost=float(data.get('qty_lost', 0)),
            unit=data.get('unit', 'g'),
            reason=data.get('reason', ''),
            logged_by=current_user.id
        )
        
        if result['success']:
            return jsonify({
                "success": True,
                "waste_id": result['waste_id'],
                "message": "Waste logged successfully"
            }), 201
        else:
            return jsonify({"success": False, "error": result.get('error')}), 400
    except Exception as e:
        current_app.logger.exception(f"Error in API log waste: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

