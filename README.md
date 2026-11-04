# ServiFácil — Servicios a domicilio

Aplicación web que conecta a **clientes** que necesitan un servicio en casa
(plomería, electricidad, limpieza, jardinería, carpintería, pintura) con
**técnicos** de su zona en Victoria de Durango, Dgo. Lleva el control de cada
solicitud desde que se pide hasta que se califica.

**Aplicación en línea:** https://servifacil.onrender.com

| | |
|---|---|
| **Integrantes** | Oswaldo Alonso Campos Ríos, Ricardo Enríquez, Rodrigo Durán |
| **Asignatura** | Programación / Desarrollo Web |
| **Docente** | Rubén Pizarro Gurrola |
| **Grupo** | 8W — 8.º semestre |

> ServiFácil es una empresa ficticia; el proyecto es académico.

## Cómo probarla

**En línea:** abrir https://servifacil.onrender.com. Si el servicio estaba dormido,
la primera carga tarda cerca de un minuto.

**En una computadora con Windows:** descargar el proyecto y dar doble clic en
`iniciar.bat`. Requiere Python e internet la primera vez; el navegador se abre solo.

La aplicación ya trae datos de ejemplo. Todas estas cuentas son ficticias y usan la
contraseña `demo1234`:

| Rol | Correo | Nombre |
|-----|--------|--------|
| Cliente | `cliente@servifacil.test` | María López |
| Técnico | `tecnico@servifacil.test` | Jorge Ramírez |

También existen `cliente2` y `cliente3`, y `tecnico2`, `tecnico3` y `tecnico4`, con
el mismo dominio. El administrador es `admin@servifacil.com`; con `iniciar.bat` su
contraseña es `admin1234`, y en línea la proporciona el equipo.

Para ver un servicio de principio a fin, entrar con cada cuenta en un navegador
distinto o en una ventana de incógnito: Jorge ya tiene una solicitud **Pendiente**
de María y ella tiene un servicio **Terminado** por calificar.

## Características

### Cliente
- Registro e inicio de sesión.
- Búsqueda de técnicos por servicio y zona, con foto y calificación; los mejor
  calificados salen primero.
- Solicitud de servicio con fecha, dirección y descripción.
- Seguimiento del estado de cada solicitud.
- Cancelación de una solicitud mientras está pendiente.
- Calificación de 1 a 5 estrellas con comentario al terminar el servicio.
- Historial de servicios terminados, rechazados y cancelados.

### Técnico
- Registro con los servicios que ofrece.
- Perfil editable: foto, teléfono, zona, servicios y descripción.
- Panel con solicitudes nuevas, servicios en curso y terminados.
- Aceptar o rechazar solicitudes y avanzar su estado.
- Consulta de su promedio y de las reseñas de sus clientes.

### Administrador
- Resumen de usuarios y solicitudes por estado.
- Catálogos: agregar, editar, activar y desactivar categorías y zonas.
- Usuarios: suspender y reactivar cuentas.
- Reseñas: ocultar o mostrar reseñas; las ocultas no cuentan para el promedio.
- Reportes: resumen general, servicios por categoría, técnicos mejor calificados
  y solicitudes por zona.

## Cómo funciona

### Flujo del servicio

1. El **técnico** se registra, elige sus servicios y completa su perfil.
2. El **cliente** se registra, entra a *Pedir servicio*, filtra por servicio y
   zona y da clic en *Solicitar* en el técnico que prefiera.
3. El cliente llena el servicio, la fecha, la dirección y lo que necesita. La
   solicitud queda **Pendiente**.
4. El técnico la ve en *Mi panel* y la **acepta** o la **rechaza**. Al aceptar,
   cada uno puede ver el teléfono del otro.
5. El técnico marca *Voy en camino* y después *Marcar terminado*.
6. El cliente **califica** el servicio, que queda en su **historial**. La reseña
   aparece en el panel del técnico y actualiza su promedio.

