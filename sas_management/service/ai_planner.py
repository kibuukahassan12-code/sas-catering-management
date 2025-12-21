"""
AI Event Planning Assistant

Rule-based planning service that analyzes past ServiceEvent records
to generate suggestions for new events. This is assistive only - all
suggestions must be manually reviewed and accepted by staff.

NO external API calls - uses heuristic analysis of historical data.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from flask import current_app

from sas_management.service.models import (
    ServiceEvent,
    ServiceStaffAssignment,
    ServiceEventItem,
    ServiceChecklistItem,
)
from sas_management.service.utils import calculate_event_total_cost


def generate_plan(
    event_type: Optional[str] = None,
    guest_count: Optional[int] = None,
    event_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Generate AI-powered planning suggestions for a service event.
    
    Args:
        event_type: Type of event (Wedding, Corporate, etc.)
        guest_count: Expected number of guests
        event_date: Date of the event
        
    Returns:
        Dictionary with:
        - staff_suggestions: List of role suggestions with counts
        - checklist: List of suggested checklist items
        - estimated_cost: Estimated total cost (float)
        - confidence_note: Human-readable confidence message
        
    This function is defensive - returns empty suggestions if data is insufficient.
    """
    try:
        # Log usage
        current_app.logger.info(
            f"AI planner used for event type: {event_type}, "
            f"guests: {guest_count}, date: {event_date}"
        )
        
        # Query similar past events
        similar_events = _find_similar_events(
            event_type=event_type,
            guest_count=guest_count,
            event_date=event_date,
        )
        
        if not similar_events:
            return {
                "staff_suggestions": [],
                "checklist": [],
                "estimated_cost": 0.0,
                "confidence_note": "No similar past events found. Suggestions disabled.",
            }
        
        # Generate suggestions from historical data
        staff_suggestions = _suggest_staff_roles(similar_events, guest_count)
        checklist = _suggest_checklist_items(similar_events, event_type)
        estimated_cost = _estimate_cost(similar_events, guest_count)
        
        # Calculate confidence
        confidence_note = _generate_confidence_note(
            len(similar_events),
            event_type,
            guest_count,
        )
        
        return {
            "staff_suggestions": staff_suggestions,
            "checklist": checklist,
            "estimated_cost": float(estimated_cost),
            "confidence_note": confidence_note,
        }
        
    except Exception as e:
        # Log as warning, not error - AI is optional
        current_app.logger.warning(f"AI planner error: {e}")
        return {
            "staff_suggestions": [],
            "checklist": [],
            "estimated_cost": 0.0,
            "confidence_note": f"Planning suggestions unavailable: {str(e)}",
        }


def _find_similar_events(
    event_type: Optional[str] = None,
    guest_count: Optional[int] = None,
    event_date: Optional[date] = None,
    limit: int = 20,
) -> List[ServiceEvent]:
    """
    Find past events similar to the given parameters.
    
    Priority:
    1. Same event_type
    2. Similar guest_count (within 20% range)
    3. Completed events (more reliable data)
    """
    try:
        query = ServiceEvent.query.filter(
            ServiceEvent.status == "Completed"  # Only use completed events for reliability
        )
        
        # Filter by event_type if provided
        if event_type:
            query = query.filter(ServiceEvent.event_type == event_type)
        
        # Filter by guest_count range if provided
        if guest_count:
            # Allow 20% variance in guest count
            lower_bound = int(guest_count * 0.8)
            upper_bound = int(guest_count * 1.2)
            query = query.filter(
                ServiceEvent.guest_count >= lower_bound,
                ServiceEvent.guest_count <= upper_bound,
            )
        
        # Order by most recent first, then by guest_count similarity
        events = query.order_by(
            ServiceEvent.event_date.desc(),
            ServiceEvent.created_at.desc(),
        ).limit(limit).all()
        
        return events or []
        
    except Exception as e:
        current_app.logger.warning(f"Error finding similar events: {e}")
        return []


