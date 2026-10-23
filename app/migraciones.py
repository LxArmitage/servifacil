from sqlalchemy import inspect, text

from app import db

# Columnas que se agregaron a tablas que ya existían.
# db.create_all() crea las tablas nuevas, pero no agrega columnas a tablas que
# ya están creadas (por ejemplo, en instance/servifacil.db o en Render).
COLUMNAS_NUEVAS = [
    ("zonas", "activa", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("usuarios", "activo", "BOOLEAN NOT NULL DEFAULT TRUE"),
    ("calificaciones", "visible", "BOOLEAN NOT NULL DEFAULT TRUE"),
]


def agregar_columnas_faltantes():
    """Agrega con ALTER TABLE las columnas de COLUMNAS_NUEVAS que falten."""
    inspector = inspect(db.engine)
    for tabla, columna, definicion in COLUMNAS_NUEVAS:
        existentes = {c["name"] for c in inspector.get_columns(tabla)}
        if columna not in existentes:
            db.session.execute(
                text(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")
            )
            db.session.commit()