### Estados de una solicitud

```text
Pendiente ──► Aceptado ──► En camino ──► Terminado ──► (calificación)
    │
    ├──► Rechazado   (lo decide el técnico)
    └──► Cancelado   (lo decide el cliente)
```

Los estados solo avanzan en ese orden y únicamente los cambia el técnico asignado.

### Reglas principales

- Solo se puede pedir un servicio que el técnico ofrece, con fecha de hoy en
  adelante.
- Una solicitud solo la ven el cliente que la hizo, el técnico asignado y el
  administrador.
- Un servicio se califica una sola vez, solo cuando está terminado y solo por el
  cliente que lo pidió.
- Una cuenta suspendida no puede iniciar sesión; si es de un técnico, deja de
  aparecer en la búsqueda.
- Las categorías y zonas no se borran, se desactivan, para conservar las
  solicitudes anteriores.

## Tecnologías

| Parte | Herramienta |
|-------|-------------|
| Backend | Python, Flask, Jinja2 |
| Datos | Flask-SQLAlchemy; PostgreSQL en la nube y SQLite en local |
| Sesiones y seguridad | Flask-Login, Flask-WTF (CSRF), hash de Werkzeug |
| Interfaz | HTML5, CSS3, Bootstrap 5 y `static/css/estilos.css` |
| Despliegue | Render, Gunicorn |
| Control de versiones | Git y GitHub |
| Pruebas | `unittest` |

## Arquitectura

```text
Navegador ──HTTPS──► Render ──► Gunicorn + Flask ──► PostgreSQL (Render)
                                      │
                                      └── plantillas Jinja2 + Bootstrap
```

## Base de datos

| Tabla | Contenido | Relaciones |
|-------|-----------|------------|
| `usuarios` | Cuenta, rol y si está activa | Base de clientes y técnicos |
| `clientes` | Teléfono y zona | 1 a 1 con `usuarios` |
| `tecnicos` | Teléfono, zona y descripción | 1 a 1 con `usuarios` |
| `fotos_tecnicos` | Imagen del técnico | 1 a 1 con `tecnicos` |
| `categorias` | Tipos de servicio | N a N con `tecnicos` |
| `tecnico_categoria` | Servicios de cada técnico | Une `tecnicos` y `categorias` |
| `zonas` | Colonias y ciudades con servicio | Clientes, técnicos y solicitudes |
| `solicitudes` | Fecha, dirección, descripción y estado | 1 cliente, 1 técnico, 1 categoría, 1 zona |
| `calificaciones` | Estrellas, comentario y si es visible | 1 a 1 con `solicitudes` |

Las tablas, las zonas, las categorías iniciales y el administrador se crean solos
al arrancar. `app/migraciones.py` agrega a las tablas existentes las columnas que
se sumaron después. `app/demo.py` carga una sola vez las cuentas y solicitudes de
ejemplo; la variable `DEMO_DATOS=0` lo desactiva.

## Estructura del proyecto

```text
servifacil/
├── run.py                   # punto de entrada
├── config.py                # configuración y variables de entorno
├── render.yaml              # despliegue en Render
├── iniciar.bat              # inicia la app en Windows con doble clic
├── requirements.txt
├── app/
│   ├── __init__.py          # crea la aplicación y registra los módulos
│   ├── models.py            # tablas y datos iniciales
│   ├── migraciones.py       # columnas nuevas en tablas existentes
│   ├── demo.py              # cuentas y solicitudes de ejemplo
│   ├── validaciones.py      # largos, correo y rutas internas
│   ├── decoradores.py       # rol_requerido()
│   ├── fechas.py            # fechas en hora de Durango
│   ├── auth/routes.py       # registro, inicio y cierre de sesión
│   ├── main/routes.py       # inicio y paneles por rol
│   ├── servicios/routes.py  # perfil, búsqueda, solicitudes y calificaciones
│   ├── admin/routes.py      # catálogos, usuarios, reseñas y reportes
│   ├── templates/           # páginas Jinja2
│   └── static/css/          # hoja de estilos
└── tests/
    └── test_servifacil.py   # pruebas automáticas
```

