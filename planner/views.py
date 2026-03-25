from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from clients.models import Cliente

from .forms import PlanificacionSemanalForm
from .models import PlanificacionSemanal, RecomendacionCliente
from .services import DIAS, agregar_cliente_a_plan, diagnostico_no_asignados, generar_recomendaciones, get_clientes_seleccionados_qs, resumen_por_dia


DIA_LABELS = {
    'lun': 'Lunes',
    'mar': 'Martes',
    'mie': 'Miercoles',
    'jue': 'Jueves',
    'vie': 'Viernes',
}

class PlanificacionListView(LoginRequiredMixin, ListView):
    model = PlanificacionSemanal
    template_name = 'planner/list.html'
    context_object_name = 'planes'
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related('empresa')
            .annotate(total_clientes=Count('recomendaciones'))
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(nombre__icontains=q)
        return queryset


class PlanificacionCreateView(LoginRequiredMixin, CreateView):
    model = PlanificacionSemanal
    form_class = PlanificacionSemanalForm
    template_name = 'planner/form.html'
    success_url = reverse_lazy('planner:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Planificacion creada. Selecciona clientes para reparto y luego genera la semana.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Nueva planificacion semanal'
        return ctx


class PlanificacionUpdateView(LoginRequiredMixin, UpdateView):
    model = PlanificacionSemanal
    form_class = PlanificacionSemanalForm
    template_name = 'planner/form.html'
    success_url = reverse_lazy('planner:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Planificacion actualizada. Puedes regenerar cuando quieras.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['titulo'] = 'Editar planificacion semanal'
        return ctx


class PlanificacionDeleteView(LoginRequiredMixin, DeleteView):
    model = PlanificacionSemanal
    template_name = 'planner/confirm_delete.html'
    success_url = reverse_lazy('planner:list')

    def form_valid(self, form):
        messages.success(self.request, 'Planificacion eliminada.')
        return super().form_valid(form)


def _normalizar_orden_plan(plan):
    for dia in DIAS:
        recs = list(
            RecomendacionCliente.objects.filter(plan=plan, dia_semana=dia)
            .select_related('cliente')
            .order_by('orden', 'id')
        )
        for index, rec in enumerate(recs, start=1):
            if rec.orden != index:
                rec.orden = index
                rec.save(update_fields=['orden', 'fecha_actualizacion'])


def _contexto_detail(plan):
    recomendaciones = RecomendacionCliente.objects.filter(plan=plan).select_related('cliente').order_by('dia_semana', 'orden', 'id')
    agrupadas = {dia: [] for dia in DIAS}
    comunas_usage = {}
    for rec in recomendaciones:
        agrupadas[rec.dia_semana].append(rec)
        comuna = (rec.cliente.comuna or '').strip()
        if not comuna:
            continue
        key = comuna.lower()
        if key not in comunas_usage:
            comunas_usage[key] = {
                'comuna': comuna,
                'dias': {d: 0 for d in DIAS},
            }
        comunas_usage[key]['dias'][rec.dia_semana] += 1

    clientes_seleccionados = get_clientes_seleccionados_qs(plan)
    clientes_asignados_ids = recomendaciones.values_list('cliente_id', flat=True)
    clientes_disponibles = clientes_seleccionados.exclude(id__in=clientes_asignados_ids).order_by('nombre')

    capacidades = plan.capacidades_por_dia()
    resumen_dias = resumen_por_dia(plan)
    no_asignados_detalle = diagnostico_no_asignados(plan, limit=80)
    comunas_divididas = []
    for item in comunas_usage.values():
        dias_activos = [d for d, count in item['dias'].items() if count > 0]
        if len(dias_activos) <= 1:
            continue
        comunas_divididas.append(
            {
                'comuna': item['comuna'],
                'dias_activos': dias_activos,
                'dias_resumen': [
                    {
                        'dia': DIA_LABELS[d],
                        'count': item['dias'][d],
                    }
                    for d in DIAS
                    if item['dias'][d] > 0
                ],
                'total_clientes': sum(item['dias'][d] for d in DIAS),
            }
        )
    comunas_divididas.sort(key=lambda x: (-len(x['dias_activos']), -x['total_clientes'], x['comuna'].lower()))
    day_sections = []
    map_points = []
    map_missing = 0
    for dia in DIAS:
        items = agrupadas[dia]
        for rec in items:
            if rec.cliente.latitud is None or rec.cliente.longitud is None:
                map_missing += 1
                continue
            map_points.append(
                {
                    'id': rec.cliente_id,
                    'nombre': rec.cliente.nombre,
                    'comuna': rec.cliente.comuna or '',
                    'direccion': rec.cliente.direccion or '',
                    'lat': float(rec.cliente.latitud),
                    'lon': float(rec.cliente.longitud),
                    'dia': dia,
                    'dia_label': DIA_LABELS[dia],
                    'orden': rec.orden,
                    'bloqueado': rec.bloqueado,
                }
            )

        day_sections.append(
            {
                'code': dia,
                'label': DIA_LABELS[dia],
                'items': items,
                'total': len(items),
                'capacity': capacidades[dia],
                'resumen': resumen_dias[dia],
            }
        )

    return {
        'plan': plan,
        'dias': DIAS,
        'dia_labels': DIA_LABELS,
        'day_options': [(d, DIA_LABELS[d]) for d in DIAS],
        'recomendaciones_por_dia': agrupadas,
        'day_sections': day_sections,
        'clientes_disponibles': clientes_disponibles,
        'clientes_seleccionados': clientes_seleccionados.order_by('nombre'),
        'clientes_todos': Cliente.objects.order_by('nombre'),
        'clientes_seleccionados_ids': list(clientes_seleccionados.values_list('id', flat=True)),
        'map_points': map_points,
        'map_missing': map_missing,
        'no_asignados_detalle': no_asignados_detalle,
        'comunas_divididas': comunas_divididas,
    }


@login_required
def planificacion_detail(request, pk):
    plan = get_object_or_404(PlanificacionSemanal, pk=pk)

    # Limpia residuos de sesion de la integracion GEMINI removida en planner.
    request.session.pop(f'planner_gemini_{plan.id}', None)
    request.session.pop(f'planner_gemini_plan_{plan.id}', None)

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        if action == 'actualizar_parametros':
            fields = {
                'max_horas_jornada': float,
                'velocidad_promedio_kmh': float,
                'minutos_servicio_por_cliente': int,
                'capacidad_lunes': int,
                'capacidad_martes': int,
                'capacidad_miercoles': int,
                'capacidad_jueves': int,
                'capacidad_viernes': int,
            }
            errores = []
            for field, caster in fields.items():
                raw = (request.POST.get(field) or '').strip()
                if raw == '':
                    if field.startswith('capacidad_'):
                        setattr(plan, field, None)
                    continue
                try:
                    value = caster(raw)
                except ValueError:
                    errores.append(f'Valor invalido en {field}.')
                    continue
                if value <= 0 and not field.startswith('capacidad_'):
                    errores.append(f'{field} debe ser mayor a 0.')
                    continue
                if value < 0 and field.startswith('capacidad_'):
                    errores.append(f'{field} no puede ser negativo.')
                    continue
                setattr(plan, field, value)

            if errores:
                for err in errores:
                    messages.error(request, err)
                return redirect('planner:detail', pk=pk)

            plan.save()
            resumen = generar_recomendaciones(plan)
            messages.success(
                request,
                (
                    'Parametros actualizados manualmente. '
                    f"Recalculo: {resumen['total_nuevos']} asignados, {resumen['no_asignados']} no asignados."
                ),
            )
            return redirect('planner:detail', pk=pk)

        if action == 'actualizar_clientes_reparto':
            ids = request.POST.getlist('clientes_reparto')
            plan.clientes_reparto.set(Cliente.objects.filter(id__in=ids))
            messages.success(request, f'Seleccion de clientes de reparto actualizada ({len(ids)} clientes).')
            return redirect('planner:detail', pk=pk)

        if action == 'generar':
            if not plan.clientes_reparto.exists():
                messages.error(request, 'Debes seleccionar al menos un cliente para reparto antes de generar la planificacion.')
                return redirect('planner:detail', pk=pk)
            resumen = generar_recomendaciones(plan)
            messages.success(
                request,
                (
                    'Recomendaciones actualizadas: '
                    f"{resumen['total_nuevos']} nuevas, "
                    f"{resumen['bloqueados']} bloqueadas, "
                    f"{resumen['no_asignados']} no asignados por restricciones."
                ),
            )
            return redirect('planner:detail', pk=pk)

        if action == 'agregar':
            cliente_id = request.POST.get('cliente_id')
            dia_semana = request.POST.get('dia_semana')
            try:
                orden = int(request.POST.get('orden') or 1)
            except ValueError:
                orden = 1

            if dia_semana not in DIAS:
                messages.error(request, 'Dia invalido para asignacion manual.')
                return redirect('planner:detail', pk=pk)

            cliente = get_object_or_404(Cliente, pk=cliente_id)
            if RecomendacionCliente.objects.filter(plan=plan, cliente=cliente).exists():
                messages.warning(request, 'Ese cliente ya esta en la planificacion.')
                return redirect('planner:detail', pk=pk)

            RecomendacionCliente.objects.create(
                plan=plan,
                cliente=cliente,
                dia_semana=dia_semana,
                orden=max(1, orden),
                origen='manual',
                bloqueado=True,
                observacion='Agregado manualmente',
            )
            _normalizar_orden_plan(plan)
            messages.success(request, 'Cliente agregado manualmente al plan.')
            return redirect('planner:detail', pk=pk)

        if action == 'actualizar':
            rec = get_object_or_404(RecomendacionCliente, pk=request.POST.get('recomendacion_id'), plan=plan)
            dia_semana = request.POST.get('dia_semana')
            observacion = (request.POST.get('observacion') or '').strip()
            try:
                orden = int(request.POST.get('orden') or rec.orden)
            except ValueError:
                orden = rec.orden

            if dia_semana in DIAS:
                rec.dia_semana = dia_semana
            rec.orden = max(1, orden)
            rec.bloqueado = request.POST.get('bloqueado') == 'on'
            rec.observacion = observacion
            rec.origen = 'manual'
            rec.save()
            _normalizar_orden_plan(plan)
            messages.success(request, 'Cambio manual aplicado.')
            return redirect('planner:detail', pk=pk)

        if action == 'eliminar':
            rec = get_object_or_404(RecomendacionCliente, pk=request.POST.get('recomendacion_id'), plan=plan)
            rec.delete()
            _normalizar_orden_plan(plan)
            messages.success(request, 'Cliente removido de la planificacion.')
            return redirect('planner:detail', pk=pk)

    context = _contexto_detail(plan)
    return render(request, 'planner/detail.html', context)
