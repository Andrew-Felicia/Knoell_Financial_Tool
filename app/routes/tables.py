from flask import Blueprint, render_template

tables_bp = Blueprint("tables", __name__)


@tables_bp.route("/")
def index():
    return render_template("tables/index.html")