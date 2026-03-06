"""
WSGI config for padaci project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import traceback
from pathlib import Path

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padaci.settings')


def _write_probe(message: str) -> None:
	base_dir = Path(__file__).resolve().parent.parent
	for path in [
		base_dir / 'tmp' / 'wsgi_probe.log',
		base_dir / 'wsgi_probe.log',
		Path('/tmp/padaci_wsgi_probe.log'),
	]:
		try:
			path.parent.mkdir(parents=True, exist_ok=True)
			with open(path, 'a', encoding='utf-8') as probe:
				probe.write(message + '\n')
			break
		except Exception:
			continue


def _fallback_application(environ, start_response):
	body = b'PADACI project wsgi fallback active. Check /tmp/padaci_passenger_wsgi_error.log'
	start_response('503 Service Unavailable', [('Content-Type', 'text/plain'), ('Content-Length', str(len(body)))])
	return [body]

try:
	_write_probe('padaci/wsgi.py loaded')
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
	_write_probe('padaci/wsgi.py failed; fallback application enabled')
	application = _fallback_application
