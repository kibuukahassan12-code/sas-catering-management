"""SAS AI Reasoning - Analyze user intent and decide response strategy."""
from typing import Dict, List, Tuple


QUESTION_TYPES = {
    "system": "system",
    "error": "error",
    "general": "general",
    "web_required": "web_required",
    "greeting": "greeting",
    "help": "help"
}


def classify_question(message: str, conversation_history: List[Dict] = None) -> Tuple[str, float]:
    """
    Classify user question to determine response strategy.
    
    Args:
        message: User's message
        conversation_history: Previous conversation messages
        
    Returns:
        Tuple of (question_type, confidence) where confidence is 0.0-1.0
    """
    message_lower = message.lower().strip()
    
    if not message_lower:
        return "greeting", 0.5
    
    # Greetings
    if any(keyword in message_lower for keyword in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"]):
        return "greeting", 0.95
    
    # Help requests
    if any(keyword in message_lower for keyword in ["help", "what can you", "how do", "what is", "explain", "tell me about"]):
        if any(keyword in message_lower for keyword in ["sas", "system", "event", "revenue", "staff", "inventory"]):
            return "system", 0.8
        return "help", 0.9
    
    # Error-related queries
    error_keywords = ["error", "bug", "issue", "problem", "broken", "not working", "fail", "crash"]
    if any(keyword in message_lower for keyword in error_keywords):
        return "error", 0.85
    
    # System queries - high confidence indicators
    system_keywords = [
        "event", "events", "how many", "count", "list", "show me", "display",
        "revenue", "profit", "sales", "income", "money earned", "financial",
        "staff", "employee", "workers", "team", "personnel",
        "inventory", "stock", "supplies", "items",
        "client", "customer", "customers",
        "this month", "last month", "quarter", "today", "week", "year",
        "report", "data", "statistics", "metrics"
    ]
    
    system_score = sum(1 for keyword in system_keywords if keyword in message_lower)
    if system_score >= 2:
        return "system", 0.9
    elif system_score >= 1:
        return "system", 0.7
    
    # Web-required queries (current events, specific facts, news)
    web_keywords = [
        "what is the", "who is", "when did", "where is",
        "latest", "news", "today's", "current", "recent",
        "definition", "meaning of", "explain what", "what does"
    ]
    
    if any(keyword in message_lower for keyword in web_keywords):
        # But not if it's about SAS system
        if not any(keyword in message_lower for keyword in ["sas", "our", "my", "this system"]):
            return "web_required", 0.8
    
    # General questions (default)
    if "?" in message or any(keyword in message_lower for keyword in ["what", "how", "why", "when", "where", "who"]):
        return "general", 0.6
    
    # Default to general
    return "general", 0.5


def determine_response_strategy(question_type: str, message: str, conversation_history: List[Dict] = None) -> Dict:
    """
    Determine the best strategy for responding to the question.
    
    Args:
        question_type: Classified question type
        message: User's message
        conversation_history: Previous conversation messages
        
    Returns:
        Dict with strategy information
    """
    strategy = {
        "type": question_type,
        "use_context": False,
        "use_retriever": False,
        "use_web": False,
        "response_style": "concise"
    }
    
    if question_type == "system":
        strategy["use_context"] = True
        strategy["response_style"] = "data_driven"
    elif question_type == "web_required":
        strategy["use_web"] = True
        strategy["use_retriever"] = True
        strategy["response_style"] = "informative"
    elif question_type == "general":
        # Try context first, then web if needed
        strategy["use_context"] = True
        strategy["use_retriever"] = True
        strategy["response_style"] = "conversational"
    elif question_type == "error":
        strategy["use_context"] = True
        strategy["response_style"] = "troubleshooting"
    elif question_type == "greeting":
        strategy["response_style"] = "friendly"
    elif question_type == "help":
        strategy["use_context"] = True
        strategy["response_style"] = "instructional"
    
    return strategy


def extract_entities(message: str) -> Dict[str, List[str]]:
    """
    Extract relevant entities from the message.
    
    Args:
        message: User's message
        
    Returns:
        Dict with entity types and values
    """
    message_lower = message.lower()
    entities = {
        "time_periods": [],
        "topics": [],
        "actions": []
    }
    
    # Time periods
    time_periods = ["today", "yesterday", "this week", "last week", "this month", 
                   "last month", "this quarter", "last quarter", "this year", "last year"]
    for period in time_periods:
        if period in message_lower:
            entities["time_periods"].append(period)
    
    # Topics
    topics = ["event", "events", "revenue", "profit", "staff", "inventory", 
             "client", "customers", "compliance", "safety"]
    for topic in topics:
        if topic in message_lower:
            entities["topics"].append(topic)
    
    # Actions
    actions = ["count", "list", "show", "display", "calculate", "analyze", 
              "explain", "help", "find"]
    for action in actions:
        if action in message_lower:
            entities["actions"].append(action)
    
    return entities

