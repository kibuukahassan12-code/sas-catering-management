"""
SAS AI Service - Wrapper for chat engine.
"""
import logging
from sqlalchemy import func
from sas_management.models import db
from sas_management.ai.chat_engine import detect_intent, process_message, get_user_role
from sas_management.ai.knowledge import SYSTEM_KNOWLEDGE
from sas_management.ai.knowledge_graph import explain_relationship, find_related_modules

logger = logging.getLogger("sas_ai")


class ContextualSASAI:
    def __init__(self):
        self.enabled = True

    def chat(self, message: str, user_id: int = None) -> dict:
        """Process message through intelligent chat engine."""
        try:
            # Detect intent and log decision
            text_lower = message.lower().strip()
            last_intent = None  # Could get from session if needed
            intent, score = detect_intent(text_lower, last_intent)
            
            # Log AI decision (production-ready format)
            logger.info(
                "AI_DECISION intent=%s score=%s message=%s",
                intent, score, message[:100]
            )
            
            # Handle specific intents explicitly
            user_role = get_user_role(user_id)
            
            if intent == "everything":
                return {
                    "message": self.handle_everything(user_role),
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
            
            if intent == "bakery":
                return {
                    "message": self.handle_bakery(user_role),
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
            
            # Handle knowledge graph queries (but NOT if it's a count/sum/list query)
            text_lower = message.lower().strip()
            
            # Skip explanation if numeric intent detected
            numeric_keywords = ["how many", "number of", "total count", "how much", "total amount", "which", "what are", "list"]
            is_numeric_query = any(k in text_lower for k in numeric_keywords)
            
            if not is_numeric_query:
                if "how does" in text_lower and ("relate" in text_lower or "work" in text_lower):
                    # Extract module name
                    all_modules = list(SYSTEM_KNOWLEDGE.keys())
                    for module in all_modules:
                        if module in text_lower:
                            explanation = explain_relationship(module)
                            if explanation:
                                response = explanation.replace("**", "")
                                return {
                                    "message": response,
                                    "chart": None,
                                    "prediction": None,
                                    "report_url": None
                                }
                
                # Handle "what is" or "explain" queries for any module
                if "what is" in text_lower or "explain" in text_lower or "tell me about" in text_lower:
                    all_modules = list(SYSTEM_KNOWLEDGE.keys())
                    for module in all_modules:
                        if module in text_lower and module != "system":
                            module_desc = SYSTEM_KNOWLEDGE.get(module, "")
                            if module_desc:
                                # Add relationship info if available
                                rel_info = explain_relationship(module)
                                if rel_info:
                                    module_desc += f"\n\n{rel_info}"
                                module_desc = module_desc.replace("**", "")
                                return {
                                    "message": module_desc,
                                    "chart": None,
                                    "prediction": None,
                                    "report_url": None
                                }
            
            # Process through main engine
            result = process_message(message, user_id)
            # Ensure result is always a dict
            if isinstance(result, str):
                # Remove markdown from string responses
                result = result.replace("**", "")
                return {
                    "message": result,
                    "chart": None,
                    "prediction": None,
                    "report_url": None
                }
            
            # Remove markdown from dict responses
            if isinstance(result, dict) and "message" in result:
                result["message"] = result["message"].replace("**", "")
            
            return result
        except Exception as e:
            error_msg = f"⚠️ An error occurred while processing this request: {str(e)}"
            logger.error(f"AI service error: {e}", exc_info=True)
            return {
                "message": error_msg,
                "chart": None,
                "prediction": None,
                "report_url": None
            }
    
    def handle_everything(self, role: str) -> str:
        """Generate comprehensive system overview."""
        summary = []
        
        # Safe model imports
        Event = None
        Venue = None
        Payment = None
        try:
            from sas_management.models import Event, Venue, AccountingPayment
            Payment = AccountingPayment
        except Exception as e:
            logger.warning(f"Could not import models for everything handler: {e}")
        
        try:
            if Event:
                count = db.session.query(func.count(Event.id)).scalar() or 0
                summary.append(f"• Events: {count}")
            else:
                summary.append("• Events: unavailable")
        except Exception as e:
            summary.append(f"• Events: unavailable ({str(e)})")
        
        try:
            if Venue:
                count = db.session.query(func.count(Venue.id)).scalar() or 0
                summary.append(f"• Venues: {count}")
            else:
                summary.append("• Venues: unavailable")
        except Exception as e:
            summary.append(f"• Venues: unavailable ({str(e)})")
        
        try:
            if Payment:
                total = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).scalar()
                if role == "admin":
                    summary.append(f"• Revenue: {total:,.2f} UGX")
                else:
                    summary.append("• Revenue: available to admins")
            else:
                summary.append("• Revenue: unavailable")
        except Exception as e:
            summary.append(f"• Revenue: unavailable ({str(e)})")
        
        summary.append("• Bakery: production & baked goods management")
        summary.append("• Production: event execution & operations")
        summary.append("• POS: point of sale and retail transactions")
        summary.append("• CRM: customer relationship management")
        summary.append("• Vendors: supplier management")
        summary.append("• Reports: comprehensive business reporting")
        summary.append("• Analytics: business intelligence and insights")
        summary.append("• Automation: workflow automation")
        summary.append("• Invoices: billing and invoicing")
        summary.append("• Quotes: quotations and estimates")
        summary.append("• Proposals: business proposals")
        summary.append("• Profitability: profit analysis")
        summary.append("• KDS: kitchen display system")
        summary.append("• Menu Builder: menu creation and management")
        summary.append("• Catering: catering operations")
        summary.append("• Dispatch: delivery and logistics")
        summary.append("• Timeline: event timeline management")
        summary.append("• Tasks: task tracking")
        summary.append("• Communication: messaging and notifications")
        summary.append("• Client Portal: customer self-service")
        summary.append("• Mobile Staff: mobile app for staff")
        summary.append("• Food Safety: compliance and safety tracking")
        summary.append("• Incidents: incident management")
        summary.append("• Floorplanner: event floor plan management")
        summary.append("• University: training and education")
        summary.append("• Payroll: employee compensation")
        summary.append("• Cashbook: cash transaction tracking")
        summary.append("• Integrations: third-party integrations")
        summary.append("• Production Recipes: recipe library")
        summary.append("• Hire: equipment rentals")
        summary.append("• BI: business intelligence")
        summary.append("• Search: system-wide search")
        summary.append("• Audit: audit trail and compliance")
        summary.append("• Branches: multi-location management")
        summary.append("• Contracts: contract management")
        summary.append("• Leads: sales lead management")
        
        return (
            "Here's a complete system overview:\n\n"
            + "\n".join(summary)
            + "\n\nWhich area would you like to explore deeper? I can explain any module in detail."
        )
    
    def handle_bakery(self, role: str) -> str:
        """Handle bakery-specific queries."""
        response = (
            "The Bakery module manages baked goods production.\n\n"
            "Features:\n"
            "• Bakery item creation\n"
            "• Recipes and ingredients\n"
            "• Production planning\n"
            "• Cost tracking\n"
            "• Integration with events and accounting"
        )
        
        try:
            from sas_management.models import InventoryItem
            count = db.session.query(func.count(InventoryItem.id)).scalar() or 0
            if role == "admin":
                response += f"\n\nYou currently have {count} bakery-related items."
        except Exception as e:
            logger.warning(f"Could not fetch bakery items count: {e}")
        
        # Remove markdown
        response = response.replace("**", "")
        return response


ai_service = ContextualSASAI()
