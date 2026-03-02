"""
Phusion Passenger WSGI entry point para cPanel Python App.
Este archivo es utilizado por Passenger para servir la aplicación Django.
"""
import sys
import os
from pathlib import Path

# Directorio raíz del proyecto
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

# Módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padaci.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
