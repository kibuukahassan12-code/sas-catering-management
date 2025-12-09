"""POS System Blueprint."""
from datetime import datetime
from decimal import Decimal

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from flask_login import current_user, login_required

from models import (
    Client,
    POSDevice,
    POSOrder,
    POSOrderLine,
    POSPayment,
    POSProduct,
    POSReceipt,
    POSShift,
    UserRole,
    db,
)
from services.pos_service import (
    add_payment,
    close_shift,
    create_order,
    generate_kitchen_tickets,
    generate_z_report,
    release_inventory,
    reserve_inventory_for_order,
    sync_orders_for_offline,
)
from utils import role_required, permission_required, paginate_query

pos_bp = Blueprint("pos", __name__, url_prefix="/pos")

@pos_bp.route("/")
@pos_bp.route("/dashboard")
@login_required
# @permission_required("pos")
def index():
    """POS dashboard with statistics and management."""
    try:
        if not current_user or not current_user.id:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("core.login"))
        
        from sqlalchemy import func
        from datetime import date, timedelta
        
        # Get devices
        devices = POSDevice.query.filter_by(is_active=True).all() or []
        open_shifts = POSShift.query.filter_by(status="open", user_id=current_user.id).all() or []
        
        # Statistics
        today = date.today()
        yesterday = today - timedelta(days=1)
        this_week_start = today - timedelta(days=today.weekday())
        
        # Today's stats
        today_orders = POSOrder.query.filter(
            db.func.date(POSOrder.order_time) == today
        ).count()
        
        today_revenue = db.session.query(func.sum(POSOrder.total_amount)).filter(
            db.func.date(POSOrder.order_time) == today,
            POSOrder.status == "paid"
        ).scalar() or Decimal("0.00")
        
        # This week's stats
        week_orders = POSOrder.query.filter(
            db.func.date(POSOrder.order_time) >= this_week_start
        ).count()
        
        week_revenue = db.session.query(func.sum(POSOrder.total_amount)).filter(
            db.func.date(POSOrder.order_time) >= this_week_start,
            POSOrder.status == "paid"
        ).scalar() or Decimal("0.00")
        
        # Active shifts
        all_open_shifts = POSShift.query.filter_by(status="open").all()
        
        # Recent orders
        recent_orders = POSOrder.query.order_by(
            POSOrder.order_time.desc()
        ).limit(10).all()
        
        # Top products
        top_products = db.session.query(
            POSOrderLine.product_name,
            func.sum(POSOrderLine.qty).label('total_qty'),
            func.sum(POSOrderLine.line_total).label('total_revenue')
        ).join(POSOrder).filter(
            db.func.date(POSOrder.order_time) >= this_week_start,
            POSOrder.status == "paid"
        ).group_by(POSOrderLine.product_name).order_by(
            func.sum(POSOrderLine.line_total).desc()
        ).limit(10).all()
        
        return render_template(
            "pos/dashboard.html",
            devices=devices,
            open_shifts=open_shifts,
            all_open_shifts=all_open_shifts,
            today_orders=today_orders,
            today_revenue=today_revenue,
            week_orders=week_orders,
            week_revenue=week_revenue,
            recent_orders=recent_orders,
            top_products=top_products,
        )
    except Exception as e:
        current_app.logger.exception("Error loading POS dashboard")
        return redirect(url_for("core.dashboard"))

@pos_bp.route("/launcher")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def launcher():
    """POS terminal launcher page."""
    try:
        if not current_user or not current_user.id:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("core.login"))
        
        devices = POSDevice.query.filter_by(is_active=True).all() or []
        open_shifts = POSShift.query.filter_by(status="open", user_id=current_user.id).all() or []
        
        return render_template(
            "pos/pos_terminal.html",
            devices=devices,
            open_shifts=open_shifts,
        )
    except Exception as e:
        current_app.logger.exception("Error loading POS launcher page")
        return redirect(url_for("core.dashboard"))

