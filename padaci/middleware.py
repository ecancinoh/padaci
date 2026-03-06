import traceback
from pathlib import Path
from django.contrib import messages
from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import redirect


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
                messages.error(
                    request,
                    'La base de datos del hosting esta desactualizada (falta migracion de rutas). '
                    'Ejecuta: python manage.py migrate routes',
                )
                return redirect('dashboard:index')
            self._write_log(request)
            raise
        except Exception:
            self._write_log(request)
            raise

    def _is_pending_routes_migration_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return 'peoneta_id' in text or 'routes_rutadia' in text

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
