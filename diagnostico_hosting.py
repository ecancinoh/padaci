"""
Diagnostico rapido para cPanel (Setup Python App -> Execute python script).
Imprime informacion clave y tambien guarda un reporte en archivo para evitar
recortes de salida en la interfaz de cPanel.
"""
import os
import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LINES = []


def out(text: str = "") -> None:
    LINES.append(text)
    print(text, flush=True)


def persist_report() -> None:
    report = "\n".join(LINES) + "\n"
    report_paths = [
        BASE_DIR / "tmp" / "diagnostico_hosting.log",
        BASE_DIR / "diagnostico_hosting.log",
        Path("/tmp/padaci_diagnostico_hosting.log"),
    ]
    for path in report_paths:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report, encoding="utf-8")
            out(f"REPORTE_GUARDADO={path}")
            return
        except Exception as exc:
            out(f"WARN no se pudo escribir {path}: {exc}")


try:
    out("=== PADACI Hosting Diagnostico ===")
    out(f"BASE_DIR={BASE_DIR}")
    out(f"PYTHON={sys.executable}")
    out(f"VERSION={sys.version}")
    out(f"CWD={Path.cwd()}")

    out("\n--- PATH (primeras 20 entradas) ---")
    for idx, p in enumerate(sys.path[:20], 1):
        out(f"{idx}. {p}")

    out("\n--- ENV CLAVE ---")
    for key in [
        "DJANGO_SETTINGS_MODULE",
        "SECRET_KEY",
        "DEBUG",
        "ALLOWED_HOSTS",
        "DB_NAME",
        "DB_USER",
        "DB_HOST",
        "DB_PORT",
    ]:
        value = os.getenv(key)
        if value and key in {"SECRET_KEY"}:
            out(f"{key}=***set***")
        else:
            out(f"{key}={value}")

    out("\n--- Import checks ---")
    for module in ["django", "decouple", "pymysql", "MySQLdb"]:
        try:
            __import__(module)
            out(f"OK import {module}")
        except Exception as exc:
            out(f"FAIL import {module}: {exc}")

    out("\n--- Django setup ---")
    try:
        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "padaci.settings")

        import django
        from django.conf import settings

        django.setup()
        out(f"OK django.setup() - version {django.get_version()}")
        out(f"SETTINGS.DEBUG={settings.DEBUG}")
        out(f"SETTINGS.ALLOWED_HOSTS={settings.ALLOWED_HOSTS}")
    except Exception:
        out("FAIL django.setup()")
        out(traceback.format_exc())

    out("\n--- WSGI load ---")
    try:
        from django.core.wsgi import get_wsgi_application

        app = get_wsgi_application()
        out(f"OK get_wsgi_application() => {app}")
    except Exception:
        out("FAIL get_wsgi_application()")
        out(traceback.format_exc())

    out("\n--- Database check ---")
    try:
        from django.conf import settings
        from django.db import connections

        db = settings.DATABASES.get("default", {})
        out(
            "DB_RESUELTA="
            f"ENGINE={db.get('ENGINE')} "
            f"NAME={db.get('NAME')} "
            f"USER={db.get('USER')} "
            f"HOST={db.get('HOST')} "
            f"PORT={db.get('PORT')}"
        )

        conn = connections["default"]
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
        out(f"OK DB connect SELECT 1 => {row}")
    except Exception:
        out("FAIL DB connect")
        out(traceback.format_exc())

    out("\n--- Request checks ---")
    try:
        from django.conf import settings
        from django.test import Client
        from django.test.utils import override_settings

        hosts = list(settings.ALLOWED_HOSTS)
        if "testserver" not in hosts:
            hosts.append("testserver")

        with override_settings(ALLOWED_HOSTS=hosts):
            client = Client()
            for path in ["/", "/accounts/login/", "/admin/"]:
                try:
                    response = client.get(path)
                    out(f"REQ {path} => status={response.status_code}")
                except Exception:
                    out(f"FAIL request {path}")
                    out(traceback.format_exc())
    except Exception:
        out("FAIL request checks setup")
        out(traceback.format_exc())

    out("=== FIN DIAGNOSTICO ===")
finally:
    persist_report()
