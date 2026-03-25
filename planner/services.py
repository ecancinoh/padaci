import math
import unicodedata
from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone

from clients.models import Cliente
from routes.models import Entrega

from .models import PlanificacionSemanal, RecomendacionCliente


DIAS = ['lun', 'mar', 'mie', 'jue', 'vie']
PENALIZACION_NUEVO_DIA_COMUNA = 180


def _normalize_text(value):
    value = (value or '').strip().lower()
    value = unicodedata.normalize('NFD', value)
    return ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn')


def _haversine(lat1, lon1, lat2, lon2):
    radio_tierra_km = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return radio_tierra_km * 2 * math.asin(math.sqrt(a))


def _build_priority_data(clientes, window_days=60):
    cliente_ids = [cliente.id for cliente in clientes]
    if not cliente_ids:
        return {}

    hoy = timezone.localdate()
    fecha_limite = hoy - timedelta(days=window_days)

    stats = (
        Entrega.objects.filter(cliente_id__in=cliente_ids, estado='entregado')
        .values('cliente_id')
        .annotate(
            ultima_fecha=Max('fecha_programada'),
            entregas_recientes=Count('id', filter=Q(fecha_programada__gte=fecha_limite)),
        )
    )

    stats_map = {row['cliente_id']: row for row in stats}
    priority_data = {}

    for cliente in clientes:
        data = stats_map.get(cliente.id)
        if not data or not data.get('ultima_fecha'):
            priority_data[cliente.id] = {
                'score': 10_000,
                'reason': 'Sin entregas previas: prioridad alta.',
            }
            continue

        ultima_fecha = data['ultima_fecha']
        dias_sin_atencion = max((hoy - ultima_fecha).days, 0)
        entregas_recientes = data.get('entregas_recientes') or 0

        # Mayor score = mayor prioridad por antigüedad + baja frecuencia reciente.
        score = (dias_sin_atencion * 1.8) + (max(0, 8 - entregas_recientes) * 12)
        priority_data[cliente.id] = {
            'score': score,
            'reason': (
                f'Ultima atencion hace {dias_sin_atencion} dias; '
                f'{entregas_recientes} entregas ultimos {window_days} dias.'
            ),
        }

    return priority_data


def _tiene_coordenadas(cliente):
    return cliente.latitud is not None and cliente.longitud is not None


def _dias_permitidos_cliente(plan, cliente):
    return DIAS


def dia_permitido_cliente(plan, cliente, dia_semana):
    return dia_semana in _dias_permitidos_cliente(plan, cliente)


def _ruta_km_aproximada(clientes):
    clientes_coords = [c for c in clientes if _tiene_coordenadas(c)]
    if len(clientes_coords) <= 1:
        return 0.0

    pendientes = clientes_coords[:]
    actual = pendientes.pop(0)
    km_total = 0.0
    while pendientes:
        siguiente = min(
            pendientes,
            key=lambda c: _haversine(
                float(actual.latitud),
                float(actual.longitud),
                float(c.latitud),
                float(c.longitud),
            ),
        )
        km_total += _haversine(
            float(actual.latitud),
            float(actual.longitud),
            float(siguiente.latitud),
            float(siguiente.longitud),
        )
        pendientes.remove(siguiente)
        actual = siguiente
    return km_total


def _minutos_estimados(clientes, plan):
    km = _ruta_km_aproximada(clientes)
    velocidad = float(plan.velocidad_promedio_kmh or 28)
    minutos_movimiento = (km / max(velocidad, 1.0)) * 60
    minutos_servicio = sum(
        int(getattr(cliente, 'tiempo_estimado_atencion', 0) or plan.minutos_servicio_por_cliente or 12)
        for cliente in clientes
    )
    return km, minutos_movimiento + minutos_servicio


def get_clientes_seleccionados_qs(plan):
    return plan.clientes_reparto.all().select_related('empresa')


def _carga_dia_estimada(plan, clientes):
    km, minutos = _minutos_estimados(clientes, plan)
    return {
        'km': round(km, 2),
        'minutos': round(minutos, 0),
        'horas': round(minutos / 60, 2),
    }


