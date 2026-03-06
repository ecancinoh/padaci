import traceback
from pathlib import Path
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
