from flask import Blueprint, render_template, redirect, url_for, request, flash

from app import db
from app.decoradores import rol_requerido
from app.models import (
    Calificacion, Categoria, Cliente, Solicitud, Tecnico, Usuario, Zona,
    ESTADO_NOMBRES, ROL_NOMBRES,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# =========================================================
# CATÁLOGOS: CATEGORÍAS Y ZONAS
# =========================================================

def validar_categoria(nombre, descripcion, actual=None):
    errores = []
    if not nombre:
        errores.append("El nombre de la categoría es obligatorio.")
    elif len(nombre) > 60:
        errores.append("El nombre de la categoría no puede pasar de 60 caracteres.")
    if len(descripcion) > 200:
        errores.append("La descripción no puede pasar de 200 caracteres.")
    repetida = Categoria.query.filter(
        db.func.lower(Categoria.nombre) == nombre.lower()
    ).first()
    if nombre and repetida is not None and repetida is not actual:
        errores.append("Ya existe una categoría con ese nombre.")
    return errores


def validar_zona(nombre, ciudad, actual=None):
    errores = []
    if not nombre or not ciudad:
        errores.append("El nombre de la zona y la ciudad son obligatorios.")
    elif len(nombre) > 80 or len(ciudad) > 80:
        errores.append("El nombre y la ciudad no pueden pasar de 80 caracteres.")
    repetida = Zona.query.filter(
        db.func.lower(Zona.nombre) == nombre.lower(),
        db.func.lower(Zona.ciudad) == ciudad.lower(),
    ).first()
    if nombre and repetida is not None and repetida is not actual:
        errores.append("Ya existe esa zona en esa ciudad.")
    return errores


def pagina_catalogos(datos_categoria=None, datos_zona=None):
    """Página con las dos tablas; se usa también para mostrar errores."""
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    zonas = Zona.query.order_by(Zona.ciudad, Zona.nombre).all()
    solicitudes_por_categoria = dict(
        db.session.query(Solicitud.categoria_id, db.func.count(Solicitud.id))
        .group_by(Solicitud.categoria_id).all()
    )
    clientes_por_zona = dict(
        db.session.query(Cliente.zona_id, db.func.count(Cliente.id))
        .group_by(Cliente.zona_id).all()
    )
    tecnicos_por_zona = dict(
        db.session.query(Tecnico.zona_id, db.func.count(Tecnico.id))
        .group_by(Tecnico.zona_id).all()
    )
    return render_template(
        "admin/catalogos.html", categorias=categorias, zonas=zonas,
        solicitudes_por_categoria=solicitudes_por_categoria,
        clientes_por_zona=clientes_por_zona, tecnicos_por_zona=tecnicos_por_zona,
        datos_categoria=datos_categoria or {}, datos_zona=datos_zona or {},
    )


@admin_bp.route("/catalogos")
@rol_requerido("administrador")
def catalogos():
    return pagina_catalogos()


@admin_bp.route("/categorias/nueva", methods=["POST"])
@rol_requerido("administrador")
def nueva_categoria():
    nombre = (request.form.get("nombre") or "").strip()
    descripcion = (request.form.get("descripcion") or "").strip()
    errores = validar_categoria(nombre, descripcion)
    if errores:
        for e in errores:
            flash(e, "danger")
        return pagina_catalogos(datos_categoria=request.form)
    db.session.add(Categoria(nombre=nombre, descripcion=descripcion))
    db.session.commit()
    flash(f"Se agregó la categoría «{nombre}».", "success")
    return redirect(url_for("admin.catalogos"))


@admin_bp.route("/categorias/<int:categoria_id>/editar", methods=["GET", "POST"])
@rol_requerido("administrador")
def editar_categoria(categoria_id):
    categoria = db.get_or_404(Categoria, categoria_id)
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        errores = validar_categoria(nombre, descripcion, actual=categoria)
        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("admin/editar_categoria.html",
                                   categoria=categoria, datos=request.form)
        categoria.nombre = nombre
        categoria.descripcion = descripcion
        db.session.commit()
        flash(f"Se guardaron los cambios de «{nombre}».", "success")
        return redirect(url_for("admin.catalogos"))
    datos = {"nombre": categoria.nombre, "descripcion": categoria.descripcion}
    return render_template("admin/editar_categoria.html",
                           categoria=categoria, datos=datos)


@admin_bp.route("/categorias/<int:categoria_id>/estado", methods=["POST"])
@rol_requerido("administrador")
def estado_categoria(categoria_id):
    # No se borra: las solicitudes viejas siguen apuntando a la categoría
    categoria = db.get_or_404(Categoria, categoria_id)
    categoria.activa = not categoria.activa
    db.session.commit()
    accion = "activó" if categoria.activa else "desactivó"
    flash(f"Se {accion} la categoría «{categoria.nombre}».", "info")
    return redirect(url_for("admin.catalogos"))


@admin_bp.route("/zonas/nueva", methods=["POST"])
@rol_requerido("administrador")
def nueva_zona():
    nombre = (request.form.get("nombre") or "").strip()
    ciudad = (request.form.get("ciudad") or "").strip()
    errores = validar_zona(nombre, ciudad)
    if errores:
        for e in errores:
            flash(e, "danger")
        return pagina_catalogos(datos_zona=request.form)
    db.session.add(Zona(nombre=nombre, ciudad=ciudad))
    db.session.commit()
    flash(f"Se agregó la zona «{nombre}, {ciudad}».", "success")
    return redirect(url_for("admin.catalogos"))


@admin_bp.route("/zonas/<int:zona_id>/editar", methods=["GET", "POST"])
@rol_requerido("administrador")
def editar_zona(zona_id):
    zona = db.get_or_404(Zona, zona_id)
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        ciudad = (request.form.get("ciudad") or "").strip()
        errores = validar_zona(nombre, ciudad, actual=zona)
        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template("admin/editar_zona.html", zona=zona,
                                   datos=request.form)
        zona.nombre = nombre
        zona.ciudad = ciudad
        db.session.commit()
        flash(f"Se guardaron los cambios de «{nombre}, {ciudad}».", "success")
        return redirect(url_for("admin.catalogos"))
    datos = {"nombre": zona.nombre, "ciudad": zona.ciudad}
    return render_template("admin/editar_zona.html", zona=zona, datos=datos)


@admin_bp.route("/zonas/<int:zona_id>/estado", methods=["POST"])
@rol_requerido("administrador")
def estado_zona(zona_id):
    zona = db.get_or_404(Zona, zona_id)
    zona.activa = not zona.activa
    db.session.commit()
    accion = "activó" if zona.activa else "desactivó"
    flash(f"Se {accion} la zona «{zona}».", "info")
    return redirect(url_for("admin.catalogos"))


# =========================================================
# USUARIOS: SUSPENDER Y REACTIVAR CUENTAS
# =========================================================

@admin_bp.route("/usuarios")
@rol_requerido("administrador")
def usuarios():
    rol = request.args.get("rol") or ""
    consulta = Usuario.query
    if rol in ROL_NOMBRES:
        consulta = consulta.filter_by(rol=rol)
    lista = consulta.order_by(Usuario.creado, Usuario.id).all()
    suspendidos = Usuario.query.filter(Usuario.activo.is_(False)).count()
    return render_template(
        "admin/usuarios.html", usuarios=lista, rol=rol, roles=ROL_NOMBRES,
        total=Usuario.query.count(), suspendidos=suspendidos,
    )


@admin_bp.route("/usuarios/<int:usuario_id>/estado", methods=["POST"])
@rol_requerido("administrador")
def estado_usuario(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    if usuario.es_admin:
        flash("No se puede suspender la cuenta de un administrador.", "warning")
    else:
        usuario.activo = not usuario.activo
        db.session.commit()
        if usuario.activo:
            flash(f"Se reactivó la cuenta de {usuario.nombre}.", "info")
        else:
            flash(f"Se suspendió la cuenta de {usuario.nombre}. Ya no puede "
                  "iniciar sesión.", "info")
    rol = request.form.get("rol")
    return redirect(url_for("admin.usuarios", rol=rol if rol in ROL_NOMBRES else None))


# =========================================================
# RESEÑAS: OCULTAR LAS QUE NO CUMPLAN LAS REGLAS
# =========================================================

@admin_bp.route("/resenas")
@rol_requerido("administrador")
def resenas():
    calificaciones = Calificacion.query.order_by(Calificacion.creada.desc()).all()
    ocultas = sum(1 for c in calificaciones if not c.visible)
    return render_template("admin/resenas.html", calificaciones=calificaciones,
                           ocultas=ocultas)


@admin_bp.route("/resenas/<int:calificacion_id>/visible", methods=["POST"])
@rol_requerido("administrador")
def visible_resena(calificacion_id):
    calificacion = db.get_or_404(Calificacion, calificacion_id)
    calificacion.visible = not calificacion.visible
    db.session.commit()
    if calificacion.visible:
        flash("La reseña vuelve a ser visible.", "info")
    else:
        flash("La reseña quedó oculta y ya no cuenta para el promedio.", "info")
    return redirect(url_for("admin.resenas"))


# =========================================================
# REPORTES
# =========================================================

@admin_bp.route("/reportes")
@rol_requerido("administrador")
def reportes():
    terminado = db.case((Solicitud.estado == "terminado", 1), else_=0)

    # Servicios por categoría (incluye las que no tienen solicitudes)
    por_categoria = (
        db.session.query(Categoria.nombre,
                         db.func.count(Solicitud.id),
                         db.func.coalesce(db.func.sum(terminado), 0))
        .outerjoin(Solicitud, Solicitud.categoria_id == Categoria.id)
        .group_by(Categoria.id, Categoria.nombre)
        .order_by(db.func.count(Solicitud.id).desc(), Categoria.nombre)
        .all()
    )

    # Solicitudes por zona
    por_zona = (
        db.session.query(Zona.nombre, db.func.count(Solicitud.id))
        .outerjoin(Solicitud, Solicitud.zona_id == Zona.id)
        .group_by(Zona.id, Zona.nombre)
        .order_by(db.func.count(Solicitud.id).desc(), Zona.nombre)
        .all()
    )

    # Técnicos mejor calificados (solo reseñas visibles)
    promedio = db.func.avg(Calificacion.estrellas).label("promedio")
    resenas = db.func.count(Calificacion.id).label("resenas")
    mejores = (
        db.session.query(Tecnico, promedio, resenas)
        .join(Solicitud, Solicitud.tecnico_id == Tecnico.id)
        .join(Calificacion, Calificacion.solicitud_id == Solicitud.id)
        .filter(Calificacion.visible.is_(True))
        .group_by(Tecnico.id)
        .order_by(promedio.desc(), resenas.desc())
        .limit(10).all()
    )
    terminados_por_tecnico = dict(
        db.session.query(Solicitud.tecnico_id, db.func.count(Solicitud.id))
        .filter(Solicitud.estado == "terminado")
        .group_by(Solicitud.tecnico_id).all()
    )

    # Resumen general
    conteo = dict(
        db.session.query(Solicitud.estado, db.func.count(Solicitud.id))
        .group_by(Solicitud.estado).all()
    )
    total = sum(conteo.values())
    # De las solicitudes que el técnico ya contestó, cuántas aceptó
    aceptadas = sum(conteo.get(e, 0) for e in ("aceptado", "en_camino", "terminado"))
    contestadas = aceptadas + conteo.get("rechazado", 0)
    promedio_general = (
        db.session.query(db.func.avg(Calificacion.estrellas))
        .filter(Calificacion.visible.is_(True)).scalar()
    )

    return render_template(
        "admin/reportes.html",
        por_categoria=por_categoria,
        max_categoria=max([f[1] for f in por_categoria] + [1]),
        por_zona=por_zona,
        max_zona=max([f[1] for f in por_zona] + [1]),
        mejores=mejores,
        terminados_por_tecnico=terminados_por_tecnico,
        total=total,
        conteo=conteo,
        nombres=ESTADO_NOMBRES,
        tasa_aceptacion=(aceptadas * 100 / contestadas) if contestadas else None,
        promedio_general=promedio_general,
    )
