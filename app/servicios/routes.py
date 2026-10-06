from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, make_response,
)
from flask_login import current_user, login_required

from app import db
from app.decoradores import rol_requerido
from app.fechas import ahora_utc, hoy_durango
from app.models import (
    Calificacion, Categoria, FotoTecnico, Solicitud, Tecnico, Usuario, Zona,
    ESTADO_NOMBRES, FLUJO_ESTADOS,
)

servicios_bp = Blueprint("servicios", __name__)

# Estados en los que el cliente y el técnico ya pueden ver el teléfono del otro
ESTADOS_CON_CONTACTO = ("aceptado", "en_camino", "terminado")

# Acciones del técnico: acción -> (estado que debe tener, estado nuevo, mensaje)
ACCIONES = {
    "aceptar": ("pendiente", "aceptado", "Aceptaste la solicitud."),
    "rechazar": ("pendiente", "rechazado", "Rechazaste la solicitud."),
    "en_camino": ("aceptado", "en_camino", "La solicitud quedó como «En camino»."),
    "terminar": ("en_camino", "terminado", "Marcaste el servicio como terminado."),
}


# Foto del técnico: tamaño máximo y formatos aceptados
FOTO_MAX_BYTES = 2 * 1024 * 1024


def tipo_de_imagen(datos):
    """Revisa los primeros bytes del archivo (no confía en la extensión)."""
    if datos.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return "image/webp"
    return None


def categorias_activas():
    return Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()


def puede_ver(solicitud):
    """Solo el cliente que la hizo, el técnico asignado y el administrador."""
    if current_user.es_admin:
        return True
    if current_user.rol == "cliente":
        return solicitud.cliente_id == current_user.cliente.id
    if current_user.rol == "tecnico":
        return solicitud.tecnico_id == current_user.tecnico.id
    return False


# =========================================================
# BUSCAR TÉCNICOS (CLIENTE)
# =========================================================

@servicios_bp.route("/buscar")
@rol_requerido("cliente")
def buscar():
    categorias = categorias_activas()
    zonas = Zona.query.order_by(Zona.nombre).all()

    # La primera vez se propone la zona del cliente
    if "zona_id" in request.args:
        zona_id = request.args.get("zona_id", type=int)
    else:
        zona_id = current_user.cliente.zona_id
    categoria_id = request.args.get("categoria_id", type=int)

    consulta = Tecnico.query.join(Usuario)
    if categoria_id:
        consulta = consulta.filter(Tecnico.categorias.any(Categoria.id == categoria_id))
    if zona_id:
        consulta = consulta.filter(Tecnico.zona_id == zona_id)
    tecnicos = consulta.order_by(Usuario.nombre).all()
    # Primero los mejor calificados (los empates quedan por nombre)
    tecnicos.sort(key=lambda t: -(t.calificacion_resumen[0] or 0))

    return render_template(
        "servicios/buscar.html", categorias=categorias, zonas=zonas,
        tecnicos=tecnicos, categoria_id=categoria_id, zona_id=zona_id
    )


# =========================================================
# MANDAR SOLICITUD (CLIENTE)
# =========================================================

@servicios_bp.route("/solicitar/<int:tecnico_id>", methods=["GET", "POST"])
@rol_requerido("cliente")
def solicitar(tecnico_id):
    tecnico = db.get_or_404(Tecnico, tecnico_id)
    cliente = current_user.cliente
    hoy = hoy_durango()

    if request.method == "POST":
        categoria_id = request.form.get("categoria_id", type=int)
        direccion = (request.form.get("direccion") or "").strip()
        fecha_texto = request.form.get("fecha_servicio") or ""
        descripcion = (request.form.get("descripcion") or "").strip()

        errores = []
        # Solo se puede pedir un servicio que el técnico sí ofrece
        categoria = next(
            (c for c in tecnico.categorias if c.id == categoria_id), None
        )
        if categoria is None:
            errores.append("Elige uno de los servicios que ofrece el técnico.")
        try:
            fecha_servicio = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
            if fecha_servicio < hoy:
                errores.append("La fecha del servicio no puede ser anterior a hoy.")
        except ValueError:
            fecha_servicio = None
            errores.append("Selecciona la fecha del servicio.")
        if not direccion:
            errores.append("Escribe la dirección donde se hará el servicio.")
        elif len(direccion) > 200:
            errores.append("La dirección no puede pasar de 200 caracteres.")
        if not descripcion:
            errores.append("Describe brevemente qué necesitas.")
        elif len(descripcion) > 300:
            errores.append("La descripción no puede pasar de 300 caracteres.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "servicios/solicitar.html", tecnico=tecnico,
                datos=request.form, hoy=hoy.isoformat()
            )

        solicitud = Solicitud(
            cliente=cliente,
            tecnico=tecnico,
            categoria=categoria,
            zona_id=cliente.zona_id or tecnico.zona_id,
            direccion=direccion,
            fecha_servicio=fecha_servicio,
            descripcion=descripcion,
        )
        db.session.add(solicitud)
        db.session.commit()
        flash(
            f"Tu solicitud se envió a {tecnico.usuario.nombre}. "
            "Aquí puedes ver en qué va.", "success"
        )
        return redirect(url_for("servicios.detalle", solicitud_id=solicitud.id))

    datos = {"categoria_id": request.args.get("categoria_id", "")}
    return render_template(
        "servicios/solicitar.html", tecnico=tecnico, datos=datos,
        hoy=hoy.isoformat()
    )


# =========================================================
# DETALLE Y SEGUIMIENTO DE UNA SOLICITUD
# =========================================================

