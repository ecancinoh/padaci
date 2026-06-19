from calendar import monthrange
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, UpdateView

from accounts.mixins import AdminSupervisorMixin, admin_supervisor_required

from .forms import AsistenciaDiariaFiltroForm, AsistenciaForm
from .models import Asistencia
from .services import build_monthly_report, get_worker_queryset, parse_month_filters


WEEKDAY_SHORT_LABELS = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']


def _build_period_dates(fecha, vista):
    if vista == AsistenciaDiariaFiltroForm.VISTA_SEMANA:
        inicio = fecha - timedelta(days=fecha.weekday())
        return [inicio + timedelta(days=offset) for offset in range(7)]

    if vista == AsistenciaDiariaFiltroForm.VISTA_MES:
        _, ultimo_dia = monthrange(fecha.year, fecha.month)
        return [fecha.replace(day=day) for day in range(1, ultimo_dia + 1)]

    return [fecha]


class AsistenciaListView(AdminSupervisorMixin, ListView):
    model = Asistencia
    template_name = 'asistencia/list.html'
    context_object_name = 'asistencias'
    paginate_by = 20

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related('usuario', 'registrado_por')
        )
        fecha = self.request.GET.get('fecha', '')
        q = self.request.GET.get('q', '').strip()

        if fecha:
            qs = qs.filter(fecha=fecha)

        if q:
            qs = qs.filter(
                Q(usuario__username__icontains=q)
                | Q(usuario__first_name__icontains=q)
                | Q(usuario__last_name__icontains=q)
            )

        return qs


class AsistenciaUpdateView(AdminSupervisorMixin, UpdateView):
    model = Asistencia
    form_class = AsistenciaForm
    template_name = 'asistencia/form.html'
    success_url = reverse_lazy('asistencia:list')

    def form_valid(self, form):
        form.instance.registrado_por = self.request.user
        messages.success(self.request, 'Asistencia actualizada correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar asistencia'
        return ctx


class AsistenciaReporteMensualView(AdminSupervisorMixin, View):
    template_name = 'asistencia/reporte_mensual.html'

    def get(self, request, *args, **kwargs):
        filters = parse_month_filters(request.GET)
        report = build_monthly_report(filters)
        context = {
            'filters': filters,
            'report': report,
        }
        return render(request, self.template_name, context)


@admin_supervisor_required
def asistencia_diaria(request):
    fecha_base = timezone.localdate()
    if request.method == 'GET':
        form = AsistenciaDiariaFiltroForm(request.GET or None, initial={'fecha': fecha_base})
    else:
        form = AsistenciaDiariaFiltroForm(request.POST or None, initial={'fecha': fecha_base})

    if form.is_valid():
        fecha = form.cleaned_data['fecha']
        vista = form.cleaned_data['vista']
    else:
        fecha = fecha_base
        vista = AsistenciaDiariaFiltroForm.VISTA_SEMANA

    fechas_periodo = _build_period_dates(fecha, vista)

    trabajadores = list(get_worker_queryset())

    asistencia_map = {
        (a.usuario_id, a.fecha): a
        for a in Asistencia.objects.filter(fecha__in=fechas_periodo, usuario__in=trabajadores)
    }

    if request.method == 'POST':
        actualizados = 0
        es_un_dia = len(fechas_periodo) == 1

        for trabajador in trabajadores:
            for fecha_celda in fechas_periodo:
                key_fecha = fecha_celda.strftime('%Y%m%d')
                presente_key = f'presente_{trabajador.pk}_{key_fecha}'
                legacy_estado = request.POST.get(f'estado_{trabajador.pk}') if es_un_dia else None

                if presente_key in request.POST:
                    estado = Asistencia.ESTADO_PRESENTE
                elif legacy_estado in {Asistencia.ESTADO_PRESENTE, Asistencia.ESTADO_AUSENTE} and es_un_dia:
                    estado = legacy_estado
                else:
                    estado = Asistencia.ESTADO_AUSENTE

                registro_actual = asistencia_map.get((trabajador.pk, fecha_celda))
                observacion_key = f'observacion_{trabajador.pk}_{key_fecha}'
                observacion_raw = request.POST.get(observacion_key)
                if observacion_raw is None and es_un_dia:
                    observacion_raw = request.POST.get(f'observacion_{trabajador.pk}')

                observacion = (observacion_raw or '').strip()
                if not observacion and registro_actual:
                    observacion = registro_actual.observacion

                Asistencia.objects.update_or_create(
                    usuario=trabajador,
                    fecha=fecha_celda,
                    defaults={
                        'estado': estado,
                        'observacion': observacion,
                        'registrado_por': request.user,
                    },
                )
                actualizados += 1

        messages.success(request, f'Asistencia guardada para {actualizados} registros en vista {vista}.')
        return redirect(f"{reverse('asistencia:diaria')}?fecha={fecha.strftime('%Y-%m-%d')}&vista={vista}")

    headers = [
        {
            'fecha': fecha_col,
            'dia_corto': WEEKDAY_SHORT_LABELS[fecha_col.weekday()],
        }
        for fecha_col in fechas_periodo
    ]

    rows = [
        {
            'trabajador': trabajador,
            'celdas': [
                {
                    'fecha': fecha_celda,
                    'checked': bool(
                        asistencia_map.get((trabajador.pk, fecha_celda))
                        and asistencia_map[(trabajador.pk, fecha_celda)].estado == Asistencia.ESTADO_PRESENTE
                    ),
                    'registro': asistencia_map.get((trabajador.pk, fecha_celda)),
                }
                for fecha_celda in fechas_periodo
            ],
            'total_presentes': sum(
                1
                for fecha_celda in fechas_periodo
                if asistencia_map.get((trabajador.pk, fecha_celda))
                and asistencia_map[(trabajador.pk, fecha_celda)].estado == Asistencia.ESTADO_PRESENTE
            ),
        }
        for trabajador in trabajadores
    ]

    context = {
        'form': form,
        'fecha': fecha,
        'vista': vista,
        'headers': headers,
        'rows': rows,
    }
    return render(request, 'asistencia/diaria.html', context)


class AsistenciaIndividualView(LoginRequiredMixin, AdminSupervisorMixin, View):
    template_name = 'asistencia/form.html'

    def get(self, request, *args, **kwargs):
        form = AsistenciaForm(initial={'fecha': timezone.localdate()})
        return render(request, self.template_name, {'form': form, 'titulo': 'Registro individual de asistencia'})

    def post(self, request, *args, **kwargs):
        form = AsistenciaForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form, 'titulo': 'Registro individual de asistencia'})

        asistencia, created = Asistencia.objects.update_or_create(
            usuario=form.cleaned_data['usuario'],
            fecha=form.cleaned_data['fecha'],
            defaults={
                'estado': form.cleaned_data['estado'],
                'observacion': form.cleaned_data['observacion'],
                'registrado_por': request.user,
            },
        )
        if created:
            messages.success(request, 'Asistencia registrada correctamente.')
        else:
            messages.success(request, 'La asistencia ya existía y fue actualizada.')
        return redirect('asistencia:list')
