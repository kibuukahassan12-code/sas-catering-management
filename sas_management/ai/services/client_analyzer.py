"""
Client Analyzer AI Service

Analyze client behavior and identify opportunities.
"""
from flask import current_app
from decimal import Decimal
from sas_management.ai.registry import is_feature_enabled


def analyze_client(client_id: int = None):
    """
    Analyze a specific client's behavior and value.
    
    Args:
        client_id: Client ID to analyze
        
    Returns:
        Dictionary with client analysis
    """
    # Check if feature is enabled
    if not is_feature_enabled("client_analyzer"):
        return {
            "success": False,
            "error": "Client Analyzer feature is disabled",
            "lifetime_value": None,
            "preferences": [],
        }
    
    try:
        current_app.logger.info(f"Client Analyzer accessed for client: {client_id}")
        
        lifetime_value = None
        preferences = []
        upsell_opportunities = []
        risk_factors = []
        
        try:
            from sas_management.models import Client, Quote, Invoice, Event
            
            if client_id:
                client = Client.query.get(client_id)
                if client:
                    # Calculate lifetime value
                    total_value = Decimal("0")
                    
                    # From quotes
                    quotes = Quote.query.filter_by(client_id=client_id, status="Accepted").all()
                    for quote in quotes:
                        if quote.total_amount:
                            total_value += Decimal(str(quote.total_amount))
                    
                    # From invoices
                    invoices = Invoice.query.filter_by(client_id=client_id, status="Paid").all() if hasattr(Invoice, "client_id") else []
                    for invoice in invoices:
                        if hasattr(invoice, "amount_paid") and invoice.amount_paid:
                            total_value += Decimal(str(invoice.amount_paid))
                    
                    lifetime_value = float(total_value)
                    
                    # Analyze preferences
                    event_types = {}
                    events = Event.query.filter_by(client_id=client_id).all()
                    for event in events:
                        if event.event_type:
                            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
                    
                    if event_types:
                        most_common = max(event_types.items(), key=lambda x: x[1])
                        preferences.append({
                            "type": "event_preference",
                            "value": most_common[0],
                            "frequency": most_common[1],
                        })
                    
                    # Upsell opportunities
                    if len(events) > 0 and lifetime_value > 0:
                        avg_event_value = lifetime_value / len(events)
                        if avg_event_value < 5000000:  # Threshold in UGX
                            upsell_opportunities.append({
                                "type": "premium_services",
                                "message": "Client may benefit from premium service packages",
                                "potential_value": avg_event_value * 1.5,
                            })
        
        except Exception as e:
            current_app.logger.warning(f"Error analyzing client: {e}")
        
        return {
            "success": True,
            "lifetime_value": lifetime_value,
            "preferences": preferences,
            "upsell_opportunities": upsell_opportunities,
            "risk_factors": risk_factors,
            "note": f"Analysis based on {len(quotes) if 'quotes' in locals() else 0} quotes and {len(events) if 'events' in locals() else 0} events" if client_id else "No client specified",
        }
        
    except Exception as e:
        current_app.logger.error(f"Client Analyzer error: {e}")
        return {
            "success": False,
            "error": str(e),
            "lifetime_value": None,
            "preferences": [],
        }

