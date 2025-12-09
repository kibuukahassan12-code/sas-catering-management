from . import hire
from flask import render_template


@hire.route("/")
def index():
    return render_template("hire/index.html")


@hire.route("/orders")
def orders_list():
    return render_template("hire/orders_list.html")

