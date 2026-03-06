from pathlib import Path
from django.urls import path
from . import views

def _write_dashboard_probe(filename, message):
    base_dir = Path(__file__).resolve().parents[1]
    candidates = [
        base_dir / 'tmp' / filename,
        base_dir / filename,
        Path('/tmp') / filename,
    ]
    for path in candidates:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('a', encoding='utf-8') as f:
                f.write(message + '\n')
            return
        except Exception:
            continue


_write_dashboard_probe('dashboard_urls_loaded.log', 'dashboard/urls.py loaded')

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
]
