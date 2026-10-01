from datetime import datetime, timedelta, timezone

# Durango usa UTC-6 todo el año (en México ya no hay horario de verano desde 2022).
# Las fechas se guardan en UTC y se muestran en hora de Durango.
HORA_DURANGO = timezone(timedelta(hours=-6), "Durango")


def ahora_utc():
    """Fecha y hora actual en UTC, sin zona horaria (así se guarda en la BD)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hoy_durango():
    """Fecha de hoy en Durango, aunque el servidor esté en otra zona horaria."""
    return datetime.now(HORA_DURANGO).date()


def fecha(valor):
    """Filtro de Jinja: 2026-10-08 -> 08/10/2026."""
    return valor.strftime("%d/%m/%Y") if valor else ""


def fecha_hora(valor):
    """Filtro de Jinja: fecha y hora guardadas en UTC -> hora de Durango."""
    if valor is None:
        return ""
    local = valor.replace(tzinfo=timezone.utc).astimezone(HORA_DURANGO)
    return local.strftime("%d/%m/%Y %H:%M")
