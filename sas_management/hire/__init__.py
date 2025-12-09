from flask import Blueprint

hire = Blueprint("hire", __name__)

from . import routes

