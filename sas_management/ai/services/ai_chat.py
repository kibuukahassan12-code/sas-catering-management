"""
SAS AI Chat Service

Premium AI chat assistant for system queries and intelligent assistance.
Backed by SASAIAssistant for conversational memory and system-aware tools.
NO external external APIs required.
"""
from flask import current_app, session
from sas_management.ai.feature_model import is_ai_feature_enabled
from sas_management.ai.core.assistant import SASAIAssistant
from sas_management.models import User, db
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional


def process_chat_message(message: str, user_id: int, context: dict = None) -> dict:
    """
    Process a chat message and return AI response with metadata.
    
    Args:
        message: User's message
        user_id: Current user ID for logging
        context: Additional context (user_id, session_id, etc.)
        
    Returns:
        Dictionary with AI response, intent, source, and suggestions
    """
    # HARD CHECK: SAS AI Chat must be enabled in DB, otherwise block execution
    if not is_ai_feature_enabled("sas_ai_chat"):
        current_app.logger.warning("AI Chat feature accessed while disabled in DB")
        return {
            "success": False,
            "error": "Feature disabled by admin",
            "reply": "SAS AI Chat is currently disabled by your administrator.",
            "intent": "general_knowledge",
            "source": "general_knowledge",
            "suggested_actions": [],
        }

    context = context or {}

    try:
        raw = (message or "").strip()
        if not raw:
            return {
                "success": True,
                "reply": "Hello! I'm SAS AI. How can I help you today?",
                "intent": "general_knowledge",
                "source": "general_knowledge",
                "suggested_actions": [
                    "How many events this month?",
                    "Show revenue this month",
                    "What tasks are due today?",
                ],
            }

        # Load user object for role/permissions awareness
        user = db.session.get(User, user_id) if user_id else None

        # Fine-grained AI chat permission
        try:
            from sas_management.ai.permission_checks import can_use_ai_chat

            if not can_use_ai_chat(user):
                return {
                    "success": False,
                    "error": None,
                    "reply": "🔒 Your role does not have access to this AI feature.",
                    "intent": "general_knowledge",
                    "source": "general_knowledge",
                    "suggested_actions": [],
                }
        except Exception as e:  # pragma: no cover - defensive
            current_app.logger.warning(
                "AI chat permission check error for user_id=%s: %s", user_id, e
            )

        assistant = SASAIAssistant(user=user)
        result = assistant.respond(raw, context=context)

        # Log usage (without message content)
        current_app.logger.info(
            f"SAS AI Chat: user_id={user_id}, intent={result.get('intent')}, "
            f"source={result.get('source')}, timestamp={datetime.utcnow().isoformat()}"
        )

        return result

    except Exception as e:
        current_app.logger.warning(f"AI Chat error (non-fatal): {e}")
        return {
            "success": False,
            "error": str(e),
            "reply": "I encountered an error processing your request. Please try again or rephrase your question.",
            "intent": "general_knowledge",
            "source": "general_knowledge",
            "suggested_actions": ["Try again", "Ask about events", "Ask about revenue"],
        }


def _detect_intent(message: str, memory: List[Dict]) -> str:
    """
    Classify message intent into: system_query, general_knowledge, or writing_assistance.
    
    Args:
        message: Lowercase message text
        memory: Previous conversation context
        
    Returns:
        Intent classification string
    """
    # Writing assistance keywords
    writing_keywords = [
        "write", "draft", "compose", "create", "generate", "help me write",
        "make a", "prepare", "format", "template", "example"
    ]
    if any(keyword in message for keyword in writing_keywords):
        return "writing_assistance"
    
    # System query keywords (data from database)
    system_keywords = [
        "event", "events", "revenue", "profit", "staff", "employee",
        "client", "customer", "inventory", "stock", "compliance", "safety",
        "how many", "what is", "show me", "list", "count", "total",
        "this month", "last quarter", "today", "upcoming", "pending",
        "status", "performance", "analysis", "report"
    ]
    if any(keyword in message for keyword in system_keywords):
        return "system_query"
    
    # Check memory for context
    if memory:
        last_intent = memory[-1].get("intent")
        if last_intent == "system_query" and any(word in message for word in ["more", "details", "tell me", "explain"]):
            return "system_query"
    
    # Default to general knowledge
    return "general_knowledge"