## Rutas

| Ruta | Quién | Para qué sirve |
|------|-------|----------------|
| `/` | Todos | Página de inicio |
| `/registro`, `/login`, `/logout` | Todos | Cuenta y sesión |
| `/dashboard` | Con sesión | Panel según el rol |
| `/perfil` | Técnico | Editar foto, servicios, zona y contacto |
| `/tecnico/<id>/foto` | Con sesión | Foto del técnico |
| `/buscar` | Cliente | Buscar técnicos por servicio y zona |
| `/solicitar/<id>` | Cliente | Mandar una solicitud a un técnico |
| `/solicitud/<id>` | Cliente, técnico, admin | Detalle y seguimiento |
| `/solicitud/<id>/estado` | Técnico | Aceptar, rechazar o avanzar el estado |
| `/solicitud/<id>/cancelar` | Cliente | Cancelar una solicitud pendiente |
| `/solicitud/<id>/calificar` | Cliente | Calificar un servicio terminado |
| `/historial` | Cliente | Servicios terminados, rechazados y cancelados |
| `/admin/catalogos` | Admin | Categorías y zonas |
| `/admin/usuarios` | Admin | Suspender o reactivar cuentas |
| `/admin/resenas` | Admin | Ocultar o mostrar reseñas |
| `/admin/reportes` | Admin | Reportes de uso |

## Instalación en local

Requiere Python 3.13 o superior.

```powershell
git clone https://github.com/LxArmitage/servifacil.git
cd servifacil
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:ADMIN_PASSWORD = "elige-una-contraseña"   # crea al administrador
python run.py
```

Abrir http://127.0.0.1:5000/. Sin `DATABASE_URL` la aplicación usa SQLite en
`instance/servifacil.db`. El administrador entra con `admin@servifacil.com` y la
contraseña de `ADMIN_PASSWORD`; clientes y técnicos se crean en *Registrarse*.

## Pruebas automáticas

```powershell
python -m unittest discover -s tests -v
```

Son 51 pruebas de registro, perfil, solicitudes, estados, calificaciones, foto,
administración, seguridad y datos de ejemplo. Usan una base de datos en memoria.

## Despliegue en Render

`render.yaml` crea la base de datos PostgreSQL y el servicio web y los conecta:

1. En https://dashboard.render.com: **New → Blueprint**.
2. Conectar este repositorio.
3. Escribir el valor de `ADMIN_PASSWORD` cuando Render lo pida.
4. Esperar a que la base quede *Available* y el servicio *Live*.

Cada cambio en la rama `main` se despliega de forma automática.

| Variable | Para qué | En Render |
|----------|----------|-----------|
| `DATABASE_URL` | Conexión a PostgreSQL | La llena el Blueprint |
| `SECRET_KEY` | Firmar las sesiones | Se genera al azar |
| `ADMIN_PASSWORD` | Contraseña del administrador | Se escribe al crear el Blueprint |
| `ADMIN_CORREO` | Correo del administrador (opcional) | `admin@servifacil.com` |

## Seguridad

- Contraseñas guardadas con hash; las claves viven en variables de entorno.
- Protección CSRF en todos los formularios.
- Cookie de sesión HttpOnly, SameSite=Lax y Secure en la nube.
- Permisos revisados en el servidor según el rol y el dueño de cada solicitud.
- Validación en el servidor de campos, largos, fechas y tipo real de las imágenes.
- Consultas mediante ORM, sin SQL armado con datos del usuario.

## Limitaciones

- En el plan gratuito de Render el servicio se duerme tras 15 minutos sin visitas;
  la primera visita después puede tardar cerca de un minuto.
- Fuera del alcance de esta versión: pagos en línea, aplicación móvil, chat en
  tiempo real y ubicación por GPS.
