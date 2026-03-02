"""
Script de configuración inicial para producción.
Ejecutar desde cPanel → Setup Python App → Execute python script:
  /home/padacicl/padaci/create_admin.py
"""
import os
import sys
import django
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padaci.settings')
django.setup()

from accounts.models import CustomUser

USERNAME = 'admin'
EMAIL    = 'admin@padaci.cl'
PASSWORD = 'Padaci2026!'

if CustomUser.objects.filter(username=USERNAME).exists():
    print(f'[OK] El usuario "{USERNAME}" ya existe.')
else:
    CustomUser.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD,
        first_name='Admin',
        last_name='PADACI',
    )
    print(f'[OK] Superusuario "{USERNAME}" creado con contraseña "{PASSWORD}".')
    print('[!] Cambia la contraseña en /admin/ después del primer login.')
