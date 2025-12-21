"""
Event Service - Report Generation Functions
"""
from datetime import datetime
from sas_management.blueprints.event_service.models import (
    EventServiceEvent,
    EventServiceOrder,
    EventCosting,
    EventStaffAssignment,
    EventVendor,
)


def generate_event_summary_report(event_id):
    """Generate a summary report for an event."""
    event = EventServiceEvent.query.get_or_404(event_id)
    
    orders = EventServiceOrder.query.filter_by(event_id=event_id).all()
    costings = EventCosting.query.filter_by(event_id=event_id).all()
    staff = EventStaffAssignment.query.filter_by(event_id=event_id).all()
    vendors = EventVendor.query.filter_by(event_id=event_id).all()
    
    total_orders = sum(float(order.total_price) for order in orders)
    total_costs = sum(float(costing.total_cost) for costing in costings)
    total_vendor_costs = sum(float(vendor.cost) for vendor in vendors)
    
    report_data = {
        "event": event,
        "orders": orders,
        "costings": costings,
        "staff": staff,
        "vendors": vendors,
        "total_orders": total_orders,
        "total_costs": total_costs,
        "total_vendor_costs": total_vendor_costs,
        "net_total": total_orders - total_costs - total_vendor_costs,
    }
    
    return report_data


def generate_financial_report(event_id):
    """Generate a financial report for an event."""
    event = EventServiceEvent.query.get_or_404(event_id)
    
    orders = EventServiceOrder.query.filter_by(event_id=event_id).all()
    costings = EventCosting.query.filter_by(event_id=event_id).all()
    vendors = EventVendor.query.filter_by(event_id=event_id).all()
    
    revenue = sum(float(order.total_price) for order in orders)
    costs = sum(float(costing.total_cost) for costing in costings)
    vendor_costs = sum(float(vendor.cost) for vendor in vendors)
    
    report_data = {
        "event": event,
        "revenue": revenue,
        "costs": costs,
        "vendor_costs": vendor_costs,
        "total_costs": costs + vendor_costs,
        "profit": revenue - costs - vendor_costs,
        "profit_margin": ((revenue - costs - vendor_costs) / revenue * 100) if revenue > 0 else 0,
    }
    
    return report_data

