import logging
from typing import Dict, Callable, Any, Optional

from sas_management.models import (
    db,
    Event,
    Invoice,
    InvoiceStatus,
    Employee,
    Department,
)


logger = logging.getLogger(__name__)


ACTIONS: Dict[str, Dict[str, Any]] = {}


def register_action(name: str, description: str, *, schedulable: bool = False):
    def decorator(fn: Callable[..., Optional[str]]):
        ACTIONS[name] = {
            "description": description,
            "handler": fn,
            "schedulable": schedulable,
        }
        return fn

    return decorator


def get_actions() -> Dict[str, Dict[str, Any]]:
    return ACTIONS


@register_action(
    "events_report",
    "Events Report",
    schedulable=True,
)
def events_report(user) -> Optional[str]:
    """
    Generate a summary report of events (READ-ONLY).
    """
    try:
        total = db.session.query(db.func.count(Event.id)).scalar()
        total = int(total or 0)

        # Group by status if available
        try:
            status_rows = (
                db.session.query(Event.status, db.func.count(Event.id))
                .group_by(Event.status)
                .all()
            )
        except Exception as e:
            logger.warning("events_report status grouping error: %s", e)
            status_rows = []

        if total == 0:
            return "There are currently no events in the system."

        lines = [f"Total events: {total}"]

        if status_rows:
            lines.append("By status:")
            for status, count in status_rows:
                label = status or "Unspecified"
                try:
                    count_int = int(count or 0)
                except Exception:
                    count_int = 0
                lines.append(f"- {label}: {count_int}")

        return "\n".join(lines)
    except Exception as e:
        logger.warning("events_report error: %s", e)
        return None


@register_action(
    "revenue_summary",
    "Revenue Summary",
    schedulable=True,
)
def revenue_summary(user) -> Optional[str]:
    """
    Generate a revenue summary (READ-ONLY).

    NOTE: RBAC for sensitive data is enforced by SASAIEngine before calling this.
    """
    try:
        # Total invoiced (all statuses)
        total_invoiced = (
            db.session.query(
                db.func.coalesce(db.func.sum(Invoice.total_amount_ugx), 0)
            ).scalar()
        )

        # Total for paid invoices only
        total_paid = (
            db.session.query(
                db.func.coalesce(db.func.sum(Invoice.total_amount_ugx), 0)
            )
            .filter(Invoice.status == InvoiceStatus.Paid)
            .scalar()
        )

        # Basic counts by status (best-effort)
        try:
            by_status = (
                db.session.query(Invoice.status, db.func.count(Invoice.id))
                .group_by(Invoice.status)
                .all()
            )
        except Exception as e:
            logger.warning("revenue_summary status grouping error: %s", e)
            by_status = []

        total_invoiced_value = float(total_invoiced or 0.0)
        total_paid_value = float(total_paid or 0.0)

        lines = [
            f"Total invoiced amount (all time): {total_invoiced_value:,.0f}",
            f"Total revenue from paid invoices (all time): {total_paid_value:,.0f}",
        ]

        if by_status:
            lines.append("By invoice status:")
            for status, count in by_status:
                label = getattr(status, "value", None) or str(status) or "Unknown"
                try:
                    count_int = int(count or 0)
                except Exception:
                    count_int = 0
                lines.append(f"- {label}: {count_int}")

        return "\n".join(lines)
    except Exception as e:
        logger.warning("revenue_summary action error: %s", e)
        return None


@register_action(
    "staff_overview",
    "Staff Overview",
    schedulable=True,
)
def staff_overview(user) -> Optional[str]:
    """
    Summarize staff and roles (READ-ONLY).
    """
    try:
        total_staff = db.session.query(db.func.count(Employee.id)).scalar()
        total_staff = int(total_staff or 0)

        if total_staff == 0:
            return "There are currently no staff records in the system."

        # Group by department where available
        try:
            dept_rows = (
                db.session.query(Department.name, db.func.count(Employee.id))
                .outerjoin(Employee, Employee.department_id == Department.id)
                .group_by(Department.name)
                .all()
            )
        except Exception as e:
            logger.warning("staff_overview department grouping error: %s", e)
            dept_rows = []

        # Group by status where available
        try:
            status_rows = (
                db.session.query(Employee.status, db.func.count(Employee.id))
                .group_by(Employee.status)
                .all()
            )
        except Exception as e:
            logger.warning("staff_overview status grouping error: %s", e)
            status_rows = []

        lines = [f"Total staff records: {total_staff}"]

        if dept_rows:
            lines.append("By department:")
            for name, count in dept_rows:
                label = name or "Unassigned"
                try:
                    count_int = int(count or 0)
                except Exception:
                    count_int = 0
                lines.append(f"- {label}: {count_int}")

        if status_rows:
            lines.append("By status:")
            for status, count in status_rows:
                label = status or "Unknown"
                try:
                    count_int = int(count or 0)
                except Exception:
                    count_int = 0
                lines.append(f"- {label}: {count_int}")

        return "\n".join(lines)
    except Exception as e:
        logger.warning("staff_overview action error: %s", e)
        return None


