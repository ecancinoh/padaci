@echo off
echo ================================================
echo  PADACI - Sistema de Logistica de Entregas
echo ================================================
echo.

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Verificar si MySQL está disponible aplicando migraciones
echo [1/3] Aplicando migraciones...
python manage.py migrate
if %errorlevel% neq 0 (
    echo ERROR: Verifica que MySQL esté corriendo y que la BD padaci_db exista.
    echo Ejecuta setup_db.sql en MySQL primero.
    pause
    exit /b 1
)

REM Crear superusuario si no existe
echo.
echo [2/3] Verificando superusuario...
python -c "from accounts.models import CustomUser; CustomUser.objects.filter(is_superuser=True).exists() or CustomUser.objects.create_superuser('admin','admin@padaci.cl','admin123', first_name='Administrador', rol='admin')"

REM Iniciar servidor
echo.
echo [3/3] Iniciando servidor en http://127.0.0.1:8000
echo       Usuario: admin  |  Contraseña: admin123
echo.
python manage.py runserver