def _suggest_staff_roles(
    similar_events: List[ServiceEvent],
    guest_count: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Analyze staff assignments from similar events to suggest roles.
    
    Returns list of role suggestions with counts.
    """
    try:
        if not similar_events:
            return []
        
        # Collect all staff assignments from similar events
        role_counts = {}
        role_shift_counts = {}
        
        for event in similar_events:
            try:
                assignments = ServiceStaffAssignment.query.filter_by(
                    service_event_id=event.id
                ).all()
                
                for assignment in assignments:
                    role = assignment.role or "General Staff"
                    shift = assignment.shift or "Full Day"
                    
                    # Count roles
                    if role not in role_counts:
                        role_counts[role] = []
                    role_counts[role].append(1)
                    
                    # Track shift patterns
                    key = f"{role}:{shift}"
                    if key not in role_shift_counts:
                        role_shift_counts[key] = 0
                    role_shift_counts[key] += 1
                    
            except Exception:
                continue
        
        # Calculate average counts per role
        suggestions = []
        for role, counts in role_counts.items():
            avg_count = sum(counts) / len(similar_events)
            # Round up to nearest integer
            suggested_count = int(avg_count) + (1 if avg_count % 1 >= 0.5 else 0)
            
            # Adjust based on guest count if provided
            if guest_count and similar_events:
                # Get average guest count from similar events
                avg_guests = sum(
                    e.guest_count or 0 for e in similar_events if e.guest_count
                ) / len([e for e in similar_events if e.guest_count])
                
                if avg_guests > 0:
                    # Scale proportionally
                    scale_factor = guest_count / avg_guests
                    suggested_count = max(1, int(suggested_count * scale_factor))
            
            suggestions.append({
                "role": role,
                "suggested_count": max(1, suggested_count),  # At least 1
                "confidence": "medium" if len(counts) >= 3 else "low",
            })
        
        # Sort by suggested count (descending)
        suggestions.sort(key=lambda x: x["suggested_count"], reverse=True)
        
        # If no historical data, provide default suggestions based on guest count
        if not suggestions and guest_count:
            suggestions = _default_staff_suggestions(guest_count)
        
        return suggestions
        
    except Exception as e:
        current_app.logger.warning(f"Error suggesting staff roles: {e}")
        return []


def _default_staff_suggestions(guest_count: int) -> List[Dict[str, Any]]:
    """
    Provide default staff suggestions when no historical data exists.
    Uses rule-based heuristics.
    """
    suggestions = []
    
    # Base staffing ratios (heuristic)
    if guest_count <= 50:
        suggestions = [
            {"role": "Manager", "suggested_count": 1, "confidence": "low"},
            {"role": "Server", "suggested_count": 2, "confidence": "low"},
            {"role": "Chef", "suggested_count": 1, "confidence": "low"},
        ]
    elif guest_count <= 100:
        suggestions = [
            {"role": "Manager", "suggested_count": 1, "confidence": "low"},
            {"role": "Server", "suggested_count": 4, "confidence": "low"},
            {"role": "Chef", "suggested_count": 2, "confidence": "low"},
        ]
    elif guest_count <= 200:
        suggestions = [
            {"role": "Manager", "suggested_count": 2, "confidence": "low"},
            {"role": "Server", "suggested_count": 6, "confidence": "low"},
            {"role": "Chef", "suggested_count": 3, "confidence": "low"},
        ]
    else:
        # Large events
        base_servers = max(6, guest_count // 30)
        suggestions = [
            {"role": "Manager", "suggested_count": 2, "confidence": "low"},
            {"role": "Server", "suggested_count": base_servers, "confidence": "low"},
            {"role": "Chef", "suggested_count": max(3, guest_count // 60), "confidence": "low"},
        ]
    
    return suggestions


def _suggest_checklist_items(
    similar_events: List[ServiceEvent],
    event_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Analyze checklist items from similar events to suggest tasks.
    
    Returns list of suggested checklist items with stages.
    """
    try:
        if not similar_events:
            return _default_checklist_items(event_type)
        
        # Collect checklist items from similar events
        checklist_frequency = {}
        
        for event in similar_events:
            try:
                items = ServiceChecklistItem.query.filter_by(
                    service_event_id=event.id
                ).all()
                
                for item in items:
                    # Create a normalized key (stage + description)
                    key = f"{item.stage or 'General'}:{item.description.strip()}"
                    
                    if key not in checklist_frequency:
                        checklist_frequency[key] = {
                            "description": item.description,
                            "stage": item.stage or "General",
                            "count": 0,
                        }
                    checklist_frequency[key]["count"] += 1
                    
            except Exception:
                continue
        
        # Convert to suggestions (items that appear in at least 2 events)
        suggestions = []
        for key, data in checklist_frequency.items():
            if data["count"] >= 2:  # Appeared in at least 2 similar events
                suggestions.append({
                    "description": data["description"],
                    "stage": data["stage"],
                    "confidence": "high" if data["count"] >= 5 else "medium",
                })
        
        # Sort by stage, then by frequency
        stage_order = {"Preparation": 1, "Setup": 2, "Service": 3, "Teardown": 4}
        suggestions.sort(
            key=lambda x: (
                stage_order.get(x["stage"], 99),
                -checklist_frequency.get(f"{x['stage']}:{x['description']}", {}).get("count", 0),
            )
        )
        
        # If no good matches, use defaults
        if not suggestions:
            suggestions = _default_checklist_items(event_type)
        
        return suggestions
        
    except Exception as e:
        current_app.logger.warning(f"Error suggesting checklist items: {e}")
        return _default_checklist_items(event_type)


def _default_checklist_items(event_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Provide default checklist items when no historical data exists.
    """
    base_items = [
        {"description": "Confirm event details with client", "stage": "Preparation", "confidence": "low"},
        {"description": "Prepare equipment and supplies list", "stage": "Preparation", "confidence": "low"},
        {"description": "Assign staff roles and shifts", "stage": "Preparation", "confidence": "low"},
        {"description": "Transport equipment to venue", "stage": "Setup", "confidence": "low"},
        {"description": "Set up service stations", "stage": "Setup", "confidence": "low"},
        {"description": "Final equipment check", "stage": "Setup", "confidence": "low"},
        {"description": "Begin service operations", "stage": "Service", "confidence": "low"},
        {"description": "Monitor service quality", "stage": "Service", "confidence": "low"},
        {"description": "Pack equipment and supplies", "stage": "Teardown", "confidence": "low"},
        {"description": "Return equipment to storage", "stage": "Teardown", "confidence": "low"},
    ]
    
    # Add event-type specific items
    if event_type:
        type_specific = {
            "Wedding": [
                {"description": "Coordinate with wedding planner", "stage": "Preparation", "confidence": "low"},
                {"description": "Prepare ceremonial setup", "stage": "Setup", "confidence": "low"},
            ],
            "Corporate": [
                {"description": "Confirm corporate branding requirements", "stage": "Preparation", "confidence": "low"},
                {"description": "Set up presentation area", "stage": "Setup", "confidence": "low"},
            ],
        }
        if event_type in type_specific:
            base_items.extend(type_specific[event_type])
    
    return base_items


def _estimate_cost(
    similar_events: List[ServiceEvent],
    guest_count: Optional[int] = None,
) -> Decimal:
    """
    Estimate total cost based on similar past events.
    
    Uses average cost per guest from historical data.
    """
    try:
        if not similar_events:
            return Decimal("0.00")
        
        # Calculate total costs for similar events
        costs = []
        guest_counts = []
        
        for event in similar_events:
            try:
                total_cost = calculate_event_total_cost(event.id)
                if total_cost and total_cost > 0:
                    costs.append(float(total_cost))
                    if event.guest_count:
                        guest_counts.append(event.guest_count)
            except Exception:
                continue
        
        if not costs:
            return Decimal("0.00")
        
        # Calculate average cost
        avg_cost = sum(costs) / len(costs)
        
        # If we have guest count data, calculate cost per guest
        if guest_count and guest_counts:
            avg_guests = sum(guest_counts) / len(guest_counts)
            if avg_guests > 0:
                cost_per_guest = avg_cost / avg_guests
                estimated = cost_per_guest * guest_count
                return Decimal(str(estimated))
        
        # Otherwise, return average cost
        return Decimal(str(avg_cost))
        
    except Exception as e:
        current_app.logger.warning(f"Error estimating cost: {e}")
        return Decimal("0.00")


def _generate_confidence_note(
    num_similar_events: int,
    event_type: Optional[str],
    guest_count: Optional[int],
) -> str:
    """
    Generate a human-readable confidence note.
    """
    if num_similar_events == 0:
        return "No similar past events found. Suggestions are based on general heuristics."
    elif num_similar_events < 3:
        return f"Based on {num_similar_events} similar past event(s). Suggestions may vary."
    elif num_similar_events < 10:
        return f"Based on {num_similar_events} similar past events. Suggestions are reasonably reliable."
    else:
        return f"Based on {num_similar_events} similar past events. High confidence in suggestions."


# ============================================================================
# FUTURE AI INTEGRATION HOOK
# ============================================================================
# Placeholder for future AI/ML integration:
#
# def _enhance_with_ai(suggestions: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Future: Enhance suggestions using external AI service.
#     This would call an AI API to refine suggestions based on:
#     - Natural language processing of event notes
#     - Machine learning models trained on past events
#     - External event planning knowledge bases
#     """
#     # Example structure:
#     # - Call AI API with event context
#     # - Merge AI suggestions with rule-based suggestions
#     # - Return enhanced suggestions
#     pass

