"""Menu Builder Blueprint - Menu engineering and package building."""
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for, send_from_directory
from flask_login import current_user, login_required
from decimal import Decimal

from models import db, MenuCategory, MenuItem, MenuPackage, UserRole
from utils import role_required
from services.menu_builder_service import (
    create_category, list_categories,
    create_menu_item, update_menu_item, get_menu_item, list_menu_items,
    create_menu_package, attach_item_to_package, get_menu_package,
    list_menu_packages, remove_item_from_package, recalculate_package_totals,
    get_upload_folder
)

menu_builder_bp = Blueprint("menu_builder", __name__, url_prefix="/menu-builder")

@menu_builder_bp.route("/dashboard")
@login_required
def dashboard():
    """Menu builder dashboard."""
    try:
        # Get statistics
        total_items = MenuItem.query.count()
        total_packages = MenuPackage.query.count()
        total_categories = MenuCategory.query.count()
        
        # Get recent items
        recent_items = MenuItem.query.order_by(MenuItem.created_at.desc()).limit(5).all()
        recent_packages = MenuPackage.query.order_by(MenuPackage.created_at.desc()).limit(5).all()
        
        # Calculate average margin
        items = MenuItem.query.filter(MenuItem.margin_percent.isnot(None)).all()
        avg_margin = sum(item.margin_percent for item in items) / len(items) if items else 0
        
        return render_template("menu_builder/menu_dashboard.html",
            total_items=total_items,
            total_packages=total_packages,
            total_categories=total_categories,
            avg_margin=round(avg_margin, 2),
            recent_items=recent_items,
            recent_packages=recent_packages
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading menu builder dashboard: {e}")
        return render_template("menu_builder/menu_dashboard.html",
            total_items=0, total_packages=0, total_categories=0,
            avg_margin=0, recent_items=[], recent_packages=[]
        )

@menu_builder_bp.route("/list")
@login_required
def menu_list():
    """List all menu items."""
    try:
        category_filter = request.args.get('category', type=int)
        status_filter = request.args.get('status')
        
        result = list_menu_items(category_id=category_filter, status=status_filter)
        items = result.get('items', [])
        
        categories_result = list_categories()
        categories = categories_result.get('categories', [])
        
        return render_template("menu_builder/menu_list.html",
            items=items,
            categories=categories,
            category_filter=category_filter,
            status_filter=status_filter
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading menu list: {e}")
        return render_template("menu_builder/menu_list.html",
            items=[], categories=[], category_filter=None, status_filter=None
        )

@menu_builder_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager, UserRole.KitchenStaff)
def menu_new():
    """Create a new menu item."""
    if request.method == "POST":
        try:
            # Create category if needed
            category_name = request.form.get('new_category', '').strip()
            category_id = request.form.get('category_id', type=int)
            
            if category_name and not category_id:
                cat_result = create_category(category_name)
                if cat_result['success']:
                    category_id = cat_result['category'].id
                else:
                    flash(f"Error creating category: {cat_result.get('error')}", "danger")
                    return redirect(url_for("menu_builder.menu_new"))
            
            data = {
                'name': request.form.get('name', '').strip(),
                'category_id': category_id,
                'description': request.form.get('description', '').strip(),
                'cost_per_portion': request.form.get('cost_per_portion', 0),
                'selling_price': request.form.get('selling_price', 0),
                'status': request.form.get('status', 'Active')
            }
            
            image_file = request.files.get('image') if 'image' in request.files else None
            
            result = create_menu_item(data, image_file)
            
            if result['success']:
                flash("Menu item created successfully!", "success")
                return redirect(url_for("menu_builder.menu_view", item_id=result['menu_item'].id))
            else:
                flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        except Exception as e:
            current_app.logger.exception(f"Error creating menu item: {e}")
    
    categories_result = list_categories()
    categories = categories_result.get('categories', [])
    return render_template("menu_builder/menu_form.html", item=None, categories=categories)

@menu_builder_bp.route("/item/<int:item_id>")
@login_required
def menu_view(item_id):
    """View a menu item."""
    try:
        result = get_menu_item(item_id)
        if not result['success']:
            flash(result.get('error', 'Menu item not found'), "danger")
            return redirect(url_for("menu_builder.menu_list"))
        
        item = result['menu_item']
        return render_template("menu_builder/menu_view.html", item=item)
    except Exception as e:
        current_app.logger.exception(f"Error viewing menu item: {e}")
        return redirect(url_for("menu_builder.menu_list"))

@menu_builder_bp.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager, UserRole.KitchenStaff)
def menu_edit(item_id):
    """Edit a menu item."""
    try:
        result = get_menu_item(item_id)
        if not result['success']:
            flash(result.get('error', 'Menu item not found'), "danger")
            return redirect(url_for("menu_builder.menu_list"))
        
        item = result['menu_item']
        
        if request.method == "POST":
            data = {
                'name': request.form.get('name', '').strip(),
                'category_id': request.form.get('category_id', type=int),
                'description': request.form.get('description', '').strip(),
                'cost_per_portion': request.form.get('cost_per_portion', 0),
                'selling_price': request.form.get('selling_price', 0),
                'status': request.form.get('status', 'Active')
            }
            
            image_file = request.files.get('image') if 'image' in request.files else None
            
            result = update_menu_item(item_id, data, image_file)
            
            if result['success']:
                flash("Menu item updated successfully!", "success")
                return redirect(url_for("menu_builder.menu_view", item_id=item_id))
            else:
                flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        
        categories_result = list_categories()
        categories = categories_result.get('categories', [])
        return render_template("menu_builder/menu_form.html", item=item, categories=categories)
    except Exception as e:
        current_app.logger.exception(f"Error editing menu item: {e}")
        return redirect(url_for("menu_builder.menu_list"))

