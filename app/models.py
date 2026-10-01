from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

# Roles disponibles en la plataforma
ROLES = ("cliente", "tecnico", "administrador")

# Nombre de cada rol tal como se muestra en pantalla
ROL_NOMBRES = {
    "cliente": "Cliente",
    "tecnico": "Técnico",
    "administrador": "Administrador",
}


class Zona(db.Model):
    __tablename__ = "zonas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    ciudad = db.Column(db.String(80), nullable=False, default="Durango")

    def __str__(self):
        return f"{self.nombre}, {self.ciudad}"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default="cliente")
    creado = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship(
        "Cliente", backref="usuario", uselist=False,
        cascade="all, delete-orphan"
    )
    tecnico = db.relationship(
        "Tecnico", backref="usuario", uselist=False,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def es_admin(self):
        return self.rol == "administrador"

    @property
    def rol_nombre(self):
        return ROL_NOMBRES.get(self.rol, self.rol)

    @property
    def perfil(self):
        """Datos de cliente o de técnico según el rol (None para el administrador)."""
        return self.cliente or self.tecnico

    def __str__(self):
        return f"{self.nombre} ({self.rol})"


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    telefono = db.Column(db.String(20))
    zona_id = db.Column(db.Integer, db.ForeignKey("zonas.id"))
    zona = db.relationship("Zona")


class Tecnico(db.Model):
    __tablename__ = "tecnicos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    telefono = db.Column(db.String(20))
    descripcion = db.Column(db.String(200))
    zona_id = db.Column(db.Integer, db.ForeignKey("zonas.id"))
    zona = db.relationship("Zona")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def inicializar_datos():
    """Crea las zonas de arranque y un usuario administrador si no existen."""
    if Zona.query.count() == 0:
        zonas = [
            Zona(nombre="Centro", ciudad="Durango"),
            Zona(nombre="Guadalupe Victoria", ciudad="Durango"),
            Zona(nombre="Nuevo Durango", ciudad="Durango"),
            Zona(nombre="Fraccionamiento Fátima", ciudad="Durango"),
            Zona(nombre="Otra", ciudad="Durango"),
        ]
        db.session.add_all(zonas)
        db.session.commit()

    if Usuario.query.filter_by(correo="admin@servifacil.com").first() is None:
        admin = Usuario(
            nombre="Administrador",
            correo="admin@servifacil.com",
            rol="administrador",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
