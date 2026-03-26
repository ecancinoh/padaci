from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect


ROLES_RESTRINGIDOS = {'conductor', 'peoneta'}


class RolRestringidoMixin(AccessMixin):
    """Bloquea el acceso a usuarios con rol Conductor o Peoneta."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.rol in ROLES_RESTRINGIDOS:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


def rol_restringido(view_func):
    """Decorador equivalente a RolRestringidoMixin para vistas basadas en función."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if request.user.rol in ROLES_RESTRINGIDOS:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper
