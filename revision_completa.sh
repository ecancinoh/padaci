#!/bin/bash
LOG=/home/padacicl/repositories/padaci/tmp/revision_completa.log
echo "===== REVISION COMPLETA $(date) =====" > $LOG

echo -e "\n=== 1. CONTENIDO EXACTO passenger_wsgi.py ===" >> $LOG
cat /home/padacicl/repositories/padaci/passenger_wsgi.py >> $LOG 2>&1

echo -e "\n=== 2. CONTENIDO EXACTO wsgi_app.py ===" >> $LOG
cat /home/padacicl/repositories/padaci/wsgi_app.py >> $LOG 2>&1

echo -e "\n=== 3. CONTENIDO public_html ===" >> $LOG
ls -la /home/padacicl/public_html/ >> $LOG 2>&1

echo -e "\n=== 4. CONTENIDO .htaccess ===" >> $LOG
cat /home/padacicl/public_html/.htaccess >> $LOG 2>&1

echo -e "\n=== 5. GIT STATUS ===" >> $LOG
cd /home/padacicl/repositories/padaci && /usr/local/cpanel/3rdparty/bin/git status >> $LOG 2>&1

echo -e "\n=== 6. GIT LOG ULTIMOS COMMITS ===" >> $LOG
cd /home/padacicl/repositories/padaci && /usr/local/cpanel/3rdparty/bin/git log --oneline -5 >> $LOG 2>&1

echo -e "\n=== 7. PERMISOS DIRECTORIOS CLAVE ===" >> $LOG
ls -la /home/padacicl/ | grep -E "repositories|public_html|virtualenv" >> $LOG 2>&1
ls -la /home/padacicl/repositories/ >> $LOG 2>&1

echo -e "\n=== 8. TEST DJANGO WSGI COMPLETO ===" >> $LOG
cd /home/padacicl/repositories/padaci && /home/padacicl/virtualenv/repositories/padaci/3.11/bin/python -c "
import sys, os, traceback
sys.path.insert(0, '/home/padacicl/repositories/padaci')
os.environ['DJANGO_SETTINGS_MODULE'] = 'padaci.settings'
try:
    from django.core.wsgi import get_wsgi_application
    app = get_wsgi_application()
    print('DJANGO WSGI: OK')
except Exception as e:
    print('DJANGO WSGI ERROR:', e)
    traceback.print_exc()
" >> $LOG 2>&1

echo -e "\n=== 9. TEST wsgi_app.py ===" >> $LOG
cd /home/padacicl/repositories/padaci && /home/padacicl/virtualenv/repositories/padaci/3.11/bin/python wsgi_app.py >> $LOG 2>&1

echo -e "\n=== 10. VARIABLES DE ENTORNO PASSENGER ===" >> $LOG
env | grep -i passenger >> $LOG 2>&1

echo -e "\n=== 11. LIMPIAR CACHE LITESPEED ===" >> $LOG
touch /home/padacicl/repositories/padaci/tmp/restart.txt >> $LOG 2>&1
echo "restart.txt touched" >> $LOG

echo -e "\n=== FIN REVISION ===" >> $LOG