def _evaluar_dia_con_clientes(plan, dia, clientes):
    razones = []
    capacidad = plan.capacidades_por_dia()[dia]
    if capacidad is not None and len(clientes) > capacidad:
        razones.append(f'cupo diario completo ({capacidad})')

    carga = _carga_dia_estimada(plan, clientes)
    max_minutos_dia = float(plan.max_horas_jornada or 8) * 60
    if max_minutos_dia > 0 and carga['minutos'] > max_minutos_dia:
        horas_limite = round(max_minutos_dia / 60, 2)
        razones.append(f"supera horas de jornada ({carga['horas']}h > {horas_limite}h)")

    return {
        'ok': len(razones) == 0,
        'razones': razones,
        'carga': carga,
    }


def _cumple_restricciones(plan, dia, clientes):
    return _evaluar_dia_con_clientes(plan, dia, clientes)['ok']


def _dias_con_comuna(dia_clientes, comuna_key):
    if not comuna_key:
        return set()

    dias = set()
    for dia, clientes in dia_clientes.items():
        for cliente in clientes:
            if _normalize_text(cliente.comuna) == comuna_key:
                dias.add(dia)
                break
    return dias


def _ordenar_grupo_por_cercania(clientes, priority_data):
    if len(clientes) <= 1:
        return clientes

    sin_coord = [c for c in clientes if c.latitud is None or c.longitud is None]
    con_coord = [c for c in clientes if c.latitud is not None and c.longitud is not None]

    if not con_coord:
        return sorted(
            sin_coord,
            key=lambda c: (-priority_data.get(c.id, {}).get('score', 0), c.nombre.lower()),
        )

    inicio = max(con_coord, key=lambda c: priority_data.get(c.id, {}).get('score', 0))
    ruta = [inicio]
    pendientes = [c for c in con_coord if c.id != inicio.id]

    while pendientes:
        actual = ruta[-1]

        def _coste(candidato):
            distancia = _haversine(
                float(actual.latitud),
                float(actual.longitud),
                float(candidato.latitud),
                float(candidato.longitud),
            )
            score = priority_data.get(candidato.id, {}).get('score', 0)
            # Penaliza distancia pero favorece candidatos de mayor prioridad.
            return distancia - (score / 1000)

        siguiente = min(
            pendientes,
            key=_coste,
        )
        ruta.append(siguiente)
        pendientes.remove(siguiente)

    return ruta + sorted(
        sin_coord,
        key=lambda c: (-priority_data.get(c.id, {}).get('score', 0), c.nombre.lower()),
    )


def _ordenar_clientes_optimizado(clientes, priority_data):
    grupos = defaultdict(list)
    for cliente in clientes:
        comuna = (cliente.comuna or '').strip().lower() or 'sin-comuna'
        grupos[comuna].append(cliente)

    # Se priorizan comunas con mejor combinación entre tamaño y urgencia de atención.
    def _comuna_score(comuna):
        clientes_comuna = grupos[comuna]
        if not clientes_comuna:
            return 0
        urgencia_promedio = sum(priority_data.get(c.id, {}).get('score', 0) for c in clientes_comuna) / len(clientes_comuna)
        return (len(clientes_comuna) * 8) + urgencia_promedio

    comunas_ordenadas = sorted(grupos.keys(), key=lambda k: (-_comuna_score(k), k))

    salida = []
    for comuna in comunas_ordenadas:
        salida.extend(_ordenar_grupo_por_cercania(grupos[comuna], priority_data))
    return salida


