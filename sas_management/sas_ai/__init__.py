"""SAS AI Module - ChatGPT-like conversational AI assistant."""
from flask import Blueprint

sas_ai_bp = Blueprint(
    "sas_ai", 
    __name__, 
    url_prefix="/sas-ai",
    template_folder="templates",
    static_folder="static"
)

# Import routes to register them
from . import routes

