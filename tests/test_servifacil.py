"""Pruebas automáticas de ServiFácil.

Ejecutar desde la carpeta del proyecto:
    python -m unittest discover -s tests -v

Cada prueba usa una base de datos SQLite en memoria, así que no toca
instance/servifacil.db.
"""
import unittest
from datetime import timedelta

from config import Config
from app import create_app, db
from app.fechas import hoy_durango
from app.models import Solicitud, Tecnico

PASSWORD = "secreto1"
PLOMERIA, ELECTRICIDAD = "1", "2"
CENTRO, NUEVO_DURANGO = "1", "3"


class ConfigPruebas(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class PruebaBase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(ConfigPruebas)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ---------- ayudas ----------

    def registrar(self, rol, correo, zona=CENTRO, categorias=None, telefono=""):
        cliente = self.app.test_client()
        datos = dict(
            rol=rol, nombre=correo.split("@")[0].title(), correo=correo,
            telefono=telefono, zona_id=zona, password=PASSWORD,
            password2=PASSWORD,
        )
        if categorias:
            datos["categorias"] = categorias
        respuesta = cliente.post("/registro", data=datos)
        self.assertEqual(respuesta.status_code, 302)
        return cliente

    def fecha(self, dias):
        return (hoy_durango() + timedelta(days=dias)).isoformat()

    def solicitar(self, cliente, tecnico_id=1, categoria=PLOMERIA, dias=1):
        return cliente.post(f"/solicitar/{tecnico_id}", data=dict(
            categoria_id=categoria, fecha_servicio=self.fecha(dias),
            direccion="Calle Negrete 120, Centro", descripcion="Fuga en el lavabo",
        ))

    def estado(self, solicitud_id):
        with self.app.app_context():
            return db.session.get(Solicitud, solicitud_id).estado


# =========================================================
# SPRINT 1: REGISTRO, INICIO DE SESIÓN Y ROLES
# =========================================================

class PruebasAutenticacion(PruebaBase):

    def test_registro_de_cliente_entra_a_su_panel(self):
        cliente = self.registrar("cliente", "ana@ejemplo.com")
        self.assertIn("Cliente: Ana", cliente.get("/dashboard").get_data(as_text=True))

    def test_registro_rechaza_contrasenas_distintas(self):
        r = self.app.test_client().post("/registro", data=dict(
            rol="cliente", nombre="Ana", correo="ana@ejemplo.com",
            password="secreto1", password2="secreto2",
        ))
        self.assertIn("no coinciden", r.get_data(as_text=True))

    def test_registro_rechaza_correo_repetido(self):
        self.registrar("cliente", "ana@ejemplo.com")
        r = self.app.test_client().post("/registro", data=dict(
            rol="cliente", nombre="Otra", correo="ana@ejemplo.com",
            password=PASSWORD, password2=PASSWORD,
        ))
        self.assertIn("Ya existe una cuenta", r.get_data(as_text=True))

    def test_login_con_contrasena_incorrecta(self):
        self.registrar("cliente", "ana@ejemplo.com")
        r = self.app.test_client().post("/login", data=dict(
            correo="ana@ejemplo.com", password="incorrecta",
        ))
        self.assertIn("incorrectos", r.get_data(as_text=True))

    def test_panel_requiere_sesion(self):
        r = self.app.test_client().get("/dashboard")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers["Location"])


# =========================================================
# SPRINT 2: PERFIL DEL TÉCNICO
# =========================================================

