#!/bin/bash
LOG=/home/padacicl/repositories/padaci/tmp/diagnostico.log
echo "===== DIAGNOSTICO $(date) =====" > $LOG

echo -e "\n--- Python version ---" >> $LOG
/home/padacicl/virtualenv/repositories/padaci/3.11/bin/python --version >> $LOG 2>&1

echo -e "\n--- Permisos del directorio ---" >> $LOG
ls -la /home/padacicl/repositories/ >> $LOG 2>&1
ls -la /home/padacicl/repositories/padaci/ >> $LOG 2>&1

echo -e "\n--- passenger_wsgi.py contenido ---" >> $LOG
cat /home/padacicl/repositories/padaci/passenger_wsgi.py >> $LOG 2>&1

echo -e "\n--- Git status ---" >> $LOG
cd /home/padacicl/repositories/padaci && /usr/local/cpanel/3rdparty/bin/git status >> $LOG 2>&1

echo -e "\n--- Git checkout passenger_wsgi.py ---" >> $LOG
cd /home/padacicl/repositories/padaci && /usr/local/cpanel/3rdparty/bin/git checkout -- passenger_wsgi.py >> $LOG 2>&1

echo -e "\n--- Paquetes instalados ---" >> $LOG
/home/padacicl/virtualenv/repositories/padaci/3.11/bin/pip list >> $LOG 2>&1

echo -e "\n--- Instalar requirements ---" >> $LOG
/home/padacicl/virtualenv/repositories/padaci/3.11/bin/pip install -r /home/padacicl/repositories/padaci/requirements.txt >> $LOG 2>&1

echo -e "\n--- Test importar Django ---" >> $LOG
/home/padacicl/virtualenv/repositories/padaci/3.11/bin/python -c "import django; print('Django OK:', django.__version__)" >> $LOG 2>&1

echo -e "\n--- Test importar passenger_wsgi ---" >> $LOG
cd /home/padacicl/repositories/padaci && /home/padacicl/virtualenv/repositories/padaci/3.11/bin/python -c "
import sys
sys.path.insert(0, '/home/padacicl/repositories/padaci')
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'padaci.settings'
try:
    from django.core.wsgi import get_wsgi_application
    app = get_wsgi_application()
    print('WSGI OK')
except Exception as e:
    print('ERROR WSGI:', e)
    import traceback
    traceback.print_exc()
" >> $LOG 2>&1

echo -e "\n--- FIN DIAGNOSTICO ---" >> $LOG
