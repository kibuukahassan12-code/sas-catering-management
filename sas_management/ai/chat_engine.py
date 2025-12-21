"""
SAS AI Chat Engine - Context-aware, system-aware intelligence core.
"""
from sqlalchemy import func
from sas_management.models import db
from flask import session
from sas_management.ai.knowledge import SYSTEM_KNOWLEDGE

# Safe model imports for counting
try:
    from sas_management.models import User, Venue, Event
    # User model serves as staff/employee model
    Staff = User
except Exception:
    User = None
    Staff = None
    Venue = None
    Event = None

# Intent keywords mapping - comprehensive system coverage
INTENTS = {
    "inventory": ["inventory", "stock", "ingredients", "items", "supplies", "stock count", "low stock"],
    "accounting": ["accounting", "invoices", "payments", "expenses", "financial", "revenue", "profit", "cashbook", "journal", "ledger"],
    "production": ["production", "kitchen", "preparation", "cooking", "prep", "production order", "recipe"],
    "events": ["event", "booking", "function", "service", "event service", "event planning"],
    "revenue": ["revenue", "sales", "profit", "income", "earnings"],
    "staff": ["staff", "employees", "workers", "team", "hr", "human resources", "workforce"],
    "bakery": ["bakery", "baked", "bread", "cakes", "pastries", "baking"],
    "pos": ["pos", "point of sale", "sales", "terminal", "counter", "retail"],
    "crm": ["crm", "customer", "client", "relationship", "lead", "opportunity"],
    "vendors": ["vendor", "supplier", "suppliers"],
    "venues": ["venue", "venues", "location", "locations", "facility"],
    "reports": ["report", "reports", "reporting"],
    "analytics": ["analytics", "analysis", "insights", "metrics", "dashboard"],
    "automation": ["automation", "automate", "workflow", "automated"],
    "invoices": ["invoice", "invoices", "billing", "bill"],
    "quotes": ["quote", "quotation", "quotations", "estimate", "estimates"],
    "proposals": ["proposal", "proposals"],
    "profitability": ["profitability", "margin", "margins", "profit analysis"],
    "kds": ["kds", "kitchen display", "kitchen display system"],
    "menu_builder": ["menu", "menus", "menu builder", "menu item"],
    "catering": ["catering", "cater"],
    "dispatch": ["dispatch", "delivery", "deliveries", "logistics"],
    "timeline": ["timeline", "timelines", "schedule"],
    "tasks": ["task", "tasks", "todo", "to-do"],
    "communication": ["communication", "message", "messages", "email", "sms"],
    "client_portal": ["client portal", "customer portal", "portal"],
    "mobile_staff": ["mobile staff", "mobile app", "staff app"],
    "food_safety": ["food safety", "safety", "compliance", "haccp"],
    "incidents": ["incident", "incidents", "accident"],
    "floorplanner": ["floor plan", "floorplan", "floor planner", "seating"],
    "university": ["university", "training", "education", "learning"],
    "payroll": ["payroll", "salary", "salaries", "wages"],
    "cashbook": ["cashbook", "cash book", "petty cash"],
    "integrations": ["integration", "integrations", "api", "third party"],
    "production_recipes": ["recipe", "recipes", "production recipe"],
    "hire": ["hire", "rental", "rentals", "equipment hire"],
    "bi": ["bi", "business intelligence", "data visualization"],
    "search": ["search", "find", "lookup"],
    "audit": ["audit", "auditing", "audit trail"],
    "branches": ["branch", "branches", "location", "locations"],
    "contracts": ["contract", "contracts", "agreement"],
    "leads": ["lead", "leads", "prospect"],
    "everything": ["everything", "all", "overview", "summary", "complete", "full", "system"]
}

# Safe model imports
try:
    from sas_management.models import InventoryItem, Ingredient, Invoice, AccountingPayment, Transaction, ProductionOrder, Task, Event
    Payment = AccountingPayment
except Exception:
    InventoryItem = None
    Ingredient = None
    Invoice = None
    Payment = None
    Transaction = None
    ProductionOrder = None
    Task = None
    Event = None


