from datetime import datetime
from flask import current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from sas_management.models import ProductionInventoryItem, ProductionInventoryMovement, db, UserRole
from sas_management.utils.helpers import get_or_404


def add_production_inventory_routes(production_bp, role_required_decorator, paginate_helper):
    """Add production daily-use inventory routes to production blueprint."""

    @production_bp.route("/daily-inventory")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def daily_inventory_list():
        """List production daily-use inventory items."""
        q = ProductionInventoryItem.query

        search = (request.args.get("q") or "").strip()
        category = (request.args.get("category") or "").strip()
        low_stock = (request.args.get("low_stock") or "").strip()

        if search:
            like = f"%{search}%"
            q = q.filter(ProductionInventoryItem.name.ilike(like))
        if category:
            q = q.filter(ProductionInventoryItem.category == category)
        if low_stock in ("1", "true", "yes", "on"):
            q = q.filter(ProductionInventoryItem.quantity <= ProductionInventoryItem.min_quantity)

        q = q.order_by(ProductionInventoryItem.name.asc())

        pagination = paginate_helper(q, per_page=20)

        try:
            categories = [
                c[0]
                for c in db.session.query(ProductionInventoryItem.category).distinct().all()
                if c and c[0]
            ]
        except Exception:
            categories = []

        return render_template(
            "production/daily_inventory_list.html",
            items=pagination.items,
            pagination=pagination,
            categories=sorted(categories),
            search=search,
            selected_category=category,
            low_stock=low_stock,
        )

    @production_bp.route("/daily-inventory/add", methods=["GET", "POST"])
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def daily_inventory_add():
        """Create a production daily-use inventory item."""
        if request.method == "POST":
            try:
                name = (request.form.get("name") or "").strip()
                if not name:
                    flash("Item name is required.", "error")
                    return render_template("production/daily_inventory_form.html", action="Add", item=None)

                category = (request.form.get("category") or "").strip() or None
                unit = (request.form.get("unit") or "").strip() or "pcs"
                condition = (request.form.get("condition") or "").strip() or "Good"
                location = (request.form.get("location") or "").strip() or None
                notes = (request.form.get("notes") or "").strip() or None

                def _to_int(val, default=0):
                    try:
                        return int(str(val).strip() or default)
                    except Exception:
                        return default

                quantity = _to_int(request.form.get("quantity"), 0)
                min_quantity = _to_int(request.form.get("min_quantity"), 0)
                if quantity < 0 or min_quantity < 0:
                    flash("Quantity values cannot be negative.", "error")
                    return render_template("production/daily_inventory_form.html", action="Add", item=None)

                item = ProductionInventoryItem(
                    name=name,
                    category=category,
                    unit=unit,
                    quantity=quantity,
                    min_quantity=min_quantity,
                    condition=condition,
                    location=location,
                    notes=notes,
                    created_by=getattr(current_user, "id", None),
                )
                db.session.add(item)
                db.session.flush()

                # Opening movement if quantity was set
                if quantity != 0:
                    db.session.add(
                        ProductionInventoryMovement(
                            item_id=item.id,
                            quantity_change=quantity,
                            resulting_quantity=quantity,
                            movement_type="opening",
                            note="Opening balance (item created).",
                            created_by=getattr(current_user, "id", None),
                        )
                    )

                db.session.commit()
                flash("Item added to Production inventory.", "success")
                return redirect(url_for("production.daily_inventory_list"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error creating production inventory item: {e}")
                flash("Failed to add item. Please check inputs and try again.", "error")

        return render_template("production/daily_inventory_form.html", action="Add", item=None)

    @production_bp.route("/daily-inventory/edit/<int:item_id>", methods=["GET", "POST"])
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def daily_inventory_edit(item_id: int):
        """Edit a production daily-use inventory item."""
        item = ProductionInventoryItem.query.get_or_404(item_id)

        if request.method == "POST":
            try:
                old_qty = int(item.quantity or 0)

                name = (request.form.get("name") or "").strip()
                if not name:
                    flash("Item name is required.", "error")
                    return render_template("production/daily_inventory_form.html", action="Edit", item=item)

                item.name = name
                item.category = (request.form.get("category") or "").strip() or None
                item.unit = (request.form.get("unit") or "").strip() or "pcs"
                item.condition = (request.form.get("condition") or "").strip() or "Good"
                item.location = (request.form.get("location") or "").strip() or None
                item.notes = (request.form.get("notes") or "").strip() or None

                def _to_int(val, default=0):
                    try:
                        return int(str(val).strip() or default)
                    except Exception:
                        return default

                new_qty = _to_int(request.form.get("quantity"), old_qty)
                new_min_qty = _to_int(request.form.get("min_quantity"), int(item.min_quantity or 0))
                if new_qty < 0 or new_min_qty < 0:
                    flash("Quantity values cannot be negative.", "error")
                    return render_template("production/daily_inventory_form.html", action="Edit", item=item)

                item.quantity = new_qty
                item.min_quantity = new_min_qty

                # log qty adjustment if changed
                delta = new_qty - old_qty
                if delta != 0:
                    db.session.add(
                        ProductionInventoryMovement(
                            item_id=item.id,
                            quantity_change=delta,
                            resulting_quantity=new_qty,
                            movement_type="adjustment",
                            note=f"Manual update (from {old_qty} to {new_qty}).",
                            created_by=getattr(current_user, "id", None),
                        )
                    )

                db.session.commit()
                flash("Production inventory item updated.", "success")
                return redirect(url_for("production.daily_inventory_list"))
            except Exception as e:
                db.session.rollback()
                current_app.logger.exception(f"Error updating production inventory item {item_id}: {e}")
                flash("Failed to update item. Please try again.", "error")

        return render_template("production/daily_inventory_form.html", action="Edit", item=item)

    @production_bp.route("/daily-inventory/delete/<int:item_id>", methods=["POST"])
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def daily_inventory_delete(item_id: int):
        item = ProductionInventoryItem.query.get_or_404(item_id)
        try:
            # Remove movements first (for sqlite FK safety)
            ProductionInventoryMovement.query.filter(ProductionInventoryMovement.item_id == item.id).delete(
                synchronize_session=False
            )
            db.session.delete(item)
            db.session.commit()
            flash("Item removed from Production inventory.", "info")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Error deleting production inventory item {item_id}: {e}")
            flash("Failed to delete item.", "error")
        return redirect(url_for("production.daily_inventory_list"))

    @production_bp.route("/daily-inventory/report")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def daily_inventory_report():
        """Production daily inventory report (current stock + low-stock)."""
        items = ProductionInventoryItem.query.order_by(
            ProductionInventoryItem.category.asc(),
            ProductionInventoryItem.name.asc(),
        ).all() or []

        low_stock_items = [i for i in items if int(i.quantity or 0) <= int(i.min_quantity or 0)]

        total_items = len(items)
        total_quantity = sum(int(i.quantity or 0) for i in items)

        return render_template(
            "production/daily_inventory_report.html",
            items=items,
            low_stock_items=low_stock_items,
            total_items=total_items,
            total_quantity=total_quantity,
            generated_at=datetime.utcnow(),
        )

    @production_bp.route("/daily-inventory/report.csv")
    @login_required
    @role_required_decorator(UserRole.Admin, UserRole.KitchenStaff)
    def daily_inventory_report_csv():
        """Download production daily inventory report (CSV)."""
        items = ProductionInventoryItem.query.order_by(
            ProductionInventoryItem.category.asc(),
            ProductionInventoryItem.name.asc(),
        ).all() or []

        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Name", "Category", "Unit", "Quantity", "Min Quantity", "Condition", "Location", "Notes"])
        for i in items:
            writer.writerow(
                [
                    i.name,
                    i.category or "",
                    i.unit or "",
                    int(i.quantity or 0),
                    int(i.min_quantity or 0),
                    i.condition or "",
                    i.location or "",
                    i.notes or "",
                ]
            )

        resp = make_response(output.getvalue())
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers[
            "Content-Disposition"
        ] = f'attachment; filename="production_daily_inventory_{datetime.utcnow().strftime("%Y%m%d_%H%M")}.csv"'
        return resp

