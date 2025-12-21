from flask import Blueprint

hire = Blueprint("hire", __name__, template_folder="templates")

from . import routes