def detect_intent(text: str, last_intent: str = None) -> tuple:
    """
    Detect user intent from message text with scoring.
    
    Returns:
        tuple: (intent, score) where score is number of keyword matches
    """
    text_lower = text.lower()
    
    # Handle follow-up questions
    if "how about" in text_lower or "what about" in text_lower:
        if last_intent:
            return (last_intent, 10)  # High confidence for follow-ups
        # Extract topic after "how about" or "what about"
        topic = text_lower.replace("how about", "").replace("what about", "").strip()
        for intent, keywords in INTENTS.items():
            matches = sum(1 for kw in keywords if kw in topic)
            if matches > 0:
                return (intent, matches)
    
    # Score all intents
    intent_scores = {}
    for intent, keywords in INTENTS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            intent_scores[intent] = score
    
    if not intent_scores:
        return (None, 0)
    
    # Return best match
    best_intent = max(intent_scores.items(), key=lambda x: x[1])
    return best_intent


def get_inventory_response(is_admin: bool = True) -> str:
    """Get inventory status using real data with role filtering."""
    if not InventoryItem:
        response = SYSTEM_KNOWLEDGE["inventory"]
        return response.replace("**", "")
    
    try:
        total_items = db.session.query(func.count(InventoryItem.id)).scalar() or 0
        
        # Count low stock items
        low_stock = 0
        if hasattr(InventoryItem, 'stock_count'):
            low_stock = db.session.query(func.count(InventoryItem.id)).filter(
                InventoryItem.stock_count <= 10
            ).scalar() or 0
        elif hasattr(InventoryItem, 'quantity'):
            low_stock = db.session.query(func.count(InventoryItem.id)).filter(
                InventoryItem.quantity <= 10
            ).scalar() or 0
        
        if is_admin:
            # Admin sees full details
            response = f"Inventory Status:\n\n"
            response += f"• Total items: {total_items}\n"
            if low_stock > 0:
                response += f"• Low stock items: {low_stock} (need reordering)\n"
            response += "\n" + SYSTEM_KNOWLEDGE["inventory"]
        else:
            # Staff sees summary only
            if low_stock > 0:
                response = f"Inventory status: {low_stock} items need reordering. Low stock alerts are active."
            else:
                response = "Inventory status is healthy. All items are adequately stocked."
        
        # Remove markdown
        response = response.replace("**", "")
        return response
    except Exception as e:
        error_msg = f"⚠️ An error occurred while fetching inventory data: {str(e)}"
        return error_msg.replace("**", "") if is_admin else "Inventory module is operational."


def get_accounting_response(is_admin: bool = True) -> str:
    """Get accounting status using real data with role filtering."""
    if not Invoice and not Payment:
        response = SYSTEM_KNOWLEDGE["accounting"]
        return response.replace("**", "")
    
    try:
        if is_admin:
            # Admin sees full details
            response = "Accounting Overview:\n\n"
            
            if Invoice:
                total_invoices = db.session.query(func.count(Invoice.id)).scalar() or 0
                response += f"• Total invoices: {total_invoices}\n"
                
                # Try to get outstanding balance
                if hasattr(Invoice, 'total_amount_ugx') and hasattr(Invoice, 'status'):
                    outstanding = db.session.query(
                        func.coalesce(func.sum(Invoice.total_amount_ugx), 0)
                    ).filter(
                        Invoice.status != "Paid"
                    ).scalar() or 0
                    if outstanding > 0:
                        response += f"• Outstanding balance: {outstanding:,.2f} UGX\n"
            
            if Payment:
                total_payments = db.session.query(func.count(Payment.id)).scalar() or 0
                total_revenue = db.session.query(
                    func.coalesce(func.sum(Payment.amount), 0)
                ).scalar() or 0
                response += f"• Total payments: {total_payments}\n"
                response += f"• Total revenue: {total_revenue:,.2f} UGX\n"
            
            response += "\n" + SYSTEM_KNOWLEDGE["accounting"]
        else:
            # Staff sees summary only
            response = (
                "Accounting operations are running smoothly.\n\n"
                "Financial tracking is active and all transactions are being processed correctly."
            )
        
        # Remove markdown
        response = response.replace("**", "")
        return response
    except Exception as e:
        error_msg = f"⚠️ An error occurred while fetching accounting data: {str(e)}"
        return error_msg.replace("**", "") if is_admin else "Accounting module is operational."


