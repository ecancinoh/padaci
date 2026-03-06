import glob
import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

ERROR_LOG_PATH = os.path.join(BASE_DIR, "passenger_wsgi_error.log")


def _write_probe(message: str) -> None:
    for path in [
        os.path.join(BASE_DIR, "tmp", "wsgi_probe.log"),
        os.path.join(BASE_DIR, "wsgi_probe.log"),
        "/tmp/padaci_wsgi_probe.log",
    ]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as probe:
                probe.write(message + "\n")
            break
        except Exception:
            continue


def _fallback_application(environ, start_response):
    body = b"PADACI WSGI fallback active. Check /tmp/padaci_passenger_wsgi_error.log"
    start_response("503 Service Unavailable", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]


def _add_venv_site_packages() -> None:
    patterns = [
        os.path.join(BASE_DIR, "venv", "lib", "python*", "site-packages"),
        os.path.join(BASE_DIR, ".venv", "lib", "python*", "site-packages"),
    ]
    for pattern in patterns:
        for site_packages in glob.glob(pattern):
            if site_packages not in sys.path:
                sys.path.insert(0, site_packages)


try:
    _write_probe("wsgi_app.py loaded")
    _add_venv_site_packages()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "padaci.settings")

    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
except Exception:
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as error_log:
        error_log.write("\n=== WSGI app startup error ===\n")
        error_log.write(traceback.format_exc())
    _write_probe("wsgi_app.py failed; fallback application enabled")
    application = _fallback_application
