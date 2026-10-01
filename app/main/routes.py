from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app import db
from app.models import Categoria, Solicitud, Usuario, Zona, ESTADO_NOMBRES

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    zonas = Zona.query.filter(Zona.nombre != "Otra").order_by(Zona.nombre).all()
    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()
    return render_template("index.html", zonas=zonas, categorias=categorias)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Muestra el panel según el rol del usuario."""
    if current_user.rol == "administrador":
        usuarios = Usuario.query.order_by(Usuario.creado).all()
        total_tecnicos = Usuario.query.filter_by(rol="tecnico").count()
        total_clientes = Usuario.query.filter_by(rol="cliente").count()

        solicitudes = Solicitud.query.order_by(Solicitud.creada.desc()).all()
        conteo = dict(
            db.session.query(Solicitud.estado, db.func.count())
            .group_by(Solicitud.estado).all()
        )
        por_estado = [(nombre, conteo.get(clave, 0))
                      for clave, nombre in ESTADO_NOMBRES.items()]
        return render_template(
            "main/dashboard_admin.html",
            usuarios=usuarios,
            total_usuarios=len(usuarios),
            total_tecnicos=total_tecnicos,
            total_clientes=total_clientes,
            solicitudes=solicitudes,
            por_estado=por_estado,
        )
    if current_user.rol == "tecnico":
        propias = Solicitud.query.filter_by(tecnico_id=current_user.tecnico.id)
        nuevas = (
            propias.filter_by(estado="pendiente")
            .order_by(Solicitud.fecha_servicio).all()
        )
        en_curso = (
            propias.filter(Solicitud.estado.in_(("aceptado", "en_camino")))
            .order_by(Solicitud.fecha_servicio).all()
        )
        cerradas = (
            propias.filter(Solicitud.estado.in_(("terminado", "rechazado")))
            .order_by(Solicitud.actualizada.desc()).all()
        )
        return render_template(
            "main/dashboard_tecnico.html", nuevas=nuevas, en_curso=en_curso,
            cerradas=cerradas
        )

    solicitudes = (
        Solicitud.query.filter_by(cliente_id=current_user.cliente.id)
        .order_by(Solicitud.creada.desc()).all()
    )
    return render_template("main/dashboard_cliente.html", solicitudes=solicitudes)
