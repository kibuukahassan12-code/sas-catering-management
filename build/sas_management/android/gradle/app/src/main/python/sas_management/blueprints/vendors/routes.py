"""Vendor Management routes."""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date
import json
import secrets

from models import db, Supplier, PurchaseOrder, PurchaseOrderItem, SupplierQuote, UserRole
from utils import role_required, permission_required
from services.vendors_service import create_purchase_order

vendors_bp = Blueprint("vendors", __name__, url_prefix="/vendors")

@vendors_bp.route("/")
@login_required
@permission_required("vendors")
def vendors_list():
    """List suppliers/vendors."""
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return render_template("vendors/vendors_list.html", suppliers=suppliers)

@vendors_bp.route("/purchase-orders")
@vendors_bp.route("/purchase-orders-list")
@login_required
@permission_required("procurement")
def purchase_orders_list():
    """List purchase orders."""
    orders = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(50).all()
    return render_template("vendors/purchase_orders.html", orders=orders)

@vendors_bp.route("/create-po", methods=["GET", "POST"])
@login_required
@role_required(UserRole.Admin, UserRole.SalesManager)
def create_po():
    """Create purchase order."""
    try:
        suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    except Exception:
        suppliers = []
    
    if request.method == "POST":
        try:
            supplier_id = request.form.get('supplier_id')
            po_date = request.form.get('po_date') or date.today().isoformat()
            expected_date = request.form.get('expected_date') or None
            reference = request.form.get('reference') or None
            action = request.form.get('action', 'create')
            items_json = request.form.get('items_json', '[]')
            
            # Basic validation
            if not supplier_id:
                flash("Please select a supplier", "danger")
                return render_template('vendors/create_po.html', suppliers=suppliers, now_date=date.today().isoformat())
            
            # Parse items
            try:
                items = json.loads(items_json)
            except json.JSONDecodeError:
                items = []
            
            if not items:
                flash("Please add at least one item to the purchase order", "danger")
                return render_template('vendors/create_po.html', suppliers=suppliers, now_date=date.today().isoformat())
            
            # Create PO using service
            po = create_purchase_order(
                supplier_id=int(supplier_id),
                user_id=current_user.id,
                po_date=po_date,
                expected_date=expected_date,
                reference=reference,
                items=items,
                status='draft' if action == 'draft' else 'open'
            )
            
            flash(f"Purchase Order {po.po_number or po.order_number} created successfully!", "success")
            return redirect(url_for('vendors.purchase_orders_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating purchase order: {str(e)}", "danger")
            return render_template('vendors/create_po.html', suppliers=suppliers, now_date=date.today().isoformat())
    
    # GET request
    return render_template('vendors/create_po.html', suppliers=suppliers, now_date=date.today().isoformat())

