# ServiFácil — Plataforma web de servicios a domicilio

Proyecto de Desarrollo Web (Flask). ServiFácil conecta a **clientes** que
necesitan un servicio en casa (plomería, electricidad, limpieza, jardinería…)
con **técnicos** disponibles cerca de su zona.

> Integrantes: Oswaldo Alonso Campos Ríos, Rodrigo Durán, Ricardo Enríquez.

## Sprint 1

Corresponde al **Incremento 1** del anteproyecto: *estructura del proyecto,
navegación y autenticación*. Incluye:

- Estructura de proyecto Flask con **blueprints** (`auth` y `main`), pensada
  para crecer en los siguientes sprints.
- **Registro** de usuarios como **cliente** o **técnico** (con teléfono y zona;
  los técnicos agregan una descripción).
- **Inicio y cierre de sesión** con contraseñas cifradas (Flask-Login +
  hashing de Werkzeug).
- **Roles**: cliente, técnico y administrador, con **panel diferenciado** por
  rol y navegación que cambia según la sesión.
- Página de inicio (landing) y base de datos con **SQLAlchemy**.
- Datos iniciales automáticos: zonas de la ciudad y un usuario administrador.

## Sprint 2

Corresponde al **Incremento 2** del anteproyecto: *funciones centrales y
persistencia*. Incluye:

- **Categorías de servicio** (plomería, electricidad, limpieza, jardinería,
  carpintería y pintura) y relación N a N `tecnico_categoria`.
- **Perfil del técnico**: elige sus servicios al registrarse y los edita en
  *Mi perfil* junto con su teléfono, zona y descripción.
- **Búsqueda** de técnicos por servicio y zona (página *Pedir servicio*).
- **Solicitud de servicio** con fecha, dirección y descripción, con
  validaciones (servicio que sí ofrece el técnico, fecha no anterior a hoy).
- El técnico **acepta o rechaza** y avanza el **estado**: pendiente →
  aceptado → en camino → terminado.
- Página de **seguimiento** de cada solicitud; los teléfonos se muestran
  hasta que el técnico acepta.
- El administrador ve las solicitudes y cuántas hay en cada estado.
- **Pruebas automáticas** con `unittest`.

## Sprint 3

Corresponde al **Incremento 3** del anteproyecto: *continuación de módulos y
reglas de negocio*. Incluye:

- **Calificaciones y reseñas**: al terminar el servicio, el cliente pone de 1 a
  5 estrellas y un comentario (una sola vez por solicitud).
- **Promedio de calificación** del técnico en la búsqueda (los mejor
  calificados salen primero), al solicitar y en su panel con las reseñas.
- **Historial** del cliente con sus servicios terminados y rechazados; su panel
  separa *solicitudes en proceso* y *servicios por calificar*.
- **Foto del técnico** guardada en la base de datos (tabla `fotos_tecnicos`),
  con validación del tipo de archivo y un máximo de 2 MB.
- 30 pruebas automáticas.

## Sprint 4 — Integración (este incremento)

Corresponde a la **Versión integrada** (semana 6 del anteproyecto):

- **Administración de catálogos**: agregar, editar, activar y desactivar
  categorías de servicio y zonas.
- **Usuarios**: el administrador suspende o reactiva cuentas; una cuenta
  suspendida no puede iniciar sesión y su técnico deja de aparecer.
- **Reseñas**: el administrador puede ocultar reseñas que no cumplan las
  reglas; las ocultas no cuentan para el promedio.
- **Reportes**: resumen general, servicios por categoría, técnicos mejor
  calificados y solicitudes por zona.
- El cliente puede **cancelar** una solicitud mientras está pendiente.
- **Seguridad**: protección CSRF, contraseña del administrador y SECRET_KEY en
  variables de entorno, cookie de sesión segura, validación de largos y de la
  redirección después del login.
- **Nube**: `render.yaml` para Render con PostgreSQL; `migraciones.py` agrega
  las columnas nuevas a bases de datos que ya existían.
- 47 pruebas automáticas.

## Tecnologías

- Python + Flask + Jinja2
- Flask-SQLAlchemy (ORM) y Flask-Login (sesiones)
- Bootstrap 5 (interfaz)
- Flask-WTF (protección CSRF en los formularios)
- Base de datos: **SQLite** en local; **PostgreSQL** en la nube (vía
  `DATABASE_URL`)