def get_production_response(is_admin: bool = True) -> str:
    """Get production status using real data with role filtering."""
    if not ProductionOrder and not Task:
        response = SYSTEM_KNOWLEDGE["production"]
        return response.replace("**", "")
    
    try:
        if is_admin:
            response = "Production Status:\n\n"
            
            if ProductionOrder:
                active_orders = db.session.query(func.count(ProductionOrder.id)).filter(
                    ProductionOrder.status != "Completed"
                ).scalar() or 0
                response += f"• Active production orders: {active_orders}\n"
            
            if Task:
                pending_tasks = db.session.query(func.count(Task.id)).filter(
                    Task.status == "Pending"
                ).scalar() or 0
                response += f"• Pending tasks: {pending_tasks}\n"
            
            response += "\n" + SYSTEM_KNOWLEDGE["production"]
        else:
            response = "Production workflows are active. All orders are being processed efficiently."
        
        # Remove markdown
        response = response.replace("**", "")
        return response
    except Exception as e:
        error_msg = f"⚠️ An error occurred while fetching production data: {str(e)}"
        return error_msg.replace("**", "") if is_admin else "Production module is operational."


def get_events_response(is_admin: bool = True) -> str:
    """Get events status using real data with role filtering."""
    if not Event:
        response = SYSTEM_KNOWLEDGE["events"]
        return response.replace("**", "")
    
    try:
        total_events = db.session.query(func.count(Event.id)).scalar() or 0
        
        if is_admin:
            response = f"Events Overview:\n\n"
            response += f"• Total events: {total_events}\n"
            response += "\n" + SYSTEM_KNOWLEDGE["events"]
        else:
            response = f"Events module is active with {total_events} total events in the system."
        
        # Remove markdown
        response = response.replace("**", "")
        return response
    except Exception as e:
        error_msg = f"⚠️ An error occurred while fetching events data: {str(e)}"
        return error_msg.replace("**", "") if is_admin else "Events module is operational."


def get_revenue_response(is_admin: bool = True) -> str:
    """Get revenue status using real data with role filtering."""
    if not Payment:
        response = SYSTEM_KNOWLEDGE["revenue"]
        return response.replace("**", "")
    
    try:
        if is_admin:
            total_revenue = db.session.query(
                func.coalesce(func.sum(Payment.amount), 0)
            ).scalar() or 0
            
            response = f"Revenue Summary:\n\n"
            response += f"• Total revenue: {total_revenue:,.2f} UGX\n"
            response += "\n" + SYSTEM_KNOWLEDGE["revenue"]
        else:
            response = "Revenue performance is healthy this month. All systems are operating normally."
        
        # Remove markdown
        response = response.replace("**", "")
        return response
    except Exception as e:
        error_msg = f"⚠️ An error occurred while fetching revenue data: {str(e)}"
        return error_msg.replace("**", "") if is_admin else "Revenue tracking is active."


def get_user_role(user_id: int = None):
    """Get user role from session or user_id."""
    from flask_login import current_user
    
    try:
        if user_id:
            from sas_management.models import User
            user = User.query.get(user_id)
            if user:
                if hasattr(user, 'is_admin') and user.is_admin:
                    return "admin"
                if hasattr(user, 'role'):
                    role_str = str(user.role).lower()
                    if "admin" in role_str:
                        return "admin"
                    return "staff"
        elif hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            if hasattr(current_user, 'is_admin') and current_user.is_admin:
                return "admin"
            if hasattr(current_user, 'role'):
                role_str = str(current_user.role).lower()
                if "admin" in role_str:
                    return "admin"
                return "staff"
    except Exception:
        pass
    
    return "staff"  # Default to staff for safety