def _seleccionar_dia_eficiente(plan, dia_clientes, cliente, priority_data):
    mejor_dia = None
    mejor_costo = None

    dias_permitidos = _dias_permitidos_cliente(plan, cliente)
    comuna_key = _normalize_text(cliente.comuna)
    dias_existentes_comuna = _dias_con_comuna(dia_clientes, comuna_key)
    for dia in dias_permitidos:
        actuales = dia_clientes[dia]
        propuesta = actuales + [cliente]
        if not _cumple_restricciones(plan, dia, propuesta):
            continue

        km_actual, min_actual = _minutos_estimados(actuales, plan)
        km_prop, min_prop = _minutos_estimados(propuesta, plan)
        delta_km = max(0.0, km_prop - km_actual)
        delta_min = max(0.0, min_prop - min_actual)

        prioridad = priority_data.get(cliente.id, {}).get('score', 0)
        # Menor costo: castiga aumento de km y minutos, premia clientes más prioritarios.
        costo = (delta_km * 1.3) + (delta_min * 0.04) - (prioridad * 0.01)

        # Evita abrir un nuevo dia para la misma comuna si ya existe uno viable.
        if dias_existentes_comuna and dia not in dias_existentes_comuna:
            costo += PENALIZACION_NUEVO_DIA_COMUNA

        if mejor_costo is None or costo < mejor_costo:
            mejor_costo = costo
            mejor_dia = dia

    return mejor_dia


def _seleccionar_dia_eficiente_grupo(plan, dia_clientes, clientes_grupo, priority_data):
    if not clientes_grupo:
        return None

    # Interseccion de dias permitidos para todo el grupo.
    dias_permitidos = set(DIAS)
    for cliente in clientes_grupo:
        dias_permitidos &= set(_dias_permitidos_cliente(plan, cliente))

    if not dias_permitidos:
        return None

    mejor_dia = None
    mejor_costo = None

    comuna_key = _normalize_text(clientes_grupo[0].comuna)
    dias_existentes_comuna = _dias_con_comuna(dia_clientes, comuna_key)

    for dia in DIAS:
        if dia not in dias_permitidos:
            continue

        actuales = dia_clientes[dia]
        propuesta = actuales + clientes_grupo
        if not _cumple_restricciones(plan, dia, propuesta):
            continue

        km_actual, min_actual = _minutos_estimados(actuales, plan)
        km_prop, min_prop = _minutos_estimados(propuesta, plan)
        delta_km = max(0.0, km_prop - km_actual)
        delta_min = max(0.0, min_prop - min_actual)
        prioridad_grupo = sum(priority_data.get(c.id, {}).get('score', 0) for c in clientes_grupo)

        # Menor costo: premiar mantener comuna unificada y de mayor prioridad.
        costo = (delta_km * 1.3) + (delta_min * 0.04) - (prioridad_grupo * 0.01)

        # Priorizamos consolidar la comuna en el mismo dia ya visitado.
        if dias_existentes_comuna and dia not in dias_existentes_comuna:
            costo += PENALIZACION_NUEVO_DIA_COMUNA

        if mejor_costo is None or costo < mejor_costo:
            mejor_costo = costo
            mejor_dia = dia

    return mejor_dia


def _seleccionar_dia_base_comuna(plan, dia_clientes, clientes_grupo, priority_data):
    if not clientes_grupo:
        return None
    # Usa el primer cliente del grupo (ya ordenado por prioridad/cercania)
    # para elegir el mejor dia base de la comuna.
    return _seleccionar_dia_eficiente(plan, dia_clientes, clientes_grupo[0], priority_data)


def _agrupar_clientes_por_comuna(clientes, priority_data):
    grupos = defaultdict(list)
    for cliente in clientes:
        comuna_key = _normalize_text(cliente.comuna) or 'sin-comuna'
        grupos[comuna_key].append(cliente)

    def _score_grupo(key):
        items = grupos[key]
        if not items:
            return 0
        avg_prioridad = sum(priority_data.get(c.id, {}).get('score', 0) for c in items) / len(items)
        # Priorizamos grupos con mas clientes para evitar idas repetidas a la misma comuna.
        return (len(items) * 10) + avg_prioridad

    orden_keys = sorted(grupos.keys(), key=lambda k: (-_score_grupo(k), k))
    salida = []
    for key in orden_keys:
        ordenados = _ordenar_grupo_por_cercania(grupos[key], priority_data)
        salida.append((key, ordenados))
    return salida


