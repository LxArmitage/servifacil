from datetime import datetime, time, timedelta

from app import db
from app.fechas import hoy_durango
from app.models import (
    Calificacion, Categoria, Cliente, Solicitud, Tecnico, Usuario, Zona,
)

# Contraseña de las cuentas de demostración. No es secreta: los datos son
# ficticios y las cuentas están en el README para que se pueda probar la app.
# El administrador no se crea aquí; sigue usando ADMIN_PASSWORD.
PASSWORD_DEMO = "demo1234"

# (correo, nombre, teléfono, zona)
CLIENTES = [
    ("cliente@servifacil.test", "María López", "618 555 0101", "Centro"),
    ("cliente2@servifacil.test", "Carlos Herrera", "618 555 0102", "Nuevo Durango"),
    ("cliente3@servifacil.test", "Lucía Fernández", "618 555 0103", "Guadalupe Victoria"),
]

# (correo, nombre, teléfono, zona, descripción, servicios)
TECNICOS = [
    ("tecnico@servifacil.test", "Jorge Ramírez", "618 555 0201", "Centro",
     "Plomero y electricista con 10 años de experiencia.",
     ["Plomería", "Electricidad"]),
    ("tecnico2@servifacil.test", "Ana Morales", "618 555 0202", "Nuevo Durango",
     "Limpieza de casas y oficinas, con material incluido.",
     ["Limpieza", "Jardinería"]),
    ("tecnico3@servifacil.test", "Luis Castillo", "618 555 0203", "Centro",
     "Reparación de muebles y pintura de interiores.",
     ["Carpintería", "Pintura"]),
    ("tecnico4@servifacil.test", "Pedro Salas", "618 555 0204", "Guadalupe Victoria",
     "Instalaciones eléctricas y fugas de agua.",
     ["Electricidad", "Plomería"]),
]

# (cliente, técnico, servicio, días desde hoy, estado, descripción, estrellas, reseña)
SOLICITUDES = [
    (0, 0, "Plomería", -30, "terminado", "Fuga de agua debajo del fregadero.",
     5, "Llegó puntual y dejó todo limpio."),
    (1, 0, "Electricidad", -24, "terminado", "Cambiar tres contactos de la sala.",
     4, "Buen trabajo, tardó un poco más de lo acordado."),
    (2, 3, "Plomería", -21, "terminado", "Instalar una llave nueva en el baño.",
     4, "Quedó bien y el precio fue justo."),
    (0, 2, "Pintura", -18, "terminado", "Pintar dos recámaras.",
     5, "Muy buen acabado."),
    (1, 1, "Limpieza", -14, "terminado", "Limpieza general después de una obra.",
     5, "La casa quedó impecable."),
    (2, 1, "Jardinería", -10, "terminado", "Podar el pasto y los arbustos.",
     3, "Cumplió, pero llegó tarde."),
    (0, 2, "Carpintería", -7, "terminado", "Ajustar las puertas del closet.",
     None, None),
    (1, 3, "Electricidad", -5, "rechazado", "Revisar el cableado de la cochera.",
     None, None),
    (2, 0, "Plomería", -3, "cancelado", "Destapar el drenaje del patio.",
     None, None),
    (1, 0, "Electricidad", 1, "en_camino", "Instalar una lámpara en el comedor.",
     None, None),
    (2, 0, "Plomería", 2, "aceptado", "Revisar el flotador del tinaco.",
     None, None),
    (0, 0, "Plomería", 3, "pendiente", "Cambiar la llave de la regadera.",
     None, None),
]


def cargar_demo():
    """Crea cuentas y solicitudes de ejemplo para presentar la aplicación.
    Solo se ejecuta una vez y no modifica los datos que ya existen."""
    if Usuario.query.filter_by(correo=CLIENTES[0][0]).first():
        return

    zonas = {z.nombre: z for z in Zona.query.all()}
    categorias = {c.nombre: c for c in Categoria.query.all()}

    # Si faltan catálogos porque se editaron a mano, no se carga nada
    servicios_usados = {s for t in TECNICOS for s in t[5]}
    if not servicios_usados <= set(categorias):
        return

    def nuevo_usuario(correo, nombre, rol):
        usuario = Usuario(nombre=nombre, correo=correo, rol=rol)
        usuario.set_password(PASSWORD_DEMO)
        return usuario

    clientes = []
    for correo, nombre, telefono, zona in CLIENTES:
        clientes.append(Cliente(
            usuario=nuevo_usuario(correo, nombre, "cliente"),
            telefono=telefono, zona=zonas.get(zona),
        ))

    tecnicos = []
    for correo, nombre, telefono, zona, descripcion, servicios in TECNICOS:
        tecnicos.append(Tecnico(
            usuario=nuevo_usuario(correo, nombre, "tecnico"),
            telefono=telefono, zona=zonas.get(zona), descripcion=descripcion,
            categorias=[categorias[s] for s in servicios],
        ))

    db.session.add_all(clientes + tecnicos)

    hoy = hoy_durango()
    for i_cliente, i_tecnico, servicio, dias, estado, descripcion, estrellas, resena \
            in SOLICITUDES:
        cliente = clientes[i_cliente]
        fecha_servicio = hoy + timedelta(days=dias)
        # Cada solicitud se hizo dos días antes del servicio (o de hoy)
        creada = datetime.combine(min(fecha_servicio, hoy) - timedelta(days=2),
                                  time(17, 0))
        solicitud = Solicitud(
            cliente=cliente, tecnico=tecnicos[i_tecnico],
            categoria=categorias[servicio], zona=cliente.zona,
            direccion=f"Calle Ejemplo {100 + i_cliente * 10 + i_tecnico}",
            fecha_servicio=fecha_servicio, descripcion=descripcion,
            estado=estado, creada=creada, actualizada=creada,
        )
        db.session.add(solicitud)
        if estrellas:
            db.session.add(Calificacion(
                solicitud=solicitud, estrellas=estrellas, comentario=resena,
                creada=creada + timedelta(days=2),
            ))

    db.session.commit()
