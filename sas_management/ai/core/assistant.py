"""
SAS AI Assistant core service.

This module implements a ChatGPT-style assistant that:
- Maintains per-user conversational memory in the database
- Is aware of SAS system context via read-only tools
- Respects user roles and permissions
- Falls back to general reasoning when data is not in the system
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app

from sas_management.models import (
    db,
    AIConversation,
    User,
    UserRole,
    Event,
    Invoice,
    InvoiceStatus,
    InventoryItem,
    Task,
    TaskStatus,
)
from sas_management.ai.sas_ai_engine import SASAIEngine


@dataclass
class ToolResult:
    name: str
    data: Any
    source: str = "system_data"


class SASAIAssistant:
    """
    Core SAS AI conversational assistant.

    This class is intentionally self-contained, side-effect free
    (read-only), and designed to be easily upgraded to use an
    external LLM in the future.
    """

    def __init__(self, user: Optional[User]):
        self.user = user
        self.user_id = getattr(user, "id", None)
        self.role_name = user.get_role_name() if user else "Unknown"
        self.is_admin = bool(getattr(user, "is_admin", False)) if user else False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def respond(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entry point: process a user message and return an AI response.
        """
        context = context or {}
        conv = self._get_or_create_conversation()
        memory_log, summary_text = self._parse_messages(conv.messages)

        intent = self._detect_intent(message, memory_log)
        tools_to_use = self.decide_tools(message, intent)
        tool_results = self._run_tools(tools_to_use)

        reply, source, suggested_actions = self.generate_response(
            message=message,
            intent=intent,
            tool_results=tool_results,
            memory_log=memory_log,
            summary=summary_text,
        )

        # Update memory
        updated_log = self._append_exchange(memory_log, message, reply, intent)
        new_summary = self.summarize_context(updated_log, summary_text)
        conv.messages = json.dumps({"log": updated_log, "summary": new_summary})
        conv.updated_at = datetime.utcnow()
        db.session.add(conv)
        db.session.commit()

        return {
            "success": True,
            "reply": reply,
            "intent": intent,
            "source": source,
            "suggested_actions": suggested_actions,
        }

    # ------------------------------------------------------------------
    # Tooling & system awareness
    # ------------------------------------------------------------------

    def decide_tools(self, message: str, intent: str) -> List[str]:
        """
        Decide which tools to call based on the message and intent.
        """
        msg = (message or "").lower()
        tools: List[str] = []

        if intent == "system_query":
            if any(w in msg for w in ["event", "events", "wedding", "corporate", "service"]):
                tools.append("get_recent_events")
            if any(w in msg for w in ["revenue", "income", "sales", "money", "invoice"]):
                tools.append("get_sales_summary")
            if any(w in msg for w in ["inventory", "stock", "shortage", "supplies"]):
                tools.append("get_inventory_status")
            if any(w in msg for w in ["staff", "schedule", "shift", "roster", "employee"]):
                tools.append("get_staff_schedule")
            if any(w in msg for w in ["module", "feature", "menu", "navigation"]):
                tools.append("get_modules")

        # Always allow role/perms context when available
        if self.user_id is not None:
            tools.append("get_user_role")
            tools.append("get_permissions")

        # Deduplicate while preserving order
        seen = set()
        ordered_tools: List[str] = []
        for t in tools:
            if t not in seen:
                seen.add(t)
                ordered_tools.append(t)
        return ordered_tools

    def _run_tools(self, tool_names: List[str]) -> List[ToolResult]:
        results: List[ToolResult] = []
        for name in tool_names:
            try:
                if name == "get_user_role":
                    data = self._tool_get_user_role()
                elif name == "get_modules":
                    data = self._tool_get_modules()
                elif name == "get_recent_events":
                    data = self._tool_get_recent_events()
                elif name == "get_sales_summary":
                    data = self._tool_get_sales_summary()
                elif name == "get_inventory_status":
                    data = self._tool_get_inventory_status()
                elif name == "get_staff_schedule":
                    data = self._tool_get_staff_schedule()
                elif name == "get_permissions":
                    data = self._tool_get_permissions()
                else:
                    continue
                results.append(ToolResult(name=name, data=data))
            except Exception as e:
                current_app.logger.warning(f"SASAIAssistant tool '{name}' failed: {e}")
        return results

    # Individual tools -------------------------------------------------

    def _tool_get_user_role(self) -> Dict[str, Any]:
        if not self.user:
            return {"role": None}
        return {
            "role": self.role_name,
            "is_admin": self.is_admin,
        }

    def _tool_get_permissions(self) -> Dict[str, Any]:
        """
        High-level permission profile (read-only, safe).
        """
        if not self.user:
            return {"profile": "anonymous", "can_view_financials": False}

        profile = "admin" if self.is_admin else "staff"
        # Admins can see everything; staff have limited access to sensitive data.
        can_view_financials = self.is_admin or getattr(self.user, "role", None) == UserRole.SalesManager
        return {
            "profile": profile,
            "can_view_financials": can_view_financials,
        }

    def _tool_get_modules(self) -> Dict[str, Any]:
        """
        Read-only snapshot of navigation modules visible to the current user.
        """
        try:
            from sas_management.navigation.modules import get_modules

            modules = get_modules()
            return {"count": len(modules), "modules": modules}
        except Exception as e:
            current_app.logger.warning(f"SASAIAssistant.get_modules error: {e}")
            return {"count": 0, "modules": []}

    def _tool_get_recent_events(self) -> Dict[str, Any]:
        try:
            today = datetime.utcnow().date()
            last_30 = today - timedelta(days=30)
            events = (
                Event.query.filter(Event.event_date != None)  # noqa: E711
                .filter(Event.event_date >= last_30)
                .order_by(Event.event_date.desc())
                .limit(10)
                .all()
            )
            items = []
            for e in events:
                items.append(
                    {
                        "id": e.id,
                        "title": getattr(e, "title", getattr(e, "event_name", "Event")),
                        "date": (e.event_date or e.date).isoformat() if (e.event_date or e.date) else None,
                        "guest_count": getattr(e, "guest_count", None),
                        "status": getattr(e, "status", None),
                    }
                )
            return {"count": len(items), "events": items}
        except Exception as e:
            current_app.logger.warning(f"SASAIAssistant.get_recent_events error: {e}")
            return {"count": 0, "events": []}

    def _tool_get_sales_summary(self) -> Dict[str, Any]:
        try:
            today = datetime.utcnow().date()
            month_start = today.replace(day=1)

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
                "period_start": month_start.isoformat(),
                "period_end": today.isoformat(),
                "invoices_count": len(invoices),
                "total_amount": total,
                "paid_amount": paid,
            }
        except Exception as e:
            current_app.logger.warning(f"SASAIAssistant.get_sales_summary error: {e}")
            return {"period_start": None, "period_end": None, "invoices_count": 0, "total_amount": 0.0, "paid_amount": 0.0}

    def _tool_get_inventory_status(self) -> Dict[str, Any]:
        try:
            low_stock = []
            all_items = InventoryItem.query.all()
            for item in all_items:
                qty = getattr(item, "stock_count", None)
                if qty is None:
                    continue
                # Simple heuristic: <= 10 is considered low stock
                if qty <= 10:
                    low_stock.append(
                        {
                            "id": item.id,
                            "name": getattr(item, "name", "Item"),
                            "stock_count": int(qty),
                        }
                    )
            return {"low_stock_count": len(low_stock), "low_stock_items": low_stock}
        except Exception as e:
            current_app.logger.warning(f"SASAIAssistant.get_inventory_status error: {e}")
            return {"low_stock_count": 0, "low_stock_items": []}

    def _tool_get_staff_schedule(self) -> Dict[str, Any]:
        """
        Very high-level view of tasks due today for the current user.
        """
        if not self.user_id:
            return {"tasks_today": 0, "tasks": []}

        try:
            today = datetime.utcnow().date()
            tasks = (
                Task.query.filter(
                    Task.assigned_user_id == self.user_id,
                    Task.due_date != None,  # noqa: E711
                    Task.due_date <= today,
                    Task.status != TaskStatus.Complete,
                )
                .order_by(Task.due_date.asc())
                .limit(10)
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
            return {"tasks_today": len(items), "tasks": items}
        except Exception as e:
            current_app.logger.warning(f"SASAIAssistant.get_staff_schedule error: {e}")
            return {"tasks_today": 0, "tasks": []}

    # ------------------------------------------------------------------
    # Conversation memory
    # ------------------------------------------------------------------

    def _get_or_create_conversation(self) -> AIConversation:
        if not self.user_id:
            # For safety, treat anonymous as a transient conversation
            conv = AIConversation(user_id=0, role="anonymous", messages="[]")
            return conv

        conv = AIConversation.query.filter_by(user_id=self.user_id).order_by(AIConversation.id.asc()).first()
        if conv:
            return conv

        conv = AIConversation(
            user_id=self.user_id,
            role=self.role_name,
            messages=json.dumps({"log": [], "summary": ""}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(conv)
        db.session.flush()
        return conv

    def _parse_messages(self, raw: str) -> Tuple[List[Dict[str, Any]], str]:
        if not raw:
            return [], ""
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                log = data.get("log", [])
                summary = data.get("summary", "")
            elif isinstance(data, list):
                log = data
                summary = ""
            else:
                log, summary = [], ""
            return log, summary
        except Exception:
            return [], ""

    def _append_exchange(
        self,
        log: List[Dict[str, Any]],
        user_message: str,
        ai_reply: str,
        intent: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        now = datetime.utcnow().isoformat()
        log = list(log)
        log.append({"role": "user", "content": user_message, "timestamp": now})
        entry = {"role": "assistant", "content": ai_reply, "timestamp": now}
        if intent:
            entry["intent"] = intent
        log.append(entry)
        # Keep only last 40 messages for efficiency
        return log[-40:]

    def summarize_context(self, log: List[Dict[str, Any]], existing_summary: str = "") -> str:
        """
        Lightweight summarization: when the log is long, compress older
        messages into a brief textual summary.
        """
        if len(log) <= 20:
            return existing_summary or ""

        # Take last 5 user messages as "recent focus"
        recent_user_msgs = [m["content"] for m in log if m.get("role") == "user"][-5:]
        summary = "Recent topics: " + "; ".join(
            (msg[:60] + "...") if len(msg) > 60 else msg for msg in recent_user_msgs
        )
        return summary

    # ------------------------------------------------------------------
    # Intent detection & response generation
    # ------------------------------------------------------------------

    def _detect_intent(self, message: str, memory_log: List[Dict[str, Any]]) -> str:
        msg = (message or "").lower()

        # ------------------------------------------------------------------
        # Explicit system intents (must map to real database queries)
        # ------------------------------------------------------------------
        # Events count
        if "how many events" in msg or "events count" in msg:
            return "system_query"

        # Hire orders / rentals
        if any(k in msg for k in ["hires", "hire orders", "hire order", "rentals", "rental"]):
            return "system_query"

        # Staff / employees count
        if any(k in msg for k in ["staff", "employees", "employee"]):
            return "system_query"

        # Revenue / sales
        if any(k in msg for k in ["revenue", "sales"]):
            return "system_query"

        # Inventory / stock
        if any(k in msg for k in ["inventory", "stock"]):
            return "system_query"

        # Writing assistance (only if no system intent matched)
        writing_keywords = [
            "write",
            "draft",
            "compose",
            "create",
            "generate",
            "prepare",
            "template",
            "email",
            "report",
        ]
        if any(k in msg for k in writing_keywords):
            return "writing_assistance"

        # Default: general knowledge / chit-chat
        return "general_knowledge"

    def generate_response(
        self,
        message: str,
        intent: str,
        tool_results: List[ToolResult],
        memory_log: List[Dict[str, Any]],
        summary: str,
    ) -> Tuple[str, str, List[str]]:
        """
        Turn tools + memory into a natural-language reply.

        Returns (reply_text, source, suggested_actions).
        """
        if intent == "system_query":
            # Prefer SASAIEngine for structured system answers
            engine = SASAIEngine(self.user)
            engine_result = engine.analyze_question(message)
            if engine_result.handled:
                return engine_result.reply, "system_data", engine_result.suggested_actions
            # No matching system intent → treat as general knowledge
            reply, actions = self._compose_general_reply(message)
            return reply, "general_knowledge", actions
        elif intent == "writing_assistance":
            reply, actions = self._compose_writing_reply(message)
            return reply, "general_knowledge", actions
        else:
            reply, actions = self._compose_general_reply(message)
            return reply, "general_knowledge", actions

    # Reply composition helpers ----------------------------------------

    def _compose_system_reply(self, message: str, tools: List[ToolResult], summary: str) -> Tuple[str, List[str]]:
        parts: List[str] = ["📊 From SAS System:"]
        suggested: List[str] = []

        # Permissions profile
        perms = next((t.data for t in tools if t.name == "get_permissions"), None)
        if perms:
            profile = perms.get("profile", "staff")
            if profile == "admin":
                parts.append("• You are signed in as **Admin** with full visibility.")
            else:
                parts.append("• You are signed in as **Staff**. Some financial details may be summarized only.")

        # Recent events
        ev = next((t.data for t in tools if t.name == "get_recent_events"), None)
        if ev and ev.get("count"):
            parts.append(f"• Recent events (last 30 days): **{ev['count']}**")
            first = ev["events"][0]
            parts.append(
                f"  - Latest event: **{first.get('title','Event')}** on {first.get('date')}, "
                f"status: {first.get('status') or 'n/a'}"
            )
            suggested.append("Show upcoming events")

        # Sales summary
        sales = next((t.data for t in tools if t.name == "get_sales_summary"), None)
        if sales and sales.get("period_start"):
            total = sales.get("total_amount", 0.0)
            paid = sales.get("paid_amount", 0.0)
            parts.append(
                f"• Sales this month: total invoices **{total:,.0f}**, "
                f"paid **{paid:,.0f}** (period starting {sales['period_start']})."
            )
            suggested.append("Revenue breakdown")

        # Inventory status
        inv = next((t.data for t in tools if t.name == "get_inventory_status"), None)
        if inv:
            parts.append(f"• Low stock items: **{inv.get('low_stock_count', 0)}**")
            suggested.append("Inventory forecast")

        # Staff schedule
        sched = next((t.data for t in tools if t.name == "get_staff_schedule"), None)
        if sched:
            parts.append(f"• Your open tasks due today or earlier: **{sched.get('tasks_today', 0)}**")
            suggested.append("View my tasks")

        if summary:
            parts.append("")
            parts.append(f"_Recent topics_: {summary}")

        if len(parts) == 1:
            # No tool data available
            parts.append(
                "I tried to read system data, but couldn't access it right now. "
                "Please try again later or check that your database is available."
            )

        suggested = list(dict.fromkeys(suggested))  # dedupe, preserve order
        return "\n".join(parts), suggested

    def _compose_writing_reply(self, message: str) -> Tuple[str, List[str]]:
        msg = (message or "").lower()
        actions: List[str] = []

        header = "🧠 General Knowledge:\n"

        if "email" in msg or "mail" in msg:
            body = (
                "Here's a professional email template you can adapt:\n\n"
                "Subject: [Your Subject]\n\n"
                "Dear [Name],\n\n"
                "[Body of your message]\n\n"
                "Best regards,\n[Your Name]\n"
            )
            actions.extend(["Draft client email", "Create follow-up email"])
        elif "report" in msg:
            body = (
                "A clear business report usually includes:\n\n"
                "1. Executive Summary\n"
                "2. Key Metrics\n"
                "3. Analysis and Insights\n"
                "4. Recommendations\n"
                "5. Next Steps\n\n"
                "Tell me what kind of report you need and I'll help structure it."
            )
            actions.extend(["Event performance report", "Revenue summary report"])
        else:
            body = (
                "I can help you draft emails, reports, and other business text. "
                "Describe what you want to write (for example: 'email to client about quotation')."
            )
            actions.extend(["Draft quotation email", "Write event summary"])

        return header + body, actions

    def _compose_general_reply(self, message: str) -> Tuple[str, List[str]]:
        msg = (message or "").lower()
        actions: List[str] = []

        header = "🧠 General Knowledge:\n"

        # Greetings
        if any(w in msg for w in ["hello", "hi", "hey", "good morning", "good evening"]):
            body = (
                "Hello! I'm **SAS AI**, your assistant inside the SAS Management System.\n\n"
                "- Ask me about your events, revenue, staff, or inventory.\n"
                "- Or ask general questions and I'll answer from general knowledge."
            )
            actions.extend(["How many events this month?", "Show revenue this month"])
            return header + body, actions

        # Help / capabilities
        if any(w in msg for w in ["help", "what can you", "capabilities", "features"]):
            body = (
                "I can help you with two kinds of questions:\n\n"
                "1. **From SAS System** – events, revenue, staff tasks, inventory, and more.\n"
                "2. **General knowledge** – logic, math, definitions, and everyday questions.\n\n"
                "When I answer, I'll clearly separate what comes from your SAS data vs. general knowledge."
            )
            actions.extend(["Events overview", "Revenue overview", "Inventory overview"])
            return header + body, actions

        # Basic general knowledge / logic
        if any(w in msg for w in ["math", "calculate", "sum", "difference", "product"]):
            body = (
                "I can handle basic reasoning and calculations. For example:\n"
                "- 'What is 25% of 80,000?'\n"
                "- 'If we add 50 guests to 120, how many in total?'\n\n"
                "Ask your question and I'll walk through the logic."
            )
            actions.extend(["Calculate 25% of 80,000", "Add 50 guests to 120"])
            return header + body, actions

        # Fallback generic response
        body = (
            "I'll treat this as a **general knowledge** question.\n\n"
            "I don't see a direct reference to your SAS data here, so I will not assume any system values. "
            "If you want me to use your data, mention events, revenue, staff, or inventory in your question."
        )
        actions.extend(["Ask about events", "Ask about revenue", "Ask about staff tasks"])
        return header + body, actions


