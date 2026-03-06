import traceback
from pathlib import Path


class ExceptionFileLoggingMiddleware:
    """Log unhandled exceptions to file in shared hosting environments."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            self._write_log(request)
            raise

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
