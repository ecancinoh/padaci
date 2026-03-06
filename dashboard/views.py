from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from clients.models import Cliente
from companies.models import Empresa
from routes.models import RutaDia
from accounts.models import CustomUser


import traceback
import os

@login_required
def index(request):
    # Log at the very start of the view
    try:
        with open('/tmp/dashboard_index_start.log', 'a', encoding='utf-8') as f:
            f.write('dashboard index view STARTED\n')
    except Exception:
        pass
    """Dashboard principal enfocado en resumen operativo general."""
    try:
        hoy = timezone.localdate()

        total_clientes = Cliente.objects.filter(activo=True).count()
        total_empresas = Empresa.objects.filter(activa=True).count()
        total_conductores = CustomUser.objects.filter(rol='conductor', activo=True).count()

        ruta_hoy = RutaDia.objects.filter(fecha=hoy).select_related('conductor').first()

        ctx = {
            'hoy': hoy,
            'total_clientes': total_clientes,
            'total_empresas': total_empresas,
            'total_conductores': total_conductores,
            'ruta_hoy': ruta_hoy,
        }
        return render(request, 'dashboard/index.html', ctx)
    except Exception as e:
        # Log error to /tmp/dashboard_index_error.log
        try:
            with open('/tmp/dashboard_index_error.log', 'a', encoding='utf-8') as f:
                f.write(f"--- Exception in dashboard index view ---\n")
                f.write(traceback.format_exc())
                f.write("\n")
        except Exception:
            pass
        raise
