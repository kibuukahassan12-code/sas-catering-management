"""SAS AI Engine - Main orchestrator for AI responses."""
from typing import Dict, List, Optional
from flask import current_app
from .context import get_system_prompt
from .reasoning import classify_question, determine_response_strategy, extract_entities
from .retriever import retrieve_answer, search_system_context
from .memory import get_conversation
from .gemini_integration import get_assistant, is_gemini_enabled


def generate_reply(session_id: str, user_message: str) -> Dict[str, str]:
    """
    Main function to generate AI reply.
    
    Args:
        session_id: Session identifier
        user_message: User's message
        
    Returns:
        Dict with 'reply', 'intent', 'source', 'metadata'
    """
    try:
        # Load conversation memory
        conversation_history = get_conversation(session_id)
        
        # Step 1: Reasoning - Classify question and determine strategy
        question_type, confidence = classify_question(user_message, conversation_history)
        strategy = determine_response_strategy(question_type, user_message, conversation_history)
        entities = extract_entities(user_message)
        
        # Step 2: Generate response based on strategy
        reply = _generate_response(
            user_message=user_message,
            question_type=question_type,
            strategy=strategy,
            entities=entities,
            conversation_history=conversation_history
        )
        
        # Step 3: Synthesize final answer
        final_reply = _synthesize_response(reply, strategy, user_message)
        
        # Prepare metadata
        metadata = {
            "intent": question_type,
            "confidence": confidence,
            "strategy": strategy,
            "entities": entities,
            "source": "system_context" if strategy.get("use_context") else "general_knowledge"
        }
        
        return {
            "reply": final_reply,
            "intent": question_type,
            "source": metadata["source"],
            "metadata": metadata
        }
        
    except Exception as e:
        current_app.logger.error(f"Error generating reply: {e}", exc_info=True)
        return {
            "reply": "I encountered an error processing your request. Please try again or rephrase your question.",
            "intent": "error",
            "source": "general_knowledge",
            "metadata": {"error": str(e)}
        }


def _generate_response(
    user_message: str,
    question_type: str,
    strategy: Dict,
    entities: Dict,
    conversation_history: List[Dict]
) -> str:
    """Generate response based on strategy."""
    
    # Handle greetings
    if question_type == "greeting":
        return _handle_greeting(conversation_history)
    
    # Handle help requests
    if question_type == "help":
        return _generate_help_response(entities)
    
    # Handle error-related queries
    if question_type == "error":
        return _handle_error_query(user_message)
    
    # System queries - query actual system data
    if question_type == "system" and strategy.get("use_context"):
        return _handle_system_query(user_message, entities, conversation_history)
    
    # Try Gemini AI for general questions if available
    if is_gemini_enabled():
        assistant = get_assistant()
        gemini_response = assistant.ask_ai(user_message)
        if gemini_response:
            return gemini_response
    
    # Try context first for general questions
    if strategy.get("use_context"):
        context_answer = search_system_context(user_message)
        if context_answer:
            return context_answer
    
    # Use retriever for web-required or general questions
    if strategy.get("use_retriever") or strategy.get("use_web"):
        retrieved = retrieve_answer(user_message, use_web=strategy.get("use_web", False))
        if retrieved:
            return retrieved
    
    # Default response
    return _generate_default_response(user_message, question_type)


def _handle_greeting(conversation_history: List[Dict]) -> str:
    """Handle greeting messages."""
    if not conversation_history or len(conversation_history) <= 2:
        return """Hello! I'm SAS AI, your intelligent assistant for SAS Best Foods Catering Management System.

I can help you with:
📅 **Events** - Query events, counts, status, details
💰 **Revenue & Finance** - Analyze revenue, profit, financial data
👥 **Staff** - Staff information, scheduling, assignments
📦 **Inventory** - Stock levels, supplies, predictions
👤 **Clients** - Customer data and information
⚠️ **Compliance** - Food safety and regulatory compliance
📊 **Reports** - Business metrics and analytics

What would you like to know?"""
    else:
        return "Hello again! How can I help you today?"


def _generate_help_response(entities: Dict) -> str:
    """Generate help response based on entities."""
    topics = entities.get("topics", [])
    
    if "event" in topics:
        return """I can help you with events! Try asking:
• "How many events this month?"
• "Show upcoming events"
• "Event details for [event name]"
• "Help me plan an event"
"""
    elif "revenue" in topics or "profit" in topics:
        return """I can help you with financial information! Try asking:
• "What's this month's revenue?"
• "Show profit analysis"
• "Revenue this quarter"
• "Profit margins"
"""
    elif "staff" in topics:
        return """I can help you with staff information! Try asking:
• "How many staff members?"
• "Staff assignments"
• "Staff scheduling"
"""
    else:
        return _generate_help_response({})


