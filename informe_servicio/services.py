from collections import Counter
from datetime import date
from decimal import Decimal
from io import BytesIO

from django.db.models import Sum
from django.utils import timezone

from companies.models import Empresa
from rendiciones.models import RendicionReparto
from routes.models import Entrega, RutaDia


WEEKDAY_LABELS = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo',
}


def _format_currency(value):
    return '$ ' + f'{int(value or 0):,}'.replace(',', '.')


def _format_decimal(value, decimals=1):
    number = Decimal(value or 0)
    return f'{number:.{decimals}f}'.replace('.', ',')


def _safe_percentage(numerator, denominator):
    if not denominator:
        return 0
    return round((numerator / denominator) * 100, 1)


def _default_period():
    today = timezone.localdate()
    start = today.replace(day=1)
    return start, today


def parse_filters(params):
    default_start, default_end = _default_period()
    start_raw = params.get('fecha_desde')
    end_raw = params.get('fecha_hasta')

    try:
        fecha_desde = date.fromisoformat(start_raw) if start_raw else default_start
    except ValueError:
        fecha_desde = default_start

    try:
        fecha_hasta = date.fromisoformat(end_raw) if end_raw else default_end
    except ValueError:
        fecha_hasta = default_end

    if fecha_hasta < fecha_desde:
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde

    empresa_qs = Empresa.objects.filter(activa=True)
    empresa_id = params.get('empresa')
    empresa = None
    if empresa_id:
        empresa = empresa_qs.filter(pk=empresa_id).first()
    if empresa is None:
        empresa = empresa_qs.order_by('nombre').first()

    return {
        'empresa': empresa,
        'empresa_id': str(empresa.pk) if empresa else '',
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'empresas': list(empresa_qs),
    }


