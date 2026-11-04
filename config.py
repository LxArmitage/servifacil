import os
import secrets


class Config:
    """Configuración base. En local usa SQLite; en la nube (Render) usa
    PostgreSQL a través de la variable de entorno DATABASE_URL.

    Ninguna contraseña ni clave va escrita aquí: se leen de variables de
    entorno (en Render se configuran en el panel del servicio)."""

    # Si no hay SECRET_KEY (en local), se genera una al azar; las sesiones
    # se cierran cada vez que se reinicia el servidor.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    _db_url = os.environ.get("DATABASE_URL", "")
    # Render puede entregar la URL como postgres://; SQLAlchemy requiere postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _db_url or "sqlite:///servifacil.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Revisa que la conexión siga viva antes de usarla (la BD en la nube
    # puede cerrar conexiones que llevan mucho tiempo sin usarse)
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Tamaño máximo de una petición (la foto del técnico es de hasta 2 MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Cookie de sesión: no se puede leer desde JavaScript, no se envía desde
    # otros sitios y en Render (HTTPS) solo viaja cifrada
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = "RENDER" in os.environ

    # Cuenta de administrador que se crea al arrancar si todavía no existe
    ADMIN_CORREO = os.environ.get("ADMIN_CORREO", "admin@servifacil.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    # Cuentas y solicitudes de ejemplo para presentar la aplicación
    # (DEMO_DATOS=0 las desactiva; ver app/demo.py)
    DEMO_DATOS = os.environ.get("DEMO_DATOS", "1") == "1"
