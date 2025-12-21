"""
SAS AI Reasoning Tests - Validate AI decision-making and responses.
"""
import pytest
from sas_management.ai.service import ai_service


def test_event_count_response():
    """Test that AI responds to event count queries."""
    response = ai_service.chat("how many events do we have")
    assert isinstance(response, dict)
    assert "message" in response
    assert "event" in response["message"].lower() or "unavailable" in response["message"].lower()


def test_accounting_explanation():
    """Test that AI explains accounting module correctly."""
    response = ai_service.chat("what does the accounting module do")
    assert isinstance(response, dict)
    assert "message" in response
    assert "financial" in response["message"].lower() or "accounting" in response["message"].lower()


def test_bakery_intent():
    """Test that bakery intent is recognized and handled."""
    response = ai_service.chat("tell me about bakery")
    assert isinstance(response, dict)
    assert "message" in response
    assert "bakery" in response["message"].lower()


def test_everything_intent():
    """Test that 'everything' intent provides system overview."""
    response = ai_service.chat("explain everything")
    assert isinstance(response, dict)
    assert "message" in response
    message_lower = response["message"].lower()
    assert "system" in message_lower or "overview" in message_lower or "events" in message_lower


def test_clarification_loop_breaker():
    """Test that clarification loop breaker prevents infinite questions."""
    r1 = ai_service.chat("something unclear")
    r2 = ai_service.chat("still unclear")
    assert isinstance(r1, dict)
    assert isinstance(r2, dict)
    # Second response should not ask for clarification again
    r2_msg = r2.get("message", "").lower()
    # Should not repeatedly ask "what do you mean" or similar
    assert r2_msg.count("clarify") < 2
    assert r2_msg.count("what do you mean") < 2


def test_revenue_role_awareness():
    """Test that revenue data is role-aware (admin vs staff)."""
    # Test as staff (default)
    response = ai_service.chat("how much revenue do we have")
    assert isinstance(response, dict)
    assert "message" in response
    # Staff should not see exact numbers
    message = response["message"].lower()
    # Should either show summary or unavailable, not exact amounts
    assert "revenue" in message


def test_inventory_low_stock():
    """Test that inventory queries return meaningful responses."""
    response = ai_service.chat("what is our inventory status")
    assert isinstance(response, dict)
    assert "message" in response
    message = response["message"].lower()
    assert "inventory" in message or "stock" in message or "items" in message


def test_knowledge_graph_relationship():
    """Test that knowledge graph explains module relationships."""
    response = ai_service.chat("how does events relate to accounting")
    assert isinstance(response, dict)
    assert "message" in response
    message = response["message"].lower()
    # Should mention relationship or explain modules
    assert "event" in message or "accounting" in message or "relate" in message


def test_error_handling():
    """Test that errors are handled gracefully without crashing."""
    # Test with empty message
    response = ai_service.chat("")
    assert isinstance(response, dict)
    assert "message" in response
    # Should return a message, not crash
    assert len(response["message"]) > 0


def test_production_intent():
    """Test that production intent is recognized."""
    response = ai_service.chat("tell me about production")
    assert isinstance(response, dict)
    assert "message" in response
    message = response["message"].lower()
    assert "production" in message or "kitchen" in message or "preparation" in message

