"""Menu Builder Service - Business logic for menu engineering and package building."""
import os
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from models import db, MenuCategory, MenuItem, MenuPackage
# MenuPackageItem removed - using JSON items field in MenuPackage instead
from decimal import Decimal

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def get_upload_folder():
    """Get the upload folder for menu images."""
    upload_folder = os.path.join(current_app.instance_path, 'premium_assets', 'menu_images')
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder


# ============================
# CATEGORIES
# ============================

def create_category(name, description=None):
    """Create a menu category."""
    try:
        # Check if category already exists
        existing = MenuCategory.query.filter_by(name=name.strip()).first()
        if existing:
            return {"success": False, "error": "Category already exists"}
        
        category = MenuCategory(
            name=name.strip(),
            description=description.strip() if description else None
        )
        
        db.session.add(category)
        db.session.commit()
        db.session.refresh(category)
        
        return {"success": True, "category": category}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating category: {e}")
        return {"success": False, "error": str(e)}


def list_categories():
    """List all menu categories."""
    try:
        categories = MenuCategory.query.order_by(MenuCategory.name.asc()).all()
        return {"success": True, "categories": categories}
    except Exception as e:
        current_app.logger.exception(f"Error listing categories: {e}")
        return {"success": False, "error": str(e), "categories": []}


# ============================
# MENU ITEMS
# ============================

def calculate_margin(cost, price):
    """Calculate margin percentage."""
    if not price or price == 0:
        return 0
    if not cost:
        cost = 0
    margin = ((float(price) - float(cost)) / float(price)) * 100
    return round(margin, 2)


def create_menu_item(data, image_file=None):
    """Create a new menu item."""
    try:
        cost = Decimal(str(data.get('cost_per_portion', 0)))
        price = Decimal(str(data.get('selling_price', 0)))
        margin = calculate_margin(cost, price)
        
        menu_item = MenuItem(
            name=data.get('name', '').strip(),
            category_id=data.get('category_id', type=int),
            description=data.get('description', '').strip() or None,
            cost_per_portion=cost,
            selling_price=price,
            margin_percent=margin,
            status=data.get('status', 'Active')
        )
        
        # Handle image upload
        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(f"menu_item_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{image_file.filename}")
            upload_folder = get_upload_folder()
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            menu_item.image_url = f"premium_assets/menu_images/{filename}"
        
        db.session.add(menu_item)
        db.session.commit()
        db.session.refresh(menu_item)
        
        return {"success": True, "menu_item": menu_item}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating menu item: {e}")
        return {"success": False, "error": str(e)}


def update_menu_item(item_id, data, image_file=None):
    """Update a menu item."""
    try:
        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            return {"success": False, "error": "Menu item not found"}
        
        # Update fields
        if 'name' in data:
            menu_item.name = data['name'].strip()
        if 'category_id' in data:
            menu_item.category_id = data['category_id']
        if 'description' in data:
            menu_item.description = data['description'].strip() or None
        if 'cost_per_portion' in data:
            menu_item.cost_per_portion = Decimal(str(data['cost_per_portion']))
        if 'selling_price' in data:
            menu_item.selling_price = Decimal(str(data['selling_price']))
        if 'status' in data:
            menu_item.status = data['status']
        
        # Recalculate margin
        menu_item.margin_percent = calculate_margin(menu_item.cost_per_portion, menu_item.selling_price)
        
        # Handle image upload
        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(f"menu_item_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{image_file.filename}")
            upload_folder = get_upload_folder()
            image_path = os.path.join(upload_folder, filename)
            image_file.save(image_path)
            menu_item.image_url = f"premium_assets/menu_images/{filename}"
        
        menu_item.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {"success": True, "menu_item": menu_item}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error updating menu item: {e}")
        return {"success": False, "error": str(e)}


def get_menu_item(item_id):
    """Get a specific menu item."""
    try:
        menu_item = MenuItem.query.get(item_id)
        if not menu_item:
            return {"success": False, "error": "Menu item not found"}
        return {"success": True, "menu_item": menu_item}
    except Exception as e:
        current_app.logger.exception(f"Error getting menu item: {e}")
        return {"success": False, "error": str(e)}


