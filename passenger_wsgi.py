import sys
import os

sys.path.insert(0, '/home/padacicl/repositories/padaci')
os.environ['DJANGO_SETTINGS_MODULE'] = 'padaci.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
