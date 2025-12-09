"""Profitability Analysis Blueprint - Event profitability reports and analysis."""
from flask import Blueprint

profitability_bp = Blueprint(
    "profitability",
    __name__,
    template_folder="templates",
    url_prefix="/profitability"
)

from . import routes

