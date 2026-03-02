from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from deliveries.models import Entrega
from clients.models import Cliente
from companies.models import Empresa
from routes.models import RutaDia
from history.models import HistorialDia
from accounts.models import CustomUser


@login_required
def index(request):
    """Dashboard principal con métricas del sistema."""
    hoy = timezone.localdate()

    # KPIs
    entregas_hoy = Entrega.objects.filter(fecha_programada=hoy)
    total_hoy = entregas_hoy.count()
    entregadas_hoy = entregas_hoy.filter(estado='entregado').count()
    pendientes_hoy = entregas_hoy.filter(estado__in=['pendiente', 'en_ruta']).count()
    fallidas_hoy = entregas_hoy.filter(estado='fallido').count()

    porcentaje_exito = round((entregadas_hoy / total_hoy * 100), 1) if total_hoy else 0

    # Totales generales
    total_clientes = Cliente.objects.filter(activo=True).count()
    total_empresas = Empresa.objects.filter(activa=True).count()
    total_conductores = CustomUser.objects.filter(rol='conductor', activo=True).count()

    # Entregas por estado (para gráfico)
    por_estado = list(
        Entrega.objects.values('estado').annotate(total=Count('id')).order_by('estado')
    )

    # Historial últimos 7 días (para gráfico de línea)
    ultimos_7 = list(
        HistorialDia.objects.order_by('-fecha')[:7].values(
            'fecha', 'total_entregas', 'entregadas', 'fallidas'
        )
    )
    ultimos_7.reverse()

    # Ruta de hoy
    ruta_hoy = RutaDia.objects.filter(fecha=hoy).select_related('conductor').first()

    # Últimas 10 entregas
    ultimas_entregas = Entrega.objects.select_related('cliente', 'empresa').order_by('-fecha_creacion')[:10]

    ctx = {
        'hoy': hoy,
        'total_hoy': total_hoy,
        'entregadas_hoy': entregadas_hoy,
        'pendientes_hoy': pendientes_hoy,
        'fallidas_hoy': fallidas_hoy,
        'porcentaje_exito': porcentaje_exito,
        'total_clientes': total_clientes,
        'total_empresas': total_empresas,
        'total_conductores': total_conductores,
        'por_estado': por_estado,
        'ultimos_7': json_safe(ultimos_7),
        'ruta_hoy': ruta_hoy,
        'ultimas_entregas': ultimas_entregas,
    }
    return render(request, 'dashboard/index.html', ctx)


def json_safe(obj):
    """Convierte objetos date a strings para usar en templates JS."""
    import json
    from datetime import date
    class DateEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, date):
                return o.isoformat()
            return super().default(o)
    return json.dumps(obj, cls=DateEncoder)