class PruebasPerfilTecnico(PruebaBase):

    def test_tecnico_debe_elegir_al_menos_un_servicio(self):
        r = self.app.test_client().post("/registro", data=dict(
            rol="tecnico", nombre="Juan", correo="juan@ejemplo.com",
            password=PASSWORD, password2=PASSWORD,
        ))
        self.assertIn("al menos un servicio", r.get_data(as_text=True))

    def test_tecnico_edita_sus_servicios_y_zona(self):
        tecnico = self.registrar("tecnico", "juan@ejemplo.com", categorias=[PLOMERIA])
        r = tecnico.post("/perfil", data=dict(
            nombre="Juan Pérez", telefono="6180000002", zona_id=NUEVO_DURANGO,
            descripcion="Plomería y electricidad",
            categorias=[PLOMERIA, ELECTRICIDAD],
        ))
        self.assertEqual(r.status_code, 302)
        with self.app.app_context():
            t = Tecnico.query.first()
            self.assertEqual(t.categorias_texto, "Electricidad, Plomería")
            self.assertEqual(t.zona_id, int(NUEVO_DURANGO))

    def test_cliente_no_entra_al_perfil_de_tecnico(self):
        cliente = self.registrar("cliente", "ana@ejemplo.com")
        self.assertEqual(cliente.get("/perfil").status_code, 302)


# =========================================================
# SPRINT 2: BÚSQUEDA Y SOLICITUDES
# =========================================================

class PruebasSolicitudes(PruebaBase):

    def setUp(self):
        super().setUp()
        self.plomero = self.registrar(
            "tecnico", "juan@ejemplo.com", zona=CENTRO,
            categorias=[PLOMERIA], telefono="6180000002")
        self.electricista = self.registrar(
            "tecnico", "lalo@ejemplo.com", zona=NUEVO_DURANGO,
            categorias=[ELECTRICIDAD])
        self.cliente = self.registrar(
            "cliente", "maria@ejemplo.com", zona=CENTRO, telefono="6180000001")

    def test_busqueda_filtra_por_servicio_y_zona(self):
        html = self.cliente.get(
            f"/buscar?categoria_id={PLOMERIA}&zona_id={CENTRO}").get_data(as_text=True)
        self.assertIn("Juan", html)
        self.assertNotIn("Lalo", html)

    def test_tecnico_no_puede_buscar(self):
        self.assertEqual(self.plomero.get("/buscar").status_code, 302)

    def test_solicitud_valida_se_guarda_pendiente(self):
        r = self.solicitar(self.cliente)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.estado(1), "pendiente")

    def test_no_se_acepta_fecha_pasada(self):
        r = self.solicitar(self.cliente, dias=-1)
        self.assertIn("anterior a hoy", r.get_data(as_text=True))

    def test_no_se_pide_servicio_que_el_tecnico_no_ofrece(self):
        r = self.solicitar(self.cliente, categoria=ELECTRICIDAD)
        self.assertIn("servicios que ofrece", r.get_data(as_text=True))

    def test_flujo_completo_de_estados(self):
        self.solicitar(self.cliente)
        for accion, esperado in [("aceptar", "aceptado"),
                                 ("en_camino", "en_camino"),
                                 ("terminar", "terminado")]:
            self.plomero.post("/solicitud/1/estado", data=dict(accion=accion))
            self.assertEqual(self.estado(1), esperado)

    def test_tecnico_rechaza_solicitud(self):
        self.solicitar(self.cliente)
        self.plomero.post("/solicitud/1/estado", data=dict(accion="rechazar"))
        self.assertEqual(self.estado(1), "rechazado")

    def test_no_se_puede_saltar_estados(self):
        self.solicitar(self.cliente)
        self.plomero.post("/solicitud/1/estado", data=dict(accion="terminar"))
        self.assertEqual(self.estado(1), "pendiente")

    def test_otro_tecnico_no_cambia_la_solicitud(self):
        self.solicitar(self.cliente)
        self.electricista.post("/solicitud/1/estado", data=dict(accion="aceptar"))
        self.assertEqual(self.estado(1), "pendiente")

    def test_otro_cliente_no_ve_la_solicitud(self):
        self.solicitar(self.cliente)
        otro = self.registrar("cliente", "pepe@ejemplo.com")
        self.assertEqual(otro.get("/solicitud/1").status_code, 302)

    def test_telefono_visible_solo_al_aceptar(self):
        self.solicitar(self.cliente)
        self.assertNotIn("6180000002", self.cliente.get("/solicitud/1").get_data(as_text=True))
        self.plomero.post("/solicitud/1/estado", data=dict(accion="aceptar"))
        self.assertIn("6180000002", self.cliente.get("/solicitud/1").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
