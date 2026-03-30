from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render
from django.utils import timezone
from django.db.utils import OperationalError
from clients.models import Cliente
from companies.models import Empresa
from routes.models import RutaDia
from accounts.models import CustomUser


import traceback
from pathlib import Path


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

@login_required
def index(request):
    # Log at the very start of the view
    _write_dashboard_probe('dashboard_index_start.log', 'dashboard index view STARTED')
    """Dashboard principal enfocado en resumen operativo general."""
    try:
        if request.GET.get('db_migration_pending'):
            messages.warning(
                request,
                'La base de datos del hosting esta desactualizada. Ejecuta: python manage.py migrate routes',
            )

        hoy = timezone.localdate()

        total_clientes = Cliente.objects.filter(activo=True).count()
        total_clientes_sin_coordenadas = Cliente.objects.filter(activo=True).filter(latitud__isnull=True).count() + Cliente.objects.filter(activo=True).filter(longitud__isnull=True).exclude(latitud__isnull=True).count()
        total_empresas = Empresa.objects.filter(activa=True).count()
        total_conductores = CustomUser.objects.filter(rol='conductor', activo=True).count()

        ruta_hoy = None
        try:
            ruta_hoy = RutaDia.objects.filter(fecha=hoy).select_related('conductor').first()
        except OperationalError as db_error:
            # Temporary compatibility path when hosting DB is behind migrations.
            if "routes_rutadia.peoneta_id" in str(db_error):
                _write_dashboard_probe(
                    'dashboard_index_error.log',
                    'RutaDia query skipped: missing column routes_rutadia.peoneta_id. Run migrations on hosting.',
                )
            else:
                raise

        ctx = {
            'hoy': hoy,
            'total_clientes': total_clientes,
            'total_empresas': total_empresas,
            'total_conductores': total_conductores,
            'ruta_hoy': ruta_hoy,
            'total_clientes_sin_coordenadas': total_clientes_sin_coordenadas,
        }
        return render(request, 'dashboard/index.html', ctx)
    except Exception:
        _write_dashboard_probe('dashboard_index_error.log', '--- Exception in dashboard index view ---')
        _write_dashboard_probe('dashboard_index_error.log', traceback.format_exc())
        raise
