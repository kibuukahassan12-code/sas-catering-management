from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from sqlalchemy.orm import joinedload

from models import (
    Client,
    Event,
    HireOrder,
    HireOrderItem,
    InventoryItem,
    UserRole,
    db,
)
from utils import role_required, permission_required, require_permission, paginate_query
from utils.helpers import parse_date

hire_bp = Blueprint("hire", __name__, url_prefix="/hire")

def _parse_order_items():
    item_ids = request.form.getlist("item_id[]")
    quantities = request.form.getlist("quantity[]")
    combined = defaultdict(int)

    for raw_id, raw_qty in zip(item_ids, quantities):
        if not raw_id:
            continue
        try:
            item_id = int(raw_id)
        except (TypeError, ValueError):
            continue
        qty = int(raw_qty or 0)
        if qty <= 0:
            continue
        combined[item_id] += qty

    return [(item_id, qty) for item_id, qty in combined.items()]

def _generate_booking_reference():
    """Generate a unique booking reference."""
    prefix = "HIRE"
    timestamp = datetime.now().strftime("%Y%m%d")
    # Get the last booking number for today
    last_order = HireOrder.query.filter(HireOrder.reference.like(f"{prefix}-{timestamp}-%")).order_by(HireOrder.id.desc()).first()
    if last_order and last_order.reference:
        try:
            last_num = int(last_order.reference.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    return f"{prefix}-{timestamp}-{new_num:04d}"

def _apply_stock_deductions(order, payload):
    total_cost = Decimal("0.00")
    for item_id, qty in payload:
        inventory_item = InventoryItem.query.get(item_id)
        if not inventory_item:
            raise ValueError("One of the selected inventory items no longer exists.")
        if inventory_item.stock_count < qty:
            raise ValueError(
                f"Insufficient stock for {inventory_item.name}. Available: {inventory_item.stock_count}, requested: {qty}."
            )
        inventory_item.stock_count -= qty
        unit_price = Decimal(inventory_item.rental_price or 0)
        subtotal = unit_price * qty
        db.session.add(
            HireOrderItem(
                order=order,
                inventory_item=inventory_item,
                quantity_rented=qty,
                unit_price=unit_price,
                subtotal=subtotal,
            )
        )
        total_cost += subtotal
    return total_cost

def _restore_stock(order):
    for item in order.items:
        if item.inventory_item:
            item.inventory_item.stock_count += item.quantity_rented

@hire_bp.route("/")
@login_required
@role_required("Admin", "HireManager")
def index():
    today = date.today()
    active_orders = (
        HireOrder.query.filter(HireOrder.end_date >= today)
        .order_by(HireOrder.start_date.asc())
        .limit(5)
        .all()
    )
    low_inventory = (
        InventoryItem.query.filter(InventoryItem.stock_count <= 10)
        .order_by(InventoryItem.stock_count.asc())
        .limit(5)
        .all()
    )
    summary = {
        "total_inventory_items": InventoryItem.query.count(),
        "total_available_units": (
            db.session.query(
                db.func.coalesce(db.func.sum(InventoryItem.stock_count), 0)
            ).scalar()
        ),
        "active_orders": HireOrder.query.filter(HireOrder.end_date >= today).count(),
        "orders_value": db.session.query(
            db.func.coalesce(db.func.sum(HireOrder.total_cost), 0)
        ).scalar(),
    }
    return render_template(
        "hire/index.html",
        summary=summary,
        active_orders=active_orders,
        low_inventory=low_inventory,
        CURRENCY=current_app.config.get("CURRENCY_PREFIX", "UGX "),
    )

@hire_bp.route("/inventory")
@login_required
@role_required("Admin", "HireManager")
def inventory_list():
    pagination = paginate_query(InventoryItem.query.order_by(InventoryItem.name.asc()))
    return render_template(
        "hire/inventory_list.html",
        items=pagination.items,
        pagination=pagination,
    )

@hire_bp.route("/inventory/add", methods=["GET", "POST"])
@login_required
@role_required("Admin", "HireManager")
def inventory_add():
    statuses = ["Available", "Damaged", "Retired"]
    if request.method == "POST":
        item = InventoryItem(
            name=request.form.get("name", "").strip(),
            category=request.form.get("category", "").strip() or None,
            sku=request.form.get("sku", "").strip() or None,
            stock_count=request.form.get("stock_count", type=int) or 0,
            rental_price=Decimal(request.form.get("rental_price") or "0"),
            replacement_cost=Decimal(request.form.get("replacement_cost") or "0") or None,
            condition=request.form.get("condition", "Good"),
            location=request.form.get("location", "").strip() or None,
            tags=request.form.get("tags", "").strip() or None,
            status=request.form.get("status", "Available"),
        )
        db.session.add(item)
        db.session.commit()
        flash("Inventory item added.", "success")
        return redirect(url_for("hire.inventory_list"))

    return render_template(
        "hire/inventory_form.html",
        action="Add",
        item=None,
        statuses=statuses,
    )

@hire_bp.route("/inventory/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
@role_required("Admin", "HireManager")
def inventory_edit(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    statuses = ["Available", "Damaged", "Retired"]

    if request.method == "POST":
        item.name = request.form.get("name", item.name).strip()
        item.category = request.form.get("category", "").strip() or None
        item.sku = request.form.get("sku", "").strip() or None
        item.stock_count = request.form.get("stock_count", type=int) or item.stock_count
        rental_price_raw = request.form.get("rental_price")
        if rental_price_raw:
            item.rental_price = Decimal(rental_price_raw)
        replacement_cost_raw = request.form.get("replacement_cost")
        if replacement_cost_raw:
            item.replacement_cost = Decimal(replacement_cost_raw) or None
        item.condition = request.form.get("condition", item.condition)
        item.location = request.form.get("location", "").strip() or None
        item.tags = request.form.get("tags", "").strip() or None
        item.status = request.form.get("status", item.status)
        db.session.commit()
        flash("Inventory item updated.", "success")
        return redirect(url_for("hire.inventory_list"))

    return render_template(
        "hire/inventory_form.html",
        action="Edit",
        item=item,
        statuses=statuses,
    )

@hire_bp.route("/inventory/delete/<int:item_id>", methods=["POST"])
@login_required
@role_required("Admin", "HireManager")
def inventory_delete(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if item.order_items:
        flash(
            "This item is referenced in existing hire orders. Update or delete those orders first.",
            "warning",
        )
        return redirect(url_for("hire.inventory_list"))

    db.session.delete(item)
    db.session.commit()
    flash("Inventory item removed.", "info")
    return redirect(url_for("hire.inventory_list"))

@hire_bp.route("/orders")
@login_required
@permission_required("hire")
def orders_list():
    query = (
        HireOrder.query.order_by(HireOrder.start_date.desc())
        .options(
            joinedload(HireOrder.client),
            joinedload(HireOrder.event),
            joinedload(HireOrder.items).joinedload(HireOrderItem.inventory_item),
        )
    )
    pagination = paginate_query(query)
    return render_template(
        "hire/orders_list.html", orders=pagination.items, pagination=pagination
    )

def _order_form_resources():
    clients = Client.query.order_by(Client.name.asc()).all()
    events = Event.query.order_by(Event.event_date.desc()).all()
    inventory_items = InventoryItem.query.order_by(InventoryItem.name.asc()).all()
    return clients, events, inventory_items

@hire_bp.route("/orders/add", methods=["GET", "POST"])
@login_required
@require_permission("orders.create")
def orders_add():
    clients, events, inventory_items = _order_form_resources()
    if not clients or not events or not inventory_items:
        flash("Ensure clients, events, and inventory items exist before creating orders.", "warning")
        return redirect(url_for("hire.orders_list"))

    if request.method == "POST":
        start_date = parse_date(request.form.get("start_date"))
        end_date = parse_date(request.form.get("end_date"))
        if not start_date or not end_date or end_date < start_date:
            flash("Please provide a valid hire window.", "danger")
            event_id_param = request.args.get("event_id", type=int)
            prefill_client_id = None
            if event_id_param:
                event = Event.query.get(event_id_param)
                if event and event.client_id:
                    prefill_client_id = event.client_id
            return render_template(
                "hire/order_form.html",
                action="Add",
                order=None,
                clients=clients,
                events=events,
                inventory_items=inventory_items,
                prefill_event_id=event_id_param,
                prefill_client_id=prefill_client_id,
            )

        payload = _parse_order_items()
        if not payload:
            flash("Add at least one inventory item to the order.", "danger")
            event_id_param = request.args.get("event_id", type=int)
            prefill_client_id = None
            if event_id_param:
                event = Event.query.get(event_id_param)
                if event and event.client_id:
                    prefill_client_id = event.client_id
            return render_template(
                "hire/order_form.html",
                action="Add",
                order=None,
                clients=clients,
                events=events,
                inventory_items=inventory_items,
                prefill_event_id=event_id_param,
                prefill_client_id=prefill_client_id,
            )

        event_id_val = request.form.get("event_id", type=int)
        order = HireOrder(
            client_id=request.form.get("client_id", type=int),
            event_id=event_id_val if event_id_val else None,
            start_date=start_date,
            end_date=end_date,
            delivery_address=request.form.get("delivery_address", "").strip(),
            status=request.form.get("status", "Draft"),
            reference=_generate_booking_reference(),
            deposit_amount=Decimal(request.form.get("deposit_amount") or "0"),
        )
        db.session.add(order)
        db.session.flush()

        try:
            total_cost = _apply_stock_deductions(order, payload)
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            event_id_param = request.args.get("event_id", type=int)
            prefill_client_id = None
            if event_id_param:
                event = Event.query.get(event_id_param)
                if event and event.client_id:
                    prefill_client_id = event.client_id
            return render_template(
                "hire/order_form.html",
                action="Add",
                order=None,
                clients=clients,
                events=events,
                inventory_items=inventory_items,
                prefill_event_id=event_id_param,
                prefill_client_id=prefill_client_id,
            )

        order.total_cost = total_cost
        db.session.commit()
        flash("Hire order created.", "success")
        return redirect(url_for("hire.orders_list"))

    # Get event_id from query parameter if provided (e.g., when coming from event view)
    event_id_param = request.args.get("event_id", type=int)
    prefill_client_id = None
    
    # If event_id is provided, get the event and pre-populate the client
    if event_id_param:
        event = Event.query.get(event_id_param)
        if event and event.client_id:
            prefill_client_id = event.client_id
    
    return render_template(
        "hire/order_form.html",
        action="Add",
        order=None,
        clients=clients,
        events=events,
        inventory_items=inventory_items,
        prefill_event_id=event_id_param,
        prefill_client_id=prefill_client_id,
    )

# Alias route for create_hire_order
@hire_bp.route("/orders/create", methods=["GET", "POST"])
@login_required
@permission_required("hire")
def create_hire_order():
    """Alias for orders_add to match expected route name."""
    return orders_add()

@hire_bp.route("/orders/edit/<int:order_id>", methods=["GET", "POST"])
@login_required
@require_permission("orders.edit")
def orders_edit(order_id):
    order = HireOrder.query.get_or_404(order_id)
    clients, events, inventory_items = _order_form_resources()

    if request.method == "POST":
        start_date = parse_date(request.form.get("start_date"))
        end_date = parse_date(request.form.get("end_date"))
        if not start_date or not end_date or end_date < start_date:
            flash("Please provide a valid hire window.", "danger")
            return render_template(
                "hire/order_form.html",
                action="Edit",
                order=order,
                clients=clients,
                events=events,
                inventory_items=inventory_items,
            )

        payload = _parse_order_items()
        if not payload:
            flash("Add at least one inventory item to the order.", "danger")
            return render_template(
                "hire/order_form.html",
                action="Edit",
                order=order,
                clients=clients,
                events=events,
                inventory_items=inventory_items,
            )

        _restore_stock(order)
        order.items.clear()
        order.client_id = request.form.get("client_id", type=int) or order.client_id
        event_id_val = request.form.get("event_id", type=int)
        order.event_id = event_id_val if event_id_val else order.event_id
        order.start_date = start_date
        order.end_date = end_date
        order.delivery_address = request.form.get(
            "delivery_address", order.delivery_address
        ).strip()
        order.status = request.form.get("status", order.status)
        deposit_amount_raw = request.form.get("deposit_amount")
        if deposit_amount_raw:
            order.deposit_amount = Decimal(deposit_amount_raw)

        try:
            total_cost = _apply_stock_deductions(order, payload)
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return render_template(
                "hire/order_form.html",
                action="Edit",
                order=order,
                clients=clients,
                events=events,
                inventory_items=inventory_items,
            )

        order.total_cost = total_cost
        db.session.commit()
        flash("Hire order updated.", "success")
        return redirect(url_for("hire.orders_list"))

    return render_template(
        "hire/order_form.html",
        action="Edit",
        order=order,
        clients=clients,
        events=events,
        inventory_items=inventory_items,
    )

@hire_bp.route("/orders/delete/<int:order_id>", methods=["POST"])
@login_required
@require_permission("orders.delete")
def orders_delete(order_id):
    order = HireOrder.query.get_or_404(order_id)
    _restore_stock(order)
    db.session.delete(order)
    db.session.commit()
    flash("Hire order deleted and stock restored.", "info")
    return redirect(url_for("hire.orders_list"))

# API Endpoints for Hire Module
@hire_bp.route("/api/items")
@login_required
@role_required("Admin", "HireManager")
def api_items():
    """API endpoint to list all hire items with availability."""
    items = InventoryItem.query.order_by(InventoryItem.name.asc()).all()
    return jsonify({
        "status": "success",
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "sku": item.sku,
                "stock_count": item.stock_count,
                "available_quantity": item.stock_count,  # For now, same as stock_count
                "rental_price": float(item.rental_price),
                "replacement_cost": float(item.replacement_cost) if item.replacement_cost else 0.0,
                "condition": item.condition,
                "location": item.location,
                "tags": item.tags.split(",") if item.tags else [],
                "status": item.status,
            }
            for item in items
        ]
    })

# Equipment Maintenance routes are in maintenance_routes.py

@hire_bp.route("/api/bookings")
@login_required
@role_required("Admin", "HireManager")
def api_bookings():
    """API endpoint to list all hire bookings."""
    bookings = HireOrder.query.options(
        joinedload(HireOrder.client),
        joinedload(HireOrder.event),
        joinedload(HireOrder.items).joinedload(HireOrderItem.inventory_item),
    ).order_by(HireOrder.start_date.desc()).all()
    
    return jsonify({
        "status": "success",
        "bookings": [
            {
                "id": booking.id,
                "reference": booking.reference,
                "client_id": booking.client_id,
                "client_name": booking.client.name if booking.client else None,
                "event_id": booking.event_id,
                "event_name": booking.event.event_name if booking.event else None,
                "status": booking.status,
                "start_date": booking.start_date.isoformat() if booking.start_date else None,
                "end_date": booking.end_date.isoformat() if booking.end_date else None,
                "delivery_date": booking.delivery_date.isoformat() if booking.delivery_date else None,
                "pickup_date": booking.pickup_date.isoformat() if booking.pickup_date else None,
                "delivery_address": booking.delivery_address,
                "total_cost": float(booking.total_cost),
                "deposit_amount": float(booking.deposit_amount) if booking.deposit_amount else 0.0,
                "items_count": len(booking.items),
            }
            for booking in bookings
        ]
    })

@hire_bp.route("/api/bookings/<int:booking_id>")
@login_required
@role_required("Admin", "HireManager")
def api_booking_detail(booking_id):
    """API endpoint to get a specific booking's details."""
    booking = HireOrder.query.options(
        joinedload(HireOrder.client),
        joinedload(HireOrder.event),
        joinedload(HireOrder.items).joinedload(HireOrderItem.inventory_item),
    ).get_or_404(booking_id)
    
    return jsonify({
        "status": "success",
        "booking": {
            "id": booking.id,
            "reference": booking.reference,
            "client_id": booking.client_id,
            "client_name": booking.client.name if booking.client else None,
            "event_id": booking.event_id,
            "event_name": booking.event.event_name if booking.event else None,
            "status": booking.status,
            "start_date": booking.start_date.isoformat() if booking.start_date else None,
            "end_date": booking.end_date.isoformat() if booking.end_date else None,
            "delivery_date": booking.delivery_date.isoformat() if booking.delivery_date else None,
            "pickup_date": booking.pickup_date.isoformat() if booking.pickup_date else None,
            "delivery_address": booking.delivery_address,
            "total_cost": float(booking.total_cost),
            "deposit_amount": float(booking.deposit_amount) if booking.deposit_amount else 0.0,
            "items": [
                {
                    "id": item.id,
                    "inventory_item_id": item.inventory_item_id,
                    "item_name": item.inventory_item.name if item.inventory_item else None,
                    "quantity_rented": item.quantity_rented,
                    "unit_price": float(item.unit_price),
                    "subtotal": float(item.subtotal),
                    "returned_quantity": item.returned_quantity,
                    "damaged_quantity": item.damaged_quantity,
                }
                for item in booking.items
            ],
        }
    })

@hire_bp.route("/api/bookings/<int:booking_id>/status", methods=["PATCH", "POST"])
@login_required
@role_required("Admin", "HireManager")
def api_booking_status(booking_id):
    """API endpoint to update booking status."""
    booking = HireOrder.query.get_or_404(booking_id)
    
    if request.is_json:
        data = request.get_json()
        new_status = data.get("status")
    else:
        new_status = request.form.get("status")
    
    if not new_status:
        return jsonify({"status": "error", "message": "Status is required"}), 400
    
    valid_statuses = ["Draft", "Quotation", "Confirmed", "Out", "Returned", "Completed", "Cancelled"]
    if new_status not in valid_statuses:
        return jsonify({"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
    
    booking.status = new_status
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": f"Booking status updated to {new_status}",
        "booking_id": booking.id,
        "new_status": new_status,
    })

@hire_bp.route("/api/bookings", methods=["POST"])
@login_required
@role_required("Admin", "HireManager")
def api_create_booking():
    """API endpoint to create a new booking."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["client_id", "start_date", "end_date", "delivery_address", "items"]
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
    
    try:
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        
        if end_date < start_date:
            return jsonify({"status": "error", "message": "End date must be after start date"}), 400
        
        booking = HireOrder(
            client_id=data["client_id"],
            event_id=data.get("event_id"),
            start_date=start_date,
            end_date=end_date,
            delivery_address=data["delivery_address"],
            status=data.get("status", "Draft"),
            reference=_generate_booking_reference(),
            deposit_amount=Decimal(str(data.get("deposit_amount", 0))),
        )
        db.session.add(booking)
        db.session.flush()
        
        # Process items
        payload = [(item["item_id"], item["quantity"]) for item in data["items"]]
        total_cost = _apply_stock_deductions(booking, payload)
        booking.total_cost = total_cost
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Booking created successfully",
            "booking_id": booking.id,
            "reference": booking.reference,
        }), 201
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

