"""Recipe Management Service - Advanced food costing and recipe management."""
import os
from datetime import datetime
from decimal import Decimal
from flask import current_app
from werkzeug.utils import secure_filename

from sas_management.models import (
    db, RecipeAdvanced, RecipeIngredient, BatchProduction, WasteLog,
    Ingredient, Employee, User
)


def create_recipe(data, image_file=None):
    """Create a new recipe."""
    try:
        db.session.begin()
        
        if not data.get('name'):
            raise ValueError("Recipe name is required")
        
        # Handle image upload
        image_url = None
        if image_file and image_file.filename:
            upload_folder = os.path.join(current_app.instance_path, "production_uploads", "recipe_images")
            os.makedirs(upload_folder, exist_ok=True)
            
            filename = secure_filename(image_file.filename)
            timestamp = str(int(datetime.utcnow().timestamp()))
            filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
            image_url = f"production_uploads/recipe_images/{filename}"
        
        recipe = RecipeAdvanced(
            name=data['name'].strip(),
            category=data.get('category', '').strip(),
            description=data.get('description', '').strip(),
            yield_percent=float(data.get('yield_percent', 100.0)),
            base_servings=int(data.get('base_servings', 1)),
            image_url=image_url,
            status=data.get('status', 'active'),
            version=1,
            created_by=data.get('created_by')
        )
        
        db.session.add(recipe)
        db.session.commit()
        
        return {"success": True, "recipe_id": recipe.id, "recipe": recipe}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating recipe: {e}")
        return {"success": False, "error": str(e)}


def update_recipe(recipe_id, data, image_file=None):
    """Update recipe."""
    try:
        db.session.begin()
        
        recipe = db.session.get(RecipeAdvanced, recipe_id)
        if not recipe:
            raise ValueError("Recipe not found")
        
        # Update fields
        if 'name' in data:
            recipe.name = data['name'].strip()
        if 'category' in data:
            recipe.category = data['category'].strip()
        if 'description' in data:
            recipe.description = data['description'].strip()
        if 'yield_percent' in data:
            recipe.yield_percent = float(data['yield_percent'])
        if 'base_servings' in data:
            recipe.base_servings = int(data['base_servings'])
        if 'status' in data:
            recipe.status = data['status']
        
        # Handle image upload
        if image_file and image_file.filename:
            upload_folder = os.path.join(current_app.instance_path, "production_uploads", "recipe_images")
            os.makedirs(upload_folder, exist_ok=True)
            
            # Delete old image if exists
            if recipe.image_url:
                old_path = os.path.join(current_app.instance_path, recipe.image_url)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except:
                        pass
            
            filename = secure_filename(image_file.filename)
            timestamp = str(int(datetime.utcnow().timestamp()))
            filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)
            recipe.image_url = f"production_uploads/recipe_images/{filename}"
        
        recipe.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "recipe": recipe}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating recipe: {e}")
        return {"success": False, "error": str(e)}


def add_ingredient(recipe_id, inventory_item_id=None, ingredient_name=None, qty_required=None, unit=None):
    """Add ingredient to recipe."""
    try:
        db.session.begin()
        
        recipe = db.session.get(RecipeAdvanced, recipe_id)
        if not recipe:
            raise ValueError("Recipe not found")
        
        # Get ingredient name
        if inventory_item_id:
            inv_item = db.session.get(Ingredient, inventory_item_id)
            if not inv_item:
                raise ValueError("Ingredient not found")
            ingredient_name = inv_item.name
            # Set cost snapshot
            cost_snapshot = inv_item.unit_cost_ugx if hasattr(inv_item, 'unit_cost_ugx') else None
        elif not ingredient_name:
            raise ValueError("Either inventory_item_id or ingredient_name is required")
        
        ingredient = RecipeIngredient(
            recipe_id=recipe_id,
            inventory_item_id=inventory_item_id,
            ingredient_name=ingredient_name,
            qty_required=float(qty_required),
            unit=unit,
            cost_snapshot=cost_snapshot
        )
        
        db.session.add(ingredient)
        db.session.commit()
        
        return {"success": True, "ingredient_id": ingredient.id, "ingredient": ingredient}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error adding ingredient: {e}")
        return {"success": False, "error": str(e)}


