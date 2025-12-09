"""
Shared helper functions for SAS Management System.
"""

from datetime import date, datetime
from decimal import Decimal

from flask import current_app, request
from flask_sqlalchemy import SQLAlchemy

from models import db


def get_decimal(value, fallback="0"):
    """Alias for _get_decimal."""
    return _get_decimal(value, fallback)

def _get_decimal(value, fallback="0"):
    """
    Safely convert a value to Decimal.
    
    Args:
        value: Value to convert (str, int, float, or None)
        fallback: Fallback value if conversion fails (default: "0")
    
    Returns:
        Decimal: Converted value or fallback
    """
    try:
        return Decimal(value or fallback)
    except (TypeError, ValueError):
        return Decimal(fallback)


def paginate_query(query, per_page=None):
    """Alias for _paginate_query."""
    return _paginate_query(query, per_page)

def _paginate_query(query, per_page=None):
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        per_page: Items per page (defaults to config DEFAULT_PAGE_SIZE or 10)
    
    Returns:
        Pagination object
    """
    page = request.args.get("page", 1, type=int)
    if per_page is None:
        per_page = current_app.config.get("DEFAULT_PAGE_SIZE", 10)
    return db.paginate(query, page=page, per_page=per_page, error_out=False)


def parse_date(raw_value, fallback=None):
    """Alias for _parse_date."""
    return _parse_date(raw_value, fallback)

def _parse_date(raw_value, fallback=None):
    """
    Parse a date string to date object.
    
    Args:
        raw_value: Date string in format "YYYY-MM-DD"
        fallback: Fallback value if parsing fails (default: None)
    
    Returns:
        date: Parsed date object or fallback
    """
    if raw_value is None:
        return fallback
    
    try:
        if isinstance(raw_value, date):
            return raw_value
        if isinstance(raw_value, datetime):
            return raw_value.date()
        return datetime.strptime(str(raw_value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return fallback


def allowed_file(filename):
    """
    Check if file extension is allowed.
    
    Args:
        filename: Name of the file to check
    
    Returns:
        bool: True if file extension is allowed
    """
    if not filename or '.' not in filename:
        return False
    
    allowed_extensions = current_app.config.get(
        'ALLOWED_EXTENSIONS',
        {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'csv'}
    )
    return filename.rsplit('.', 1)[1].lower() in allowed_extensions