def build_service_report(filters):
    empresa = filters['empresa']
    fecha_desde = filters['fecha_desde']
    fecha_hasta = filters['fecha_hasta']

    entregas = (
        Entrega.objects.filter(fecha_programada__range=(fecha_desde, fecha_hasta))
        .select_related('cliente', 'empresa', 'conductor')
        .order_by('fecha_programada', 'cliente__nombre')
    )
    rutas = RutaDia.objects.filter(fecha__range=(fecha_desde, fecha_hasta)).select_related('empresa', 'conductor', 'peoneta')
    rendiciones = RendicionReparto.objects.filter(fecha__range=(fecha_desde, fecha_hasta)).select_related('ruta')

    if empresa:
        entregas = entregas.filter(empresa=empresa)
        rutas = rutas.filter(empresa=empresa)
        rendiciones = rendiciones.filter(ruta__empresa=empresa)

    entregas_totales = entregas.count()
    entregas_exitosas = entregas.filter(estado='entregado').count()
    entregas_fallidas = entregas.filter(estado='fallido').count()
    entregas_reprogramadas = entregas.filter(estado='reprogramado').count()
    entregas_con_evidencia = entregas.filter(foto_evidencia__isnull=False).exclude(foto_evidencia='').count()
    clientes_atendidos = entregas.filter(estado='entregado').values('cliente_id').distinct().count()
    comunas_cubiertas = (
        entregas.filter(estado='entregado')
        .exclude(cliente__comuna='')
        .values('cliente__comuna')
        .distinct()
        .count()
    )

    total_consolidado = rutas.filter(estado='completada').aggregate(total=Sum('total_consolidado'))['total'] or Decimal('0')
    total_km = rendiciones.aggregate(total=Sum('total_kilometros_recorridos'))['total'] or Decimal('0')
    total_facturas_entregadas = rendiciones.aggregate(total=Sum('facturas_entregadas'))['total'] or 0
    total_facturas_nulas = rendiciones.aggregate(total=Sum('facturas_nulas'))['total'] or 0

    weekday_counter = Counter()
    comuna_counter = Counter()
    for entrega in entregas:
        weekday_counter[entrega.fecha_programada.weekday()] += 1
        comuna = (entrega.cliente.comuna or 'Sin comuna').strip()
        comuna_counter[comuna] += 1

    cargas_por_dia = [
        {
            'dia': WEEKDAY_LABELS[weekday],
            'total': weekday_counter.get(weekday, 0),
        }
        for weekday in range(7)
        if weekday_counter.get(weekday, 0)
    ]
    top_comunas = [
        {'nombre': nombre, 'total': total}
        for nombre, total in comuna_counter.most_common(5)
    ]

    metrics = {
        'entregas_totales': entregas_totales,
        'entregas_exitosas': entregas_exitosas,
        'entregas_fallidas': entregas_fallidas,
        'entregas_reprogramadas': entregas_reprogramadas,
        'tasa_exito': _safe_percentage(entregas_exitosas, entregas_totales),
        'cobertura_evidencia': _safe_percentage(entregas_con_evidencia, entregas_exitosas),
        'entregas_con_evidencia': entregas_con_evidencia,
        'clientes_atendidos': clientes_atendidos,
        'comunas_cubiertas': comunas_cubiertas,
        'total_consolidado': total_consolidado,
        'total_km': total_km,
        'total_facturas_entregadas': total_facturas_entregadas,
        'total_facturas_nulas': total_facturas_nulas,
    }

    metric_cards = [
        {
            'label': 'Entregas del período',
            'value': str(metrics['entregas_totales']),
            'helper': f"{metrics['entregas_exitosas']} entregadas correctamente",
            'icon': 'fa-boxes-stacked',
            'color': 'primary',
        },
        {
            'label': 'Cumplimiento de entrega',
            'value': f"{metrics['tasa_exito']}%",
            'helper': f"{metrics['entregas_fallidas']} fallidas y {metrics['entregas_reprogramadas']} reprogramadas",
            'icon': 'fa-circle-check',
            'color': 'success',
        },
        {
            'label': 'Monto consolidado',
            'value': _format_currency(metrics['total_consolidado']),
            'helper': f"{metrics['total_facturas_entregadas']} facturas entregadas",
            'icon': 'fa-sack-dollar',
            'color': 'info',
        },
        {
            'label': 'Kilómetros recorridos',
            'value': f"{_format_decimal(metrics['total_km'])} km",
            'helper': f"{metrics['clientes_atendidos']} clientes atendidos en {metrics['comunas_cubiertas']} comunas",
            'icon': 'fa-route',
            'color': 'warning',
        },
    ]

    insights = build_narrative(metrics, cargas_por_dia, top_comunas)
    detail_rows = [
        {
            'fecha_programada': entrega.fecha_programada,
            'cliente': entrega.cliente.nombre,
            'comuna': entrega.cliente.comuna or 'Sin comuna',
            'estado': entrega.get_estado_display(),
            'conductor': entrega.conductor.get_full_name() if entrega.conductor else 'Sin asignar',
            'evidencia': bool(entrega.foto_evidencia),
        }
        for entrega in entregas[:200]
    ]

    return {
        'empresa': empresa,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'generated_at': timezone.localtime(),
        'metrics': metrics,
        'metric_cards': metric_cards,
        'cargas_por_dia': cargas_por_dia,
        'top_comunas': top_comunas,
        'insights': insights,
        'detail_rows': detail_rows,
        'has_data': entregas_totales > 0 or rutas.exists() or rendiciones.exists(),
        'summary': {
            'total_consolidado_label': _format_currency(metrics['total_consolidado']),
            'total_km_label': f"{_format_decimal(metrics['total_km'])} km",
            'cobertura_evidencia_label': f"{metrics['cobertura_evidencia']}%",
        },
    }


def build_narrative(metrics, cargas_por_dia, top_comunas):
    insights = []

    tasa_exito = metrics['tasa_exito']
    if tasa_exito >= 90:
        insights.append('El período muestra un cumplimiento operativo alto, con una tasa de entrega exitosa que respalda la continuidad y calidad del servicio prestado.')
    elif tasa_exito >= 75:
        insights.append('El servicio mantiene un nivel de cumplimiento sólido, aunque todavía existe margen para reducir intentos fallidos y reforzar la eficiencia operativa.')
    else:
        insights.append('El período presenta una oportunidad clara de mejora en cumplimiento, por lo que conviene revisar causas de fallas y reprogramaciones antes de una conversación comercial.')

    if metrics['cobertura_evidencia'] >= 70:
        insights.append('La trazabilidad operativa es consistente: una proporción alta de entregas exitosas cuenta con evidencia registrada, lo que fortalece la transparencia frente a la empresa.')

    if top_comunas:
        comuna_principal = top_comunas[0]
        insights.append(
            f"La operación tuvo mayor concentración en {comuna_principal['nombre']}, lo que ayuda a mostrar cobertura territorial y experiencia sostenida en los sectores de mayor demanda."
        )

    if cargas_por_dia:
        max_day = max(cargas_por_dia, key=lambda item: item['total'])
        min_day = min(cargas_por_dia, key=lambda item: item['total'])
        if max_day['total'] >= (min_day['total'] * 2) and max_day['total'] - min_day['total'] >= 3:
            insights.append(
                f"Se observa una carga semanal desbalanceada: {max_day['dia']} concentra {max_day['total']} entregas versus {min_day['dia']} con {min_day['total']}. Esto abre una oportunidad concreta para redistribuir sectores cercanos y estabilizar la operación semanal."
            )
        else:
            insights.append('La distribución semanal de entregas se ve relativamente equilibrada, lo que refleja una operación estable y una buena utilización de la capacidad disponible.')

    return insights