def calculate_recipe_cost(recipe_id):
    """Calculate recipe cost based on current inventory prices."""
    try:
        recipe = db.session.get(RecipeAdvanced, recipe_id)
        if not recipe:
            return {"success": False, "error": "Recipe not found"}
        
        total_cost = 0.0
        ingredient_costs = []
        
        for ingredient in recipe.ingredients:
            if ingredient.inventory_item:
                unit_cost = float(ingredient.inventory_item.unit_cost_ugx) if hasattr(ingredient.inventory_item, 'unit_cost_ugx') and ingredient.inventory_item.unit_cost_ugx else float(ingredient.cost_snapshot or 0)
                cost = unit_cost * float(ingredient.qty_required)
            else:
                cost = float(ingredient.cost_snapshot or 0)
            total_cost += cost
            
            ingredient_costs.append({
                "ingredient_id": ingredient.id,
                "ingredient_name": ingredient.ingredient_name,
                "qty_required": float(ingredient.qty_required),
                "unit": ingredient.unit,
                "cost": cost
            })
        
        # Adjust for yield percentage
        adjusted_cost = total_cost / (recipe.yield_percent / 100.0) if recipe.yield_percent > 0 else total_cost
        
        # Cost per serving
        cost_per_serving = adjusted_cost / recipe.base_servings if recipe.base_servings > 0 else adjusted_cost
        
        return {
            "success": True,
            "total_cost": round(total_cost, 2),
            "adjusted_cost": round(adjusted_cost, 2),  # After yield adjustment
            "cost_per_serving": round(cost_per_serving, 2),
            "yield_percent": recipe.yield_percent,
            "base_servings": recipe.base_servings,
            "ingredient_costs": ingredient_costs
        }
    except Exception as e:
        current_app.logger.exception(f"Error calculating recipe cost: {e}")
        return {"success": False, "error": str(e)}


