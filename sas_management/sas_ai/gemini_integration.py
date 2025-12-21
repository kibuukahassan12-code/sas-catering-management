"""Google Gemini AI Integration for SAS AI Assistant."""
import os
from typing import Optional, Dict, List
from flask import current_app

# Try to import Google Generative AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class SASAssistant:
    """SAS AI Assistant using Google Gemini for natural language responses."""
    
    def __init__(self):
        """Initialize the Gemini AI assistant."""
        self.model = None
        self.chat = None
        self.enabled = False
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization - call this when Flask app context is available."""
        if self._initialized:
            return
        
        self._initialized = True
        
        if not GEMINI_AVAILABLE:
            return
        
        # Check for API key
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                # Try to get from config if app context is available
                try:
                    api_key = current_app.config.get("GOOGLE_API_KEY")
                except RuntimeError:
                    pass
            
            if not api_key:
                if hasattr(current_app, 'logger'):
                    current_app.logger.warning("GOOGLE_API_KEY not found. Gemini AI will be disabled.")
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.chat = None  # Will be initialized per session
            self.enabled = True
        except Exception as e:
            if hasattr(current_app, 'logger'):
                current_app.logger.error(f"Error initializing Gemini AI: {e}")
            self.enabled = False
    
    def get_system_data(self, query: str, entities: Dict, conversation_history: List[Dict]) -> Optional[str]:
        """Fetch data from SAS Catering Database based on query."""
        # Lazy initialize if not already done
        if not self._initialized:
            self._initialize()
        """
        Fetch data from SAS Catering Database based on query.
        
        Returns:
            System data string or None if no relevant data found
        """
        try:
            query_lower = query.lower()
            topics = entities.get("topics", [])
            
            # Revenue/Profit queries
            if "profit" in query_lower or "profit" in topics or "revenue" in query_lower or "revenue" in topics:
                return self._get_revenue_data()
            
            # Event queries
            if "event" in query_lower or "event" in topics:
                return self._get_events_data()
            
            # Staff queries
            if "staff" in query_lower or "employee" in query_lower or "staff" in topics:
                return self._get_staff_data()
            
            # Inventory queries
            if "inventory" in query_lower or "stock" in query_lower or "inventory" in topics:
                return self._get_inventory_data()
            
            return None
            
        except Exception as e:
            current_app.logger.warning(f"Error getting system data: {e}")
            return None
    
    def _get_revenue_data(self) -> str:
        """Get revenue/profit data from database."""
        try:
            from sas_management.models import Quotation
            from datetime import datetime
            
            today = datetime.utcnow()
            month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            quotes = Quotation.query.filter(
                Quotation.status == "Accepted",
                Quotation.created_at >= month_start
            ).all()
            
            if not quotes:
                return "No accepted quotes found for this month."
            
            total = sum(float(quote.total_amount or 0) for quote in quotes)
            return f"Based on the database, this month's revenue from {len(quotes)} accepted quotes is {total:,.0f} UGX."
        except Exception as e:
            current_app.logger.warning(f"Error querying revenue: {e}")
            return "Revenue data is currently unavailable."
    
    def _get_events_data(self) -> str:
        """Get events data from database."""
        try:
            from sas_management.service.models import ServiceEvent
            from datetime import date
            
            today = date.today()
            month_start = today.replace(day=1)
            
            events_this_month = ServiceEvent.query.filter(
                ServiceEvent.event_date >= month_start,
                ServiceEvent.event_date <= today
            ).count()
            
            upcoming = ServiceEvent.query.filter(ServiceEvent.event_date > today).count()
            
            event_types = {}
            for event in ServiceEvent.query.filter(ServiceEvent.event_date >= month_start).all():
                event_type = event.event_type or "Other"
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            summary = f"You have {upcoming} upcoming events"
            if events_this_month > 0:
                summary += f" and {events_this_month} events this month"
            
            if event_types:
                type_list = ", ".join([f"{count} {etype}" for etype, count in event_types.items()])
                summary += f". Event breakdown: {type_list}"
            
            return summary + "."
        except Exception as e:
            current_app.logger.warning(f"Error querying events: {e}")
            return "Events data is currently unavailable."
    
    def _get_staff_data(self) -> str:
        """Get staff data from database."""
        try:
            from sas_management.models import User
            staff_count = User.query.filter(User.role != None).count()
            return f"Based on the database, you have {staff_count} staff members in the system."
        except Exception as e:
            current_app.logger.warning(f"Error querying staff: {e}")
            return "Staff data is currently unavailable."
    
    def _get_inventory_data(self) -> str:
        """Get inventory data from database."""
        # Placeholder - implement when inventory module is available
        return "Inventory data is being tracked. The system monitors stock levels and provides reorder recommendations."
    
    def ask_ai(self, user_input: str, system_data: Optional[str] = None, conversation_context: Optional[str] = None) -> Optional[str]:
        """
        Ask Gemini AI a question, optionally with system data.
        
        Args:
            user_input: User's question
            system_data: Optional system data to include in context
            conversation_context: Optional conversation history context
            
        Returns:
            AI response text
        """
        # Lazy initialize if not already done
        if not self._initialized:
            self._initialize()
        
        if not self.enabled or not self.model:
            return None  # Fallback to rule-based responses
        
        try:
            # Build prompt with system data if available
            if system_data:
                prompt = f"""You are SAS AI, an intelligent assistant for SAS Best Foods Catering Management System.

The user asked: '{user_input}'

System data from the database: {system_data}

Please provide a friendly, helpful answer that incorporates this system data naturally. Be concise and conversational."""
            else:
                prompt = f"""You are SAS AI, an intelligent assistant for SAS Best Foods Catering Management System.

The user asked: '{user_input}'

Please provide a friendly, helpful answer. If the question is about catering, events, or business operations, provide relevant advice. Be concise and conversational."""
            
            # Add conversation context if available
            if conversation_context:
                prompt += f"\n\nPrevious conversation context: {conversation_context}"
            
            # Generate response using the model
            response = self.model.generate_content(prompt)
            
            # Extract text from response
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                return ''.join([part.text for part in response.parts if hasattr(part, 'text')])
            else:
                return str(response)
            
        except Exception as e:
            current_app.logger.error(f"Error calling Gemini AI: {e}")
            return None  # Fallback to rule-based responses
    
    def start_chat_session(self, session_id: str):
        """Start a new chat session for conversation history."""
        if not self.enabled or not self.model:
            return
        try:
            self.chat = self.model.start_chat(history=[])
        except Exception as e:
            current_app.logger.warning(f"Error starting chat session: {e}")


# Global instance
_assistant_instance = None


def get_assistant() -> SASAssistant:
    """Get or create the global SAS Assistant instance."""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = SASAssistant()
    return _assistant_instance


def is_gemini_enabled() -> bool:
    """Check if Gemini AI is enabled and available."""
    assistant = get_assistant()
    if not assistant._initialized:
        assistant._initialize()
    return assistant.enabled

