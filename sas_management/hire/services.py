from flask import current_app
from math import ceil


def paginate_query(query, page=1, per_page=20):
    """
    Wrapper that returns a Flask-SQLAlchemy-style pagination object.
    If the query supports .paginate, use it. Otherwise emulate a simple paginator.
    """
    try:
        # Use Flask-SQLAlchemy db.paginate() for SQLAlchemy 2.x compatibility
        from flask import current_app
        from sas_management.models import db
        return db.paginate(query, page=page, per_page=per_page, error_out=False)
    except Exception:
        # Fallback for plain SQLAlchemy Query
        page = max(int(page or 1), 1)
        per_page = max(int(per_page or 20), 1)
        total = query.count()
        items = query.limit(per_page).offset((page - 1) * per_page).all()
        
        class SimplePagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = int(ceil(total / float(per_page))) if per_page else 0
                self.has_prev = page > 1
                self.has_next = page < self.pages
            
            def iter_pages(self):
                return range(1, self.pages + 1)
        
        return SimplePagination(items, page, per_page, total)


def serialize_item(item):
    """
    Convert InventoryItem-like object into JSON-serializable dict.
    Adjust keys as needed if your model uses different field names.
    """
    stock_count = int(getattr(item, "stock_count", getattr(item, "quantity_available", getattr(item, "qty_available", 0)) or 0))
    rental_price = float(getattr(item, "rental_price", getattr(item, "daily_price", getattr(item, "price", 0)) or 0))
    
    return {
        "id": getattr(item, "id", None),
        "name": getattr(item, "name", "") or getattr(item, "title", ""),
        "category": getattr(item, "category", "") or getattr(item, "type", ""),
        "stock_count": stock_count,
        "qty_available": stock_count,
        "rental_price": rental_price,
        "daily_price": rental_price,
        "sku": getattr(item, "sku", "") or "",
        "status": getattr(item, "status", "Available"),
        "maintenance_status": getattr(item, "maintenance_status", getattr(item, "status", "ok")),
        "notes": getattr(item, "notes", getattr(item, "description", "")) or ""
    }
