"""
WSGI config for padaci project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import traceback

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padaci.settings')

try:
	application = get_wsgi_application()
except Exception:
	# Fallback logging for hosts that invoke this module directly.
	for log_path in [
		os.path.join(os.path.dirname(os.path.dirname(__file__)), 'passenger_wsgi_error.log'),
		os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tmp', 'passenger_wsgi_error.log'),
		'/tmp/padaci_passenger_wsgi_error.log',
	]:
		try:
			os.makedirs(os.path.dirname(log_path), exist_ok=True)
			with open(log_path, 'a', encoding='utf-8') as error_log:
				error_log.write('\n=== padaci.wsgi startup error ===\n')
				error_log.write(traceback.format_exc())
			break
		except Exception:
			continue
	raise