def _handle_system_query(message: str, memory: List[Dict]) -> Dict:
    """Handle system data queries with memory context."""
    try:
        message_lower = message.lower()
        
        # Use memory for follow-up context
        if memory:
            last_exchange = memory[-1]
            last_intent = last_exchange.get("intent")
            last_ai_reply = last_exchange.get("ai", "").lower()
            
            # If previous was about events and current is follow-up
            if last_intent == "system_query" and "event" in last_ai_reply:
                if any(word in message_lower for word in ["more", "details", "tell me more", "explain"]):
                    return _handle_events_query(message_lower, detailed=True)
        
        # Events queries
        if any(word in message_lower for word in ["event", "events", "wedding", "corporate", "service"]):
            return _handle_events_query(message_lower)
        
        # Revenue queries
        if any(word in message_lower for word in ["revenue", "income", "sales", "money earned"]):
            return _handle_revenue_query(message_lower)
        
        # Profit queries
        if any(word in message_lower for word in ["profit", "margin", "earnings", "net", "quarter"]):
            return _handle_profit_query(message_lower)
        
        # Staff queries
        if any(word in message_lower for word in ["staff", "employee", "worker", "team"]):
            return _handle_staff_query(message_lower)
        
        # Compliance queries
        if any(word in message_lower for word in ["compliance", "safety", "hygiene", "food safety"]):
            return _handle_compliance_query(message_lower)
        
        # Inventory queries
        if any(word in message_lower for word in ["inventory", "stock", "supplies", "items"]):
            return _handle_inventory_query(message_lower)
        
        # Client queries
        if any(word in message_lower for word in ["client", "customer", "client value"]):
            return _handle_client_query(message_lower)
        
        # Default system response
        return {
            "reply": "I can help you query your system data. Try asking about events, revenue, staff, or compliance.",
            "source": "system_data",
            "suggested_actions": ["How many events this month?", "Show revenue", "Staff count"],
        }
    except Exception as e:
        current_app.logger.warning(f"Error handling system query: {e}")
        return {
            "reply": "I'm having trouble accessing your system data right now. Please try again in a moment.",
            "source": "system_data",
            "suggested_actions": [],
        }


def _handle_general_knowledge(message: str, memory: List[Dict]) -> Dict:
    """Handle general knowledge and conversational queries."""
    message_lower = message.lower()
    
    # Greetings
    if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
        return {
            "reply": "Hello! I'm SAS AI Chat, your intelligent assistant. I can help you with business queries, data analysis, and general questions. How can I assist you today?",
            "source": "general_knowledge",
            "suggested_actions": ["How many events this month?", "What can you help with?", "Explain revenue"],
        }
    
    # Help requests
    if any(word in message_lower for word in ["help", "what can", "how do", "explain", "tell me about"]):
        return {
            "reply": "I'm SAS AI Chat! I can help you with:\n\n"
                    "📅 **Events**: Count events, check status, plan new events\n"
                    "💰 **Revenue**: Analyze sales, income, financial data\n"
                    "📊 **Profit**: Review margins, costs, profitability\n"
                    "👥 **Staff**: Staff information and performance\n"
                    "⚠️ **Compliance**: Food safety and regulatory compliance\n"
                    "📦 **Inventory**: Stock levels and predictions\n"
                    "👤 **Clients**: Client analysis and value\n\n"
                    "Try asking: 'How many events this month?' or 'Explain last quarter profit'",
            "source": "general_knowledge",
            "suggested_actions": [
                "How many events this month?",
                "Explain last quarter profit",
                "What is food safety compliance?",
            ],
        }
    
    # Thanks
    if any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
        return {
            "reply": "You're welcome! Is there anything else I can help you with?",
            "source": "general_knowledge",
            "suggested_actions": ["Ask another question", "View events", "Check revenue"],
        }
    
    # Default general response
    return {
        "reply": "I understand you're asking about that. For specific business data, try asking about events, revenue, staff, or compliance. For general questions, I'm here to help!",
        "source": "general_knowledge",
        "suggested_actions": [
            "How many events this month?",
            "What can you help with?",
            "Explain revenue",
        ],
    }


def _handle_writing_assistance(message: str, memory: List[Dict]) -> Dict:
    """Handle writing and content generation requests."""
    message_lower = message.lower()
    
    # Email templates
    if any(word in message_lower for word in ["email", "message", "send"]):
        return {
            "reply": "I can help you draft professional emails. Here's a template:\n\n"
                    "Subject: [Your Subject]\n\n"
                    "Dear [Name],\n\n"
                    "[Body of your message]\n\n"
                    "Best regards,\n[Your Name]\n\n"
                    "Would you like me to customize this for a specific purpose?",
            "source": "general_knowledge",
            "suggested_actions": ["Draft client email", "Create event invitation", "Write follow-up"],
        }
    
    # Reports
    if any(word in message_lower for word in ["report", "summary", "document"]):
        return {
            "reply": "I can help you structure reports. A good report includes:\n\n"
                    "1. Executive Summary\n"
                    "2. Key Findings\n"
                    "3. Data Analysis\n"
                    "4. Recommendations\n"
                    "5. Conclusion\n\n"
                    "Would you like me to help you create a specific type of report?",
            "source": "general_knowledge",
            "suggested_actions": ["Event report template", "Revenue report", "Staff report"],
        }
    
    # Default writing help
    return {
        "reply": "I can help you with writing emails, reports, and other business documents. What would you like to create?",
        "source": "general_knowledge",
        "suggested_actions": ["Draft email", "Create report", "Write proposal"],
    }


