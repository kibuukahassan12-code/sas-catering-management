"""SAS AI Retriever - Search and retrieve information from system context and web."""
from typing import Dict, List, Optional
from flask import current_app
import re


def search_system_context(query: str, context_data: Dict = None) -> Optional[str]:
    """
    Search SAS system context for relevant information.
    
    Args:
        query: Search query
        context_data: Optional context data dictionary
        
    Returns:
        Relevant context information or None
    """
    query_lower = query.lower()
    
    # System knowledge snippets
    system_knowledge = {
        "events": "SAS manages events including weddings, corporate events, and catering services. Events have dates, client information, guest counts, and menu items.",
        "revenue": "Revenue is tracked through accepted quotes and invoices. You can query monthly revenue, profit margins, and financial reports.",
        "staff": "Staff information includes employee roles, assignments, and scheduling. You can query staff count, roles, and assignments.",
        "inventory": "Inventory includes ingredients, supplies, and stock levels. The system tracks inventory levels and can predict shortages.",
        "clients": "Client data includes customer information, event history, and preferences. You can query client lists and details.",
        "compliance": "SAS follows food safety guidelines and compliance requirements. Safety logs and compliance reports are maintained.",
    }
    
    # Search for matching topics
    for topic, info in system_knowledge.items():
        if topic in query_lower:
            return info
    
    return None


def search_web_safe(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Search the web safely without requiring API keys.
    Uses a simple approach that can be enhanced later.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of result dicts with 'title', 'snippet', 'url'
    """
    # For now, return structured responses based on common queries
    # In production, you could integrate DuckDuckGo API or similar free service
    # This is a safe fallback that doesn't require external APIs
    
    query_lower = query.lower()
    
    # Provide helpful responses for common queries without external API
    common_responses = {
        "food safety": {
            "title": "Food Safety Guidelines",
            "snippet": "Food safety involves proper handling, storage, and preparation of food to prevent contamination. Key practices include: maintaining proper temperatures, avoiding cross-contamination, proper hand hygiene, and following HACCP principles.",
            "url": "https://www.foodsafety.gov"
        },
        "catering": {
            "title": "Catering Best Practices",
            "snippet": "Successful catering requires careful planning, quality ingredients, professional staff, and attention to detail. Key factors include menu planning, portion estimation, logistics coordination, and customer service.",
            "url": "https://www.cateringindustry.com"
        },
        "event planning": {
            "title": "Event Planning Guide",
            "snippet": "Effective event planning involves: setting objectives, budget planning, venue selection, vendor coordination, timeline management, and post-event evaluation. Communication and attention to detail are critical.",
            "url": "https://www.eventplanning.com"
        }
    }
    
    results = []
    for key, response in common_responses.items():
        if key in query_lower:
            results.append(response)
            if len(results) >= max_results:
                break
    
    # If no specific match, provide a generic helpful response
    if not results:
        return [{
            "title": f"Information about: {query}",
            "snippet": f"I can help you with information about '{query}'. For specific SAS system data, try asking about events, revenue, staff, or inventory. For general questions, I'll do my best to help based on my knowledge.",
            "url": ""
        }]
    
    return results


def summarize_retrieved_info(results: List[Dict[str, str]], query: str) -> str:
    """
    Summarize retrieved information into a coherent response.
    
    Args:
        results: List of retrieved result dicts
        query: Original query
        
    Returns:
        Summarized response text
    """
    if not results:
        return f"I don't have specific information about '{query}' in my knowledge base. Would you like me to help you with SAS system data instead?"
    
    summary_parts = []
    summary_parts.append("Based on available information:\n")
    
    for i, result in enumerate(results[:3], 1):
        snippet = result.get("snippet", "")
        if snippet:
            # Clean up snippet
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            summary_parts.append(f"{snippet}")
    
    return "\n\n".join(summary_parts)


def retrieve_answer(query: str, use_web: bool = False) -> str:
    """
    Main retrieval function that searches context and optionally web.
    
    Args:
        query: User's question
        use_web: Whether to attempt web search
        
    Returns:
        Retrieved answer text
    """
    # First, try system context
    system_info = search_system_context(query)
    if system_info:
        return system_info
    
    # If web search requested and system context didn't help
    if use_web:
        web_results = search_web_safe(query)
        if web_results:
            return summarize_retrieved_info(web_results, query)
    
    return None

