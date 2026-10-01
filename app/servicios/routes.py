from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user

from app import db
from app.decoradores import rol_requerido
from app.models import Categoria, Zona

servicios_bp = Blueprint("servicios", __name__)


def categorias_activas():
    return Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()


# =========================================================
# PERFIL DEL TÉCNICO
# =========================================================

@servicios_bp.route("/perfil", methods=["GET", "POST"])
@rol_requerido("tecnico")
def perfil_tecnico():
    tecnico = current_user.tecnico
    zonas = Zona.query.order_by(Zona.nombre).all()
    categorias = categorias_activas()

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        telefono = (request.form.get("telefono") or "").strip()
        zona_id = request.form.get("zona_id") or None
        descripcion = (request.form.get("descripcion") or "").strip()
        ids = request.form.getlist("categorias")

        errores = []
        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not ids:
            errores.append("Selecciona al menos un servicio que ofreces.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "servicios/perfil_tecnico.html", zonas=zonas,
                categorias=categorias, datos=request.form, seleccionadas=ids
            )

        current_user.nombre = nombre
        tecnico.telefono = telefono
        tecnico.zona_id = zona_id
        tecnico.descripcion = descripcion
        tecnico.categorias = Categoria.query.filter(Categoria.id.in_(ids)).all()
        db.session.commit()
        flash("Tu perfil se guardó correctamente.", "success")
        return redirect(url_for("main.dashboard"))

    datos = {
        "nombre": current_user.nombre,
        "telefono": tecnico.telefono,
        "zona_id": str(tecnico.zona_id or ""),
        "descripcion": tecnico.descripcion,
    }
    seleccionadas = [str(c.id) for c in tecnico.categorias]
    return render_template(
        "servicios/perfil_tecnico.html", zonas=zonas, categorias=categorias,
        datos=datos, seleccionadas=seleccionadas
    )