def list_menu_items(category_id=None, status=None):
    """List menu items."""
    try:
        query = MenuItem.query
        if category_id:
            query = query.filter_by(category_id=category_id)
        if status:
            query = query.filter_by(status=status)
        items = query.order_by(MenuItem.name.asc()).all()
        return {"success": True, "items": items}
    except Exception as e:
        current_app.logger.exception(f"Error listing menu items: {e}")
        return {"success": False, "error": str(e), "items": []}


# ============================
# MENU PACKAGES
# ============================

def create_menu_package(data):
    """Create a menu package."""
    try:
        package = MenuPackage(
            name=data.get('name', '').strip(),
            category=data.get('category', '').strip() or None,
            description=data.get('description', '').strip() or None,
            total_price=Decimal(str(data.get('total_price', 0))),
            status=data.get('status', 'Active')
        )
        
        db.session.add(package)
        db.session.commit()
        db.session.refresh(package)
        
        return {"success": True, "package": package}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error creating menu package: {e}")
        return {"success": False, "error": str(e)}


def attach_item_to_package(package_id, item_id, quantity=1, notes=None):
    """Add an item to a package - UPDATED to use JSON items field."""
    try:
        package = MenuPackage.query.get(package_id)
        menu_item = MenuItem.query.get(item_id)
        
        if not package or not menu_item:
            return {"success": False, "error": "Package or item not found"}
        
        # Use JSON items field instead of MenuPackageItem relationship
        items = package.items if package.items else []
        
        # Check if item already in package
        item_dict = {"id": item_id, "name": menu_item.name, "quantity": quantity}
        if notes:
            item_dict["notes"] = notes.strip()
        
        # Add or update item in JSON list
        found = False
        for i, existing_item in enumerate(items):
            if existing_item.get("id") == item_id:
                items[i]["quantity"] = items[i].get("quantity", 0) + quantity
                if notes:
                    items[i]["notes"] = notes.strip()
                found = True
                break
        
        if not found:
            items.append(item_dict)
        
        package.items = items
        db.session.commit()
        
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error attaching item to package: {e}")
        return {"success": False, "error": str(e)}


def recalculate_package_totals(package_id):
    """Recalculate package total cost and margin - UPDATED to use JSON items."""
    try:
        package = MenuPackage.query.get(package_id)
        if not package:
            return
        
        # Use JSON items field instead of MenuPackageItem relationship
        items = package.items if package.items else []
        total_cost = Decimal(0)
        
        for item_data in items:
            item_id = item_data.get("id")
            quantity = item_data.get("quantity", 1)
            menu_item = MenuItem.query.get(item_id)
            if menu_item and hasattr(menu_item, 'cost_per_portion'):
                item_cost = menu_item.cost_per_portion * quantity
                total_cost += item_cost
        
        # Note: MenuPackage now uses price_per_guest instead of total_price
        # This function may need further updates based on menu_builder requirements
        package.updated_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        current_app.logger.exception(f"Error recalculating package totals: {e}")
        db.session.rollback()


def get_menu_package(package_id):
    """Get a specific menu package with items."""
    try:
        package = MenuPackage.query.get(package_id)
        if not package:
            return {"success": False, "error": "Package not found"}
        return {"success": True, "package": package}
    except Exception as e:
        current_app.logger.exception(f"Error getting menu package: {e}")
        return {"success": False, "error": str(e)}


def list_menu_packages(category=None):
    """List menu packages."""
    try:
        query = MenuPackage.query
        if category:
            query = query.filter_by(category=category)
        packages = query.order_by(MenuPackage.name.asc()).all()
        return {"success": True, "packages": packages}
    except Exception as e:
        current_app.logger.exception(f"Error listing menu packages: {e}")
        return {"success": False, "error": str(e), "packages": []}


def remove_item_from_package(package_id, item_id):
    """Remove an item from a package - UPDATED to use JSON items field."""
    try:
        package = MenuPackage.query.get(package_id)
        if not package:
            return {"success": False, "error": "Package not found"}
        
        # Use JSON items field instead of MenuPackageItem relationship
        items = package.items if package.items else []
        original_count = len(items)
        items = [item for item in items if item.get("id") != item_id]
        
        if len(items) == original_count:
            return {"success": False, "error": "Item not found in package"}
        
        package.items = items
        
        # Recalculate package totals
        recalculate_package_totals(package_id)
        
        db.session.commit()
        return {"success": True}
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error removing item from package: {e}")
        return {"success": False, "error": str(e)}

