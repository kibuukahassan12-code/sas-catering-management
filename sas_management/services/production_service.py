"""Production service layer for business logic."""
import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from sas_management.models import (
    Event,
    Ingredient,
    ProductionLineItem,
    ProductionOrder,
    Recipe,
    db,
)


def generate_production_reference():
    """Generate a unique production order reference."""
    prefix = "PROD"
    timestamp = datetime.now().strftime("%Y%m%d")
    last_order = (
        ProductionOrder.query.filter(ProductionOrder.reference.like(f"{prefix}-{timestamp}-%"))
        .order_by(ProductionOrder.id.desc())
        .first()
    )
    if last_order and last_order.reference:
        try:
            last_num = int(last_order.reference.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    return f"{prefix}-{timestamp}-{new_num:04d}"


def create_production_order(event_id, items, schedule_times):
    """
    Create a production order with line items.
    
    Args:
        event_id: Optional event ID to link
        items: List of dicts with 'recipe_id', 'portions', 'recipe_name'
        schedule_times: Dict with 'prep', 'cook', 'pack', 'load' datetime strings
    
    Returns:
        ProductionOrder instance
    """
    try:
        reference = generate_production_reference()
        
        # Parse schedule times
        def parse_datetime(dt_str):
            if not dt_str:
                return None
            try:
                # Handle both ISO format and HTML datetime-local format
                if 'T' in dt_str:
                    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                else:
                    return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M')
            except (ValueError, AttributeError):
                return None
        
        scheduled_prep = parse_datetime(schedule_times.get("prep")) or datetime.now()
        scheduled_cook = parse_datetime(schedule_times.get("cook"))
        scheduled_pack = parse_datetime(schedule_times.get("pack"))
        scheduled_load = parse_datetime(schedule_times.get("load"))
        
        order = ProductionOrder(
            event_id=event_id,
            reference=reference,
            scheduled_prep=scheduled_prep,
            scheduled_cook=scheduled_cook,
            scheduled_pack=scheduled_pack,
            scheduled_load=scheduled_load,
            status="Planned",
        )
        db.session.add(order)
        db.session.flush()
        
        total_portions = 0
        total_cost = Decimal("0.00")
        
        for item in items:
            recipe = db.session.get(Recipe, item["recipe_id"])
            if not recipe:
                raise ValueError(f"Recipe {item['recipe_id']} not found")
            
            portions = item.get("portions", 0)
            line_item = ProductionLineItem(
                order_id=order.id,
                recipe_id=item["recipe_id"],
                recipe_name=item.get("recipe_name", recipe.name),
                portions=portions,
                unit=item.get("unit", "portion"),
                status="Pending",
            )
            db.session.add(line_item)
            
            total_portions += portions
            cost = Decimal(recipe.cost_per_portion or 0) * portions
            total_cost += cost
        
        order.total_portions = total_portions
        order.total_cost = total_cost
        db.session.commit()
        return order
        
    except Exception as e:
        db.session.rollback()
        raise


def scale_recipe(recipe_id, guest_count):
    """
    Scale recipe ingredients for a given guest count.
    
    Args:
        recipe_id: Recipe ID
        guest_count: Number of guests/portions needed
    
    Returns:
        Dict mapping ingredient_id to required quantity
    """
    recipe = Recipe.query.get_or_404(recipe_id)
    
    try:
        ingredients_data = json.loads(recipe.ingredients) if isinstance(recipe.ingredients, str) else recipe.ingredients
    except (json.JSONDecodeError, TypeError):
        ingredients_data = []
    
    scale_factor = guest_count / recipe.portions if recipe.portions > 0 else 1
    
    scaled_ingredients = {}
    for ing in ingredients_data:
        ingredient_id = ing.get("ingredient_id")
        qty_per_portion = Decimal(str(ing.get("qty_per_portion", 0)))
        required_qty = qty_per_portion * scale_factor
        scaled_ingredients[ingredient_id] = float(required_qty)
    
    return scaled_ingredients


def reserve_ingredients(ingredients_map):
    """
    Reserve ingredients from inventory (decrement stock).
    
    Args:
        ingredients_map: Dict mapping ingredient_id to quantity needed
    
    Returns:
        List of reserved items
    """
    try:
        reserved = []
        
        for ingredient_id, qty_needed in ingredients_map.items():
            ingredient = db.session.get(Ingredient, ingredient_id)
            if not ingredient:
                raise ValueError(f"Ingredient {ingredient_id} not found")
            
            qty_decimal = Decimal(str(qty_needed))
            if ingredient.stock_count < qty_decimal:
                raise ValueError(
                    f"Insufficient stock for {ingredient.name}. Available: {ingredient.stock_count}, needed: {qty_decimal}"
                )
            
            ingredient.stock_count -= qty_decimal
            reserved.append({"ingredient_id": ingredient_id, "quantity": float(qty_decimal)})
        
        db.session.commit()
        return reserved
        
    except Exception as e:
        db.session.rollback()
        raise


def release_reservations(order_id):
    """
    Release reserved ingredients back to inventory.
    
    Args:
        order_id: Production order ID
    """
    try:
        order = ProductionOrder.query.get_or_404(order_id)
        
        # Get all recipes from line items
        for line_item in order.items:
            recipe = db.session.get(Recipe, line_item.recipe_id)
            if recipe:
                try:
                    ingredients_data = json.loads(recipe.ingredients) if isinstance(recipe.ingredients, str) else recipe.ingredients
                except (json.JSONDecodeError, TypeError):
                    ingredients_data = []
                
                scale_factor = line_item.portions / recipe.portions if recipe.portions > 0 else 1
                
                for ing in ingredients_data:
                    ingredient_id = ing.get("ingredient_id")
                    qty_per_portion = Decimal(str(ing.get("qty_per_portion", 0)))
                    qty_to_restore = qty_per_portion * scale_factor
                    
                    ingredient = db.session.get(Ingredient, ingredient_id)
                    if ingredient:
                        ingredient.stock_count += qty_to_restore
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        raise


def compute_cogs_for_order(order_id):
    """
    Compute total cost of goods for a production order.
    
    Args:
        order_id: Production order ID
    
    Returns:
        Total COGS as Decimal
    """
    order = ProductionOrder.query.get_or_404(order_id)
    total_cogs = Decimal("0.00")
    
    for line_item in order.items:
        recipe = db.session.get(Recipe, line_item.recipe_id)
        if recipe:
            try:
                ingredients_data = json.loads(recipe.ingredients) if isinstance(recipe.ingredients, str) else recipe.ingredients
            except (json.JSONDecodeError, TypeError):
                ingredients_data = []
            
            scale_factor = line_item.portions / recipe.portions if recipe.portions > 0 else 1
            
            for ing in ingredients_data:
                ingredient_id = ing.get("ingredient_id")
                qty_per_portion = Decimal(str(ing.get("qty_per_portion", 0)))
                unit_cost = Decimal(str(ing.get("unit_cost", 0)))
                total_qty = qty_per_portion * scale_factor
                total_cogs += total_qty * unit_cost
    
    return total_cogs


def generate_production_sheet(order_id):
    """
    Generate production sheet data for an order.
    
    Args:
        order_id: Production order ID
    
    Returns:
        Dict with production sheet data
    """
    order = ProductionOrder.query.get_or_404(order_id)
    
    line_items_data = []
    all_ingredients = {}
    
    for line_item in order.items:
        recipe = db.session.get(Recipe, line_item.recipe_id)
        if recipe:
            try:
                ingredients_data = json.loads(recipe.ingredients) if isinstance(recipe.ingredients, str) else recipe.ingredients
            except (json.JSONDecodeError, TypeError):
                ingredients_data = []
            
            scale_factor = line_item.portions / recipe.portions if recipe.portions > 0 else 1
            
            recipe_ingredients = []
            for ing in ingredients_data:
                ingredient_id = ing.get("ingredient_id")
                ingredient = db.session.get(Ingredient, ingredient_id)
                if ingredient:
                    qty_per_portion = Decimal(str(ing.get("qty_per_portion", 0)))
                    unit = ing.get("unit", ingredient.unit_of_measure)
                    total_qty = qty_per_portion * scale_factor
                    
                    recipe_ingredients.append({
                        "name": ingredient.name,
                        "quantity": float(total_qty),
                        "unit": unit,
                    })
                    
                    # Aggregate for total shopping list
                    key = f"{ingredient.name}_{unit}"
                    if key not in all_ingredients:
                        all_ingredients[key] = {"name": ingredient.name, "quantity": 0, "unit": unit}
                    all_ingredients[key]["quantity"] += float(total_qty)
            
            line_items_data.append({
                "recipe_name": line_item.recipe_name,
                "portions": line_item.portions,
                "prep_time": recipe.prep_time_mins,
                "cook_time": recipe.cook_time_mins,
                "ingredients": recipe_ingredients,
                "status": line_item.status,
            })
    
    return {
        "order": {
            "id": order.id,
            "reference": order.reference,
            "event_id": order.event_id,
            "event_name": order.event.event_name if order.event else None,
            "scheduled_prep": order.scheduled_prep.isoformat() if order.scheduled_prep else None,
            "scheduled_cook": order.scheduled_cook.isoformat() if order.scheduled_cook else None,
            "scheduled_pack": order.scheduled_pack.isoformat() if order.scheduled_pack else None,
            "scheduled_load": order.scheduled_load.isoformat() if order.scheduled_load else None,
            "status": order.status,
            "total_portions": order.total_portions,
            "assigned_team": order.assigned_team,
            "notes": order.notes,
        },
        "line_items": line_items_data,
        "shopping_list": list(all_ingredients.values()),
        "total_cogs": float(compute_cogs_for_order(order_id)),
    }