def _normalizar_orden(plan):
    recomendaciones = RecomendacionCliente.objects.filter(plan=plan).select_related('cliente')
    for dia in DIAS:
        items = list(recomendaciones.filter(dia_semana=dia).order_by('orden', 'id'))
        for index, rec in enumerate(items, start=1):
            if rec.orden != index:
                rec.orden = index
                rec.save(update_fields=['orden', 'fecha_actualizacion'])


def generar_recomendaciones(plan):
    recomendaciones_qs = RecomendacionCliente.objects.filter(plan=plan).select_related('cliente')
    bloqueados = list(recomendaciones_qs.filter(bloqueado=True))

    bloqueados_ids = {rec.cliente_id for rec in bloqueados}

    recomendaciones_qs.filter(bloqueado=False).delete()

    clientes = get_clientes_seleccionados_qs(plan)

    clientes = clientes.exclude(id__in=bloqueados_ids)

    clientes_lista = list(clientes)
    priority_data = _build_priority_data(clientes_lista, window_days=60)
    grupos_comuna = _agrupar_clientes_por_comuna(clientes_lista, priority_data)

    dia_clientes = {dia: [] for dia in DIAS}
    for rec in bloqueados:
        dia_clientes[rec.dia_semana].append(rec.cliente)

    total_nuevos = 0
    no_asignados = 0

    for comuna_key, clientes_grupo in grupos_comuna:
        # Paso 1: intentamos asignar comuna completa a un solo dia.
        dia_objetivo = _seleccionar_dia_eficiente_grupo(plan, dia_clientes, clientes_grupo, priority_data)

        if dia_objetivo is not None:
            for cliente in clientes_grupo:
                dia_clientes[dia_objetivo].append(cliente)
                orden = len(dia_clientes[dia_objetivo])
                RecomendacionCliente.objects.create(
                    plan=plan,
                    cliente=cliente,
                    dia_semana=dia_objetivo,
                    orden=orden,
                    origen='auto',
                    bloqueado=False,
                    observacion=(
                        priority_data.get(cliente.id, {}).get('reason', '')
                        + f' | Comuna agrupada: {comuna_key}'
                    ).strip(),
                )
                total_nuevos += 1
            continue

        # Paso 2: si la comuna no cabe completa, mantenemos un unico dia base.
        # Evita viajes repetidos a la misma comuna en dias distintos.
        dia_base = _seleccionar_dia_base_comuna(plan, dia_clientes, clientes_grupo, priority_data)
        if dia_base is None:
            no_asignados += len(clientes_grupo)
            continue

        for cliente in clientes_grupo:
            propuesta = dia_clientes[dia_base] + [cliente]
            if not _cumple_restricciones(plan, dia_base, propuesta):
                no_asignados += 1
                continue

            dia_clientes[dia_base].append(cliente)
            orden = len(dia_clientes[dia_base])
            RecomendacionCliente.objects.create(
                plan=plan,
                cliente=cliente,
                dia_semana=dia_base,
                orden=orden,
                origen='auto',
                bloqueado=False,
                observacion=(
                    priority_data.get(cliente.id, {}).get('reason', '')
                    + f' | Comuna consolidada en dia unico: {comuna_key}'
                ).strip(),
            )
            total_nuevos += 1

    _normalizar_orden(plan)

    return {
        'total_nuevos': total_nuevos,
        'bloqueados': len(bloqueados),
        'no_asignados': no_asignados,
        'total_final': RecomendacionCliente.objects.filter(plan=plan).count(),
    }


def _dia_destino_para_plan(plan):
    recomendaciones = RecomendacionCliente.objects.filter(plan=plan).select_related('cliente').order_by('dia_semana', 'orden', 'id')
    dia_clientes = {dia: [] for dia in DIAS}
    for rec in recomendaciones:
        dia_clientes[rec.dia_semana].append(rec.cliente)

    mejor_dia = None
    mejor_km = None
    for dia in DIAS:
        if not _cumple_restricciones(plan, dia, dia_clientes[dia]):
            continue
        km = _carga_dia_estimada(plan, dia_clientes[dia])['km']
        if mejor_km is None or km < mejor_km:
            mejor_km = km
            mejor_dia = dia
    return mejor_dia