@pos_bp.route("/terminal/<device_code>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def terminal(device_code):
    """POS terminal UI page."""
    try:
        if not current_user or not current_user.id:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("core.login"))
        
        if not device_code:
            flash("Device code is required.", "error")
            return redirect(url_for("pos.index"))
        
        device = POSDevice.query.filter_by(terminal_code=device_code, is_active=True).first()
        if not device:
            flash(f"Device '{device_code}' not found or inactive.", "error")
            return redirect(url_for("pos.index"))
        
        open_shift = POSShift.query.filter_by(
            device_id=device.id,
            user_id=current_user.id,
            status="open"
        ).first()
        
        # Update device last seen
        try:
            device.last_seen = datetime.utcnow()
            db.session.commit()
        except Exception as db_error:
            current_app.logger.warning(f"Failed to update device last_seen: {db_error}")
            db.session.rollback()
            # Continue anyway - this is not critical
        
        # Get printer settings from device
        printer_settings = {
            "enabled": device.printer_enabled if hasattr(device, 'printer_enabled') else False,
            "auto_print": device.auto_print_receipts if hasattr(device, 'auto_print_receipts') else False,
            "printer_name": device.printer_name if hasattr(device, 'printer_name') else None,
            "paper_width": device.printer_paper_width if hasattr(device, 'printer_paper_width') else 80,
            "copies": device.printer_copies if hasattr(device, 'printer_copies') else 1,
        }
        
        return render_template(
            "pos/pos_terminal_ui.html",
            device=device,
            open_shift=open_shift,
            printer_settings=printer_settings,
        )
    except Exception as e:
        current_app.logger.exception(f"Error loading POS terminal for device {device_code}")
        db.session.rollback()
        return redirect(url_for("pos.index"))

# REST API Endpoints

@pos_bp.route("/api/devices")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_devices_list():
    """API: List POS devices."""
    devices = POSDevice.query.filter_by(is_active=True).all()
    
    return jsonify({
        "status": "success",
        "devices": [
            {
                "id": device.id,
                "name": device.name,
                "terminal_code": device.terminal_code,
                "location": device.location,
                "is_active": device.is_active,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "printer_settings": {
                    "enabled": device.printer_enabled if hasattr(device, 'printer_enabled') else False,
                    "auto_print": device.auto_print_receipts if hasattr(device, 'auto_print_receipts') else False,
                    "printer_name": device.printer_name if hasattr(device, 'printer_name') else None,
                    "paper_width": device.printer_paper_width if hasattr(device, 'printer_paper_width') else 80,
                    "copies": device.printer_copies if hasattr(device, 'printer_copies') else 1,
                } if hasattr(device, 'printer_enabled') else {},
            }
            for device in devices
        ],
    })

