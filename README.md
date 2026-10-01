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

## Sprint 2 (este incremento)

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
- **Pruebas automáticas** con `unittest` (19 pruebas).

Pendiente para siguientes sprints: calificaciones y reseñas, historial del
cliente y administración de categorías y zonas.

## Tecnologías

- Python + Flask + Jinja2
- Flask-SQLAlchemy (ORM) y Flask-Login (sesiones)
- Bootstrap 5 (interfaz)
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
    ├── models.py          # Usuario, Cliente, Tecnico, Zona, Categoria, Solicitud
    ├── fechas.py          # fechas en hora de Durango
    ├── decoradores.py     # rol_requerido()
    ├── auth/routes.py     # registro, login, logout
    ├── main/routes.py     # inicio y paneles por rol
    ├── servicios/routes.py  # perfil del técnico, búsqueda, solicitudes y estados
    ├── templates/         # base, index, auth/, main/, servicios/
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

## Ejecutar en local

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Abrir: http://127.0.0.1:5000/

## Pruebas automáticas

```powershell
python -m unittest discover -s tests -v
```

Usan una base de datos en memoria, así que no modifican `instance/servifacil.db`.

**Administrador de prueba:** correo `admin@servifacil.com` / contraseña `admin123`.
Los clientes y técnicos se crean desde la página de registro.

## Despliegue en la nube (Render)

- **Build:** `pip install -r requirements.txt`
- **Start:** `gunicorn run:app`
- Variables: `SECRET_KEY` y `DATABASE_URL` (base PostgreSQL de Render).
