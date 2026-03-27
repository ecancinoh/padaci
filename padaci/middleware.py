import traceback
from pathlib import Path
from django.contrib import messages
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponseRedirect


class ExceptionFileLoggingMiddleware:
    """Log unhandled exceptions to file in shared hosting environments."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except (OperationalError, ProgrammingError) as exc:
            if self._is_pending_routes_migration_error(exc):
                self._write_log(request)
                # Avoid django.contrib.messages here because this middleware
                # runs before Session/Message middleware in settings.
                return HttpResponseRedirect('/dashboard/?db_migration_pending=1')
            self._write_log(request)
            raise
        except Exception:
            self._write_log(request)
            raise

    def _is_pending_routes_migration_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return (
            'peoneta_id' in text
            or 'routes_rutadia' in text
            or 'rendiciones_rendicionreparto' in text
            or ("doesn't exist" in text and 'rendiciones_' in text)
        )

    def _write_log(self, request) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        payload = (
            "\n=== Unhandled exception ===\n"
            f"path={request.path}\n"
            f"method={request.method}\n"
            + traceback.format_exc()
            + "\n"
        )

        log_paths = [
            base_dir / "tmp" / "runtime_errors.log",
            base_dir / "tmp" / "padaci_runtime_errors.log",
            base_dir / "runtime_errors.log",
            Path("/tmp/padaci_runtime_errors.log"),
        ]

        for log_path in log_paths:
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as handler:
                    handler.write(payload)
                break
            except Exception:
                continue


class RoleAccessMiddleware:
    """Role-based restrictions for supervisor users."""

    READONLY_BLOCKED_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
    MUTATION_GET_TOKENS = ('/nuevo/', '/nueva/', '/editar/', '/eliminar/', '/generar/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or getattr(user, 'rol', None) != 'supervisor':
            return self.get_response(request)

        path = request.path or '/'
        method = (request.method or 'GET').upper()

        if method in self.READONLY_BLOCKED_METHODS:
            return self._deny(request, 'Tu perfil supervisor tiene acceso solo de lectura.')

        if method == 'GET' and any(token in path for token in self.MUTATION_GET_TOKENS):
            return self._deny(request, 'No tienes permisos para acciones de creacion o edicion.')

        if path.startswith('/empresas/'):
            return self._deny(request, 'No tienes permisos para acceder a la seccion Empresas.')

        if path.startswith('/historial/'):
            return self._deny(request, 'No tienes permisos para acceder a la seccion Historial.')

        if path.startswith('/accounts/') and not self._is_allowed_accounts_path(path, user.pk):
            return self._deny(request, 'No tienes permisos para acceder a la seccion Usuarios.')

        return self.get_response(request)

    def _is_allowed_accounts_path(self, path: str, user_pk: int) -> bool:
        own_profile_slash = f'/accounts/{user_pk}/'
        own_profile_no_slash = f'/accounts/{user_pk}'
        allowed_paths = {
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/perfil/cambiar-password/',
            own_profile_slash,
            own_profile_no_slash,
        }
        return path in allowed_paths

    def _deny(self, request, message_text: str):
        messages.error(request, message_text)
        return HttpResponseRedirect('/dashboard/')
