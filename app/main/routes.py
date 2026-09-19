from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models import Usuario

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Muestra el panel según el rol del usuario."""
    if current_user.rol == "administrador":
        total_usuarios = Usuario.query.count()
        total_tecnicos = Usuario.query.filter_by(rol="tecnico").count()
        total_clientes = Usuario.query.filter_by(rol="cliente").count()
        return render_template(
            "main/dashboard_admin.html",
            total_usuarios=total_usuarios,
            total_tecnicos=total_tecnicos,
            total_clientes=total_clientes,
        )
    if current_user.rol == "tecnico":
        return render_template("main/dashboard_tecnico.html")
    return render_template("main/dashboard_cliente.html")
