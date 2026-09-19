from flask import (
    Blueprint, render_template, redirect, url_for, request, flash
)
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import Usuario, Cliente, Tecnico, Zona

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    zonas = Zona.query.order_by(Zona.nombre).all()

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        correo = (request.form.get("correo") or "").strip().lower()
        password = request.form.get("password") or ""
        password2 = request.form.get("password2") or ""
        rol = request.form.get("rol") or "cliente"
        telefono = (request.form.get("telefono") or "").strip()
        zona_id = request.form.get("zona_id") or None
        descripcion = (request.form.get("descripcion") or "").strip()

        # Validaciones
        errores = []
        if not nombre or not correo or not password:
            errores.append("Nombre, correo y contraseña son obligatorios.")
        if rol not in ("cliente", "tecnico"):
            errores.append("Selecciona un tipo de cuenta válido.")
        if password != password2:
            errores.append("Las contraseñas no coinciden.")
        if len(password) < 6:
            errores.append("La contraseña debe tener al menos 6 caracteres.")
        if Usuario.query.filter_by(correo=correo).first():
            errores.append("Ya existe una cuenta con ese correo.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "auth/registro.html", zonas=zonas, datos=request.form
            )

        # Crear usuario y su perfil según el rol
        usuario = Usuario(nombre=nombre, correo=correo, rol=rol)
        usuario.set_password(password)
        db.session.add(usuario)
        db.session.flush()  # obtener usuario.id

        if rol == "cliente":
            db.session.add(Cliente(
                usuario_id=usuario.id, telefono=telefono, zona_id=zona_id
            ))
        else:
            db.session.add(Tecnico(
                usuario_id=usuario.id, telefono=telefono,
                descripcion=descripcion, zona_id=zona_id
            ))

        db.session.commit()
        login_user(usuario)
        flash("¡Cuenta creada! Bienvenido a ServiFácil.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/registro.html", zonas=zonas, datos={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        correo = (request.form.get("correo") or "").strip().lower()
        password = request.form.get("password") or ""

        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario is None or not usuario.check_password(password):
            flash("Correo o contraseña incorrectos.", "danger")
            return render_template("auth/login.html", datos=request.form)

        login_user(usuario)
        flash(f"Hola de nuevo, {usuario.nombre}.", "success")
        siguiente = request.args.get("next")
        return redirect(siguiente or url_for("main.dashboard"))

    return render_template("auth/login.html", datos={})


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("main.index"))
