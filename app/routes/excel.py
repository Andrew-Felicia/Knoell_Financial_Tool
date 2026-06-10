from flask import Blueprint, render_template

excel_bp = Blueprint("excel", __name__)


@excel_bp.route("/", methods=["GET", "POST"])
def index():
    return render_template("excel/index.html")