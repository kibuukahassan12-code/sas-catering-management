"""Seed Recipe Management sample data."""
from app import create_app
from models import db, RecipeAdvanced, RecipeIngredient, Ingredient
from datetime import datetime
import os
import shutil

def seed_recipe_data():
    """Seed recipe sample data."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if sample recipe already exists
            existing = RecipeAdvanced.query.filter_by(name="Vanilla Sponge Base").first()
            if existing:
                print("✓ Sample recipe already exists")
                return
            
            # Get or create ingredients
            ingredients_data = [
                {"name": "Flour", "unit_of_measure": "kg", "stock_count": 100.0, "unit_cost_ugx": 5000},
                {"name": "Sugar", "unit_of_measure": "kg", "stock_count": 50.0, "unit_cost_ugx": 6000},
                {"name": "Eggs", "unit_of_measure": "pcs", "stock_count": 500.0, "unit_cost_ugx": 500},
                {"name": "Butter", "unit_of_measure": "kg", "stock_count": 30.0, "unit_cost_ugx": 12000},
            ]
            
            ingredient_objs = {}
            for ing_data in ingredients_data:
                existing_ing = Ingredient.query.filter_by(name=ing_data["name"]).first()
                if existing_ing:
                    ingredient_objs[ing_data["name"]] = existing_ing
                else:
                    ing = Ingredient(**ing_data)
                    db.session.add(ing)
                    ingredient_objs[ing_data["name"]] = ing
            
            db.session.commit()
            
            # Copy sample image
            sample_photo_source = "/mnt/data/drwa.JPG"
            upload_folder = os.path.join(app.instance_path, "production_uploads", "recipe_images")
            os.makedirs(upload_folder, exist_ok=True)
            sample_photo_dest = os.path.join(upload_folder, "sample_ing.jpg")
            
            photo_url = None
            if os.path.exists(sample_photo_source):
                try:
                    shutil.copy2(sample_photo_source, sample_photo_dest)
                    photo_url = "production_uploads/recipe_images/sample_ing.jpg"
                    print(f"✓ Copied sample image to {photo_url}")
                except Exception as e:
                    print(f"⚠️  Could not copy sample photo: {e}")
                    # Create placeholder
                    photo_url = "production_uploads/recipe_images/sample_ing.jpg"
            else:
                print(f"⚠️  Sample image not found at {sample_photo_source}")
                # Use placeholder path anyway
                photo_url = "production_uploads/recipe_images/sample_ing.jpg"
            
            # Create recipe
            recipe = RecipeAdvanced(
                name="Vanilla Sponge Base",
                category="bakery",
                description="Classic vanilla sponge cake base recipe. Perfect for layer cakes and cupcakes.",
                yield_percent=92.0,  # 8% loss during baking/prep
                base_servings=8,
                image_url=photo_url,
                status="active",
                version=1
            )
            
            db.session.add(recipe)
            db.session.flush()  # Get recipe.id
            
            # Add ingredients
            recipe_ingredients = [
                {"ingredient": ingredient_objs["Flour"], "qty": 500, "unit": "g"},
                {"ingredient": ingredient_objs["Sugar"], "qty": 200, "unit": "g"},
                {"ingredient": ingredient_objs["Eggs"], "qty": 4, "unit": "pcs"},
                {"ingredient": ingredient_objs["Butter"], "qty": 150, "unit": "g"},
            ]
            
            for ing_data in recipe_ingredients:
                ing = ing_data["ingredient"]
                ri = RecipeIngredient(
                    recipe_id=recipe.id,
                    inventory_item_id=ing.id,
                    ingredient_name=ing.name,
                    qty_required=ing_data["qty"],
                    unit=ing_data["unit"],
                    cost_snapshot=ing.unit_cost_ugx
                )
                db.session.add(ri)
            
            db.session.commit()
            
            print(f"✓ Created sample recipe: {recipe.name}")
            print(f"  - Category: {recipe.category}")
            print(f"  - Yield: {recipe.yield_percent}%")
            print(f"  - Servings: {recipe.base_servings}")
            print(f"  - Ingredients: {len(recipe_ingredients)}")
            
            # Calculate and display cost
            from services.recipe_service import calculate_recipe_cost
            cost_result = calculate_recipe_cost(recipe.id)
            if cost_result['success']:
                print(f"  - Total Cost: {cost_result['total_cost']} UGX")
                print(f"  - Cost per Serving: {cost_result['cost_per_serving']} UGX")
            
            print("✓ Recipe sample data seeded successfully")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error seeding recipe data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    seed_recipe_data()

