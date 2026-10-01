from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager
from app.fechas import ahora_utc

# Roles disponibles en la plataforma
ROLES = ("cliente", "tecnico", "administrador")

# Nombre de cada rol tal como se muestra en pantalla
ROL_NOMBRES = {
    "cliente": "Cliente",
    "tecnico": "Técnico",
    "administrador": "Administrador",
}

# Estados por los que pasa una solicitud de servicio
ESTADO_NOMBRES = {
    "pendiente": "Pendiente",
    "aceptado": "Aceptado",
    "en_camino": "En camino",
    "terminado": "Terminado",
    "rechazado": "Rechazado",
}

# Orden normal del servicio (el rechazo lo termina antes)
FLUJO_ESTADOS = ("pendiente", "aceptado", "en_camino", "terminado")

# Categorías de servicio con las que arranca la plataforma
CATEGORIAS_INICIALES = [
    ("Plomería", "Fugas, instalación de llaves, tinacos y drenaje"),
    ("Electricidad", "Contactos, apagadores, cableado y lámparas"),
    ("Limpieza", "Limpieza de casa, oficinas y después de obra"),
    ("Jardinería", "Poda, corte de pasto y mantenimiento de jardines"),
    ("Carpintería", "Reparación de puertas, muebles y closets"),
    ("Pintura", "Pintura de interiores, exteriores y fachadas"),
]

# Relación N a N: qué categorías ofrece cada técnico
tecnico_categoria = db.Table(
    "tecnico_categoria",
    db.Column("tecnico_id", db.Integer, db.ForeignKey("tecnicos.id"),
              primary_key=True),
    db.Column("categoria_id", db.Integer, db.ForeignKey("categorias.id"),
              primary_key=True),
)


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
    creado = db.Column(db.DateTime, default=ahora_utc)

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
    categorias = db.relationship(
        "Categoria", secondary=tecnico_categoria, backref="tecnicos",
        order_by="Categoria.nombre"
    )

    @property
    def categorias_texto(self):
        return ", ".join(c.nombre for c in self.categorias)


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(60), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    activa = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.nombre


class Solicitud(db.Model):
    __tablename__ = "solicitudes"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey("tecnicos.id"), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    zona_id = db.Column(db.Integer, db.ForeignKey("zonas.id"))
    direccion = db.Column(db.String(200), nullable=False)
    fecha_servicio = db.Column(db.Date, nullable=False)
    descripcion = db.Column(db.String(300), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    creada = db.Column(db.DateTime, default=ahora_utc)
    actualizada = db.Column(db.DateTime, default=ahora_utc)

    cliente = db.relationship("Cliente", backref="solicitudes")
    tecnico = db.relationship("Tecnico", backref="solicitudes")
    categoria = db.relationship("Categoria")
    zona = db.relationship("Zona")

    @property
    def estado_nombre(self):
        return ESTADO_NOMBRES.get(self.estado, self.estado)

    def __str__(self):
        return f"Solicitud {self.id} ({self.estado})"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


def inicializar_datos():
    """Crea las zonas, las categorías y un usuario administrador si no existen."""
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

    if Categoria.query.count() == 0:
        db.session.add_all([
            Categoria(nombre=nombre, descripcion=descripcion)
            for nombre, descripcion in CATEGORIAS_INICIALES
        ])
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