@pos_bp.route("/api/devices", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_device_create():
    """API: Register new POS device."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    try:
        device = POSDevice(
            name=data.get("name"),
            terminal_code=data.get("terminal_code"),
            location=data.get("location"),
            is_active=data.get("is_active", True),
            printer_enabled=data.get("printer_enabled", False),
            auto_print_receipts=data.get("auto_print_receipts", False),
            printer_name=data.get("printer_name"),
            printer_paper_width=data.get("printer_paper_width", 80),
            printer_copies=data.get("printer_copies", 1),
        )
        db.session.add(device)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Device registered",
            "device_id": device.id,
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@pos_bp.route("/api/devices/<int:device_id>/printer", methods=["GET", "POST", "PUT"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_device_printer_settings(device_id):
    """API: Get or update printer settings for a device."""
    device = POSDevice.query.get_or_404(device_id)
    
    if request.method == "GET":
        return jsonify({
            "status": "success",
            "printer_settings": {
                "enabled": device.printer_enabled if hasattr(device, 'printer_enabled') else False,
                "auto_print": device.auto_print_receipts if hasattr(device, 'auto_print_receipts') else False,
                "printer_name": device.printer_name if hasattr(device, 'printer_name') else None,
                "paper_width": device.printer_paper_width if hasattr(device, 'printer_paper_width') else 80,
                "copies": device.printer_copies if hasattr(device, 'printer_copies') else 1,
            }
        })
    
    # POST/PUT - Update printer settings
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    try:
        if hasattr(device, 'printer_enabled'):
            device.printer_enabled = data.get("enabled", device.printer_enabled)
        if hasattr(device, 'auto_print_receipts'):
            device.auto_print_receipts = data.get("auto_print", device.auto_print_receipts)
        if hasattr(device, 'printer_name'):
            device.printer_name = data.get("printer_name")
        if hasattr(device, 'printer_paper_width'):
            device.printer_paper_width = int(data.get("paper_width", device.printer_paper_width))
        if hasattr(device, 'printer_copies'):
            device.printer_copies = int(data.get("copies", device.printer_copies))
        
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Printer settings updated",
            "printer_settings": {
                "enabled": device.printer_enabled if hasattr(device, 'printer_enabled') else False,
                "auto_print": device.auto_print_receipts if hasattr(device, 'auto_print_receipts') else False,
                "printer_name": device.printer_name if hasattr(device, 'printer_name') else None,
                "paper_width": device.printer_paper_width if hasattr(device, 'printer_paper_width') else 80,
                "copies": device.printer_copies if hasattr(device, 'printer_copies') else 1,
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error updating printer settings")
        return jsonify({"status": "error", "message": str(e)}), 400

@pos_bp.route("/api/shifts/start", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_shift_start():
    """API: Start a new shift."""
    try:
        # Validate request format
        if not request.is_json:
            return jsonify({"status": "error", "message": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate device code
        device_code = data.get("device_code")
        if not device_code:
            return jsonify({"status": "error", "message": "Device code is required"}), 400
        
        # Validate starting cash
        try:
            starting_cash = Decimal(str(data.get("starting_cash", 0)))
            if starting_cash < 0:
                return jsonify({"status": "error", "message": "Starting cash cannot be negative"}), 400
        except (ValueError, TypeError) as e:
            return jsonify({"status": "error", "message": f"Invalid starting cash amount: {str(e)}"}), 400
        
        # Validate user is authenticated
        if not current_user or not current_user.id:
            return jsonify({"status": "error", "message": "User not authenticated"}), 401
        
        # Find device
        device = POSDevice.query.filter_by(terminal_code=device_code, is_active=True).first()
        if not device:
            return jsonify({"status": "error", "message": f"Device '{device_code}' not found or inactive"}), 404
        
        # Check for existing open shift on this device by this user
        existing_shift = POSShift.query.filter_by(
            device_id=device.id,
            user_id=current_user.id,
            status="open"
        ).first()
        
        if existing_shift:
            return jsonify({
                "status": "error",
                "message": "You already have an open shift on this device",
                "shift_id": existing_shift.id,
            }), 400
        
        # Check for any open shift on this device by any user
        any_open_shift = POSShift.query.filter_by(
            device_id=device.id,
            status="open"
        ).first()
        
        if any_open_shift:
            return jsonify({
                "status": "error",
                "message": "This device already has an open shift. Please close it first.",
                "shift_id": any_open_shift.id,
            }), 400
        
        # Create new shift with explicit started_at
        shift = POSShift(
            device_id=device.id,
            user_id=current_user.id,
            starting_cash=starting_cash,
            status="open",
            started_at=datetime.utcnow(),  # Explicitly set started_at
        )
        
        db.session.add(shift)
        
        try:
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            current_app.logger.exception(f"Database error starting shift: {db_error}")
            return jsonify({
                "status": "error",
                "message": "Failed to save shift to database. Please try again."
            }), 500
        
        # Refresh to get the committed object
        db.session.refresh(shift)
        
        return jsonify({
            "status": "success",
            "message": "Shift started successfully",
            "shift_id": shift.id,
            "started_at": shift.started_at.isoformat() if shift.started_at else datetime.utcnow().isoformat(),
        }), 201
        
    except ValueError as ve:
        db.session.rollback()
        current_app.logger.warning(f"Validation error starting shift: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Unexpected error starting POS shift")
        # Return a generic message to user but log full error
        error_msg = "An unexpected error occurred while starting the shift. Please try again."
        return jsonify({"status": "error", "message": error_msg}), 500

@pos_bp.route("/api/shifts/<int:shift_id>/close", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_shift_close(shift_id):
    """API: Close shift and generate Z-report."""
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        try:
            ending_cash = Decimal(str(data.get("ending_cash", 0)))
        except (ValueError, TypeError) as e:
            return jsonify({"status": "error", "message": f"Invalid ending cash amount: {str(e)}"}), 400
        
        shift = POSShift.query.get(shift_id)
        if not shift:
            return jsonify({"status": "error", "message": "Shift not found"}), 404
        
        if shift.user_id != current_user.id:
            return jsonify({"status": "error", "message": "You can only close your own shifts"}), 403
        
        if shift.status == "closed":
            return jsonify({"status": "error", "message": "Shift is already closed"}), 400
        
        z_report = close_shift(shift_id, float(ending_cash))
        
        return jsonify({
            "status": "success",
            "message": "Shift closed successfully",
            "shift_id": shift.id,
            "z_report": z_report,
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error closing POS shift")
        return jsonify({"status": "error", "message": f"Failed to close shift: {str(e)}"}), 500

@pos_bp.route("/api/orders")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_orders_list():
    """API: List POS orders."""
    status_filter = request.args.get("status")
    date_filter = request.args.get("date")
    
    query = POSOrder.query
    
    if status_filter:
        query = query.filter(POSOrder.status == status_filter)
    
    if date_filter:
        try:
            filter_date = datetime.fromisoformat(date_filter).date()
            query = query.filter(db.func.date(POSOrder.order_time) == filter_date)
        except (ValueError, TypeError):
            pass
    
    query = query.order_by(POSOrder.order_time.desc())
    pagination = paginate_query(query)
    
    return jsonify({
        "status": "success",
        "orders": [
            {
                "id": order.id,
                "reference": order.reference,
                "client_id": order.client_id,
                "client_name": order.client.name if order.client else None,
                "order_time": order.order_time.isoformat(),
                "total_amount": float(order.total_amount),
                "status": order.status,
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

@pos_bp.route("/api/orders", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_order_create():
    """API: Create POS order."""
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate required fields
        items = data.get("items", [])
        if not items or len(items) == 0:
            return jsonify({"status": "error", "message": "Order must contain at least one item"}), 400
        
        # Get shift_id - handle null/None from frontend
        shift_id = data.get("shift_id")
        if shift_id is None or shift_id == "" or shift_id == "null":
            shift_id = None
        
        # Get device_code - validate it's provided
        device_code = data.get("device_code")
        if not device_code:
            return jsonify({"status": "error", "message": "Device code is required"}), 400
        
        # Validate shift if provided
        if shift_id:
            try:
                shift_id = int(shift_id)
                shift = POSShift.query.get(shift_id)
                if not shift:
                    return jsonify({"status": "error", "message": f"Shift with ID {shift_id} not found"}), 404
                if shift.status != "open":
                    return jsonify({"status": "error", "message": f"Cannot create order for closed shift (ID: {shift_id})"}), 400
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": "Invalid shift ID format"}), 400
        
        # Create order using service
        order = create_order(
            payload=data,
            device_code=device_code,
            shift_id=shift_id,
        )
        
        return jsonify({
            "status": "success",
            "message": "Order created successfully",
            "order_id": order.id,
            "reference": order.reference,
        }), 201
        
    except ValueError as ve:
        db.session.rollback()
        current_app.logger.warning(f"Validation error creating order: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error creating POS order")
        error_message = str(e) if str(e) else "Failed to create order. Please try again."
        return jsonify({"status": "error", "message": error_message}), 500

@pos_bp.route("/api/orders/<int:order_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_order_detail(order_id):
    """API: Get order details."""
    order = POSOrder.query.get_or_404(order_id)
    
    return jsonify({
        "status": "success",
        "order": {
            "id": order.id,
            "reference": order.reference,
            "client_id": order.client_id,
            "client_name": order.client.name if order.client else None,
            "order_time": order.order_time.isoformat(),
            "total_amount": float(order.total_amount),
            "tax_amount": float(order.tax_amount),
            "discount_amount": float(order.discount_amount),
            "status": order.status,
            "is_delivery": order.is_delivery,
            "delivery_address": order.delivery_address,
            "lines": [
                {
                    "id": line.id,
                    "product_id": line.product_id,
                    "product_name": line.product_name,
                    "qty": line.qty,
                    "unit_price": float(line.unit_price),
                    "line_total": float(line.line_total),
                    "note": line.note,
                }
                for line in order.lines
            ],
            "payments": [
                {
                    "id": payment.id,
                    "amount": float(payment.amount),
                    "method": payment.method,
                    "ref": payment.ref,
                    "payment_time": payment.payment_time.isoformat() if payment.payment_time else None,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None,
                    "receipt_id": payment.receipt.id if payment.receipt else None,
                    "receipt_ref": payment.receipt.receipt_ref if payment.receipt else None,
                }
                for payment in order.payments
            ],
        },
    })

@pos_bp.route("/api/orders/<int:order_id>/status", methods=["PATCH", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_order_status(order_id):
    """API: Update order status."""
    order = POSOrder.query.get_or_404(order_id)
    
    if request.is_json:
        data = request.get_json()
        new_status = data.get("status")
    else:
        new_status = request.form.get("status")
    
    if not new_status:
        return jsonify({"status": "error", "message": "Status is required"}), 400
    
    valid_statuses = ["draft", "paid", "partially_paid", "cancelled", "refunded"]
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

@pos_bp.route("/api/orders/<int:order_id>/payments", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_order_payment(order_id):
    """API: Record payment for order."""
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate amount
        try:
            amount = Decimal(str(data.get("amount", 0)))
            if amount <= 0:
                return jsonify({"status": "error", "message": "Payment amount must be greater than 0"}), 400
        except (ValueError, TypeError) as e:
            return jsonify({"status": "error", "message": f"Invalid payment amount: {str(e)}"}), 400
        
        method = data.get("method", "cash")
        ref = data.get("ref")
        
        # Validate order exists (service will also check, but check here first for better error)
        order = POSOrder.query.get(order_id)
        if not order:
            return jsonify({"status": "error", "message": f"Order with ID {order_id} not found"}), 404
        
        # Use service to add payment (returns tuple: payment, receipt)
        # Receipt is generated immediately when payment is created
        payment, receipt = add_payment(
            order_id=order_id,
            amount=float(amount),
            method=method,
            ref=ref,
            received_by=current_user.id
        )
        
        # Ensure payment and receipt are properly refreshed
        db.session.refresh(payment)
        db.session.refresh(receipt)
        db.session.refresh(order)
        
        # Get all payment records for this order to track payment history
        all_payments = POSPayment.query.filter_by(order_id=order_id).order_by(POSPayment.payment_time.asc()).all()
        payment_history = [
            {
                "id": p.id,
                "amount": float(p.amount),
                "method": p.method,
                "ref": p.ref,
                "payment_time": p.payment_time.isoformat() if p.payment_time else None,
                "receipt_ref": p.receipt.receipt_ref if p.receipt else None,
            }
            for p in all_payments
        ]
        
        # Calculate payment summary
        total_paid = sum(Decimal(str(p.amount)) for p in all_payments)
        remaining = Decimal(str(order.total_amount)) - total_paid
        
        return jsonify({
            "status": "success",
            "message": "Payment recorded successfully",
            "payment": {
                "id": payment.id,
                "amount": float(payment.amount),
                "method": payment.method,
                "ref": payment.ref,
                "payment_time": payment.payment_time.isoformat() if payment.payment_time else None,
            },
            "receipt": {
                "id": receipt.id,
                "receipt_ref": receipt.receipt_ref,
                "issued_at": receipt.issued_at.isoformat() if receipt.issued_at else None,
            },
            "order": {
                "id": order.id,
                "reference": order.reference,
                "total_amount": float(order.total_amount),
                "status": order.status,
            },
            "payment_summary": {
                "total_amount": float(order.total_amount),
                "total_paid": float(total_paid),
                "remaining": float(remaining) if remaining > 0 else 0,
                "is_fully_paid": remaining <= 0,
            },
            "payment_history": payment_history,
        }), 201
        
    except ValueError as ve:
        db.session.rollback()
        current_app.logger.warning(f"Validation error recording payment: {ve}")
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error recording payment")
        error_message = str(e) if str(e) else "Failed to record payment. Please try again."
        return jsonify({"status": "error", "message": error_message}), 500

@pos_bp.route("/api/orders/<int:order_id>/reserve", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_order_reserve(order_id):
    """API: Reserve inventory for order."""
    try:
        reserve_inventory_for_order(order_id)
        return jsonify({
            "status": "success",
            "message": "Inventory reserved",
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@pos_bp.route("/api/orders/<int:order_id>/release", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_order_release(order_id):
    """API: Release inventory for order."""
    try:
        release_inventory(order_id)
        return jsonify({
            "status": "success",
            "message": "Inventory released",
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@pos_bp.route("/api/orders/<int:order_id>/receipt")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_order_receipt(order_id):
    """API: Get receipt for order."""
    order = POSOrder.query.get_or_404(order_id)
    payment = POSPayment.query.filter_by(order_id=order_id).order_by(POSPayment.payment_time.desc()).first()
    
    if not payment:
        return jsonify({"status": "error", "message": "No payment found for this order"}), 404
    
    receipt = POSReceipt.query.filter_by(payment_id=payment.id).first()
    
    if not receipt:
        return jsonify({"status": "error", "message": "No receipt found for this payment"}), 404
    
    return jsonify({
        "status": "success",
        "receipt": {
            "id": receipt.id,
            "receipt_ref": receipt.receipt_ref,
            "payment_id": payment.id,
            "amount": float(payment.amount),
            "method": payment.method,
            "issued_at": receipt.issued_at.isoformat() if receipt.issued_at else None,
        },
    })

@pos_bp.route("/receipts/<int:receipt_id>/print")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def receipt_print(receipt_id):
    """Print preview page for POS receipt."""
    receipt = POSReceipt.query.get_or_404(receipt_id)
    payment = receipt.payment
    order = payment.order
    
    # Get all payment records for this order
    all_payments = POSPayment.query.filter_by(order_id=order.id).order_by(POSPayment.payment_time.asc()).all()
    total_paid = sum(Decimal(str(p.amount)) for p in all_payments)
    
    payment_summary = {
        "total_amount": float(order.total_amount),
        "total_paid": float(total_paid),
        "remaining": float(Decimal(str(order.total_amount)) - total_paid) if Decimal(str(order.total_amount)) - total_paid > 0 else 0,
        "is_fully_paid": total_paid >= Decimal(str(order.total_amount)),
    }
    
    return render_template(
        "pos/receipt_print.html",
        receipt=receipt,
        payment=payment,
        order=order,
        payment_summary=payment_summary,
    )

@pos_bp.route("/api/receipts/<int:receipt_id>")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_receipt_detail(receipt_id):
    """API: Get receipt details."""
    receipt = POSReceipt.query.get_or_404(receipt_id)
    payment = receipt.payment
    order = payment.order
    
    # Get all payment records for this order to show payment history
    all_payments = POSPayment.query.filter_by(order_id=order.id).order_by(POSPayment.payment_time.asc()).all()
    payment_history = [
        {
            "id": p.id,
            "amount": float(p.amount),
            "method": p.method,
            "ref": p.ref,
            "payment_time": p.payment_time.isoformat() if p.payment_time else None,
            "receipt_ref": p.receipt.receipt_ref if p.receipt else None,
        }
        for p in all_payments
    ]
    
    total_paid = sum(Decimal(str(p.amount)) for p in all_payments)
    
    return jsonify({
        "status": "success",
        "receipt": {
            "id": receipt.id,
            "receipt_ref": receipt.receipt_ref,
            "payment_id": payment.id,
            "order_id": order.id,
            "order_reference": order.reference,
            "amount": float(payment.amount),
            "method": payment.method,
            "payment_ref": payment.ref,
            "issued_at": receipt.issued_at.isoformat() if receipt.issued_at else None,
            "payment_time": payment.payment_time.isoformat() if payment.payment_time else None,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
        },
        "order": {
            "id": order.id,
            "reference": order.reference,
            "order_time": order.order_time.isoformat() if order.order_time else None,
            "status": order.status,
            "order_lines": [
                {
                    "product_name": line.product_name,
                    "qty": line.qty,
                    "unit_price": float(line.unit_price),
                    "line_total": float(line.line_total),
                }
                for line in order.lines
            ],
            "subtotal": float(order.total_amount - order.tax_amount),
            "tax": float(order.tax_amount),
            "discount": float(order.discount_amount),
            "total": float(order.total_amount),
        },
        "payment_summary": {
            "total_amount": float(order.total_amount),
            "total_paid": float(total_paid),
            "remaining": float(Decimal(str(order.total_amount)) - total_paid) if Decimal(str(order.total_amount)) - total_paid > 0 else 0,
            "is_fully_paid": total_paid >= Decimal(str(order.total_amount)),
        },
        "payment_history": payment_history,
    })

@pos_bp.route("/api/orders/<int:order_id>/payments")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_order_payments_list(order_id):
    """API: Get all payment records for an order."""
    order = POSOrder.query.get_or_404(order_id)
    
    # Get all payment records with receipts
    payments = POSPayment.query.filter_by(order_id=order_id).order_by(POSPayment.payment_time.asc()).all()
    
    payment_records = []
    total_paid = Decimal("0.00")
    
    for payment in payments:
        payment_amount = Decimal(str(payment.amount))
        total_paid += payment_amount
        
        payment_records.append({
            "id": payment.id,
            "amount": float(payment.amount),
            "method": payment.method,
            "ref": payment.ref,
            "payment_time": payment.payment_time.isoformat() if payment.payment_time else None,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "receipt": {
                "id": payment.receipt.id if payment.receipt else None,
                "receipt_ref": payment.receipt.receipt_ref if payment.receipt else None,
                "issued_at": payment.receipt.issued_at.isoformat() if payment.receipt and payment.receipt.issued_at else None,
            } if payment.receipt else None,
        })
    
    remaining = Decimal(str(order.total_amount)) - total_paid
    
    return jsonify({
        "status": "success",
        "order": {
            "id": order.id,
            "reference": order.reference,
            "total_amount": float(order.total_amount),
            "status": order.status,
        },
        "payments": payment_records,
        "payment_summary": {
            "total_amount": float(order.total_amount),
            "total_paid": float(total_paid),
            "remaining": float(remaining) if remaining > 0 else 0,
            "is_fully_paid": remaining <= 0,
            "payment_count": len(payment_records),
        },
    })

def get_image_url(item, item_type):
    """Get image URL for a product item, with placeholder fallback."""
    if hasattr(item, 'image_url') and item.image_url:
        return item.image_url
    # Return placeholder image URL
    return url_for('static', filename='images/product-placeholder.png', _external=True) if hasattr(current_app, 'app_context') else '/static/images/product-placeholder.png'

@pos_bp.route("/products")
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_products():
    """API: Get all products available for POS (Catering, Bakery, and custom POS products)."""
    try:
        from models import CateringItem, BakeryItem
        from decimal import Decimal
        
        # Get catering items with current prices
        catering_items = CateringItem.query.all()
        catering_products = []
        for item in catering_items:
            try:
                current_price = item.get_current_price()
                # Ensure we have a valid price
                if current_price is None:
                    current_price = Decimal("0.00")
                # Convert to float safely
                price_float = float(current_price) if isinstance(current_price, Decimal) else float(str(current_price))
                if price_float > 0:  # Only include items with prices
                    catering_products.append({
                        "id": item.id,
                        "name": item.name,
                        "type": "CATERING",
                        "price": price_float,
                        "category": "Catering",
                        "image_url": item.image_url if hasattr(item, 'image_url') and item.image_url else url_for('static', filename='images/product-placeholder.svg'),
                    })
            except Exception as e:
                current_app.logger.warning(f"Error getting price for catering item {item.id}: {e}")
                continue
        
        # Get bakery items with current prices
        bakery_items = BakeryItem.query.filter_by(status="Active").all()
        bakery_products = []
        for item in bakery_items:
            try:
                current_price = item.get_current_price()
                # Ensure we have a valid price
                if current_price is None:
                    current_price = Decimal("0.00")
                # Convert to float safely
                price_float = float(current_price) if isinstance(current_price, Decimal) else float(str(current_price))
                if price_float > 0:  # Only include items with prices
                    bakery_products.append({
                        "id": item.id,
                        "name": item.name,
                        "type": "BAKERY",
                        "price": price_float,
                        "category": item.category or "Bakery",
                        "image_url": item.image_url if hasattr(item, 'image_url') and item.image_url else url_for('static', filename='images/product-placeholder.svg'),
                    })
            except Exception as e:
                current_app.logger.warning(f"Error getting price for bakery item {item.id}: {e}")
                continue
        
        # Get custom POS products
        pos_products = POSProduct.query.filter_by(is_active=True).all()
        custom_products = []
        for item in pos_products:
            try:
                custom_products.append({
                    "id": f"POS-{item.id}",  # Prefix to distinguish from Catering/Bakery items
                    "name": item.name,
                    "type": "POS_PRODUCT",
                    "price": float(item.price),
                    "category": item.category or "Custom",
                    "image_url": item.image_url if item.image_url else url_for('static', filename='images/product-placeholder.png'),
                    "description": item.description,
                })
            except Exception as e:
                current_app.logger.warning(f"Error processing POS product {item.id}: {e}")
                continue
        
        all_products = catering_products + bakery_products + custom_products
        
        return jsonify({
            "status": "success",
            "products": all_products,
            "count": len(all_products),
        })
    except Exception as e:
        current_app.logger.exception("Error fetching POS products")
        return jsonify({"status": "error", "message": str(e)}), 500

@pos_bp.route("/api/products/upload-image", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_product_upload_image():
    """API: Upload product image."""
    try:
        if 'image' not in request.files:
            return jsonify({"status": "error", "message": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
        if not file.filename or '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({"status": "error", "message": "File type not allowed. Use PNG, JPG, JPEG, GIF, WEBP, or SVG"}), 400
        
        # Create upload directory if it doesn't exist
        upload_folder = os.path.join(current_app.instance_path, "..", "static", "uploads", "pos_products")
        upload_folder = os.path.abspath(upload_folder)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{timestamp}{ext}"
        
        # Save file
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Generate URL path (relative to static folder)
        image_url = f"/static/uploads/pos_products/{filename}"
        
        return jsonify({
            "status": "success",
            "message": "Image uploaded successfully",
            "image_url": image_url,
        }), 200
        
    except Exception as e:
        current_app.logger.exception("Error uploading product image")
        return jsonify({"status": "error", "message": str(e)}), 500

@pos_bp.route("/api/products", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_product_create():
    """API: Add a new custom product to POS."""
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Request must be JSON"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Validate required fields
        name = data.get("name")
        if not name:
            return jsonify({"status": "error", "message": "Product name is required"}), 400
        
        try:
            price = Decimal(str(data.get("price", 0)))
            if price < 0:
                return jsonify({"status": "error", "message": "Price cannot be negative"}), 400
        except (ValueError, TypeError) as e:
            return jsonify({"status": "error", "message": f"Invalid price: {str(e)}"}), 400
        
        # Check for duplicate name
        existing = POSProduct.query.filter_by(name=name, is_active=True).first()
        if existing:
            return jsonify({"status": "error", "message": f"Product with name '{name}' already exists"}), 400
        
        # Create new POS product
        product = POSProduct(
            name=name,
            description=data.get("description"),
            category=data.get("category"),
            price=price,
            image_url=data.get("image_url"),
            barcode=data.get("barcode"),
            sku=data.get("sku"),
            tax_rate=Decimal(str(data.get("tax_rate", 18.0))),
            is_active=True,
            created_by=current_user.id,
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Product added successfully",
            "product_id": product.id,
            "product": {
                "id": f"POS-{product.id}",
                "name": product.name,
                "type": "POS_PRODUCT",
                "price": float(product.price),
                "category": product.category or "Custom",
                "image_url": product.image_url or url_for('static', filename='images/product-placeholder.svg'),
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error creating POS product")
        return jsonify({"status": "error", "message": str(e)}), 500

@pos_bp.route("/api/products/<int:product_id>", methods=["DELETE", "PUT"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_product_manage(product_id):
    """API: Remove or update a custom POS product."""
    try:
        product = POSProduct.query.get_or_404(product_id)
        
        if request.method == "DELETE":
            # Soft delete - set is_active to False
            product.is_active = False
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Product removed successfully",
                "product_id": product.id,
            })
        
        elif request.method == "PUT":
            # Update product
            if not request.is_json:
                return jsonify({"status": "error", "message": "Request must be JSON"}), 400
            
            data = request.get_json()
            
            if data.get("name"):
                product.name = data.get("name")
            if "description" in data:
                product.description = data.get("description")
            if "category" in data:
                product.category = data.get("category")
            if "price" in data:
                try:
                    product.price = Decimal(str(data.get("price")))
                    if product.price < 0:
                        return jsonify({"status": "error", "message": "Price cannot be negative"}), 400
                except (ValueError, TypeError) as e:
                    return jsonify({"status": "error", "message": f"Invalid price: {str(e)}"}), 400
            if "image_url" in data:
                product.image_url = data.get("image_url")
            if "barcode" in data:
                product.barcode = data.get("barcode")
            if "sku" in data:
                product.sku = data.get("sku")
            if "tax_rate" in data:
                product.tax_rate = Decimal(str(data.get("tax_rate", 18.0)))
            if "is_active" in data:
                product.is_active = bool(data.get("is_active"))
            
            db.session.commit()
            
            return jsonify({
                "status": "success",
                "message": "Product updated successfully",
                "product_id": product.id,
                "product": {
                    "id": f"POS-{product.id}",
                    "name": product.name,
                    "type": "POS_PRODUCT",
                    "price": float(product.price),
                    "category": product.category or "Custom",
                    "image_url": product.image_url or url_for('static', filename='images/product-placeholder.svg'),
                }
            })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error managing POS product {product_id}")
        return jsonify({"status": "error", "message": str(e)}), 500

@pos_bp.route("/api/sync", methods=["POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def api_sync():
    """API: Sync offline orders."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400
    
    data = request.get_json()
    device_code = data.get("device_code")
    orders = data.get("orders", [])
    
    try:
        result = sync_orders_for_offline(device_code, orders)
        return jsonify({
            "status": "success",
            "message": "Orders synced",
            "synced_count": result.get("synced_count", 0),
            "failed_count": result.get("failed_count", 0),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

