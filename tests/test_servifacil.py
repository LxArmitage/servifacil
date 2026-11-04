"""Pruebas automáticas de ServiFácil.

Ejecutar desde la carpeta del proyecto:
    python -m unittest discover -s tests -v

Cada prueba usa una base de datos SQLite en memoria, así que no toca
instance/servifacil.db.
"""
import io
import unittest
from datetime import timedelta

from config import Config
from app import create_app, db
from app.demo import PASSWORD_DEMO, SOLICITUDES, cargar_demo
from app.fechas import hoy_durango
from app.migraciones import agregar_columnas_faltantes
from app.models import (
    Calificacion, Categoria, FotoTecnico, Solicitud, Tecnico, Usuario, Zona,
)

PASSWORD = "secreto1"
PLOMERIA, ELECTRICIDAD = "1", "2"
CENTRO, NUEVO_DURANGO = "1", "3"


class ConfigPruebas(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ADMIN_PASSWORD = "admin-de-pruebas"
    DEMO_DATOS = False
    # El token CSRF se prueba aparte en PruebasSeguridad
    WTF_CSRF_ENABLED = False


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


# =========================================================
# SPRINT 3: CALIFICACIONES, PROMEDIO E HISTORIAL
# =========================================================

class PruebasCalificaciones(PruebaBase):

    def setUp(self):
        super().setUp()
        self.plomero = self.registrar(
            "tecnico", "juan@ejemplo.com", categorias=[PLOMERIA])
        self.cliente = self.registrar("cliente", "maria@ejemplo.com")
        self.solicitar(self.cliente)

    def terminar(self, solicitud_id=1, tecnico=None):
        for accion in ("aceptar", "en_camino", "terminar"):
            (tecnico or self.plomero).post(
                f"/solicitud/{solicitud_id}/estado", data=dict(accion=accion))

    def calificar(self, cliente=None, estrellas="5", comentario="Muy bien"):
        return (cliente or self.cliente).post(
            "/solicitud/1/calificar",
            data=dict(estrellas=estrellas, comentario=comentario))

    def total_calificaciones(self):
        with self.app.app_context():
            return Calificacion.query.count()

    def test_no_se_califica_un_servicio_sin_terminar(self):
        self.calificar()
        self.assertEqual(self.total_calificaciones(), 0)

    def test_cliente_califica_servicio_terminado(self):
        self.terminar()
        self.calificar(estrellas="4")
        with self.app.app_context():
            self.assertEqual(Tecnico.query.first().calificacion_resumen, (4.0, 1))

    def test_no_se_califica_dos_veces(self):
        self.terminar()
        self.calificar(estrellas="5")
        self.calificar(estrellas="1")
        self.assertEqual(self.total_calificaciones(), 1)

    def test_estrellas_fuera_de_rango(self):
        self.terminar()
        self.calificar(estrellas="6")
        self.assertEqual(self.total_calificaciones(), 0)

    def test_otro_cliente_no_puede_calificar(self):
        self.terminar()
        otro = self.registrar("cliente", "pepe@ejemplo.com")
        self.calificar(cliente=otro)
        self.assertEqual(self.total_calificaciones(), 0)

    def test_busqueda_ordena_por_calificacion(self):
        otro_plomero = self.registrar(
            "tecnico", "beto@ejemplo.com", categorias=[PLOMERIA])
        self.solicitar(self.cliente, tecnico_id=2)
        self.terminar(solicitud_id=2, tecnico=otro_plomero)
        self.cliente.post("/solicitud/2/calificar", data=dict(estrellas="5"))
        html = self.cliente.get(f"/buscar?categoria_id={PLOMERIA}").get_data(as_text=True)
        # Solo la tabla de resultados (arriba puede haber avisos con los nombres)
        tabla = html[html.index("<tbody>"):]
        # Beto tiene calificación y Juan no: Beto sale primero
        self.assertLess(tabla.index("Beto"), tabla.index("Juan"))

    def test_historial_muestra_terminados_y_rechazados(self):
        self.terminar()
        self.solicitar(self.cliente)
        self.plomero.post("/solicitud/2/estado", data=dict(accion="rechazar"))
        html = self.cliente.get("/historial").get_data(as_text=True)
        self.assertIn("estado-terminado", html)
        self.assertIn("estado-rechazado", html)


# =========================================================
# SPRINT 3: FOTO DEL TÉCNICO
# =========================================================

JPG_PRUEBA = b"\xff\xd8\xff\xe0" + b"0" * 100


class PruebasFotoTecnico(PruebaBase):

    def setUp(self):
        super().setUp()
        self.tecnico = self.registrar(
            "tecnico", "juan@ejemplo.com", categorias=[PLOMERIA])
        self.datos = dict(nombre="Juan", telefono="", zona_id=CENTRO,
                          descripcion="", categorias=[PLOMERIA])

    def subir(self, contenido, nombre="foto.jpg"):
        return self.tecnico.post(
            "/perfil", content_type="multipart/form-data",
            data={**self.datos, "foto": (io.BytesIO(contenido), nombre)})

    def total_fotos(self):
        with self.app.app_context():
            return FotoTecnico.query.count()

    def test_sube_foto_valida(self):
        self.subir(JPG_PRUEBA)
        respuesta = self.tecnico.get("/tecnico/1/foto")
        self.assertEqual(respuesta.headers["Content-Type"], "image/jpeg")
        self.assertEqual(respuesta.data, JPG_PRUEBA)

    def test_rechaza_archivo_que_no_es_imagen(self):
        r = self.subir(b"<html>no es una imagen</html>", nombre="foto.jpg")
        self.assertIn("JPG, PNG o WEBP", r.get_data(as_text=True))
        self.assertEqual(self.total_fotos(), 0)

    def test_rechaza_foto_de_mas_de_2_mb(self):
        r = self.subir(b"\xff\xd8\xff" + b"0" * (2 * 1024 * 1024 + 1))
        self.assertIn("2 MB", r.get_data(as_text=True))
        self.assertEqual(self.total_fotos(), 0)

    def test_quitar_foto(self):
        self.subir(JPG_PRUEBA)
        self.tecnico.post("/perfil", content_type="multipart/form-data",
                          data={**self.datos, "quitar_foto": "1"})
        self.assertEqual(self.total_fotos(), 0)


# =========================================================
# SEGURIDAD
# =========================================================

class ConfigConCSRF(ConfigPruebas):
    WTF_CSRF_ENABLED = True


class PruebasSeguridad(PruebaBase):

    def test_formulario_sin_token_csrf_es_rechazado(self):
        app = create_app(ConfigConCSRF)
        r = app.test_client().post("/registro", data=dict(
            rol="cliente", nombre="Ana", correo="ana@ejemplo.com",
            password=PASSWORD, password2=PASSWORD,
        ))
        self.assertEqual(r.status_code, 302)
        with app.app_context():
            self.assertEqual(Usuario.query.filter_by(rol="cliente").count(), 0)

    def test_login_ignora_next_de_otro_sitio(self):
        self.registrar("cliente", "ana@ejemplo.com")
        r = self.app.test_client().post(
            "/login?next=https://otro-sitio.com",
            data=dict(correo="ana@ejemplo.com", password=PASSWORD))
        self.assertEqual(r.headers["Location"], "/dashboard")

    def test_campo_demasiado_largo(self):
        r = self.app.test_client().post("/registro", data=dict(
            rol="cliente", nombre="A" * 121, correo="ana@ejemplo.com",
            password=PASSWORD, password2=PASSWORD,
        ))
        self.assertIn("no puede pasar de 120", r.get_data(as_text=True))

    def test_admin_se_crea_con_la_variable_de_entorno(self):
        r = self.app.test_client().post("/login", data=dict(
            correo="admin@servifacil.com", password="admin-de-pruebas"))
        self.assertEqual(r.status_code, 302)


# =========================================================
# ENTREGABLE 6: CANCELAR SOLICITUDES
# =========================================================

class PruebasCancelar(PruebaBase):

    def setUp(self):
        super().setUp()
        self.plomero = self.registrar(
            "tecnico", "juan@ejemplo.com", categorias=[PLOMERIA])
        self.cliente = self.registrar("cliente", "maria@ejemplo.com")
        self.solicitar(self.cliente)

    def test_cliente_cancela_solicitud_pendiente(self):
        self.cliente.post("/solicitud/1/cancelar")
        self.assertEqual(self.estado(1), "cancelado")

    def test_no_se_cancela_una_solicitud_aceptada(self):
        self.plomero.post("/solicitud/1/estado", data=dict(accion="aceptar"))
        self.cliente.post("/solicitud/1/cancelar")
        self.assertEqual(self.estado(1), "aceptado")

    def test_otro_cliente_no_cancela(self):
        otro = self.registrar("cliente", "pepe@ejemplo.com")
        otro.post("/solicitud/1/cancelar")
        self.assertEqual(self.estado(1), "pendiente")


# =========================================================
# ENTREGABLE 6: ADMINISTRACIÓN
# =========================================================

class PruebasAdministracion(PruebaBase):

    def setUp(self):
        super().setUp()
        self.admin = self.app.test_client()
        self.admin.post("/login", data=dict(
            correo="admin@servifacil.com", password="admin-de-pruebas"))

    def test_solo_el_administrador_entra(self):
        cliente = self.registrar("cliente", "maria@ejemplo.com")
        for ruta in ("/admin/catalogos", "/admin/usuarios",
                     "/admin/resenas", "/admin/reportes"):
            self.assertEqual(self.admin.get(ruta).status_code, 200)
            self.assertEqual(cliente.get(ruta).status_code, 302)

    def test_agregar_categoria(self):
        self.admin.post("/admin/categorias/nueva",
                        data=dict(nombre="Cerrajería", descripcion="Chapas"))
        with self.app.app_context():
            self.assertEqual(Categoria.query.filter_by(nombre="Cerrajería").count(), 1)

    def test_categoria_repetida(self):
        r = self.admin.post("/admin/categorias/nueva",
                            data=dict(nombre="plomería", descripcion=""))
        self.assertIn("Ya existe una categoría", r.get_data(as_text=True))

    def test_categoria_desactivada_no_aparece_en_el_registro(self):
        self.admin.post("/admin/categorias/6/estado")  # Pintura
        html = self.app.test_client().get("/registro").get_data(as_text=True)
        self.assertNotIn("Pintura", html)

    def test_zona_desactivada_no_aparece_en_el_registro(self):
        self.admin.post("/admin/zonas/nueva",
                        data=dict(nombre="Jardines", ciudad="Durango"))
        with self.app.app_context():
            zona_id = Zona.query.filter_by(nombre="Jardines").first().id
        self.admin.post(f"/admin/zonas/{zona_id}/estado")
        html = self.app.test_client().get("/registro").get_data(as_text=True)
        self.assertNotIn("Jardines", html)

    def test_cuenta_suspendida_no_puede_entrar(self):
        self.registrar("cliente", "maria@ejemplo.com")
        with self.app.app_context():
            usuario_id = Usuario.query.filter_by(correo="maria@ejemplo.com").first().id
        self.admin.post(f"/admin/usuarios/{usuario_id}/estado")
        r = self.app.test_client().post("/login", data=dict(
            correo="maria@ejemplo.com", password=PASSWORD))
        self.assertIn("suspendida", r.get_data(as_text=True))

    def test_no_se_suspende_al_administrador(self):
        self.admin.post("/admin/usuarios/1/estado")
        with self.app.app_context():
            self.assertTrue(db.session.get(Usuario, 1).activo)

    def test_resena_oculta_no_cuenta_en_el_promedio(self):
        plomero = self.registrar("tecnico", "juan@ejemplo.com", categorias=[PLOMERIA])
        cliente = self.registrar("cliente", "maria@ejemplo.com")
        self.solicitar(cliente)
        for accion in ("aceptar", "en_camino", "terminar"):
            plomero.post("/solicitud/1/estado", data=dict(accion=accion))
        cliente.post("/solicitud/1/calificar", data=dict(estrellas="1"))
        self.admin.post("/admin/resenas/1/visible")
        with self.app.app_context():
            self.assertEqual(Tecnico.query.first().calificacion_resumen, (None, 0))

    def test_reportes(self):
        html = self.admin.get("/admin/reportes").get_data(as_text=True)
        self.assertIn("Servicios por categoría", html)
        self.assertIn("Técnicos mejor calificados", html)


# =========================================================
# ENTREGABLE 6: COLUMNAS NUEVAS EN BASES DE DATOS EXISTENTES
# =========================================================

class PruebasMigraciones(PruebaBase):

    def test_agrega_columnas_que_faltan(self):
        from sqlalchemy import inspect, text
        with self.app.app_context():
            # Simula una base de datos creada antes del entregable 6
            db.session.execute(text("ALTER TABLE zonas DROP COLUMN activa"))
            db.session.commit()
            agregar_columnas_faltantes()
            columnas = {c["name"] for c in inspect(db.engine).get_columns("zonas")}
            self.assertIn("activa", columnas)
            self.assertTrue(Zona.query.first().activa)


class ConfigConDemo(ConfigPruebas):
    DEMO_DATOS = True


class PruebasDemo(PruebaBase):

    def setUp(self):
        self.app = create_app(ConfigConDemo)

    def entrar(self, correo, password=PASSWORD_DEMO):
        cliente = self.app.test_client()
        cliente.post("/login", data=dict(correo=correo, password=password))
        return cliente

    def test_crea_datos_una_sola_vez(self):
        with self.app.app_context():
            self.assertEqual(Solicitud.query.count(), len(SOLICITUDES))
            cargar_demo()
            self.assertEqual(Solicitud.query.count(), len(SOLICITUDES))

    def test_cada_servicio_lo_ofrece_su_tecnico(self):
        with self.app.app_context():
            for solicitud in Solicitud.query.all():
                self.assertIn(solicitud.categoria, solicitud.tecnico.categorias)

    def test_cuentas_entran_y_ven_sus_paginas(self):
        cliente = self.entrar("cliente@servifacil.test")
        self.assertEqual(cliente.get("/historial").status_code, 200)
        self.assertIn("Jorge Ramírez",
                      cliente.get("/buscar").get_data(as_text=True))
        tecnico = self.entrar("tecnico@servifacil.test")
        self.assertIn("Cambiar la llave de la regadera",
                      tecnico.get("/dashboard").get_data(as_text=True))

    def test_administrador_ve_reportes_con_datos(self):
        admin = self.entrar("admin@servifacil.com", "admin-de-pruebas")
        self.assertIn("Jorge Ramírez",
                      admin.get("/admin/reportes").get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