def agregar_cliente_a_plan(plan, cliente):
    if RecomendacionCliente.objects.filter(plan=plan, cliente=cliente).exists():
        return False

    recomendaciones = RecomendacionCliente.objects.filter(plan=plan).select_related('cliente').order_by('dia_semana', 'orden', 'id')
    dia_clientes = {dia: [] for dia in DIAS}
    for rec in recomendaciones:
        dia_clientes[rec.dia_semana].append(rec.cliente)

    priority_data = _build_priority_data([cliente], window_days=60)
    dia_destino = _seleccionar_dia_eficiente(plan, dia_clientes, cliente, priority_data)
    if dia_destino is None:
        return False

    dia_clientes[dia_destino].append(cliente)
    orden = len(dia_clientes[dia_destino])
    reason = priority_data.get(cliente.id, {}).get('reason', '')

    RecomendacionCliente.objects.create(
        plan=plan,
        cliente=cliente,
        dia_semana=dia_destino,
        orden=orden,
        origen='auto',
        bloqueado=False,
        observacion=reason,
    )
    return True


def agregar_cliente_a_planes_activos(cliente):
    planes = PlanificacionSemanal.objects.filter(activo=True)
    asignados = 0
    for plan in planes:
        if agregar_cliente_a_plan(plan, cliente):
            asignados += 1
    return asignados


def reoptimizar_planes_por_cliente(cliente):
    recomendaciones = RecomendacionCliente.objects.filter(
        cliente=cliente,
        plan__activo=True,
    ).select_related('plan')

    planes_reoptimizados = 0
    procesados = set()
    for recomendacion in recomendaciones:
        plan = recomendacion.plan
        if plan.id in procesados:
            continue
        procesados.add(plan.id)

        # Si la recomendacion del cliente esta bloqueada, se respeta sin recálculo.
        if recomendacion.bloqueado:
            continue

        generar_recomendaciones(plan)
        planes_reoptimizados += 1

    return planes_reoptimizados


def resumen_por_dia(plan):
    recomendaciones = RecomendacionCliente.objects.filter(plan=plan).select_related('cliente').order_by('dia_semana', 'orden', 'id')
    dia_clientes = {dia: [] for dia in DIAS}
    for rec in recomendaciones:
        dia_clientes[rec.dia_semana].append(rec.cliente)

    resultado = {}
    for dia in DIAS:
        carga = _carga_dia_estimada(plan, dia_clientes[dia])
        resultado[dia] = {
            'km': carga['km'],
            'horas': carga['horas'],
            'minutos': int(carga['minutos']),
            'total': len(dia_clientes[dia]),
            'cumple': _cumple_restricciones(plan, dia, dia_clientes[dia]),
        }
    return resultado


def diagnostico_no_asignados(plan, limit=50):
    recomendaciones = RecomendacionCliente.objects.filter(plan=plan).select_related('cliente').order_by('dia_semana', 'orden', 'id')
    dia_clientes = {dia: [] for dia in DIAS}
    for rec in recomendaciones:
        dia_clientes[rec.dia_semana].append(rec.cliente)

    asignados_ids = set(recomendaciones.values_list('cliente_id', flat=True))
    pendientes = list(get_clientes_seleccionados_qs(plan).exclude(id__in=asignados_ids).order_by('nombre')[:limit])

    resultados = []
    for cliente in pendientes:
        motivos = []
        dias_permitidos = _dias_permitidos_cliente(plan, cliente)
        if len(dias_permitidos) == 1:
            motivos.append(
                f"Cliente de comuna exclusiva: solo puede asignarse en {dias_permitidos[0].upper()}"
            )

        for dia in dias_permitidos:
            evaluacion = _evaluar_dia_con_clientes(plan, dia, dia_clientes[dia] + [cliente])
            if evaluacion['ok']:
                motivos = []
                break
            motivos.append(f"{dia.upper()}: {', '.join(evaluacion['razones'])}")

        if motivos:
            resultados.append(
                {
                    'cliente_id': cliente.id,
                    'nombre': cliente.nombre,
                    'comuna': cliente.comuna or '-',
                    'motivo': ' | '.join(motivos),
                }
            )

    return resultados
