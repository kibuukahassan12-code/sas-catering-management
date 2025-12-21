"""
SAS AI Engine

Reasoning layer that inspects SQLAlchemy models, queries real data,
and produces structured answers for system questions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app

from sas_management.models import (
    db,
    User,
    UserRole,
    Employee,
    Event,
    Invoice,
    InvoiceStatus,
    Task,
    TaskStatus,
    InventoryItem,
    BakeryOrder,
    Order as HireOrder,
    POSOrder,
)


_ENGINE_CACHE: Dict[str, Any] = {
    "initialized": False,
    "models": {},   # key models referenced by the engine
    "metrics": {},  # lightweight cached counts / totals
    "schema": {},   # table / column / relationship map for learning phase
}


def _ensure_metadata_loaded():
    """
    Scan key models and cache basic metrics for faster answers.

    This runs once per process and is read-only.
    """
    if _ENGINE_CACHE["initialized"]:
        return

    try:
        # Register key models the engine knows how to reason about.
        models: Dict[str, Any] = {
            "User": User,
            "Employee": Employee,
            "Event": Event,
            "Invoice": Invoice,
            "InventoryItem": InventoryItem,
            "Task": Task,
            "BakeryOrder": BakeryOrder,
            "HireOrder": HireOrder,
            "POSOrder": POSOrder,
        }
        _ENGINE_CACHE["models"] = models

        # ------------------------------------------------------------------
        # Precompute lightweight metrics (learning phase)
        # ------------------------------------------------------------------
        metrics: Dict[str, Any] = {}
        try:
            metrics["user_count"] = User.query.count()
        except Exception:
            metrics["user_count"] = None
        try:
            metrics["employee_count"] = Employee.query.count()
        except Exception:
            metrics["employee_count"] = None
        try:
            metrics["event_count"] = Event.query.count()
        except Exception:
            metrics["event_count"] = None
        try:
            metrics["task_count"] = Task.query.count()
        except Exception:
            metrics["task_count"] = None
        try:
            metrics["inventory_item_count"] = InventoryItem.query.count()
        except Exception:
            metrics["inventory_item_count"] = None
        try:
            metrics["bakery_order_count"] = BakeryOrder.query.count()
        except Exception:
            metrics["bakery_order_count"] = None
        try:
            metrics["hire_order_count"] = HireOrder.query.count()
        except Exception:
            metrics["hire_order_count"] = None
        try:
            metrics["pos_order_count"] = POSOrder.query.count()
        except Exception:
            metrics["pos_order_count"] = None
        try:
            # Total invoiced amount in the system (all time)
            total_amount = db.session.query(db.func.coalesce(db.func.sum(Invoice.total_amount_ugx), 0)).scalar()
            metrics["invoice_total_amount"] = float(total_amount or 0)
        except Exception:
            metrics["invoice_total_amount"] = None
        try:
            # Total amount for paid invoices only (all time)
            paid_amount = (
                db.session.query(db.func.coalesce(db.func.sum(Invoice.total_amount_ugx), 0))
                .filter(Invoice.status == InvoiceStatus.Paid)
                .scalar()
            )
            metrics["invoice_paid_amount"] = float(paid_amount or 0)
        except Exception:
            metrics["invoice_paid_amount"] = None

        _ENGINE_CACHE["metrics"] = metrics

        # ------------------------------------------------------------------
        # Lightweight schema map: table names, columns, relationships
        # ------------------------------------------------------------------
        schema: Dict[str, Any] = {}
        for name, model in models.items():
            try:
                table_name = getattr(model, "__tablename__", None)
                columns = []
                relationships = []

                table = getattr(model, "__table__", None)
                if table is not None:
                    try:
                        columns = [c.name for c in table.columns]
                    except Exception:
                        columns = []

                mapper = getattr(model, "__mapper__", None)
                if mapper is not None:
                    try:
                        relationships = [rel.key for rel in mapper.relationships]
                    except Exception:
                        relationships = []

                schema[name] = {
                    "table": table_name,
                    "columns": columns,
                    "relationships": relationships,
                }
            except Exception:
                schema[name] = {
                    "table": getattr(model, "__tablename__", None),
                    "columns": [],
                    "relationships": [],
                }

        _ENGINE_CACHE["schema"] = schema

        _ENGINE_CACHE["initialized"] = True
        current_app.logger.info("SASAIEngine metadata cache initialized")
    except Exception as e:
        current_app.logger.warning(f"SASAIEngine metadata initialization error: {e}")
        _ENGINE_CACHE["initialized"] = True


@dataclass
class EngineResult:
    handled: bool
    reply: str = ""
    suggested_actions: List[str] = None

    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


class SASAIEngine:
    """
    Structured reasoning engine for SAS AI.

    - Detects specific intents for system questions
    - Performs real SQLAlchemy queries
    - Aggregates metrics (COUNT, SUM, GROUP BY style)
    - Produces formatted answers clearly marked as SAS data
    """

    def __init__(self, user: Optional[User]):
        self.user = user
        self.user_id = getattr(user, "id", None)
        self.role = getattr(user, "role", None)
        self.is_admin = bool(getattr(user, "is_admin", False)) if user else False
        self.can_view_financials = self.is_admin or (self.role == UserRole.SalesManager)
        _ensure_metadata_loaded()

    # ------------------------------------------------------------------
    # Public orchestration
    # ------------------------------------------------------------------

    def analyze_question(self, question: str) -> EngineResult:
        """
        Full reasoning pipeline for a single question.
        """
        if not question:
            return EngineResult(handled=False)

        intent = self.detect_intent(question)
        if not intent:
            # No concrete system intent matched – let caller treat as general knowledge
            return EngineResult(handled=False)

        data, ok = self.fetch_system_data(intent)
        # If a system intent was detected but the data could not be read,
        # block bad responses and return a clear "no data" message.
        if not ok or not data:
            reply = "📊 From SAS System:\n• No data found for this query."
            return EngineResult(handled=True, reply=reply, suggested_actions=[])

        # Optional additional reasoning step
        data = self.reason_over_data(intent, data)
        reply, actions = self.generate_final_answer(intent, data)
        return EngineResult(handled=True, reply=reply, suggested_actions=actions)

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def detect_intent(self, question: str) -> Optional[str]:
        """
        Map natural language question to a concrete intent code.
        """
        q = (question or "").lower()

        # Events – explicit count
        if "how many events" in q or "events count" in q:
            return "events_total"

        # Events – time-bounded helpers (kept for richer questions)
        if "event" in q or "events" in q:
            if "this month" in q or "current month" in q:
                return "events_this_month"
            if "upcoming" in q or "next" in q:
                return "events_upcoming"

        # Hire orders / rentals
        if "hires" in q or "hire orders" in q or "hire order" in q or "rentals" in q or "rental" in q:
            return "hire_orders_total"

        # Staff / employees
        if "staff" in q or "employees" in q or "employee" in q or "team" in q:
            return "staff_count"

        # Revenue / sales
        if "revenue" in q or "sales" in q or "income" in q:
            # Generic revenue question – use all-time total for paid invoices
            return "revenue_total"

        # Inventory / stock / shortages
        if "inventory" in q or "stock" in q or "shortage" in q or "low stock" in q:
            return "inventory_overview"

        if "task" in q or "todo" in q or "to-do" in q or "due today" in q:
            return "tasks_for_user_today"

        if "bakery order" in q or ("bakery" in q and "order" in q):
            return "bakery_orders_recent"

        if ("hire" in q and "order" in q) or "equipment hire" in q:
            return "hire_orders_recent"

        if "pos" in q and "order" in q:
            return "pos_orders_recent"

        return None

    # ------------------------------------------------------------------
    # Data access (read-only)
    # ------------------------------------------------------------------

    def fetch_system_data(self, intent: str) -> Tuple[Dict[str, Any], bool]:
        """
        Fetch and aggregate data for a given intent.

        Returns (data, ok) where ok=False indicates that we should not answer.
        """
        try:
            if intent == "staff_count":
                return self._fetch_staff_count(), True
            if intent == "events_total":
                return self._fetch_events_total(), True
            if intent == "events_this_month":
                return self._fetch_events_this_month(), True
            if intent == "events_upcoming":
                return self._fetch_events_upcoming(), True
            if intent == "hire_orders_total":
                return self._fetch_hire_orders_total(), True
            if intent == "revenue_total":
                if not self.can_view_financials:
                    return {"error": "insufficient_permissions"}, False
                return self._fetch_revenue_total(), True
            if intent == "revenue_overview_month":
                if not self.can_view_financials:
                    return {"error": "insufficient_permissions"}, False
                return self._fetch_revenue_overview_month(), True
            if intent == "inventory_overview":
                return self._fetch_inventory_overview(), True
            if intent == "tasks_for_user_today":
                if not self.user_id:
                    return {"error": "no_user"}, False
                return self._fetch_tasks_for_user_today(), True
            if intent == "bakery_orders_recent":
                return self._fetch_bakery_orders_recent(), True
            if intent == "hire_orders_recent":
                return self._fetch_hire_orders_recent(), True
            if intent == "pos_orders_recent":
                return self._fetch_pos_orders_recent(), True
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine.fetch_system_data error for intent '{intent}': {e}")
            return {}, False

        return {}, False

    def _fetch_staff_count(self) -> Dict[str, Any]:
        staff_total = None
        employees_total = None
        try:
            staff_total = User.query.count()
        except Exception:
            pass
        try:
            employees_total = Employee.query.count()
        except Exception:
            pass
        return {
            "staff_total": staff_total,
            "employees_total": employees_total,
        }

    def _fetch_events_total(self) -> Dict[str, Any]:
        """Count all events in the system."""
        try:
            total = Event.query.count()
            return {"events_total": total}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_events_total error: {e}")
            return {}

    def _fetch_events_this_month(self) -> Dict[str, Any]:
        today = date.today()
        month_start = today.replace(day=1)
        try:
            q = Event.query
            # Use event_date when available, otherwise date
            if hasattr(Event, "event_date"):
                q = q.filter(Event.event_date != None)  # noqa: E711
                q = q.filter(Event.event_date >= month_start, Event.event_date <= today)
            else:
                q = q.filter(Event.date >= month_start, Event.date <= today)
            count = q.count()
            return {"month_start": month_start, "today": today, "events_count": count}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_events_this_month error: {e}")
            return {}

    def _fetch_events_upcoming(self) -> Dict[str, Any]:
        today = date.today()
        horizon = today + timedelta(days=30)
        try:
            q = Event.query
            if hasattr(Event, "event_date"):
                q = q.filter(Event.event_date != None)  # noqa: E711
                q = q.filter(Event.event_date > today, Event.event_date <= horizon)
            else:
                q = q.filter(Event.date > today, Event.date <= horizon)
            events = q.order_by(Event.event_date.asc() if hasattr(Event, "event_date") else Event.date.asc()).limit(10).all()
            items = []
            for e in events:
                items.append(
                    {
                        "id": e.id,
                        "title": getattr(e, "title", getattr(e, "event_name", "Event")),
                        "date": (e.event_date or e.date).isoformat() if (getattr(e, "event_date", None) or getattr(e, "date", None)) else None,
                        "status": getattr(e, "status", None),
                    }
                )
            return {"today": today, "horizon": horizon, "events": items}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_events_upcoming error: {e}")
            return {}

    def _fetch_revenue_overview_month(self) -> Dict[str, Any]:
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        try:
            invoices = (
                Invoice.query.filter(
                    Invoice.status.in_([InvoiceStatus.Paid, InvoiceStatus.Issued, InvoiceStatus.Draft])
                )
                .filter(Invoice.issue_date >= month_start)
                .all()
            )
            total = 0.0
            paid = 0.0
            for inv in invoices:
                amount = float(inv.total_amount_ugx or 0)
                total += amount
                if inv.status == InvoiceStatus.Paid:
                    paid += amount
            return {
                "period_start": month_start,
                "period_end": today,
                "total_amount": total,
                "paid_amount": paid,
                "invoices_count": len(invoices),
            }
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_revenue_overview_month error: {e}")
            return {}

    def _fetch_hire_orders_total(self) -> Dict[str, Any]:
        """Count all hire orders in the system."""
        try:
            total = HireOrder.query.count()
            return {"hire_orders_total": total}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_hire_orders_total error: {e}")
            return {}

    def _fetch_revenue_total(self) -> Dict[str, Any]:
        """
        Sum revenue from invoices for all time (paid invoices only).
        """
        try:
            total_paid = (
                db.session.query(db.func.coalesce(db.func.sum(Invoice.total_amount_ugx), 0))
                .filter(Invoice.status == InvoiceStatus.Paid)
                .scalar()
            )
            return {"total_revenue_paid": float(total_paid or 0.0)}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_revenue_total error: {e}")
            return {}

    def _fetch_inventory_overview(self) -> Dict[str, Any]:
        try:
            total_items = InventoryItem.query.count()
            low_stock = []
            all_items = InventoryItem.query.all()
            for item in all_items:
                qty = getattr(item, "stock_count", None)
                if qty is None:
                    continue
                if qty <= 10:
                    low_stock.append(
                        {
                            "id": item.id,
                            "name": getattr(item, "name", "Item"),
                            "stock_count": int(qty),
                        }
                    )
            return {
                "items_total": total_items,
                "low_stock_items": low_stock,
            }
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_inventory_low_stock error: {e}")
            return {}

    def _fetch_tasks_for_user_today(self) -> Dict[str, Any]:
        today = datetime.utcnow().date()
        try:
            tasks = (
                Task.query.filter(
                    Task.assigned_user_id == self.user_id,
                    Task.due_date != None,  # noqa: E711
                    Task.due_date <= today,
                    Task.status != TaskStatus.Complete,
                )
                .order_by(Task.due_date.asc())
                .all()
            )
            items = []
            for t in tasks:
                items.append(
                    {
                        "id": t.id,
                        "title": t.title,
                        "due_date": t.due_date.isoformat() if t.due_date else None,
                        "status": t.status.value if isinstance(t.status, TaskStatus) else str(t.status),
                    }
                )
            return {"today": today, "tasks": items}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_tasks_for_user_today error: {e}")
            return {}

    def _fetch_bakery_orders_recent(self) -> Dict[str, Any]:
        try:
            since = datetime.utcnow() - timedelta(days=30)
            orders = BakeryOrder.query.filter(BakeryOrder.created_at >= since).all()
            return {"since": since, "count": len(orders)}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_bakery_orders_recent error: {e}")
            return {}

    def _fetch_hire_orders_recent(self) -> Dict[str, Any]:
        try:
            since = datetime.utcnow() - timedelta(days=30)
            orders = HireOrder.query.filter(HireOrder.created_at >= since).all()
            return {"since": since, "count": len(orders)}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_hire_orders_recent error: {e}")
            return {}

    def _fetch_pos_orders_recent(self) -> Dict[str, Any]:
        try:
            since = datetime.utcnow() - timedelta(days=30)
            orders = POSOrder.query.filter(POSOrder.created_at >= since).all()
            return {"since": since, "count": len(orders)}
        except Exception as e:
            current_app.logger.warning(f"SASAIEngine._fetch_pos_orders_recent error: {e}")
            return {}

    # ------------------------------------------------------------------
    # Reasoning & final answer
    # ------------------------------------------------------------------

    def reason_over_data(self, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hook for additional derived metrics. Currently returns data unchanged.
        """
        return data

    def generate_final_answer(self, intent: str, data: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Convert data into a human-readable answer.
        """
        actions: List[str] = []

        # Safety net – if data dict is empty, treat as "no data found"
        if not data:
            return "📊 From SAS System:\n• No data found for this query.", actions

        if intent == "events_total":
            total = data.get("events_total")
            if total is None:
                return "📊 From SAS System:\n• No data found for this query.", actions
            reply = "📊 From SAS System:\n" f"• Total events in system: {total}"
            return reply, actions

        if intent == "staff_count":
            staff_total = data.get("staff_total")
            employees_total = data.get("employees_total")
            if staff_total is None and employees_total is None:
                return "📊 From SAS System:\n• No data found for this query.", actions
            reply_lines = ["📊 From SAS System:"]
            if employees_total is not None:
                reply_lines.append(f"• Total staff (employees): {employees_total}")
            if staff_total is not None:
                reply_lines.append(f"• User accounts in system: {staff_total}")
            return "\n".join(reply_lines), actions

        if intent == "events_this_month":
            count = data.get("events_count")
            if count is None:
                return "📊 From SAS System:\n• No data found for this query.", actions
            start = data.get("month_start")
            end = data.get("today")
            reply = (
                "📊 From SAS System:\n"
                f"• Events this month ({start} to {end}): {count}"
            )
            actions.append("Show upcoming events")
            return reply, actions

        if intent == "events_upcoming":
            events = data.get("events", [])
            if not events:
                reply = (
                    "📊 From SAS System:\n"
                    "• There are no upcoming events in the next 30 days."
                )
                return reply, actions
            reply_lines = [
                "📊 From SAS System:",
                f"• Upcoming events in the next 30 days: {len(events)}",
            ]
            for e in events[:5]:
                reply_lines.append(
                    f"  - {e.get('date')}: {e.get('title')} (status: {e.get('status') or 'n/a'})"
                )
            actions.append("View all upcoming events")
            return "\n".join(reply_lines), actions

        if intent == "revenue_overview_month":
            total = data.get("total_amount")
            paid = data.get("paid_amount")
            if total is None:
                return "📊 From SAS System:\n• No data found for this query.", actions
            start = data.get("period_start")
            end = data.get("period_end")
            reply_lines = [
                "📊 From SAS System:",
                f"• Revenue period: {start} to {end}",
                f"• Total invoiced amount: {total:,.0f}",
                f"• Amount marked as paid: {paid:,.0f}",
            ]
            actions.extend(["Revenue breakdown", "Profit analysis"])
            return "\n".join(reply_lines), actions

        if intent == "inventory_overview":
            items_total = data.get("items_total")
            low_items = data.get("low_stock_items", [])
            if items_total is None:
                return "📊 From SAS System:\n• No data found for this query.", actions
            reply_lines = ["📊 From SAS System:"]
            reply_lines.append(f"• Inventory items in system: {items_total}")
            reply_lines.append(f"• Low-stock items (≤ 10 units): {len(low_items)}")
            if low_items:
                for item in low_items[:5]:
                    reply_lines.append(
                        f"  - {item.get('name')}: {item.get('stock_count')} units remaining"
                    )
            actions.append("Inventory forecast")
            return "\n".join(reply_lines), actions

        if intent == "revenue_total":
            total_paid = data.get("total_revenue_paid")
            if total_paid is None:
                return "📊 From SAS System:\n• No data found for this query.", actions
            reply = (
                "📊 From SAS System:\n"
                f"• Total revenue from paid invoices: {total_paid:,.0f}"
            )
            return reply, actions

        if intent == "tasks_for_user_today":
            tasks = data.get("tasks", [])
            today = data.get("today")
            reply_lines = [
                "📊 From SAS System:",
                f"• Open tasks due on or before {today}: {len(tasks)}",
            ]
            for t in tasks[:5]:
                reply_lines.append(
                    f"  - {t.get('due_date')}: {t.get('title')} (status: {t.get('status')})"
                )
            actions.append("View my tasks")
            return "\n".join(reply_lines), actions

        if intent == "bakery_orders_recent":
            count = data.get("count")
            since = data.get("since")
            if count is None:
                return "📊 From SAS System:\n• No data found for this query.", actions
            reply = (
                "📊 From SAS System:\n"
                f"• Bakery orders created in the last 30 days (since {since.date()}): {count}"
            )
            actions.append("View bakery orders")
            return reply, actions

        if intent == "hire_orders_recent":
            count = data.get("count")
            since = data.get("since")
            reply = (
                "📊 From SAS System:\n"
                f"• Hire orders created in the last 30 days (since {since.date()}): {count or 0}"
            )
            actions.append("View hire orders")
            return reply, actions

        if intent == "pos_orders_recent":
            count = data.get("count")
            since = data.get("since")
            reply = (
                "📊 From SAS System:\n"
                f"• POS orders created in the last 30 days (since {since.date()}): {count or 0}"
            )
            actions.append("View POS orders")
            return reply, actions

        # Fallback for unhandled intents – treat as "no data found"
        reply = "📊 From SAS System:\n• No data found for this query."
        return reply, actions