def _handle_error_query(message: str) -> str:
    """Handle error-related queries."""
    return """I can help troubleshoot issues. Common solutions:

1. **System Errors**: Check logs, verify data integrity, restart services if needed
2. **Data Issues**: Verify input data, check database connections
3. **Feature Not Working**: Ensure feature is enabled in settings
4. **Performance Issues**: Check system resources, database queries

For specific errors, please describe:
- What you were trying to do
- What error message you saw
- When it occurred

I can then provide more targeted assistance."""


def _handle_system_query(message: str, entities: Dict, conversation_history: List[Dict]) -> str:
    """Handle system data queries with actual database queries, enhanced with Gemini AI."""
    try:
        # Try to use Gemini AI if available
        if is_gemini_enabled():
            assistant = get_assistant()
            system_data = assistant.get_system_data(message, entities, conversation_history)
            
            if system_data:
                # Use Gemini to make the response natural
                gemini_response = assistant.ask_ai(message, system_data=system_data)
                if gemini_response:
                    return gemini_response
        
        # Fallback to rule-based responses
        message_lower = message.lower()
        topics = entities.get("topics", [])
        time_periods = entities.get("time_periods", [])
        
        # Events queries
        if "event" in topics or "event" in message_lower:
            return _query_events(time_periods)
        
        # Revenue queries
        if "revenue" in topics or "revenue" in message_lower or "profit" in topics:
            return _query_revenue(time_periods)
        
        # Staff queries
        if "staff" in topics or "employee" in message_lower:
            return _query_staff()
        
        # Inventory queries
        if "inventory" in topics or "stock" in message_lower:
            return _query_inventory()
        
        # Default system response
        return "I can help you query system data. Try asking about events, revenue, staff, or inventory."
        
    except Exception as e:
        current_app.logger.warning(f"Error in system query: {e}")
        return "I'm having trouble accessing system data right now. Please try again in a moment."


def _query_events(time_periods: List[str]) -> str:
    """Query events data."""
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
        total = ServiceEvent.query.count()
        
        return f"""**Events Overview:**
• Total events: {total}
• Events this month: {events_this_month}
• Upcoming events: {upcoming}

Would you like details on a specific event or help planning a new one?"""
    except Exception:
        return "I can help you query events data. Try asking: 'How many events this month?' or 'Show upcoming events'"


def _query_revenue(time_periods: List[str]) -> str:
    """Query revenue data."""
    try:
        # Safe import - use Quotation instead of Quote
        try:
            from sas_management.models import Quotation
            Quote = Quotation  # Alias for backward compatibility
        except ImportError:
            Quote = None
        
        if Quote is None:
            return "I can help you query revenue data. The revenue module may not be available right now."
        
        from datetime import datetime
        
        today = datetime.utcnow()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        quotes = Quote.query.filter(
            Quote.status == "Accepted",
            Quote.created_at >= month_start
        ).all()
        
        if not quotes:
            return "No accepted quotes found for this month. Would you like to check a different time period?"
        
        total = sum(float(quote.total_amount or 0) for quote in quotes)
        
        return f"""**Revenue Overview (This Month):**
• Total revenue: {total:,.0f} UGX
• From {len(quotes)} accepted quotes

Would you like profit analysis or details on specific quotes?"""
    except Exception:
        return "I can help you analyze revenue. Try asking about monthly revenue or profit margins."


def _query_staff() -> str:
    """Query staff data."""
    try:
        from sas_management.models import User
        staff_count = User.query.filter(User.role != None).count()
        return f"""**Staff Overview:**
• Total staff members: {staff_count}

I can help you with staff scheduling, assignments, or planning for events."""
    except Exception:
        return "I can help you with staff information. Try asking about staff count or scheduling."


def _query_inventory() -> str:
    """Query inventory data."""
    return """**Inventory Management:**
I can help you with inventory queries. The system tracks:
• Stock levels
• Ingredient availability
• Shortage predictions
• Reorder recommendations

Try asking: 'Show inventory levels' or 'Inventory shortages'"""


def _generate_default_response(message: str, question_type: str) -> str:
    """Generate default response when no specific handler matches."""
    if "?" in message or any(word in message.lower() for word in ["what", "how", "why", "when", "where", "who"]):
        return f"I understand you're asking about '{message}'. I can help you with:\n\n• SAS system data (events, revenue, staff, inventory)\n• General business questions\n• Event planning and catering advice\n\nCould you rephrase your question or ask about a specific topic?"
    
    return "I'm here to help! I can assist with system queries, general questions, or business advice. What would you like to know?"


def _synthesize_response(raw_response: str, strategy: Dict, original_message: str) -> str:
    """Synthesize and polish the final response."""
    response_style = strategy.get("response_style", "concise")
    
    # Clean up response
    response = raw_response.strip()
    
    # Add helpful context if needed
    if response_style == "conversational" and len(response) < 100:
        response += "\n\nIs there anything else you'd like to know?"
    
    return response
