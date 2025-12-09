"""Procurement service."""
from flask import current_app

def create_rfq(items, supplier_ids=None):
    """Create Request for Quotation."""
    try:
        from models import Supplier, SupplierQuote, db
        quotes = []
        
        suppliers = Supplier.query.filter_by(is_active=True).all()
        if supplier_ids:
            suppliers = [s for s in suppliers if s.id in supplier_ids]
        
        for supplier in suppliers:
            # TODO: Calculate quote from items
            quote = SupplierQuote(
                supplier_id=supplier.id,
                items_json=str(items),
                price_total=0,  # TODO: Calculate
                status='pending'
            )
            db.session.add(quote)
            quotes.append(quote)
        
        db.session.commit()
        return {'success': True, 'quotes': quotes}
    except Exception as e:
        if current_app:
            current_app.logger.exception(f"Error creating RFQ: {e}")
        return {'success': False, 'error': str(e)}

