from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.mixins import RolRestringidoMixin, rol_restringido
from django.views.generic import ListView, DetailView
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from .models import HistorialDia, DetalleHistorial
from routes.models import Entrega


class HistorialListView(RolRestringidoMixin, ListView):
    model = HistorialDia
    template_name = 'history/list.html'
    context_object_name = 'historiales'
    paginate_by = 30

    def get_queryset(self):
        qs = super().get_queryset().select_related('conductor')
        fecha_desde = self.request.GET.get('fecha_desde', '')
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        conductor = self.request.GET.get('conductor', '')
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if conductor:
            qs = qs.filter(conductor_id=conductor)
        return qs


class HistorialDetailView(RolRestringidoMixin, DetailView):
    model = HistorialDia
    template_name = 'history/detail.html'
    context_object_name = 'historial'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['detalles'] = self.object.detalles.select_related('entrega__cliente', 'entrega__empresa').all()
        return ctx


@rol_restringido
def generar_historial_hoy(request):
    """Genera o actualiza el historial del día de hoy a partir de las entregas registradas."""
    hoy = timezone.localdate()
    entregas_hoy = Entrega.objects.filter(fecha_programada=hoy)

    historial, _ = HistorialDia.objects.get_or_create(fecha=hoy)
    historial.total_entregas = entregas_hoy.count()
    historial.entregadas = entregas_hoy.filter(estado='entregado').count()
    historial.fallidas = entregas_hoy.filter(estado='fallido').count()
    historial.reprogramadas = entregas_hoy.filter(estado='reprogramado').count()
    historial.devueltas = entregas_hoy.filter(estado='devuelto').count()
    historial.save()

    for entrega in entregas_hoy:
        DetalleHistorial.objects.get_or_create(
            historial=historial,
            entrega=entrega,
            defaults={'estado_final': entrega.estado},
        )

    messages.success(request, f'Historial del {hoy} generado/actualizado.')
    return render(request, 'history/list.html', {
        'historiales': HistorialDia.objects.all().order_by('-fecha'),
    })
