# ServiFácil — Plataforma web de servicios a domicilio

Proyecto de Desarrollo Web (Flask). ServiFácil conecta a **clientes** que
necesitan un servicio en casa (plomería, electricidad, limpieza, jardinería…)
con **técnicos** disponibles cerca de su zona.

> Integrantes: Oswaldo Alonso Campos Ríos, Rodrigo Durán, Ricardo Enríquez.

## Sprint 1 (este incremento)

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

Pendiente para siguientes sprints: solicitudes de servicio, aceptación por el
técnico, estados, calificaciones e historial.

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
    ├── models.py          # Usuario, Cliente, Tecnico, Zona
    ├── auth/routes.py     # registro, login, logout
    ├── main/routes.py     # inicio y paneles por rol
    ├── templates/         # base, index, auth/, main/
    └── static/css/
```

## Ejecutar en local

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Abrir: http://127.0.0.1:5000/

**Administrador de prueba:** correo `admin@servifacil.com` / contraseña `admin123`.
Los clientes y técnicos se crean desde la página de registro.

## Despliegue en la nube (Render)

- **Build:** `pip install -r requirements.txt`
- **Start:** `gunicorn run:app`
- Variables: `SECRET_KEY` y `DATABASE_URL` (base PostgreSQL de Render).