def _handle_events_query(message: str, detailed: bool = False) -> Dict:
    """Handle events-related queries."""
    try:
        from sas_management.service.models import ServiceEvent
        
        today = date.today()
        month_start = today.replace(day=1)
        
        # Count events this month
        events_this_month = ServiceEvent.query.filter(
            ServiceEvent.event_date >= month_start,
            ServiceEvent.event_date <= today
        ).count()
        
        # Count upcoming events
        upcoming = ServiceEvent.query.filter(
            ServiceEvent.event_date > today
        ).count()
        
        # Count by status
        planned = ServiceEvent.query.filter_by(status="Planned").count()
        confirmed = ServiceEvent.query.filter_by(status="Confirmed").count()
        
        reply = f"Here's your events overview:\n\n"
        reply += f"• Events this month: {events_this_month}\n"
        reply += f"• Upcoming events: {upcoming}\n"
        reply += f"• Planned: {planned}\n"
        reply += f"• Confirmed: {confirmed}\n\n"
        reply += "Would you like details on a specific event?"
        
        return {
            "reply": reply,
            "source": "system_data",
            "suggested_actions": ["Show upcoming events", "Event planning help", "View event details"],
        }
    except Exception as e:
        current_app.logger.warning(f"Error handling events query: {e}")
        return {
            "reply": "I can help with events, but I'm having trouble accessing the data right now. Please try again.",
            "source": "system_data",
            "suggested_actions": [],
        }


def _handle_revenue_query(message: str) -> Dict:
    """Handle revenue-related queries."""
    try:
        from sas_management.models import Quote, Invoice
        
        today = datetime.utcnow()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        quotes = Quote.query.filter(
            Quote.status == "Accepted",
            Quote.created_at >= month_start
        ).all()
        
        total_revenue = Decimal("0")
        for quote in quotes:
            if quote.total_amount:
                total_revenue += Decimal(str(quote.total_amount))
        
        invoices = Invoice.query.filter(
            Invoice.status == "Paid",
            Invoice.created_at >= month_start
        ).all() if hasattr(Invoice, "status") else []
        
        invoice_revenue = Decimal("0")
        for inv in invoices:
            if hasattr(inv, "amount_paid") and inv.amount_paid:
                invoice_revenue += Decimal(str(inv.amount_paid))
        
        total = total_revenue + invoice_revenue
        
        reply = f"Revenue Overview:\n\n"
        reply += f"• This month's revenue: {float(total):,.0f} UGX\n"
        reply += f"• From quotes: {float(total_revenue):,.0f} UGX\n"
        if invoice_revenue > 0:
            reply += f"• From invoices: {float(invoice_revenue):,.0f} UGX\n"
        reply += f"\nBased on {len(quotes)} accepted quotes this month."
        
        return {
            "reply": reply,
            "source": "system_data",
            "suggested_actions": ["Profit analysis", "Revenue forecast", "View quotes"],
        }
    except Exception as e:
        current_app.logger.warning(f"Error handling revenue query: {e}")
        return {
            "reply": "I can help with revenue analysis, but I'm having trouble accessing the data right now.",
            "source": "system_data",
            "suggested_actions": [],
        }


