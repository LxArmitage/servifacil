from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."
login_manager.login_message_category = "warning"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # Blueprints
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.servicios.routes import servicios_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(servicios_bp)

    # Crear tablas y datos iniciales (zonas y administrador)
    with app.app_context():
        from app import models
        db.create_all()
        models.inicializar_datos()

    return app