@servicios_bp.route("/solicitud/<int:solicitud_id>")
@login_required
def detalle(solicitud_id):
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    if not puede_ver(solicitud):
        flash("No tienes permiso para ver esa solicitud.", "warning")
        return redirect(url_for("main.dashboard"))

    paso_actual = (
        FLUJO_ESTADOS.index(solicitud.estado)
        if solicitud.estado in FLUJO_ESTADOS else -1
    )
    return render_template(
        "servicios/detalle.html", solicitud=solicitud,
        flujo=FLUJO_ESTADOS, nombres=ESTADO_NOMBRES, paso_actual=paso_actual,
        con_contacto=solicitud.estado in ESTADOS_CON_CONTACTO
    )


# =========================================================
# ACEPTAR, RECHAZAR Y CAMBIAR ESTADO (TÉCNICO)
# =========================================================

@servicios_bp.route("/solicitud/<int:solicitud_id>/estado", methods=["POST"])
@rol_requerido("tecnico")
def cambiar_estado(solicitud_id):
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    if solicitud.tecnico_id != current_user.tecnico.id:
        flash("No tienes permiso para cambiar esa solicitud.", "warning")
        return redirect(url_for("main.dashboard"))

    accion = request.form.get("accion")
    if accion not in ACCIONES:
        flash("Acción no válida.", "danger")
    else:
        requerido, nuevo, mensaje = ACCIONES[accion]
        # El estado solo avanza en orden: no se puede terminar algo pendiente
        if solicitud.estado != requerido:
            flash(
                f"No se puede hacer eso: la solicitud está "
                f"«{solicitud.estado_nombre}».", "warning"
            )
        else:
            solicitud.estado = nuevo
            solicitud.actualizada = ahora_utc()
            db.session.commit()
            flash(mensaje, "success")

    if request.form.get("volver") == "detalle":
        return redirect(url_for("servicios.detalle", solicitud_id=solicitud.id))
    return redirect(url_for("main.dashboard"))


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
        archivo = request.files.get("foto")
        quitar_foto = request.form.get("quitar_foto") == "1"

        errores = []
        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not ids:
            errores.append("Selecciona al menos un servicio que ofreces.")

        datos_foto, tipo_foto = None, None
        if archivo and archivo.filename:
            datos_foto = archivo.read()
            tipo_foto = tipo_de_imagen(datos_foto)
            if len(datos_foto) > FOTO_MAX_BYTES:
                errores.append("La foto no puede pesar más de 2 MB.")
            elif tipo_foto is None:
                errores.append("La foto debe ser una imagen JPG, PNG o WEBP.")

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
        if datos_foto:
            if tecnico.foto is None:
                tecnico.foto = FotoTecnico(datos=datos_foto, tipo=tipo_foto)
            else:
                tecnico.foto.datos = datos_foto
                tecnico.foto.tipo = tipo_foto
                tecnico.foto.actualizada = ahora_utc()
        elif quitar_foto:
            tecnico.foto = None
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


# =========================================================
# CALIFICAR UN SERVICIO TERMINADO (CLIENTE)
# =========================================================

@servicios_bp.route("/solicitud/<int:solicitud_id>/calificar", methods=["POST"])
@rol_requerido("cliente")
def calificar(solicitud_id):
    solicitud = db.get_or_404(Solicitud, solicitud_id)
    if solicitud.cliente_id != current_user.cliente.id:
        flash("No tienes permiso para calificar esa solicitud.", "warning")
        return redirect(url_for("main.dashboard"))

    estrellas = request.form.get("estrellas", type=int)
    comentario = (request.form.get("comentario") or "").strip()

    if solicitud.estado != "terminado":
        flash("Solo puedes calificar un servicio terminado.", "warning")
    elif solicitud.calificacion is not None:
        flash("Ya calificaste este servicio.", "warning")
    elif estrellas not in (1, 2, 3, 4, 5):
        flash("Elige de 1 a 5 estrellas.", "danger")
    elif len(comentario) > 300:
        flash("El comentario no puede pasar de 300 caracteres.", "danger")
    else:
        db.session.add(Calificacion(
            solicitud=solicitud, estrellas=estrellas, comentario=comentario
        ))
        db.session.commit()
        flash("Gracias, tu calificación se guardó.", "success")

    return redirect(url_for("servicios.detalle", solicitud_id=solicitud.id))


# =========================================================
# HISTORIAL DE SERVICIOS (CLIENTE)
# =========================================================

@servicios_bp.route("/historial")
@rol_requerido("cliente")
def historial():
    solicitudes = (
        Solicitud.query.filter_by(cliente_id=current_user.cliente.id)
        .filter(Solicitud.estado.in_(("terminado", "rechazado")))
        .order_by(Solicitud.fecha_servicio.desc(), Solicitud.id.desc()).all()
    )
    terminadas = [s for s in solicitudes if s.estado == "terminado"]
    return render_template(
        "servicios/historial.html", solicitudes=solicitudes,
        total_terminadas=len(terminadas),
        total_rechazadas=len(solicitudes) - len(terminadas),
        total_calificadas=sum(1 for s in terminadas if s.calificacion),
    )


# =========================================================
# FOTO DEL TÉCNICO
# =========================================================

@servicios_bp.route("/tecnico/<int:tecnico_id>/foto")
@login_required
def foto_tecnico(tecnico_id):
    foto = db.get_or_404(FotoTecnico, tecnico_id)
    respuesta = make_response(foto.datos)
    respuesta.headers["Content-Type"] = foto.tipo
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["Cache-Control"] = "private, max-age=3600"
    return respuesta
