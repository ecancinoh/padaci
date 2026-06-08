from datetime import date

from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import CustomUser

from .models import Asistencia


MONTH_OPTIONS = [
    (1, 'Enero'),
    (2, 'Febrero'),
    (3, 'Marzo'),
    (4, 'Abril'),
    (5, 'Mayo'),
    (6, 'Junio'),
    (7, 'Julio'),
    (8, 'Agosto'),
    (9, 'Septiembre'),
    (10, 'Octubre'),
    (11, 'Noviembre'),
    (12, 'Diciembre'),
]


def parse_month_filters(params):
    today = timezone.localdate()
    month_raw = params.get('mes', '')
    year_raw = params.get('anio', '')

    try:
        mes = int(month_raw)
    except (TypeError, ValueError):
        mes = today.month

    try:
        anio = int(year_raw)
    except (TypeError, ValueError):
        anio = today.year

    if mes < 1 or mes > 12:
        mes = today.month

    if anio < 2000 or anio > 2100:
        anio = today.year

    month_map = dict(MONTH_OPTIONS)

    return {
        'mes': mes,
        'anio': anio,
        'mes_label': month_map.get(mes, date(anio, mes, 1).strftime('%B').capitalize()),
        'meses': MONTH_OPTIONS,
    }


def get_worker_queryset():
    return CustomUser.objects.filter(
        rol__in=['conductor', 'peoneta'],
        activo=True,
    ).order_by('last_name', 'first_name', 'username')


def build_monthly_report(filters):
    mes = filters['mes']
    anio = filters['anio']

    asistencias_mes = Asistencia.objects.filter(fecha__year=anio, fecha__month=mes)

    resumen = list(
        get_worker_queryset().annotate(
            presentes=Count('asistencias', filter=Q(asistencias__fecha__year=anio, asistencias__fecha__month=mes, asistencias__estado=Asistencia.ESTADO_PRESENTE)),
            ausentes=Count('asistencias', filter=Q(asistencias__fecha__year=anio, asistencias__fecha__month=mes, asistencias__estado=Asistencia.ESTADO_AUSENTE)),
            total_registros=Count('asistencias', filter=Q(asistencias__fecha__year=anio, asistencias__fecha__month=mes)),
        )
    )

    for item in resumen:
        total = item.total_registros or 0
        item.porcentaje = round((item.presentes / total) * 100, 1) if total else 0

    return {
        'resumen': resumen,
        'total_registros': asistencias_mes.count(),
        'total_presentes': asistencias_mes.filter(estado=Asistencia.ESTADO_PRESENTE).count(),
        'total_ausentes': asistencias_mes.filter(estado=Asistencia.ESTADO_AUSENTE).count(),
        'has_data': asistencias_mes.exists(),
    }
