from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from clients.models import Cliente
from companies.models import Empresa
from routes.models import RutaDia
from accounts.models import CustomUser


@login_required
def index(request):
    """Dashboard principal enfocado en resumen operativo general."""
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
