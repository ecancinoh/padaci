"""
Diagnostico rapido para cPanel (Setup Python App -> Execute python script).
Imprime informacion clave de entorno y prueba carga de Django/WSGI.
"""
import os
import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
print("=== PADACI Hosting Diagnostico ===")
print(f"BASE_DIR={BASE_DIR}")
print(f"PYTHON={sys.executable}")
print(f"VERSION={sys.version}")
print(f"CWD={Path.cwd()}")
print("\n--- PATH (primeras 10 entradas) ---")
for idx, p in enumerate(sys.path[:10], 1):
    print(f"{idx}. {p}")

print("\n--- ENV CLAVE ---")
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
    if value and key in {"SECRET_KEY", "DB_PASSWORD"}:
        print(f"{key}=***set***")
    else:
        print(f"{key}={value}")

print("\n--- Import checks ---")
for module in ["django", "decouple", "pymysql", "MySQLdb"]:
    try:
        __import__(module)
        print(f"OK import {module}")
    except Exception as exc:
        print(f"FAIL import {module}: {exc}")

print("\n--- Django setup ---")
try:
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "padaci.settings")

    import django

    django.setup()
    print(f"OK django.setup() - version {django.get_version()}")
except Exception:
    print("FAIL django.setup()")
    traceback.print_exc()

print("\n--- WSGI load ---")
try:
    from django.core.wsgi import get_wsgi_application

    app = get_wsgi_application()
    print(f"OK get_wsgi_application() => {app}")
except Exception:
    print("FAIL get_wsgi_application()")
    traceback.print_exc()

print("=== FIN DIAGNOSTICO ===")
