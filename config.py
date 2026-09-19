import os


class Config:
    """Configuración base. En local usa SQLite; en la nube (Render) usa
    PostgreSQL a través de la variable de entorno DATABASE_URL."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-servifacil-cambia-esto")

    _db_url = os.environ.get("DATABASE_URL", "")
    # Render entrega la URL como postgres://; SQLAlchemy requiere postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _db_url or "sqlite:///servifacil.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
