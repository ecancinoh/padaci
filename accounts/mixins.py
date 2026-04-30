from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect


ROLES_RESTRINGIDOS = {'conductor', 'peoneta'}
ROLES_ADMIN_SUPERVISOR = {'admin', 'supervisor'}


class RolRestringidoMixin(AccessMixin):
    """Bloquea el acceso a usuarios con rol Conductor o Peoneta."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.rol in ROLES_RESTRINGIDOS:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


class AdminSupervisorMixin(AccessMixin):
    """Permite acceso solo a administradores y supervisores."""

    allowed_roles = ROLES_ADMIN_SUPERVISOR

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.rol not in self.allowed_roles:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


def rol_restringido(view_func):
    """Decorador equivalente a RolRestringidoMixin para vistas basadas en función."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if request.user.rol in ROLES_RESTRINGIDOS:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_supervisor_required(view_func):
    """Decorador para vistas basadas en función con acceso admin/supervisor."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        if request.user.rol not in ROLES_ADMIN_SUPERVISOR:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)

    return wrapper