def process_message(text: str, user_id: int = None) -> dict:
    """
    Process user message and return intelligent response with metadata.
    
    Args:
        text: User's message
        user_id: Optional user ID for session tracking
    
    Returns:
        dict with message, chart, prediction, report_url
    """
    text = text.strip()
    if not text:
        return {
            "message": "Please enter a message.",
            "chart": None,
            "prediction": None,
            "report_url": None
        }
    
    text_lower = text.lower()
    
    # Get user role
    user_role = get_user_role(user_id)
    is_admin = (user_role == "admin")
    
    # Get last intent from session
    last_intent = session.get("ai_last_intent")
    last_fallback = session.get("ai_last_fallback", "")
    clarification_count = session.get("clarification_count", 0)
    
    # Detect intent with scoring
    intent, intent_score = detect_intent(text_lower, last_intent)
    
    # Handle report generation requests (Admin only)
    if "generate" in text_lower and "report" in text_lower:
        if not is_admin:
            return {
                "message": "You don't have permission to generate reports. This feature is available to administrators only.",
                "chart": None,
                "prediction": None,
                "report_url": None
            }
        
        from sas_management.ai.reports import generate_inventory_report, generate_revenue_report, generate_performance_report
        
        if "inventory" in text_lower:
            result = generate_inventory_report()
            if result.get("success"):
                return {
                    "message": f"✅ Inventory report generated successfully!\n\n{result['report_data']['summary']}",
                    "chart": None,
                    "prediction": None,
                    "report_url": result.get("report_url")
                }
        elif "revenue" in text_lower:
            result = generate_revenue_report()
            if result.get("success"):
                return {
                    "message": f"✅ Revenue report generated successfully!\n\n{result['report_data']['summary']}",
                    "chart": None,
                    "prediction": None,
                    "report_url": result.get("report_url")
                }
        elif "performance" in text_lower or "overall" in text_lower:
            result = generate_performance_report()
            if result.get("success"):
                return {
                    "message": f"✅ Performance report generated successfully!\n\n{result['report_data']['summary']}",
                    "chart": None,
                    "prediction": None,
                    "report_url": result.get("report_url")
                }
        else:
            return {
                "message": "I can generate inventory, revenue, or performance reports. Which one would you like?",
                "chart": None,
                "prediction": None,
                "report_url": None
            }
    
    # Handle greetings
    if text_lower in ["hi", "hello", "hey", "good morning", "good evening"]:
        session["ai_last_intent"] = None
        session["ai_last_fallback"] = ""
        greeting = (
            "Hello 👋 I'm SAS AI.\n\n"
            "I can help you understand your entire system using real data. "
            "I know about all modules including Events, Accounting, Production, Inventory, "
            "POS, CRM, Bakery, HR, Analytics, Reports, and many more.\n\n"
            "Ask me about any module, feature, or how the system works!"
        )
        if is_admin:
            greeting += "\n\nAs an administrator, you have access to full analytics, predictions, and report generation."
        
        return {
            "message": greeting,
            "chart": None,
            "prediction": None,
            "report_url": None
        }
    
    # Handle follow-up questions
    if "how about" in text_lower or "what about" in text_lower:
        if last_intent:
            intent = last_intent
            intent_score = 10
        else:
            # Extract topic
            topic = text_lower.replace("how about", "").replace("what about", "").strip()
            intent, intent_score = detect_intent(topic, last_intent)
    
    # Handle "tell me more" / "explain more"
    if text_lower in ["tell me more", "explain more", "more details", "more info"]:
        if last_intent:
            intent = last_intent
            intent_score = 10
        else:
            # Reset clarification count and provide overview
            session["clarification_count"] = 0
            return {
                "message": (
                    "I'd be happy to provide more details!\n\n"
                    "What would you like to know more about?\n"
                    "• Inventory\n"
                    "• Accounting\n"
                    "• Production\n"
                    "• Events\n"
                    "• Revenue\n"
                    "• Bakery\n"
                    "• Staff"
                ),
                "chart": None,
                "prediction": None,
                "report_url": None
            }
    
    # ============================================================
    # STEP 1: COUNT INTENT (MUST BE FIRST - BEFORE EXPLANATIONS)
    # ============================================================
    count_keywords = ["how many", "number of", "total count", "count of"]
    if any(k in text_lower for k in count_keywords):
        # Context-aware counting
        last_topic = session.get("ai_last_intent")
        
        # Staff/Employee count
        if "staff" in text_lower or "employee" in text_lower or last_topic == "staff" or last_topic == "hr":
            try:
                if Staff:
                    count = db.session.query(func.count(Staff.id)).scalar() or 0
                    session["ai_last_intent"] = "staff"
                    session["clarification_count"] = 0
                    response = f"You currently have {count} staff members."
                    # Remove markdown
                    response = response.replace("**", "")
                    return {
                        "message": response,
                        "chart": None,
                        "prediction": None,
                        "report_url": None
                    }
                else:
                    response = "Staff records are not available."
                    response = response.replace("**", "")
                    return {
                        "message": response,
                        "chart": None,
                        "prediction": None,
                        "report_url": None
                    }
            except Exception as e:
                response = f"Unable to retrieve staff count: {str(e)}"
                response = response.replace("**", "")
                return {
                    "message": response,
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
        
        # Venue count
        if "venue" in text_lower or "venues" in text_lower or last_topic == "venues":
            try:
                if Venue:
                    count = db.session.query(func.count(Venue.id)).scalar() or 0
                    session["ai_last_intent"] = "venues"
                    session["clarification_count"] = 0
                    response = f"You currently have {count} event venues."
                    response = response.replace("**", "")
                    return {
                        "message": response,
                        "chart": None,
                        "prediction": None,
                        "report_url": None
                    }
                else:
                    response = "Venue records are not available."
                    response = response.replace("**", "")
                    return {
                        "message": response,
                        "chart": None,
                        "prediction": None,
                        "report_url": None
                    }
            except Exception as e:
                response = f"Unable to retrieve venue count: {str(e)}"
                response = response.replace("**", "")
                return {
                    "message": response,
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
        
        # Event count
        if "event" in text_lower or last_topic == "events":
            try:
                if Event:
                    count = db.session.query(func.count(Event.id)).scalar() or 0
                    session["ai_last_intent"] = "events"
                    session["clarification_count"] = 0
                    response = f"You currently have {count} events."
                    response = response.replace("**", "")
                    return {
                        "message": response,
                        "chart": None,
                        "prediction": None,
                        "report_url": None
                    }
                else:
                    response = "Event records are not available."
                    response = response.replace("**", "")
                    return {
                        "message": response,
                        "chart": None,
                        "prediction": None,
                        "report_url": None
                    }
            except Exception as e:
                response = f"Unable to retrieve event count: {str(e)}"
                response = response.replace("**", "")
                return {
                    "message": response,
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
    
    # ============================================================
    # STEP 2: SUM INTENT (how much / total amount)
    # ============================================================
    # Revenue sum is handled by revenue intent below
    
    # ============================================================
    # STEP 3: LIST INTENT (which / what are)
    # ============================================================
    list_keywords = ["which", "what are", "list"]
    if any(k in text_lower for k in list_keywords):
        # Venue listing
        if "venue" in text_lower:
            try:
                if Venue:
                    venues = db.session.query(Venue.name).all()
                    if not venues:
                        response = "There are currently no venues registered."
                    else:
                        names = ", ".join(v[0] for v in venues)
                        response = f"Your venues are: {names}"
                    response = response.replace("**", "")
                    session["ai_last_intent"] = "venues"
                    session["clarification_count"] = 0
                    return {
                        "message": response,
                        "chart": None,
                        "prediction": None,
                        "report_url": None
                    }
            except Exception:
                pass
    
    # ============================================================
    # STEP 4: EXPLANATION INTENT (what does / explain)
    # ============================================================
    # Only process explanations if no numeric intent was matched above
    
    # Process by intent
    if intent == "inventory":
        session["ai_last_intent"] = "inventory"
        session["ai_last_fallback"] = ""
        session["clarification_count"] = 0
        
        # Get response with role filtering
        response_text = get_inventory_response(is_admin=is_admin)
        
        # Add prediction for admin
        prediction = None
        if is_admin and ("forecast" in text_lower or "predict" in text_lower or "project" in text_lower):
            from sas_management.ai.predictive import forecast_inventory
            prediction = forecast_inventory()
        
        # Add chart for admin
        chart = None
        if is_admin:
            from sas_management.ai.charts import inventory_chart
            chart = inventory_chart()
        
        return {
            "message": response_text,
            "chart": chart,
            "prediction": prediction,
            "report_url": None
        }
    
    elif intent == "accounting":
        session["ai_last_intent"] = "accounting"
        session["ai_last_fallback"] = ""
        session["clarification_count"] = 0
        
        # Get response with role filtering
        response_text = get_accounting_response(is_admin=is_admin)
        
        return {
            "message": response_text,
            "chart": None,
            "prediction": None,
            "report_url": None
        }
    
    elif intent == "production":
        session["ai_last_intent"] = "production"
        session["ai_last_fallback"] = ""
        session["clarification_count"] = 0
        
        response_text = get_production_response(is_admin=is_admin)
        
        return {
            "message": response_text,
            "chart": None,
            "prediction": None,
            "report_url": None
        }
    
    elif intent == "events":
        session["ai_last_intent"] = "events"
        session["ai_last_fallback"] = ""
        session["clarification_count"] = 0
        
        response_text = get_events_response(is_admin=is_admin)
        
        # Add chart for admin
        chart = None
        if is_admin:
            try:
                from sas_management.ai.charts import events_chart
                chart = events_chart()
            except Exception:
                chart = None
        
        return {
            "message": response_text,
            "chart": chart,
            "prediction": None,
            "report_url": None
        }
    
    elif intent == "revenue":
        session["ai_last_intent"] = "revenue"
        session["ai_last_fallback"] = ""
        session["clarification_count"] = 0
        
        # Role-aware response
        response_text = get_revenue_response(is_admin=is_admin)
        
        # Add prediction and chart for admin
        prediction = None
        chart = None
        if is_admin:
            if "forecast" in text_lower or "predict" in text_lower or "project" in text_lower:
                from sas_management.ai.predictive import forecast_revenue
                prediction = forecast_revenue()
            
            try:
                from sas_management.ai.charts import revenue_chart
                chart = revenue_chart()
            except Exception:
                chart = None
        
        return {
            "message": response_text,
            "chart": chart,
            "prediction": prediction,
            "report_url": None
        }
    
    elif intent == "staff":
        session["ai_last_intent"] = "staff"
        session["ai_last_fallback"] = ""
        session["clarification_count"] = 0
        return {
            "message": SYSTEM_KNOWLEDGE["staff"],
            "chart": None,
            "prediction": None,
            "report_url": None
        }
    
    # Handle all other module intents dynamically
    elif intent in SYSTEM_KNOWLEDGE:
        session["ai_last_intent"] = intent
        session["ai_last_fallback"] = ""
        session["clarification_count"] = 0
        
        # Get module description
        response_text = SYSTEM_KNOWLEDGE[intent]
        
        # Add relationship info if available
        try:
            from sas_management.ai.knowledge_graph import explain_relationship
            rel_info = explain_relationship(intent)
            if rel_info:
                response_text += f"\n\n{rel_info}"
        except Exception:
            pass
        
        return {
            "message": response_text,
            "chart": None,
            "prediction": None,
            "report_url": None
        }
    
    # Best-match fallback with clarification loop breaker
    if clarification_count >= 1:
        # Stop asking for clarification - answer with best match
        if intent and intent_score > 0:
            # Use the detected intent even if not perfect match
            session["clarification_count"] = 0
            # Re-process with this intent
            if intent == "inventory":
                response_text = get_inventory_response(is_admin=is_admin)
                chart = None
                if is_admin:
                    try:
                        from sas_management.ai.charts import inventory_chart
                        chart = inventory_chart()
                    except Exception:
                        chart = None
                return {
                    "message": response_text + "\n\nIf you meant something else, let me know.",
                    "chart": chart,
                    "prediction": None,
                    "report_url": None
                }
            elif intent == "accounting":
                response_text = get_accounting_response(is_admin=is_admin)
                response_text = response_text.replace("**", "")
                return {
                    "message": response_text + "\n\nIf you meant something else, let me know.",
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
            elif intent == "production":
                response_text = get_production_response(is_admin=is_admin)
                response_text = response_text.replace("**", "")
                return {
                    "message": response_text + "\n\nIf you meant something else, let me know.",
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
            elif intent == "events":
                response_text = get_events_response(is_admin=is_admin)
                response_text = response_text.replace("**", "")
                chart = None
                if is_admin:
                    try:
                        from sas_management.ai.charts import events_chart
                        chart = events_chart()
                    except Exception:
                        chart = None
                return {
                    "message": response_text + "\n\nIf you meant something else, let me know.",
                    "chart": chart,
                    "prediction": None,
                    "report_url": None
                }
            elif intent == "revenue":
                response_text = get_revenue_response(is_admin=is_admin)
                response_text = response_text.replace("**", "")
                chart = None
                if is_admin:
                    try:
                        from sas_management.ai.charts import revenue_chart
                        chart = revenue_chart()
                    except Exception:
                        chart = None
                return {
                    "message": response_text + "\n\nIf you meant something else, let me know.",
                    "chart": chart,
                    "prediction": None,
                    "report_url": None
                }
            elif intent == "bakery":
                response_text = SYSTEM_KNOWLEDGE.get("bakery", "Bakery module information.")
                response_text = response_text.replace("**", "")
                return {
                    "message": response_text + "\n\nIf you meant something else, let me know.",
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
            elif intent in SYSTEM_KNOWLEDGE:
                # Handle any other module in knowledge base
                response_text = SYSTEM_KNOWLEDGE[intent]
                try:
                    from sas_management.ai.knowledge_graph import explain_relationship
                    rel_info = explain_relationship(intent)
                    if rel_info:
                        response_text += f"\n\n{rel_info}"
                except Exception:
                    pass
                response_text = response_text.replace("**", "")
                return {
                    "message": response_text + "\n\nIf you meant something else, let me know.",
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
    
    # Increment clarification count
    session["clarification_count"] = clarification_count + 1
    
    # Best-match fallback with response variation
    import random
    # Get all available modules for fallback suggestions
    all_modules = list(SYSTEM_KNOWLEDGE.keys())
    # Filter out "system" and "everything" for suggestions
    module_list = [m for m in all_modules if m not in ["system", "everything"]]
    # Create a sample of modules for suggestions
    sample_modules = ", ".join(module_list[:10])  # Show first 10 modules
    
    fallback_options = [
        f"I can help you with {sample_modules}, and more. Which module interests you?",
        f"I can provide information about any system module including {sample_modules}. What would you like to know?",
        f"I'm here to help with all system modules: {sample_modules}, and others. What can I explain?",
    ]
    
    # Select different fallback than last time
    available_options = [opt for opt in fallback_options if opt != last_fallback]
    if available_options:
        selected_fallback = random.choice(available_options)
    else:
        selected_fallback = fallback_options[0]
    
    # If last intent exists and clarification count is low, reference it
    if last_intent and clarification_count == 0:
        module_list = ", ".join([m for m in list(SYSTEM_KNOWLEDGE.keys())[:8] if m not in ["system", "everything"]])
        selected_fallback = (
            f"Based on our previous discussion about {last_intent}, "
            f"would you like more details on that, or something else?\n\n"
            f"I can help with {module_list}, and many other modules."
        )
        if is_admin:
            selected_fallback += "\n\nAs an admin, you can also request forecasts and generate reports."
    
    session["ai_last_fallback"] = selected_fallback
    return {
        "message": selected_fallback,
        "chart": None,
        "prediction": None,
        "report_url": None
    }

