from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user, login_required


def rol_requerido(*roles):
    """Permite entrar a la vista solo a usuarios con alguno de los roles dados."""
    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(*args, **kwargs):
            if current_user.rol not in roles:
                flash("No tienes permiso para entrar a esa página.", "warning")
                return redirect(url_for("main.dashboard"))
            return vista(*args, **kwargs)
        return envoltura
    return decorador