def record_batch_production(recipe_id, batch_size, servings_produced=None, performed_by=None, notes=None):
    """Record batch production and auto-deduct inventory."""
    try:
        db.session.begin()
        
        recipe = db.session.get(RecipeAdvanced, recipe_id)
        if not recipe:
            raise ValueError("Recipe not found")
        
        # Calculate costs
        cost_result = calculate_recipe_cost(recipe_id)
        if not cost_result['success']:
            raise ValueError(cost_result.get('error', 'Failed to calculate cost'))
        
        # Scale cost by batch size
        base_cost = cost_result['adjusted_cost']
        batch_cost = base_cost * float(batch_size)
        
        # Calculate servings produced if not provided
        if servings_produced is None:
            servings_produced = int(recipe.base_servings * batch_size)
        
        cost_per_serving = batch_cost / servings_produced if servings_produced > 0 else batch_cost
        
        # Deduct inventory (scale each ingredient by batch_size)
        for ingredient in recipe.ingredients:
            if ingredient.inventory_item:
                qty_to_deduct = ingredient.qty_required * batch_size
                # Update inventory stock
                if hasattr(ingredient.inventory_item, 'stock_count'):
                    current_stock = float(ingredient.inventory_item.stock_count or 0)
                    new_stock = max(0, current_stock - qty_to_deduct)
                    ingredient.inventory_item.stock_count = new_stock
        
        # Create batch production record
        batch = BatchProduction(
            recipe_id=recipe_id,
            batch_size=batch_size,
            servings_produced=servings_produced,
            total_cost=batch_cost,
            cost_per_serving=cost_per_serving,
            performed_by=performed_by,
            notes=notes
        )
        
        db.session.add(batch)
        db.session.commit()
        
        return {
            "success": True,
            "batch_id": batch.id,
            "batch": batch,
            "total_cost": round(batch_cost, 2),
            "cost_per_serving": round(cost_per_serving, 2)
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error recording batch production: {e}")
        return {"success": False, "error": str(e)}


def log_waste(recipe_id, ingredient_id=None, ingredient_name=None, qty_lost=None, unit=None, reason=None, logged_by=None):
    """Log waste for recipe ingredients."""
    try:
        db.session.begin()
        
        recipe = db.session.get(RecipeAdvanced, recipe_id) if recipe_id else None
        
        # Get ingredient info
        cost_lost = None
        if ingredient_id:
            inv_item = db.session.get(Ingredient, ingredient_id)
            if inv_item:
                if not ingredient_name:
                    ingredient_name = inv_item.name
                # Calculate cost
                unit_cost = float(inv_item.unit_cost_ugx) if hasattr(inv_item, 'unit_cost_ugx') and inv_item.unit_cost_ugx else 0
                cost_lost = unit_cost * float(qty_lost)
        
        waste = WasteLog(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            ingredient_name=ingredient_name,
            qty_lost=float(qty_lost),
            unit=unit,
            cost_lost=cost_lost,
            reason=reason,
            logged_by=logged_by
        )
        
        db.session.add(waste)
        db.session.commit()
        
        return {"success": True, "waste_id": waste.id, "waste": waste}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error logging waste: {e}")
        return {"success": False, "error": str(e)}


def recalc_cost_on_inventory_price_change(inventory_item_id):
    """Recalculate recipe costs when inventory item price changes."""
    try:
        # Find all recipes using this ingredient
        ingredients = RecipeIngredient.query.filter_by(inventory_item_id=inventory_item_id).all()
        
        affected_recipes = set()
        for ingredient in ingredients:
            affected_recipes.add(ingredient.recipe_id)
        
        # Update cost snapshots (optional - for audit trail)
        for ingredient in ingredients:
            inv_item = db.session.get(Ingredient, inventory_item_id)
            if inv_item and hasattr(inv_item, 'unit_cost_ugx'):
                ingredient.cost_snapshot = inv_item.unit_cost_ugx
                db.session.add(ingredient)
        
        db.session.commit()
        
        return {
            "success": True,
            "affected_recipes": list(affected_recipes),
            "count": len(affected_recipes)
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error recalculating costs: {e}")
        return {"success": False, "error": str(e)}


def get_recipe(recipe_id):
    """Get recipe by ID with full details."""
    try:
        recipe = db.session.get(RecipeAdvanced, recipe_id)
        if not recipe:
            return {"success": False, "error": "Recipe not found"}
        
        # Calculate current cost
        cost_result = calculate_recipe_cost(recipe_id)
        
        return {
            "success": True,
            "recipe": recipe,
            "costs": cost_result if cost_result['success'] else None
        }
    except Exception as e:
        current_app.logger.exception(f"Error getting recipe: {e}")
        return {"success": False, "error": str(e)}


def list_recipes(filters=None):
    """List recipes with optional filters."""
    try:
        query = RecipeAdvanced.query
        
        if filters:
            if filters.get('category'):
                query = query.filter(RecipeAdvanced.category == filters['category'])
            if filters.get('status'):
                query = query.filter(RecipeAdvanced.status == filters['status'])
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(RecipeAdvanced.name.ilike(search_term))
        
        recipes = query.order_by(RecipeAdvanced.name.asc()).all()
        
        # Calculate costs for each recipe
        recipes_with_costs = []
        for recipe in recipes:
            cost_result = calculate_recipe_cost(recipe.id)
            recipes_with_costs.append({
                "recipe": recipe,
                "cost_per_serving": cost_result.get('cost_per_serving', 0) if cost_result['success'] else 0,
                "total_cost": cost_result.get('total_cost', 0) if cost_result['success'] else 0
            })
        
        return {"success": True, "recipes": recipes_with_costs}
    except Exception as e:
        current_app.logger.exception(f"Error listing recipes: {e}")
        return {"success": False, "error": str(e), "recipes": []}

