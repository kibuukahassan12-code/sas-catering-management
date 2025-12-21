from flask import render_template, request, redirect, url_for, flash, current_app
from . import hire
from sas_management.models import InventoryItem, Order, OrderItem, db, Client, Event
from .services import paginate_query, serialize_item
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, date
from decimal import Decimal
import json


# 1. Hire Overview
@hire.route("/")
def index():
    """Hire Department Overview Dashboard."""
    # Get statistics
    total_items = InventoryItem.query.count()
    available_items = InventoryItem.query.filter_by(status="Available").count()
    rented_items = InventoryItem.query.filter_by(status="Rented").count()
    maintenance_items = InventoryItem.query.filter_by(status="Maintenance").count()
    
    # Get recent orders (if HireOrder model exists, otherwise use placeholder)
    recent_orders = []
    
    # Get maintenance alerts
    maintenance_alerts = InventoryItem.query.filter_by(status="Maintenance").limit(5).all()
    
    return render_template(
        "hire/index.html",
        total_items=total_items,
        available_items=available_items,
        rented_items=rented_items,
        maintenance_items=maintenance_items,
        recent_orders=recent_orders,
        maintenance_alerts=maintenance_alerts
    )


# 2. Hire Inventory
@hire.route("/inventory")
def inventory_list():
    """List all hire equipment inventory."""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Get filter parameters
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    
    query = InventoryItem.query
    
    if category_filter:
        query = query.filter(InventoryItem.category == category_filter)
    if status_filter:
        query = query.filter(InventoryItem.status == status_filter)
    
    query = query.order_by(InventoryItem.name.asc())
    pagination = paginate_query(query, page, per_page)
    
    # Get unique categories for filter
    categories = db.session.query(InventoryItem.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template(
        "hire/inventory.html",
        items=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category=category_filter,
        current_status=status_filter
    )


@hire.route("/inventory/new", methods=["GET", "POST"])
def new_item():
    """Create a new equipment item."""
    if request.method == "POST":
        try:
            item = InventoryItem(
                name=request.form.get("name", "").strip(),
                category=request.form.get("category", "").strip(),
                sku=request.form.get("sku", "").strip(),
                stock_count=int(request.form.get("stock_count", 0)),
                rental_price=Decimal(request.form.get("rental_price", 0)) if request.form.get("rental_price") else None,
                replacement_cost=Decimal(request.form.get("replacement_cost", 0)) if request.form.get("replacement_cost") else None,
                condition=request.form.get("condition", "Good"),
                location=request.form.get("location", "").strip(),
                tags=request.form.get("tags", "").strip(),
                status=request.form.get("status", "Available"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(item)
            db.session.commit()
            flash("Equipment item added successfully.", "success")
            return redirect(url_for("hire.inventory_list"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding item: {str(e)}", "error")
    
    return render_template("hire/new_item.html")


# 3. Hire Orders
@hire.route("/orders")
def orders_list():
    """List all hire orders with pagination and chart data."""
    # get paging params
    try:
        page = int(request.args.get("page", 1))
    except Exception:
        page = 1
    try:
        per_page = int(request.args.get("per_page", 10))
    except Exception:
        per_page = 10

    # base query for orders with eager loading
    try:
        query = Order.query.options(joinedload(Order.items)).order_by(Order.created_at.desc())
    except Exception:
        # fallback for plain SQLAlchemy session if Order.query not available
        query = db.session.query(Order).order_by(getattr(Order, "created_at", Order.id).desc())

    # paginate using the new helper
    pagination = paginate_query(query, page=page, per_page=per_page)
    orders = getattr(pagination, "items", pagination.items)

    # Serialize orders for table display (with all fields)
    orders_serialized = []
    for o in orders:
        try:
            # Safely get items count
            items_count = 0
            try:
                items_count = len(getattr(o, "items", []))
            except Exception:
                pass
            
            # Safely format dates
            def safe_date_format(date_obj):
                if date_obj:
                    try:
                        return date_obj.isoformat()
                    except Exception:
                        return None
                return None
            
            orders_serialized.append({
                "id": getattr(o, "id", None),
                "reference": getattr(o, "reference", None) or f"HO-{getattr(o, 'id', 0)}",
                "client_name": getattr(o, "client_name", "") or getattr(o, "customer_name", "") or "Unknown",
                "telephone": getattr(o, "telephone", None) or None,
                "email": getattr(o, "email", None) or None,
                "event_id": getattr(o, "event_id", None),
                "event": getattr(o, "event", None),
                "client_id": getattr(o, "client_id", None),
                "client": getattr(o, "client", None),
                "event_date": safe_date_format(getattr(o, "event_date", None)),
                "start_date": safe_date_format(getattr(o, "start_date", None)),
                "end_date": safe_date_format(getattr(o, "end_date", None)),
                "delivery_date": safe_date_format(getattr(o, "delivery_date", None)),
                "pickup_date": safe_date_format(getattr(o, "pickup_date", None)),
                "delivery_address": getattr(o, "delivery_address", None) or None,
                "status": getattr(o, "status", "Pending") or "Pending",
                "total_cost": float(getattr(o, "total_cost", 0) or 0),
                "amount_paid": float(getattr(o, "amount_paid", 0) or 0),
                "balance_due": float(getattr(o, "balance_due", 0) or 0),
                "comments": getattr(o, "comments", None) or None,
                "created_at": safe_date_format(getattr(o, "created_at", None)),
                "items_count": items_count
            })
        except Exception as e:
            current_app.logger.exception(f"Error serializing order {getattr(o, 'id', 'unknown')}: {e}")
            # Add a minimal entry to prevent template errors
            orders_serialized.append({
                "id": getattr(o, "id", None),
                "reference": f"HO-{getattr(o, 'id', 0)}",
                "client_name": "Error loading",
                "telephone": None,
                "email": None,
                "status": "Error",
                "total_cost": 0.0,
                "amount_paid": 0.0,
                "balance_due": 0.0,
                "items_count": 0,
                "start_date": None,
                "end_date": None
            })

    # Chart 1: Status counts
    try:
        status_counts = db.session.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
        status_labels = [str(s) for s, c in status_counts if s]
        status_values = [int(c) for s, c in status_counts if s]
    except Exception as e:
        current_app.logger.exception(f"Error getting status counts: {e}")
        # fallback: compute from paginated list (may be partial)
        counts = {}
        for o in orders_serialized:
            status = o.get("status", "Unknown")
            counts[status] = counts.get(status, 0) + 1
        status_labels = list(counts.keys())
        status_values = list(counts.values())
    
    # Ensure we have data for charts
    if not status_labels:
        status_labels = ["No Data"]
        status_values = [0]

    # Chart 2: Monthly revenue (last 12 months)
    try:
        # works for sqlite and many DBs using strftime; if not available, compute in python
        rev_q = db.session.query(
            func.strftime("%Y-%m", Order.created_at).label("month"), 
            func.coalesce(func.sum(Order.total_cost), 0)
        ).group_by("month").order_by("month")
        rev_rows = rev_q.all()
        revenue_labels = [str(r[0]) for r in rev_rows if r[0]]
        revenue_values = [float(r[1] or 0) for r in rev_rows if r[0]]
    except Exception as e:
        current_app.logger.exception(f"Error getting revenue data: {e}")
        # fallback: compute from all orders (may be expensive)
        try:
            all_orders = db.session.query(Order).all()
            rev = {}
            for o in all_orders:
                m = getattr(o, "created_at", None)
                if m:
                    try:
                        key = m.strftime("%Y-%m")
                    except Exception:
                        key = "unknown"
                else:
                    key = "unknown"
                rev[key] = rev.get(key, 0) + float(getattr(o, "total_cost", 0) or 0)
            revenue_labels = sorted(rev.keys())
            revenue_values = [rev[k] for k in revenue_labels]
        except Exception:
            revenue_labels = []
            revenue_values = []
    
    # Ensure we have data for charts
    if not revenue_labels:
        revenue_labels = ["No Data"]
        revenue_values = [0]

    return render_template(
        "hire/orders.html",
        orders=orders_serialized,
        pagination=pagination,
        status_labels=status_labels,
        status_values=status_values,
        rev_labels=revenue_labels,
        rev_values=revenue_values
    )


@hire.route("/orders/new", methods=["GET", "POST"])
def new_order():
    """Create a new hire order."""
    if request.method == "POST":
        # ---- Handle form submission ----
        try:
            client_name = request.form.get("client_name", "").strip()
            client_id = request.form.get("client_id", type=int) or None
            event_id = request.form.get("event_id", type=int) or None
            telephone = request.form.get("telephone", "").strip() or None
            email = request.form.get("email", "").strip() or None
            delivery_address = request.form.get("delivery_address", "").strip() or None
            comments = request.form.get("comments", "").strip() or None
            
            # Parse dates
            def parse_date(date_str):
                if not date_str:
                    return None
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    return None
            
            event_date = parse_date(request.form.get("event_date", "").strip())
            start_date = parse_date(request.form.get("start_date", "").strip())
            end_date = parse_date(request.form.get("end_date", "").strip())
            delivery_date = parse_date(request.form.get("delivery_date", "").strip())
            pickup_date = parse_date(request.form.get("pickup_date", "").strip())
            
            # Amount paid
            amount_paid = Decimal(request.form.get("amount_paid", 0) or 0)
            
            # Items are submitted as JSON in a hidden field 'items_json'
            items_json = request.form.get("items_json", "[]")
            items = json.loads(items_json)

            # Validate client_name
            if not client_name:
                flash("Client name is required.", "danger")
                return redirect(url_for("hire.new_order"))
            
            # Validate items
            if not items or len(items) == 0:
                flash("Please add at least one item to the order.", "danger")
                return redirect(url_for("hire.new_order"))
            
            # Validate dates
            if start_date and end_date and start_date > end_date:
                flash("End date must be after start date.", "danger")
                return redirect(url_for("hire.new_order"))

            # Create Order (reference will be set after flush)
            order = Order(
                client_name=client_name,
                client_id=client_id,
                event_id=event_id,
                event_date=event_date,
                start_date=start_date,
                end_date=end_date,
                delivery_date=delivery_date,
                pickup_date=pickup_date,
                delivery_address=delivery_address,
                telephone=telephone,
                email=email,
                comments=comments,
                amount_paid=amount_paid,
                status="Pending",
                created_at=datetime.utcnow()
            )
            db.session.add(order)
            db.session.flush()  # get order.id without commit
            
            # Generate reference number with actual order ID
            order.reference = f"HO-{datetime.now().strftime('%Y%m%d')}-{order.id:04d}"

            total_cost = Decimal('0.00')
            insufficient_stock_items = []
            
            for it in items:
                item_id = int(it.get("id"))
                qty = int(it.get("qty", 0))
                price = Decimal(str(it.get("price", 0)))
                
                if qty <= 0:
                    continue
                
                # Verify availability and check stock
                inv = db.session.get(InventoryItem, item_id)
                if not inv:
                    flash(f"Item ID {item_id} not found.", "warning")
                    continue
                
                # Check if sufficient stock is available
                if inv.stock_count < qty:
                    insufficient_stock_items.append(f"{inv.name} (Available: {inv.stock_count}, Requested: {qty})")
                    continue
                
                # Calculate subtotal (considering rental period if applicable)
                days = 1
                if start_date and end_date:
                    days = max(1, (end_date - start_date).days + 1)
                
                subtotal = qty * price * days
                
                # Create OrderItem
                order_item = OrderItem(
                    order_id=order.id,
                    item_id=inv.id,
                    qty=qty,
                    price=price,
                    subtotal=subtotal
                )
                db.session.add(order_item)
                total_cost += subtotal

                # Deduct stock from inventory
                inv.stock_count = max(0, inv.stock_count - qty)
                
                # Update item status if stock is depleted
                if inv.stock_count == 0:
                    inv.status = "Rented"
                elif inv.status == "Available" and inv.stock_count < qty:
                    inv.status = "Low Stock"
                
                db.session.add(inv)
            
            # Check for insufficient stock
            if insufficient_stock_items:
                db.session.rollback()
                flash(f"Insufficient stock for: {', '.join(insufficient_stock_items)}", "danger")
                return redirect(url_for("hire.new_order"))

            # Save total cost and calculate balance
            order.total_cost = total_cost
            order.calculate_balance()

            db.session.commit()
            currency = current_app.config.get("CURRENCY_PREFIX", "UGX ")
            flash(f"Order {order.reference} created successfully. Balance due: {currency}{order.balance_due:.2f}", "success")
            return redirect(url_for("hire.orders_list"))

        except Exception as e:
            current_app.logger.exception("Failed to create hire order")
            db.session.rollback()
            flash("Failed to create order: " + str(e), "danger")
            return redirect(url_for("hire.new_order"))

    # ---- GET: render form ----
    # Query available inventory items with stock > 0
    items = InventoryItem.query.filter(
        InventoryItem.stock_count > 0
    ).order_by(InventoryItem.name).all()
    available_items = [serialize_item(i) for i in items]
    
    # Get clients and events for dropdowns
    clients = Client.query.order_by(Client.name).all()
    events = Event.query.filter(Event.status.in_(["Confirmed", "Pending"])).order_by(Event.event_date.desc()).limit(50).all()

    # Pass serialized list to template — JSON serializable
    return render_template("hire/new_order.html", 
                         available_items=available_items,
                         clients=clients,
                         events=events)


@hire.route("/orders/<int:order_id>")
def order_details(order_id):
    """View hire order details."""
    order = Order.query.options(
        joinedload(Order.items).joinedload(OrderItem.inventory_item),
        joinedload(Order.client),
        joinedload(Order.event)
    ).get_or_404(order_id)
    
    # Calculate days if dates are available
    rental_days = 1
    if order.start_date and order.end_date:
        rental_days = max(1, (order.end_date - order.start_date).days + 1)
    
    return render_template(
        "hire/order_details.html",
        order_id=order_id,
        order=order,
        rental_days=rental_days
    )


# 4. Equipment Maintenance
@hire.route("/maintenance")
def maintenance_list():
    """List equipment maintenance records."""
    # Get items that need maintenance
    maintenance_items = InventoryItem.query.filter_by(status="Maintenance").order_by(InventoryItem.updated_at.desc()).all()
    
    # Get items with poor condition
    poor_condition_items = InventoryItem.query.filter(
        InventoryItem.condition.in_(["Poor", "Damaged"])
    ).order_by(InventoryItem.updated_at.desc()).all()
    
    return render_template(
        "hire/maintenance.html",
        maintenance_items=maintenance_items,
        poor_condition_items=poor_condition_items
    )
