import re

# Correo con forma usuario@dominio.ext (la validación completa la hace el navegador)
CORREO_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Largo máximo de cada campo; coincide con las columnas de models.py.
# PostgreSQL rechaza textos más largos, así que se revisan antes de guardar.
LARGOS = {
    "nombre": ("Nombre", 120),
    "correo": ("Correo", 120),
    "telefono": ("Teléfono", 20),
    "descripcion": ("Descripción", 200),
}


def errores_de_largo(**campos):
    """Mensajes de error para los campos que pasan de su largo máximo."""
    errores = []
    for campo, valor in campos.items():
        etiqueta, maximo = LARGOS[campo]
        if len(valor) > maximo:
            errores.append(f"El campo «{etiqueta}» no puede pasar de {maximo} caracteres.")
    return errores


def es_ruta_interna(url):
    """True solo para rutas de este mismo sitio, como /dashboard.
    Evita que ?next= mande al usuario a otra página después del login."""
    return bool(url) and url.startswith("/") and not url.startswith("//") \
        and "\\" not in url