## Estructura

```text
servifacil/
├── run.py                 # punto de entrada
├── config.py              # configuración (SQLite / PostgreSQL)
├── requirements.txt
└── app/
    ├── __init__.py        # app factory (db, login, blueprints)
    ├── models.py          # Usuario, Cliente, Tecnico, Zona, Categoria, Solicitud,
    │                      # Calificacion, FotoTecnico
    ├── fechas.py          # fechas en hora de Durango
    ├── decoradores.py     # rol_requerido()
    ├── validaciones.py    # largos de campos, correo y rutas internas
    ├── migraciones.py     # agrega columnas nuevas a tablas existentes
    ├── admin/routes.py    # catálogos, usuarios, reseñas y reportes
    ├── auth/routes.py     # registro, login, logout
    ├── main/routes.py     # inicio y paneles por rol
    ├── servicios/routes.py  # perfil, búsqueda, solicitudes, estados, calificaciones,
    │                        # historial y foto
    ├── templates/         # base, index, auth/, main/, servicios/, admin/
    └── static/css/
tests/
└── test_servifacil.py     # pruebas automáticas
```

## Rutas

| Ruta | Quién | Para qué sirve |
|------|-------|----------------|
| `/` | Todos | Página de inicio |
| `/registro`, `/login`, `/logout` | Todos | Cuenta y sesión |
| `/dashboard` | Con sesión | Panel según el rol |
| `/perfil` | Técnico | Editar servicios, zona y contacto |
| `/buscar` | Cliente | Buscar técnicos por servicio y zona |
| `/solicitar/<id>` | Cliente | Mandar una solicitud a un técnico |
| `/solicitud/<id>` | Cliente, técnico, admin | Detalle y seguimiento |
| `/solicitud/<id>/estado` | Técnico | Aceptar, rechazar o avanzar el estado (POST) |
| `/solicitud/<id>/calificar` | Cliente | Calificar un servicio terminado (POST) |
| `/historial` | Cliente | Servicios terminados y rechazados |
| `/tecnico/<id>/foto` | Con sesión | Foto del técnico |
| `/solicitud/<id>/cancelar` | Cliente | Cancelar una solicitud pendiente (POST) |
| `/admin/catalogos` | Admin | Categorías y zonas |
| `/admin/usuarios` | Admin | Suspender o reactivar cuentas |
| `/admin/resenas` | Admin | Ocultar o mostrar reseñas |
| `/admin/reportes` | Admin | Reportes de uso |

## Ejecutar en local

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:ADMIN_PASSWORD = "una-contraseña-para-el-admin"   # solo la primera vez
python run.py
```

Abrir: http://127.0.0.1:5000/

El administrador (`admin@servifacil.com`) se crea al arrancar con la contraseña
de la variable `ADMIN_PASSWORD`; la contraseña no se guarda en el código. Los
clientes y técnicos se crean desde la página de registro.

## Pruebas automáticas

```powershell
python -m unittest discover -s tests -v
```

Usan una base de datos en memoria, así que no modifican `instance/servifacil.db`.

## Despliegue en la nube (Render + PostgreSQL)

El archivo `render.yaml` crea la base de datos PostgreSQL y la aplicación web y
las conecta solas:

1. En https://dashboard.render.com: **New → Blueprint**.
2. Conectar el repositorio `servifacil` de GitHub y aceptar.
3. Escribir el valor de `ADMIN_PASSWORD` cuando Render lo pida.
4. Esperar a que la base de datos quede *Available* y el servicio *Live*.

Variables de entorno que usa la aplicación:

| Variable | Para qué | En Render |
|----------|----------|-----------|
| `DATABASE_URL` | Conexión a PostgreSQL | La llena el Blueprint |
| `SECRET_KEY` | Firmar las sesiones | Se genera al azar |
| `ADMIN_PASSWORD` | Contraseña del administrador | La escribes tú |
| `ADMIN_CORREO` | Correo del administrador (opcional) | `admin@servifacil.com` |

En el plan gratuito el servicio se duerme tras 15 minutos sin visitas; la
primera visita después tarda alrededor de un minuto en responder.
