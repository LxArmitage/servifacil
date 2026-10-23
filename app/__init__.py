from flask import Flask, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect, CSRFError

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
# Protección CSRF: cada formulario POST lleva un token que el servidor revisa
csrf = CSRFProtect()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."
login_manager.login_message_category = "warning"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Filtros de Jinja para mostrar fechas en formato dd/mm/aaaa
    from app.fechas import fecha, fecha_hora
    app.add_template_filter(fecha, "fecha")
    app.add_template_filter(fecha_hora, "fecha_hora")

    # Blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.servicios.routes import servicios_bp
    from app.admin.routes import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(servicios_bp)
    app.register_blueprint(admin_bp)

    # Archivo más grande que MAX_CONTENT_LENGTH (por ejemplo, una foto pesada)
    @app.errorhandler(413)
    def archivo_muy_grande(error):
        flash("El archivo es demasiado grande. La foto no puede pesar más de 2 MB.",
              "danger")
        if current_user.is_authenticated and current_user.rol == "tecnico":
            return redirect(url_for("servicios.perfil_tecnico"))
        return redirect(url_for("main.dashboard"))

    # Formulario sin token CSRF válido (por ejemplo, la página llevaba
    # mucho tiempo abierta o la petición vino de otro sitio)
    @app.errorhandler(CSRFError)
    def token_invalido(error):
        flash("La página expiró. Vuelve a intentarlo.", "warning")
        if current_user.is_authenticated:
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("auth.login"))

    # Crear tablas y datos iniciales (zonas y administrador)
    with app.app_context():
        from app import models
        from app.migraciones import agregar_columnas_faltantes
        db.create_all()
        agregar_columnas_faltantes()
        models.inicializar_datos()

    return app
