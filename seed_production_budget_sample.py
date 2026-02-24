"""
Seed a sample Production Budget for the next upcoming event and submit to Admin.

Idempotent:
- If an event already has a submitted/approved/rejected budget, it will not create another unless --force is used.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from decimal import Decimal

from sas_management.app import app, db
from sas_management.models import (
    Event,
    User,
    UserRole,
    ProductionBudget,
    ProductionBudgetItem,
    ProductionBudgetStatus,
    BudgetItemCategory,
)


def _money(v) -> Decimal:
    try:
        return Decimal(str(v or 0))
    except Exception:
        return Decimal("0")


def seed(force: bool = False) -> None:
    with app.app_context():
        # Ensure tables exist (dev safety)
        try:
            db.create_all()
        except Exception:
            pass

        today = datetime.utcnow().date()
        next_30 = today + timedelta(days=30)
        event_date_expr = db.func.coalesce(Event.date, Event.event_date)
        excluded_statuses = ["Done", "Completed", "Cancelled", "Canceled"]

        ev = (
            Event.query.filter(
                event_date_expr >= today,
                event_date_expr <= next_30,
                ~Event.status.in_(excluded_statuses),
            )
            .order_by(event_date_expr.asc(), Event.created_at.asc())
            .first()
        )
        if not ev:
            print("No upcoming event found (next 30 days). Create an event first.")
            return

        if not force:
            existing = (
                ProductionBudget.query.filter_by(event_id=ev.id)
                .filter(ProductionBudget.status != ProductionBudgetStatus.Draft)
                .first()
            )
            if existing:
                print(f"Event already has a submitted budget: id={existing.id} status={existing.status.value}")
                return

        # Choose a creator (KitchenStaff if available, else Admin, else first user)
        creator = User.query.filter_by(role=UserRole.KitchenStaff).first()
        if not creator:
            creator = User.query.filter_by(role=UserRole.Admin).first()
        if not creator:
            creator = User.query.first()
        if not creator:
            print("No users found to assign as budget creator.")
            return

        # If force, delete old budgets for the event
        if force:
            ProductionBudget.query.filter_by(event_id=ev.id).delete(synchronize_session=False)
            db.session.commit()

        # Build sample budget lines
        guest_count = getattr(ev, "guest_count", None) or 100

        lines = [
            (BudgetItemCategory.Food, "Rice", guest_count, 1500, "Estimated per-guest ingredient allocation"),
            (BudgetItemCategory.Food, "Beef / Chicken Mix", guest_count, 6500, "Protein allocation per guest"),
            (BudgetItemCategory.Food, "Vegetables & Salad", guest_count, 1200, "Fresh produce"),
            (BudgetItemCategory.Food, "Cooking Gas & Utilities", 1, 180000, "Gas, charcoal, water"),
            (BudgetItemCategory.KitchenTeam, "Chef & Kitchen Team Allowance", 1, 450000, "Team allowance for prep + service day"),
            (BudgetItemCategory.KitchenTeam, "Overtime / Night Prep", 1, 200000, "If required due to schedule"),
            (BudgetItemCategory.HireItems, "Extra Hot Boxes / Serving Trays Hire", 10, 25000, "Hire serving equipment"),
            (BudgetItemCategory.Other, "Contingency (5%)", 1, 0, "Calculated manually if needed"),
        ]

        budget = ProductionBudget(
            event_id=ev.id,
            created_by=creator.id,
            status=ProductionBudgetStatus.Submitted,
            submitted_at=datetime.utcnow(),
        )

        items = []
        subtotal = Decimal("0.00")
        for cat, desc, qty, unit, notes in lines:
            it = ProductionBudgetItem(
                category=cat,
                description=desc,
                quantity=_money(qty),
                unit_cost_ugx=_money(unit),
                notes=notes,
            )
            it.recalc()
            subtotal += Decimal(str(it.total_cost_ugx or 0))
            items.append(it)

        # Fill contingency as 5% of subtotal
        for it in items:
            if it.description.lower().startswith("contingency"):
                it.unit_cost_ugx = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
                it.quantity = Decimal("1.00")
                it.recalc()

        budget.items = items
        budget.recalc_totals()

        db.session.add(budget)
        db.session.commit()

        title = getattr(ev, "title", None) or getattr(ev, "event_name", None) or "Event"
        print(f"Created and submitted sample production budget: budget_id={budget.id} event={title} total={budget.total_cost_ugx}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Replace any existing budgets for the event.")
    args = parser.parse_args()
    seed(force=args.force)