def _handle_profit_query(message: str) -> Dict:
    """Handle profit-related queries."""
    try:
        from sas_management.models import Event
        
        cutoff = datetime.utcnow() - timedelta(days=90)
        events = Event.query.filter(Event.created_at >= cutoff).all()
        
        total_revenue = Decimal("0")
        total_cogs = Decimal("0")
        count = 0
        
        for event in events:
            try:
                revenue = Decimal("0")
                if hasattr(event, "quote") and event.quote and event.quote.total_amount:
                    revenue = Decimal(str(event.quote.total_amount))
                
                cogs = Decimal("0")
                if hasattr(event, "actual_cogs_ugx") and event.actual_cogs_ugx:
                    cogs = Decimal(str(event.actual_cogs_ugx))
                
                if revenue > 0:
                    total_revenue += revenue
                    total_cogs += cogs
                    count += 1
            except Exception:
                continue
        
        if count > 0:
            profit = total_revenue - total_cogs
            margin = (profit / total_revenue * 100) if total_revenue > 0 else 0
            
            reply = f"Profit Analysis (Last 90 Days):\n\n"
            reply += f"• Total Revenue: {float(total_revenue):,.0f} UGX\n"
            reply += f"• Total COGS: {float(total_cogs):,.0f} UGX\n"
            reply += f"• Net Profit: {float(profit):,.0f} UGX\n"
            reply += f"• Profit Margin: {margin:.1f}%\n"
            reply += f"\nBased on {count} events."
            
            if margin < 20:
                reply += "\n\n⚠️ Margin is below 20%. Consider reviewing pricing or costs."
        else:
            reply = "I don't have enough profit data to analyze right now."
        
        return {
            "reply": reply,
            "source": "system_data",
            "suggested_actions": ["Cost optimization", "Pricing recommendations", "View events"],
        }
    except Exception as e:
        current_app.logger.warning(f"Error handling profit query: {e}")
        return {
            "reply": "I can help with profit analysis, but I'm having trouble accessing the data right now.",
            "source": "system_data",
            "suggested_actions": [],
        }


def _handle_staff_query(message: str) -> Dict:
    """Handle staff-related queries."""
    try:
        from sas_management.models import User
        from sas_management.service.models import ServiceStaffAssignment
        
        staff_count = User.query.filter(User.role != None).count()
        assignments = ServiceStaffAssignment.query.count()
        
        reply = f"Staff Overview:\n\n"
        reply += f"• Total staff members: {staff_count}\n"
        reply += f"• Total service assignments: {assignments}\n\n"
        reply += "I can help you analyze staff performance or plan staffing for events."
        
        return {
            "reply": reply,
            "source": "system_data",
            "suggested_actions": ["Staff performance", "Staffing recommendations", "View assignments"],
        }
    except Exception as e:
        current_app.logger.warning(f"Error handling staff query: {e}")
        return {
            "reply": "I can help with staff information, but I'm having trouble accessing the data right now.",
            "source": "system_data",
            "suggested_actions": [],
        }


def _handle_compliance_query(message: str) -> Dict:
    """Handle compliance-related queries."""
    reply = "Food Safety & Compliance:\n\n"
    reply += "• Regular food safety logs should be maintained\n"
    reply += "• Event checklists must be completed before service\n"
    reply += "• Hygiene reports should be documented\n\n"
    reply += "Use the Compliance Monitor feature for detailed analysis."
    
    return {
        "reply": reply,
        "source": "system_data",
        "suggested_actions": ["Check compliance status", "View safety logs", "Compliance report"],
    }


def _handle_inventory_query(message: str) -> Dict:
    """Handle inventory-related queries."""
    reply = "Inventory Management:\n\n"
    reply += "• Monitor stock levels regularly\n"
    reply += "• Reorder when items reach reorder level\n"
    reply += "• Plan inventory based on upcoming events\n\n"
    reply += "Use the Inventory Predictor feature for forecasts."
    
    return {
        "reply": reply,
        "source": "system_data",
        "suggested_actions": ["Inventory forecast", "Reorder recommendations", "View stock levels"],
    }


def _handle_client_query(message: str) -> Dict:
    """Handle client-related queries."""
    try:
        from sas_management.models import Client
        
        client_count = Client.query.count()
        
        reply = f"Client Overview:\n\n"
        reply += f"• Total clients: {client_count}\n\n"
        reply += "Use the Client Analyzer feature to analyze client value and preferences."
        
        return {
            "reply": reply,
            "source": "system_data",
            "suggested_actions": ["Client analysis", "Top clients", "Client reports"],
        }
    except Exception as e:
        current_app.logger.warning(f"Error handling client query: {e}")
        return {
            "reply": "I can help with client information, but I'm having trouble accessing the data right now.",
            "source": "system_data",
            "suggested_actions": [],
        }


def _get_session_memory() -> List[Dict]:
    """Get last 5 messages from session."""
    if "ai_chat_memory" not in session:
        session["ai_chat_memory"] = []
    return session["ai_chat_memory"][-5:]  # Last 5 messages only


def _update_session_memory(user_message: str, ai_reply: str, intent: str = None):
    """Update session memory with new exchange."""
    if "ai_chat_memory" not in session:
        session["ai_chat_memory"] = []
    
    memory_entry = {
        "user": user_message,
        "ai": ai_reply,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if intent:
        memory_entry["intent"] = intent
    
    session["ai_chat_memory"].append(memory_entry)
    
    # Keep only last 5 exchanges
    session["ai_chat_memory"] = session["ai_chat_memory"][-5:]
    session.modified = True