@menu_builder_bp.route("/package/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def package_new():
    """Create a new menu package."""
    if request.method == "POST":
        try:
            data = {
                'name': request.form.get('name', '').strip(),
                'category': request.form.get('category', '').strip(),
                'description': request.form.get('description', '').strip(),
                'total_price': request.form.get('total_price', 0),
                'status': request.form.get('status', 'Active')
            }
            
            result = create_menu_package(data)
            
            if result['success']:
                package_id = result['package'].id
                
                # Add items to package
                item_ids = request.form.getlist('item_ids')
                quantities = request.form.getlist('quantities')
                
                for item_id, qty in zip(item_ids, quantities):
                    if item_id and qty:
                        attach_item_to_package(package_id, int(item_id), int(qty))
                
                flash("Menu package created successfully!", "success")
                return redirect(url_for("menu_builder.package_view", package_id=package_id))
            else:
                flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        except Exception as e:
            current_app.logger.exception(f"Error creating menu package: {e}")
    
    items_result = list_menu_items(status='Active')
    items = items_result.get('items', [])
    categories_result = list_categories()
    categories = categories_result.get('categories', [])
    
    return render_template("menu_builder/menu_package_form.html",
        package=None, items=items, categories=categories)

@menu_builder_bp.route("/package/<int:package_id>")
@login_required
def package_view(package_id):
    """View a menu package."""
    try:
        result = get_menu_package(package_id)
        if not result['success']:
            flash(result.get('error', 'Package not found'), "danger")
            return redirect(url_for("menu_builder.dashboard"))
        
        package = result['package']
        return render_template("menu_builder/package_view.html", package=package)
    except Exception as e:
        current_app.logger.exception(f"Error viewing package: {e}")
        return redirect(url_for("menu_builder.dashboard"))

@menu_builder_bp.route("/package/<int:package_id>/add-item", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def package_add_item(package_id):
    """Add item to package."""
    try:
        item_id = request.form.get('item_id', type=int)
        quantity = request.form.get('quantity', type=int, default=1)
        
        result = attach_item_to_package(package_id, item_id, quantity)
        
        if result['success']:
            flash("Item added to package!", "success")
        else:
            flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        
        return redirect(url_for("menu_builder.package_view", package_id=package_id))
    except Exception as e:
        current_app.logger.exception(f"Error adding item to package: {e}")
        return redirect(url_for("menu_builder.package_view", package_id=package_id))

@menu_builder_bp.route("/package/<int:package_id>/remove-item/<int:item_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def package_remove_item(package_id, item_id):
    """Remove item from package."""
    try:
        result = remove_item_from_package(package_id, item_id)
        
        if result['success']:
            flash("Item removed from package!", "success")
        else:
            flash(f"Error: {result.get('error', 'Unknown error')}", "danger")
        
        return redirect(url_for("menu_builder.package_view", package_id=package_id))
    except Exception as e:
        current_app.logger.exception(f"Error removing item from package: {e}")
        return redirect(url_for("menu_builder.package_view", package_id=package_id))

@menu_builder_bp.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    """Serve uploaded menu images."""
    try:
        upload_folder = get_upload_folder()
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        current_app.logger.exception(f"Error serving file: {e}")
        flash("File not found.", "danger")
        return redirect(url_for("menu_builder.dashboard"))

