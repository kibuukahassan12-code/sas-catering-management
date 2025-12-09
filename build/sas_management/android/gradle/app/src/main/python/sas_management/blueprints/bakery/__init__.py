from datetime import date, datetime
from decimal import Decimal
import os
from werkzeug.utils import secure_filename

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import login_required

from models import (
    BakeryItem, BakeryOrder, BakeryOrderItem, BakeryProductionTask,
    PriceHistory, UserRole, User, Client, db
)
from utils import get_decimal, paginate_query, role_required
# Safe import - use wildcard to prevent ImportError if functions are missing
try:
    from services.bakery_service import *
except ImportError:
    # Fallback if bakery_service is not fully implemented
    from services.bakery_service import (
        create_bakery_order, add_item_to_order, update_order_status,
        assign_production_task, start_production_task, complete_production_task,
        get_daily_sales, get_top_items, get_staff_productivity
    )

bakery_bp = Blueprint("bakery", __name__, url_prefix="/bakery")


@bakery_bp.route("/")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def index():
    return redirect(url_for("bakery.dashboard"))


# Legacy menu routes - kept for backward compatibility
@bakery_bp.route("/menu")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def menu_list():
    """Legacy route - redirects to items_list."""
    return redirect(url_for("bakery.items_list"))


@bakery_bp.route("/menu/add", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def menu_add():
    statuses = ["Active", "Retired"]
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        unit_price = get_decimal(request.form.get("unit_price"))
        status = request.form.get("status", "Active")

        if not name or not category:
            flash("Name and category are required.", "danger")
            return render_template(
                "bakery/item_form.html",
                action="Add",
                item=None,
                statuses=statuses,
            )

        # Create the bakery item first
        new_item = BakeryItem(
            name=name,
            category=category,
            status=status,
        )
        db.session.add(new_item)
        db.session.flush()  # Get the ID

        # Create initial price history record
        price_history = PriceHistory(
            item_id=new_item.id,
            item_type="BAKERY",
            price_ugx=unit_price,
            effective_date=date.today(),
            user_id=current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(price_history)
        db.session.commit()
        flash("Bakery menu item added.", "success")
        return redirect(url_for("bakery.menu_list"))

    return render_template(
        "bakery/item_form.html", action="Add", item=None, statuses=statuses
    )


@bakery_bp.route("/menu/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def menu_edit(item_id):
    item = BakeryItem.query.get_or_404(item_id)
    statuses = ["Active", "Retired"]

    if request.method == "POST":
        item.name = request.form.get("name", item.name).strip()
        item.category = request.form.get("category", item.category).strip()
        unit_price_raw = request.form.get("unit_price")
        item.status = request.form.get("status", item.status)
        
        # Handle price change - create new PriceHistory record if price changed
        if unit_price_raw:
            new_price = get_decimal(unit_price_raw)
            current_price = item.get_current_price()
            if new_price != current_price:
                price_history = PriceHistory(
                    item_id=item.id,
                    item_type="BAKERY",
                    price_ugx=new_price,
                    effective_date=date.today(),
                    user_id=current_user.id if current_user.is_authenticated else None,
                )
                db.session.add(price_history)
        
        db.session.commit()
        flash("Bakery menu item updated.", "success")
        return redirect(url_for("bakery.menu_list"))

    return render_template(
        "bakery/item_form.html", action="Edit", item=item, statuses=statuses
    )


@bakery_bp.route("/menu/delete/<int:item_id>", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def menu_delete(item_id):
    item = BakeryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Bakery menu item removed.", "info")
    return redirect(url_for("bakery.menu_list"))


# ============================
# BAKERY DASHBOARD
# ============================

@bakery_bp.route("/dashboard")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def dashboard():
    """Bakery dashboard with overview statistics."""
    try:
        # Get statistics
        total_orders = BakeryOrder.query.count()
        pending_orders = BakeryOrder.query.filter_by(order_status="Draft").count()
        in_production = BakeryOrder.query.filter_by(order_status="In Production").count()
        ready_orders = BakeryOrder.query.filter_by(order_status="Ready").count()
        
        # Recent orders
        recent_orders = BakeryOrder.query.order_by(BakeryOrder.created_at.desc()).limit(10).all()
        
        # Today's sales
        today_sales = get_daily_sales(date.today(), date.today())
        
        # Top items
        top_items = get_top_items(limit=5)
        
        return render_template(
            "bakery/bakery_dashboard.html",
            total_orders=total_orders,
            pending_orders=pending_orders,
            in_production=in_production,
            ready_orders=ready_orders,
            recent_orders=recent_orders,
            today_sales=today_sales,
            top_items=top_items
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading bakery dashboard: {e}")
        flash("Error loading dashboard. Please try again.", "danger")
        return render_template("bakery/bakery_dashboard.html", total_orders=0, pending_orders=0,
                             in_production=0, ready_orders=0, recent_orders=[], today_sales={}, top_items=[])


# ============================
# BAKERY ITEMS (Enhanced)
# ============================

@bakery_bp.route("/items")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def items_list():
    """List all bakery items."""
    pagination = paginate_query(BakeryItem.query.order_by(BakeryItem.name.asc()))
    return render_template(
        "bakery/items_list.html", items=pagination.items, pagination=pagination
    )


@bakery_bp.route("/items/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def items_new():
    """Create new bakery item."""
    statuses = ["Active", "Retired"]
    categories = ["Cake", "Pastry", "Bread", "Custom", "Other"]
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        selling_price = get_decimal(request.form.get("selling_price", "0"))
        cost_price = get_decimal(request.form.get("cost_price", "0"))
        preparation_time = request.form.get("preparation_time")
        status = request.form.get("status", "Active")
        
        if not name or not category:
            flash("Name and category are required.", "danger")
            return render_template(
                "bakery/item_form.html",
                action="Add",
                item=None,
                statuses=statuses,
                categories=categories,
            )
        
        new_item = BakeryItem(
            name=name,
            category=category,
            status=status,
            selling_price=selling_price,
            cost_price=cost_price,
            preparation_time=int(preparation_time) if preparation_time else None
        )
        
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join(current_app.instance_path, "bakery_uploads")
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, f"{new_item.id}_{filename}")
                image_file.save(filepath)
                new_item.image_url = f"bakery_uploads/{new_item.id}_{filename}"
        
        db.session.add(new_item)
        db.session.flush()
        
        # Create price history
        price_history = PriceHistory(
            item_id=new_item.id,
            item_type="BAKERY",
            price_ugx=selling_price,
            effective_date=date.today(),
            user_id=current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(price_history)
        db.session.commit()
        flash("Bakery item added successfully.", "success")
        return redirect(url_for("bakery.items_list"))
    
    return render_template(
        "bakery/item_form.html", action="Add", item=None, statuses=statuses, categories=categories
    )


@bakery_bp.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def items_edit(item_id):
    """Edit bakery item."""
    item = BakeryItem.query.get_or_404(item_id)
    statuses = ["Active", "Retired"]
    categories = ["Cake", "Pastry", "Bread", "Custom", "Other"]
    
    if request.method == "POST":
        item.name = request.form.get("name", item.name).strip()
        item.category = request.form.get("category", item.category).strip()
        item.selling_price = get_decimal(request.form.get("selling_price", "0"))
        item.cost_price = get_decimal(request.form.get("cost_price", "0"))
        prep_time = request.form.get("preparation_time")
        item.preparation_time = int(prep_time) if prep_time else None
        item.status = request.form.get("status", item.status)
        
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join(current_app.instance_path, "bakery_uploads")
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, f"{item.id}_{filename}")
                image_file.save(filepath)
                item.image_url = f"bakery_uploads/{item.id}_{filename}"
        
        # Update price history if price changed
        current_price = item.get_current_price()
        if item.selling_price != current_price:
            price_history = PriceHistory(
                item_id=item.id,
                item_type="BAKERY",
                price_ugx=item.selling_price,
                effective_date=date.today(),
                user_id=current_user.id if current_user.is_authenticated else None,
            )
            db.session.add(price_history)
        
        db.session.commit()
        flash("Bakery item updated successfully.", "success")
        return redirect(url_for("bakery.items_list"))
    
    return render_template(
        "bakery/item_form.html", action="Edit", item=item, statuses=statuses, categories=categories
    )


# ============================
# BAKERY ORDERS
# ============================

@bakery_bp.route("/orders")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def orders_list():
    """List all bakery orders."""
    status_filter = request.args.get("status")
    query = BakeryOrder.query.order_by(BakeryOrder.created_at.desc())
    
    if status_filter:
        query = query.filter_by(order_status=status_filter)
    
    pagination = paginate_query(query)
    return render_template(
        "bakery/orders_list.html", orders=pagination.items, pagination=pagination, status_filter=status_filter
    )


@bakery_bp.route("/orders/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def orders_new():
    """Create new bakery order."""
    try:
        clients = Client.query.order_by(Client.name.asc()).all()
        items = BakeryItem.query.filter_by(status="Active").order_by(BakeryItem.name.asc()).all()
    except Exception as e:
        current_app.logger.exception(f"Error loading data for new order form: {e}")
        clients = []
        items = []
    
    if request.method == "POST":
        try:
            customer_id = request.form.get("customer_id")
            customer_id = int(customer_id) if customer_id else None
            customer_name = request.form.get("customer_name", "").strip()
            customer_phone = request.form.get("customer_phone", "").strip()
            customer_email = request.form.get("customer_email", "").strip()
            pickup_date_str = request.form.get("pickup_date")
            pickup_date = datetime.strptime(pickup_date_str, "%Y-%m-%d").date() if pickup_date_str else None
            delivery_address = request.form.get("delivery_address", "").strip()
            bakery_notes = request.form.get("bakery_notes", "").strip()
            
            # Create order
            order = create_bakery_order(
                customer_id=customer_id,
                customer_name=customer_name if not customer_id else None,
                customer_phone=customer_phone,
                customer_email=customer_email,
                pickup_date=pickup_date,
                delivery_address=delivery_address,
                bakery_notes=bakery_notes,
                created_by=current_user.id
            )
            
            # Handle reference image upload
            if 'reference_image' in request.files:
                image_file = request.files['reference_image']
                if image_file and image_file.filename:
                    filename = secure_filename(image_file.filename)
                    upload_folder = os.path.join(current_app.instance_path, "bakery_uploads")
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, f"ref_{order.id}_{filename}")
                    image_file.save(filepath)
                    order.reference_image = f"bakery_uploads/ref_{order.id}_{filename}"
                    db.session.commit()
            
            # Add items
            item_ids = request.form.getlist("item_id")
            item_names = request.form.getlist("item_name")
            item_qtys = request.form.getlist("item_qty")
            item_prices = request.form.getlist("item_price")
            item_notes = request.form.getlist("item_notes")
            
            for i, item_id in enumerate(item_ids):
                if item_id:
                    qty = int(item_qtys[i]) if i < len(item_qtys) and item_qtys[i] else 1
                    price = get_decimal(item_prices[i]) if i < len(item_prices) and item_prices[i] else None
                    notes = item_notes[i] if i < len(item_notes) else None
                    add_item_to_order(order.id, item_id=int(item_id), qty=qty, custom_price=price, custom_notes=notes)
                elif i < len(item_names) and item_names[i]:
                    # Custom item
                    qty = int(item_qtys[i]) if i < len(item_qtys) and item_qtys[i] else 1
                    price = get_decimal(item_prices[i]) if i < len(item_prices) and item_prices[i] else Decimal("0.00")
                    notes = item_notes[i] if i < len(item_notes) else None
                    add_item_to_order(order.id, item_name=item_names[i], qty=qty, custom_price=price, custom_notes=notes)
            
            flash("Bakery order created successfully.", "success")
            return redirect(url_for("bakery.orders_view", order_id=order.id))
        except Exception as e:
            current_app.logger.exception(f"Error creating order: {e}")
            flash(f"Error creating order: {str(e)}", "danger")
    
    from datetime import date
    try:
        today = date.today()
        return render_template("bakery/order_form.html", order=None, clients=clients, items=items or [], today=today)
    except Exception as e:
        current_app.logger.exception(f"Error rendering order form template: {e}")
        flash(f"Error loading order form: {str(e)}", "danger")
        return redirect(url_for("bakery.orders_list"))


@bakery_bp.route("/orders/<int:order_id>")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def orders_view(order_id):
    """View bakery order details."""
    order = BakeryOrder.query.get_or_404(order_id)
    staff = User.query.filter(User.role.in_([UserRole.KitchenStaff, UserRole.BakeryManager])).all()
    return render_template("bakery/order_view.html", order=order, staff=staff)


@bakery_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def orders_update_status(order_id):
    """Update order status."""
    new_status = request.form.get("status")
    if not new_status:
        flash("Status is required.", "danger")
        return redirect(url_for("bakery.orders_view", order_id=order_id))
    
    try:
        update_order_status(order_id, new_status)
        flash(f"Order status updated to {new_status}.", "success")
    except Exception as e:
        current_app.logger.exception(f"Error updating status: {e}")
        flash(f"Error updating status: {str(e)}", "danger")
    
    return redirect(url_for("bakery.orders_view", order_id=order_id))


@bakery_bp.route("/orders/<int:order_id>/assign", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def orders_assign(order_id):
    """Assign production task to staff."""
    staff_id = request.form.get("staff_id")
    task_type = request.form.get("task_type")
    notes = request.form.get("notes", "").strip()
    
    if not staff_id or not task_type:
        flash("Staff and task type are required.", "danger")
        return redirect(url_for("bakery.orders_view", order_id=order_id))
    
    try:
        assign_production_task(order_id, int(staff_id), task_type, notes)
        flash("Task assigned successfully.", "success")
    except Exception as e:
        current_app.logger.exception(f"Error assigning task: {e}")
        flash(f"Error assigning task: {str(e)}", "danger")
    
    return redirect(url_for("bakery.orders_view", order_id=order_id))


# ============================
# PRODUCTION SHEET
# ============================

@bakery_bp.route("/production")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def production_sheet():
    """Production sheet showing all active production tasks."""
    in_production_orders = BakeryOrder.query.filter_by(order_status="In Production").all()
    tasks = BakeryProductionTask.query.filter_by(status="In Progress").all()
    return render_template("bakery/production_sheet.html", orders=in_production_orders, tasks=tasks)


@bakery_bp.route("/production/tasks/<int:task_id>/start", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def production_task_start(task_id):
    """Start a production task."""
    try:
        start_production_task(task_id)
        flash("Task started.", "success")
    except Exception as e:
        current_app.logger.exception(f"Error starting task: {e}")
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for("bakery.production_sheet"))


@bakery_bp.route("/production/tasks/<int:task_id>/complete", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def production_task_complete(task_id):
    """Complete a production task."""
    notes = request.form.get("notes", "").strip()
    try:
        complete_production_task(task_id, notes)
        flash("Task completed.", "success")
    except Exception as e:
        current_app.logger.exception(f"Error completing task: {e}")
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for("bakery.production_sheet"))


# ============================
# REPORTS
# ============================

@bakery_bp.route("/reports")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def reports():
    """Bakery reports page."""
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else date.today()
    
    daily_sales = get_daily_sales(start_date, end_date)
    top_items = get_top_items(limit=20, start_date=start_date, end_date=end_date)
    staff_productivity = get_staff_productivity(start_date=start_date, end_date=end_date)
    
    return render_template(
        "bakery/reports.html",
        daily_sales=daily_sales,
        top_items=top_items,
        staff_productivity=staff_productivity,
        start_date=start_date,
        end_date=end_date
    )


# ============================
# FILE UPLOADS
# ============================

@bakery_bp.route("/uploads/<path:filename>")
@login_required
@role_required(UserRole.Admin, UserRole.BakeryManager)
def serve_upload(filename):
    """Serve uploaded bakery images."""
    return send_from_directory(os.path.join(current_app.instance_path, "bakery_uploads"), filename)

