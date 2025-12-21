import logging
from typing import Optional, Tuple, Dict, Any

from flask import current_app

from sas_management.models import (
    db,
    Event,
    Client,
    Employee,
    InventoryItem,
    Invoice,
    InvoiceStatus,
)
from sas_management.ai.actions import get_actions
from sas_management.ai.analytics_explainer import analytics_explainer
from sas_management.ai.memory import conversation_memory
from sas_management.ai.scheduler import ai_scheduler, ScheduledAction
from sas_management.ai.permission_checks import (
    can_use_ai_actions,
    can_use_ai_analytics,
    can_use_ai_memory,
    can_use_ai_scheduling,
)
from sas_management.utils.permissions import can_use_ai, can_access_sensitive_ai_data


logger = logging.getLogger(__name__)


_SENSITIVE_KEYWORDS = (
    "password",
    "passcode",
    "secret",
    "api key",
    "apikey",
    "access key",
    "access_key",
    "client_secret",
    "token",
    "refresh token",
    "private key",
    "ssh-rsa",
)


def _looks_sensitive(text: Optional[str]) -> bool:
    """
    Heuristic check to avoid storing obviously sensitive payloads in memory.
    """
    if not text:
        return False
    lowered = str(text).lower()
    return any(keyword in lowered for keyword in _SENSITIVE_KEYWORDS)


