import glob
import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# cPanel/Passenger can fail silently on import errors. This log captures startup issues.
ERROR_LOG_PATH = os.path.join(BASE_DIR, "passenger_wsgi_error.log")


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
    _add_venv_site_packages()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "padaci.settings")

    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
except Exception:
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as error_log:
        error_log.write("\n=== Passenger WSGI startup error ===\n")
        error_log.write(traceback.format_exc())
    raise