def export_report_to_excel(report):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError as exc:
        raise RuntimeError('La exportación Excel requiere openpyxl instalado en el entorno.') from exc

    workbook = Workbook()
    resumen = workbook.active
    resumen.title = 'Resumen'
    resumen.append(['Informe de Servicio'])
    resumen.append(['Empresa', report['empresa'].nombre if report['empresa'] else 'Sin empresa'])
    resumen.append(['Periodo', f"{report['fecha_desde']} a {report['fecha_hasta']}"])
    resumen.append([])
    resumen.append(['Indicador', 'Valor'])
    for cell in resumen[5]:
        cell.font = Font(bold=True)

    rows = [
        ('Entregas del período', report['metrics']['entregas_totales']),
        ('Entregas exitosas', report['metrics']['entregas_exitosas']),
        ('Tasa de éxito', f"{report['metrics']['tasa_exito']}%"),
        ('Monto consolidado', _format_currency(report['metrics']['total_consolidado'])),
        ('Kilómetros recorridos', report['summary']['total_km_label']),
        ('Clientes atendidos', report['metrics']['clientes_atendidos']),
        ('Comunas cubiertas', report['metrics']['comunas_cubiertas']),
        ('Cobertura de evidencia', report['summary']['cobertura_evidencia_label']),
    ]
    for row in rows:
        resumen.append(list(row))

    detalle = workbook.create_sheet('Detalle')
    detalle.append(['Fecha programada', 'Cliente', 'Comuna', 'Estado', 'Conductor', 'Evidencia'])
    for cell in detalle[1]:
        cell.font = Font(bold=True)

    for row in report['detail_rows']:
        detalle.append([
            row['fecha_programada'].isoformat(),
            row['cliente'],
            row['comuna'],
            row['estado'],
            row['conductor'],
            'Sí' if row['evidencia'] else 'No',
        ])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def export_report_to_pdf(report):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RuntimeError('La exportación PDF requiere reportlab instalado en el entorno.') from exc

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    pdf.setTitle('Informe de Servicio')
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(50, y, 'PADACI - Informe de Servicio')
    y -= 24
    pdf.setFont('Helvetica', 11)
    empresa_nombre = report['empresa'].nombre if report['empresa'] else 'Sin empresa seleccionada'
    pdf.drawString(50, y, f'Empresa: {empresa_nombre}')
    y -= 16
    pdf.drawString(50, y, f"Periodo: {report['fecha_desde']} a {report['fecha_hasta']}")
    y -= 24

    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(50, y, 'Resumen Ejecutivo')
    y -= 18
    pdf.setFont('Helvetica', 10)
    lines = [
        f"Entregas del período: {report['metrics']['entregas_totales']}",
        f"Entregas exitosas: {report['metrics']['entregas_exitosas']} ({report['metrics']['tasa_exito']}%)",
        f"Monto consolidado: {_format_currency(report['metrics']['total_consolidado'])}",
        f"Kilómetros recorridos: {report['summary']['total_km_label']}",
        f"Clientes atendidos: {report['metrics']['clientes_atendidos']}",
        f"Comunas cubiertas: {report['metrics']['comunas_cubiertas']}",
    ]
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 15

    y -= 8
    pdf.setFont('Helvetica-Bold', 12)
    pdf.drawString(50, y, 'Conclusiones automáticas')
    y -= 18
    pdf.setFont('Helvetica', 10)
    for insight in report['insights']:
        for chunk in _split_text(insight, 95):
            pdf.drawString(50, y, f'- {chunk}')
            y -= 14
            if y < 70:
                pdf.showPage()
                y = height - 50
                pdf.setFont('Helvetica', 10)

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


def _split_text(value, max_len):
    words = value.split()
    lines = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + len(current) > max_len:
            lines.append(' '.join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word)
    if current:
        lines.append(' '.join(current))
    return lines