class SASAIEngine:
    """
    Canonical SAS AI engine.
    All AI chat requests (new and legacy) must flow through here.

    Phase 4: system-data answers are based on READ-ONLY queries only.
    """

    SYSTEM_PREFIX = "📊 From SAS System:\n"
    GENERAL_PREFIX = "🧠 General Knowledge:\n"

    # ---------------------------------------------------------------------
    # Public entrypoint
    # ---------------------------------------------------------------------

    def answer(self, question: str, user):
        """
        Main entrypoint for SAS AI answers (crash-proof wrapper).

        Returns a dict with:
        - text: human-readable answer
        - source: "system" or "general_knowledge"
        """
        try:
            # Existing logic moved to _answer_internal for safety
            return self._answer_internal(question, user)
        except Exception as e:
            current_app.logger.error("AI failure", exc_info=True)
            return {
                "text": "⚠️ SAS AI encountered an internal issue. Please try again.",
                "source": "system"
            }
    
    def _answer_internal(self, question: str, user):
        """
        Internal implementation of answer logic (moved from answer()).
        All existing logic preserved exactly as before.
        """
        user_id = getattr(user, "id", None)

        # ------------------------------------------------------------------
        # Conversation memory (Phase 1: in-memory only, fail-safe)
        # ------------------------------------------------------------------
        history = []
        memory_allowed = can_use_ai_memory(user) if user else False
        try:
            if user_id is not None and memory_allowed:
                history = conversation_memory.get(user_id)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Conversation memory get error for user %s: %s", user_id, e)
            history = []

        # User-controlled memory reset phrases (do not clear automatically).
        normalized = (question or "").strip().lower()
        clear_phrases = ("clear memory", "reset conversation", "new conversation")
        if any(phrase in normalized for phrase in clear_phrases):
            if memory_allowed and user_id is not None:
                try:
                    conversation_memory.clear(user_id)
                except Exception as e:  # pragma: no cover - defensive
                    logger.warning(
                        "Conversation memory clear error for user %s: %s", user_id, e
                    )
            text = "🧹 Conversation memory cleared."
            if memory_allowed:
                try:
                    if user_id is not None and not _looks_sensitive(text):
                        conversation_memory.add(user_id, "ai", text)
                except Exception as e:  # pragma: no cover - defensive
                    logger.warning(
                        "Conversation memory add(ai) error for user %s: %s", user_id, e
                    )
            return {"text": text, "source": "system"}

        # Store the user question in memory when it is not obviously sensitive.
        try:
            if memory_allowed and user_id is not None and not _looks_sensitive(question):
                conversation_memory.add(user_id, "user", question)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(
                "Conversation memory add(user) error for user %s: %s", user_id, e
            )

        def _remember_ai_response(response_text: Optional[str]) -> None:
            """
            Best-effort storage of AI replies; never crashes callers.
            """
            if (
                not memory_allowed
                or user_id is None
                or not response_text
                or _looks_sensitive(response_text)
            ):
                return
            try:
                conversation_memory.add(user_id, "ai", response_text)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(
                    "Conversation memory add(ai) error for user %s: %s", user_id, exc
                )

        # ------------------------------------------------------------------
        # Safe scheduling of AI actions (Phase 1, in-memory only)
        # ------------------------------------------------------------------
        schedule_keywords = (
            "schedule",
            "daily report",
            "weekly report",
            "every day",
            "every week",
        )
        if any(k in normalized for k in schedule_keywords):
            text = self._handle_scheduling_request(question, user)
            _remember_ai_response(text)
            return {"text": text, "source": "system"}

        # First, check if this looks like an AI action (report/summary/plan).
        action_name, needs_clarification = self._detect_action(question)
        if needs_clarification:
            text = self._format_action_clarification()
            _remember_ai_response(text)
            return {"text": text, "source": "system"}
        if action_name:
            text = self._execute_action(action_name, user)
            _remember_ai_response(text)
            return {"text": text, "source": "system"}

        # Otherwise fall back to system intents (counts, simple summaries).
        intent = self._detect_intent(question)

        # Analytics explanation intent – descriptive only, no new computations.
        if intent == "analytics_explanation":
            text = self._handle_analytics_explanation(question, user)
            _remember_ai_response(text)
            return {"text": text, "source": "system"}

        # No system intent matched → treat as general-knowledge style response.
        if not intent:
            text = self._format_general_knowledge_answer(question)
            _remember_ai_response(text)
            return {"text": text, "source": "general_knowledge"}

        # Sensitive intents must respect RBAC.
        if intent in {"revenue_summary"}:
            if not can_access_sensitive_ai_data(user):
                # Non-admins are intentionally blocked for sensitive data.
                text = "🔒 This information is restricted to administrators."
                _remember_ai_response(text)
                return {
                    "text": text,
                    "source": "system",
                }

        # Route to read-only system query handlers.
        try:
            text = self._handle_intent(intent)
        except Exception as e:  # Fail-safe: never crash callers
            logger.warning("SASAIEngine intent handler error (%s): %s", intent, e)
            text = None

        if not text:
            text = self._no_data_message()

        _remember_ai_response(text)
        return {"text": text, "source": "system"}

    # ---------------------------------------------------------------------
    # Intent detection (simple keyword-based, no ML)
    # ---------------------------------------------------------------------

    def _detect_action(self, question: Optional[str]) -> (Optional[str], bool):
        """
        Detect high-level AI actions like reports and summaries.

        Returns (action_name, needs_clarification).
        """
        q = (question or "").lower()

        keywords = (
            "generate report",
            "create report",
            "report",
            "summarize",
            "summary",
            "overview",
            "analysis",
            "plan",
        )
        if not any(k in q for k in keywords):
            return None, False

        topic_events = any(k in q for k in ("event", "events"))
        topic_revenue = any(k in q for k in ("revenue", "sales", "income"))
        topic_staff = any(k in q for k in ("staff", "employee", "employees", "hr", "human resources"))

        matches = []
        if topic_events:
            matches.append("events_report")
        if topic_revenue:
            matches.append("revenue_summary")
        if topic_staff:
            matches.append("staff_overview")

        if len(matches) == 1:
            return matches[0], False

        # Ambiguous or unknown domain → ask user to clarify.
        return None, True

    def _detect_intent(self, question: Optional[str]) -> Optional[str]:
        """
        Map natural language question to a concrete system intent.

        INTENTS:
        - events_count → ["how many events", "events do we have"]
        - hires_count → ["hires", "hire orders", "rentals"]
        - staff_count → ["staff", "employees"]
        - clients_count → ["clients", "customers"]
        - revenue_summary → ["revenue", "sales", "income"]
        - inventory_count → ["inventory", "stock"]
        """
        q = (question or "").lower()

        # Analytics explanation intent: "explain" + metric references.
        analytics_keywords = (
            "explain",
            "why",
            "what does this mean",
            "analysis",
            "trend",
            "performance",
        )
        if any(k in q for k in analytics_keywords) and any(
            kw in q
            for kw in (
                "revenue",
                "sales",
                "event",
                "events",
                "staff",
                "employee",
                "employees",
                "inventory",
                "stock",
                "dashboard",
            )
        ):
            return "analytics_explanation"

        if "how many events" in q or "events do we have" in q:
            return "events_count"

        if any(kw in q for kw in ("hires", "hire orders", "rentals")):
            return "hires_count"

        if any(kw in q for kw in ("staff", "employees")):
            return "staff_count"

        if any(kw in q for kw in ("clients", "customers")):
            return "clients_count"

        if any(kw in q for kw in ("revenue", "sales", "income")):
            return "revenue_summary"

        if any(kw in q for kw in ("inventory", "stock")):
            return "inventory_count"

        return None

    # ---------------------------------------------------------------------
    # Scheduling helpers – in-memory, descriptive only
    # ---------------------------------------------------------------------

    def _handle_scheduling_request(self, question: Optional[str], user) -> str:
        """
        Handle user requests to schedule existing AI actions (daily/weekly).

        Phase 1:
        - In-memory only
        - No notifications, logs only on execution
        """
        if not can_use_ai_scheduling(user):
            return "🔒 Your role does not have access to this AI feature."

        q = (question or "").lower()
        actions = get_actions()

        # Determine candidate action from text.
        action_name = None
        if "event" in q or "events" in q:
            action_name = "events_report"
        elif "revenue" in q or "sales" in q or "income" in q:
            action_name = "revenue_summary"
        elif "staff" in q or "employee" in q or "employees" in q or "team" in q:
            action_name = "staff_overview"

        # Determine frequency from text.
        frequency = None
        if "daily report" in q or "every day" in q or "daily" in q:
            frequency = "daily"
        elif "weekly report" in q or "every week" in q or "weekly" in q:
            frequency = "weekly"

        # If neither action nor frequency is clear, ask for both.
        if not action_name and not frequency:
            return (
                "To schedule a report, please tell me which report you want "
                "(events report, revenue summary, or staff overview) and "
                "whether it should run daily or weekly."
            )

        # Clarify missing action.
        if not action_name:
            return (
                "Which report would you like to schedule?\n"
                "- Events report\n"
                "- Revenue summary\n"
                "- Staff overview"
            )

        # Clarify missing frequency.
        if not frequency:
            human_name = action_name.replace("_", " ").replace("report", "report").title()
            return (
                f"How often should I run the {human_name}? "
                "Please reply with daily or weekly."
            )

        # Validate action exists and is schedulable.
        action_def = actions.get(action_name)
        if not action_def or not action_def.get("schedulable"):
            return "This report cannot be scheduled yet."

        # RBAC: revenue summary is sensitive – admin-only.
        if action_name == "revenue_summary" and not can_access_sensitive_ai_data(user):
            return "🔒 This scheduled revenue report is restricted to administrators."

        user_id = getattr(user, "id", None)
        if user_id is None:
            return "Unable to schedule this report because no user is associated with the request."

        try:
            job = ScheduledAction(
                action_name=action_name,
                user_id=user_id,
                frequency=frequency,
            )
            ai_scheduler.add_job(job)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(
                "Failed to add scheduled AI action '%s' for user_id=%s: %s",
                action_name,
                user_id,
                e,
            )
            return "📊 Unable to schedule this report at the moment."

        # Confirmation message – descriptive only.
        title = action_def.get("description") or action_name.replace("_", " ").title()
        return (
            "⏱️ AI Action Scheduled:\n"
            f"{title}\n"
            f"Frequency: {frequency}"
        )

    # ---------------------------------------------------------------------
    # Intent handlers – READ-ONLY queries with graceful failure
    # ---------------------------------------------------------------------

    def _handle_intent(self, intent: str) -> Optional[str]:
        if intent == "events_count":
            count = self._safe_count(Event, "Event")
            if count is None:
                return None
            return self._system_message("Total events", int(count))

        if intent == "hires_count":
            # Hire orders are stored in the hire_order table via Order model.
            from sas_management.models import Order

            count = self._safe_count(Order, "HireOrder")
            if count is None:
                return None
            return self._system_message("Total hire orders", int(count))

        if intent == "staff_count":
            count = self._safe_count(Employee, "Employee")
            if count is None:
                return None
            return self._system_message("Total staff (employees)", int(count))

        if intent == "clients_count":
            count = self._safe_count(Client, "Client")
            if count is None:
                return None
            return self._system_message("Total clients", int(count))

        if intent == "inventory_count":
            count = self._safe_count(InventoryItem, "InventoryItem")
            if count is None:
                return None
            return self._system_message("Tracked inventory items", int(count))

        if intent == "revenue_summary":
            total = self._safe_revenue_total()
            if total is None:
                return None
            # Simple all-time summary from paid invoices.
            label = "Total revenue from paid invoices (all time)"
            # Format as integer for readability
            return self._system_message(label, f"{total:,.0f}")

        # Unknown intent should be treated as "no data"
        return None

    # ---------------------------------------------------------------------
    # Analytics explanations – READ-ONLY, descriptive only
    # ---------------------------------------------------------------------

    def _handle_analytics_explanation(self, question: Optional[str], user) -> str:
        """
        Explain existing analytics (events, revenue, staff, inventory, dashboard)
        using already-computed BI metrics. Never computes new KPIs.
        """
        if not can_use_ai_analytics(user):
            return "🔒 Your role does not have access to this AI feature."

        q = (question or "").lower()

        # Determine which metric family is being referenced.
        metric_type = "dashboard"
        if "revenue" in q or "sales" in q:
            metric_type = "revenue"
        elif "event" in q or "events" in q:
            metric_type = "events"
        elif "staff" in q or "employee" in q or "employees" in q:
            metric_type = "staff"
        elif "inventory" in q or "stock" in q:
            metric_type = "inventory"
        elif "dashboard" in q:
            metric_type = "dashboard"

        # RBAC: financial analytics are restricted.
        if metric_type in {"revenue"} and not can_access_sensitive_ai_data(user):
            return "🔒 This analytics explanation is restricted to administrators."

        try:
            metric_name, data = self._fetch_analytics_metric(metric_type)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(
                "SASAIEngine analytics metric fetch error (%s): %s", metric_type, e
            )
            return "📊 Unable to explain this metric at the moment."

        if not data:
            # Metric exists in the system but has no rows yet.
            return "📊 This metric exists but no data is available yet."

        try:
            return analytics_explainer.explain(metric_name, data)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(
                "SASAIEngine analytics explanation error (%s): %s", metric_type, e
            )
            return "📊 Unable to explain this metric at the moment."

    def _fetch_analytics_metric(self, metric_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Fetch existing analytics data for explanation.

        Uses BI dashboard metrics only; no new calculations or DB writes.
        """
        try:
            from sas_management.services.bi_service import get_bi_dashboard_metrics
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Unable to import BI service for analytics: %s", e)
            return "analytics metrics", {}

        try:
            result = get_bi_dashboard_metrics()
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("Error fetching BI dashboard metrics: %s", e)
            return "analytics metrics", {}

        if not result or not result.get("success"):
            return "analytics metrics", {}

        metrics = result.get("metrics") or {}

        if metric_type == "revenue":
            events_metrics = metrics.get("events") or {}
            if not events_metrics:
                return "event revenue and profit", {}
            data = {
                "Total revenue (events)": events_metrics.get("total_revenue"),
                "Total profit (events)": events_metrics.get("total_profit"),
                "Average margin (%)": events_metrics.get("avg_margin"),
            }
            return "event revenue and profit", data

        if metric_type == "events":
            events_metrics = metrics.get("events") or {}
            if not events_metrics:
                return "event profitability", {}
            return "event profitability overview", events_metrics

        if metric_type == "staff":
            staff_metrics = metrics.get("staff_performance") or {}
            if not staff_metrics:
                return "staff performance analytics", {}
            return "staff performance analytics", staff_metrics

        if metric_type == "inventory":
            inv_metrics = metrics.get("price_trends") or {}
            if not inv_metrics:
                return "ingredient price trend analytics", {}
            return "ingredient price trend analytics", inv_metrics

        if metric_type == "dashboard":
            if not metrics:
                return "BI dashboard metrics", {}
            return "overall BI dashboard metrics", metrics

        # Fallback: return whatever dashboard metrics exist.
        return "analytics metrics", metrics

    # ---------------------------------------------------------------------
    # Action execution – READ-ONLY AI actions
    # ---------------------------------------------------------------------

    def _execute_action(self, action_name: str, user) -> str:
        actions = get_actions()
        action_def = actions.get(action_name)

        if not action_def:
            logger.warning("Unknown AI action requested: %s", action_name)
            return self._format_action_result(
                "AI Action",
                "Unable to generate this report due to missing data.",
            )

        title = action_def.get("description") or action_name.replace("_", " ").title()

        # Fine-grained permission check for AI actions.
        if not can_use_ai_actions(user):
            body = "🔒 Your role does not have access to this AI feature."
            return self._format_action_result(title, body)

        # RBAC: sensitive actions (revenue) are admin-only.
        if action_name == "revenue_summary":
            if not can_access_sensitive_ai_data(user):
                body = "🔒 This action is restricted to administrators."
                return self._format_action_result(title, body)
        else:
            # Generic AI access check (Phase 3: observe + log only for non-admins).
            if not can_use_ai(user):
                body = "Unable to run this action for the current user."
                return self._format_action_result(title, body)

        handler = action_def.get("handler")
        if not callable(handler):
            logger.warning("AI action '%s' has no callable handler", action_name)
            return self._format_action_result(
                title,
                "Unable to generate this report due to missing data.",
            )

        try:
            summary = handler(user=user)
        except Exception as e:
            logger.warning("AI action '%s' execution error: %s", action_name, e)
            summary = None

        if not summary:
            body = "Unable to generate this report due to missing data."
        else:
            body = str(summary)

        return self._format_action_result(title, body)

    def _safe_count(self, model, model_name: str) -> Optional[int]:
        """
        Safely count rows for a given model.

        Returns None on any error so callers can fall back gracefully.
        """
        try:
            return db.session.query(db.func.count(model.id)).scalar()
        except Exception as e:
            logger.warning("SASAIEngine count error for %s: %s", model_name, e)
            return None

    def _safe_revenue_total(self) -> Optional[float]:
        """
        Safely compute total revenue from paid invoices.

        This uses existing accounting models and performs a single aggregate
        query. Returns None on error.
        """
        try:
            total_paid = (
                db.session.query(
                    db.func.coalesce(db.func.sum(Invoice.total_amount_ugx), 0)
                )
                .filter(Invoice.status == InvoiceStatus.Paid)
                .scalar()
            )
            if total_paid is None:
                return None
            return float(total_paid or 0.0)
        except Exception as e:
            logger.warning("SASAIEngine revenue summary error: %s", e)
            return None

    # ---------------------------------------------------------------------
    # Formatting helpers
    # ---------------------------------------------------------------------

    def _system_message(self, metric_label: str, value) -> str:
        """
        Standardized system answer format:

        📊 From SAS System:
        • <clear metric name>: <value>
        """
        return f"{self.SYSTEM_PREFIX}• {metric_label}: {value}"

    def _no_data_message(self) -> str:
        """
        Fallback when no data is available or a query fails.
        """
        return f"{self.SYSTEM_PREFIX}• No data available for this query."

    def _format_action_result(self, title: str, body: str) -> str:
        """
        Standardized AI action result format:

        📄 AI Action Result:
        <Action title>
        —————————
        <text summary>
        """
        return f"📄 AI Action Result:\n{title}\n—————————\n{body}"

    def _format_general_knowledge_answer(self, question: Optional[str]) -> str:
        """
        Keep a clear separation for non-system / general questions.

        GENERAL KNOWLEDGE FORMAT:

        🧠 General Knowledge:
        <answer>
        """
        base = [
            self.GENERAL_PREFIX.rstrip(),
            "I'm not certain how to answer that from SAS system data yet.",
            "You can also ask things like:",
            "• How many events do we have?",
            "• How many staff members do we have?",
            "• What is our total revenue?",
        ]
        # Do not echo the question verbatim to avoid noisy logs/PII.
        return "\n".join(base)

    def _format_action_clarification(self) -> str:
        """
        Ask the user to clarify which report/overview they want.
        """
        title = "AI Action Clarification"
        body = (
            "I can generate the following read-only reports:\n"
            "- Events report\n"
            "- Revenue summary\n"
            "- Staff overview\n\n"
            "Please specify which one you would like."
        )
        return self._format_action_result(title, body)

