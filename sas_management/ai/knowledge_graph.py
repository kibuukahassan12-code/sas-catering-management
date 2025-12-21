"""
SAS AI Knowledge Graph - System module relationships and dependencies.
"""

KNOWLEDGE_GRAPH = {
    "system": {
        "depends_on": [],
        "describes": [
            "events", "accounting", "inventory", "hr", "production", "bakery",
            "pos", "crm", "vendors", "venues", "reports", "analytics", "automation"
        ],
    },
    "events": {
        "depends_on": ["venues", "staff", "inventory", "crm", "vendors"],
        "feeds": ["accounting", "production", "invoices", "quotes", "proposals", "timeline", "tasks"],
    },
    "production": {
        "depends_on": ["events", "inventory", "staff", "production_recipes"],
        "feeds": ["accounting", "kds", "food_safety"],
    },
    "bakery": {
        "depends_on": ["inventory", "production", "production_recipes"],
        "feeds": ["events", "accounting", "pos"],
    },
    "accounting": {
        "depends_on": ["events", "production", "bakery", "pos", "invoices", "payroll"],
        "feeds": ["reports", "analytics", "profitability", "cashbook"],
    },
    "inventory": {
        "depends_on": ["vendors"],
        "feeds": ["events", "production", "bakery", "pos"],
    },
    "venues": {
        "depends_on": [],
        "feeds": ["events", "floorplanner"],
    },
    "staff": {
        "depends_on": ["hr"],
        "feeds": ["events", "production", "mobile_staff", "payroll"],
    },
    "hr": {
        "depends_on": [],
        "feeds": ["staff", "accounting", "payroll", "university"],
    },
    "pos": {
        "depends_on": ["inventory", "menu_builder"],
        "feeds": ["accounting", "kds", "reports"],
    },
    "crm": {
        "depends_on": [],
        "feeds": ["events", "leads", "proposals", "quotes"],
    },
    "vendors": {
        "depends_on": [],
        "feeds": ["events", "inventory", "contracts"],
    },
    "reports": {
        "depends_on": ["accounting", "events", "production", "analytics"],
        "feeds": [],
    },
    "analytics": {
        "depends_on": ["accounting", "events", "production", "pos"],
        "feeds": ["reports", "bi"],
    },
    "invoices": {
        "depends_on": ["events", "quotes"],
        "feeds": ["accounting", "client_portal"],
    },
    "quotes": {
        "depends_on": ["events", "crm"],
        "feeds": ["invoices", "proposals"],
    },
    "proposals": {
        "depends_on": ["events", "crm"],
        "feeds": ["quotes", "events"],
    },
    "profitability": {
        "depends_on": ["accounting", "events", "production"],
        "feeds": ["reports", "analytics"],
    },
    "kds": {
        "depends_on": ["pos", "production"],
        "feeds": ["production"],
    },
    "menu_builder": {
        "depends_on": [],
        "feeds": ["events", "pos", "catering"],
    },
    "catering": {
        "depends_on": ["menu_builder", "production"],
        "feeds": ["events"],
    },
    "dispatch": {
        "depends_on": ["events", "production"],
        "feeds": ["events"],
    },
    "timeline": {
        "depends_on": ["events"],
        "feeds": ["events"],
    },
    "tasks": {
        "depends_on": ["events", "production"],
        "feeds": ["events", "production"],
    },
    "communication": {
        "depends_on": [],
        "feeds": ["events", "crm", "client_portal"],
    },
    "client_portal": {
        "depends_on": ["events", "invoices", "communication"],
        "feeds": ["events", "crm"],
    },
    "mobile_staff": {
        "depends_on": ["staff", "events", "production"],
        "feeds": ["events", "production"],
    },
    "food_safety": {
        "depends_on": ["production"],
        "feeds": ["incidents", "reports"],
    },
    "incidents": {
        "depends_on": ["events", "production", "food_safety"],
        "feeds": ["reports"],
    },
    "floorplanner": {
        "depends_on": ["venues"],
        "feeds": ["events"],
    },
    "university": {
        "depends_on": [],
        "feeds": ["hr", "staff"],
    },
    "payroll": {
        "depends_on": ["hr", "staff"],
        "feeds": ["accounting"],
    },
    "cashbook": {
        "depends_on": ["accounting"],
        "feeds": ["accounting", "reports"],
    },
    "automation": {
        "depends_on": [],
        "feeds": ["events", "production", "accounting"],
    },
    "integrations": {
        "depends_on": [],
        "feeds": ["accounting", "crm", "communication"],
    },
    "production_recipes": {
        "depends_on": ["inventory"],
        "feeds": ["production", "bakery"],
    },
    "hire": {
        "depends_on": ["inventory"],
        "feeds": ["events"],
    },
    "bi": {
        "depends_on": ["analytics", "reports"],
        "feeds": ["reports"],
    },
    "search": {
        "depends_on": [],
        "feeds": ["all_modules"],
    },
    "audit": {
        "depends_on": [],
        "feeds": ["all_modules"],
    },
    "branches": {
        "depends_on": [],
        "feeds": ["all_modules"],
    },
    "contracts": {
        "depends_on": ["vendors", "crm"],
        "feeds": ["events", "vendors"],
    },
    "leads": {
        "depends_on": [],
        "feeds": ["crm", "events"],
    },
}


def explain_relationship(module: str) -> str:
    """
    Explain how a module relates to other system modules.
    
    Args:
        module: Module name (e.g., "events", "accounting")
    
    Returns:
        Formatted explanation of module relationships, or None if module not found
    """
    node = KNOWLEDGE_GRAPH.get(module.lower())
    if not node:
        return None
    
    response = [f"**{module.capitalize()} module relationships:**\n"]
    
    if node.get("depends_on"):
        deps = ", ".join(node["depends_on"])
        response.append(f"• Depends on: {deps}")
    
    if node.get("feeds"):
        feeds = ", ".join(node["feeds"])
        response.append(f"• Feeds into: {feeds}")
    
    if node.get("describes"):
        describes = ", ".join(node["describes"])
        response.append(f"• Describes: {describes}")
    
    return "\n".join(response)


def find_related_modules(module: str) -> list:
    """
    Find all modules related to the given module.
    
    Args:
        module: Module name
    
    Returns:
        List of related module names
    """
    node = KNOWLEDGE_GRAPH.get(module.lower())
    if not node:
        return []
    
    related = set()
    if node.get("depends_on"):
        related.update(node["depends_on"])
    if node.get("feeds"):
        related.update(node["feeds"])
    if node.get("describes"):
        related.update(node["describes"])
    
    return list(related)

