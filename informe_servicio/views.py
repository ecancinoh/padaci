from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.utils.text import slugify
from django.views import View

from accounts.mixins import AdminSupervisorMixin, admin_supervisor_required

from .services import (
    build_service_report,
    export_report_to_excel,
    export_report_to_pdf,
    parse_filters,
)


class InformeServicioView(AdminSupervisorMixin, View):
    template_name = 'informe_servicio/index.html'

    def get(self, request, *args, **kwargs):
        filters = parse_filters(request.GET)
        report = build_service_report(filters)
        context = {
            'filters': filters,
            'report': report,
        }
        return render(request, self.template_name, context)


@admin_supervisor_required
def exportar_excel(request):
    filters = parse_filters(request.GET)
    report = build_service_report(filters)
    try:
        buffer = export_report_to_excel(report)
    except RuntimeError as exc:
        messages.error(request, str(exc))
        return redirect('informe_servicio:index')

    empresa_slug = slugify(report['empresa'].nombre) if report['empresa'] else 'empresa'
    filename = f"informe_servicio_{empresa_slug}_{report['fecha_desde']}_{report['fecha_hasta']}.xlsx"
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


@admin_supervisor_required
def exportar_pdf(request):
    filters = parse_filters(request.GET)
    report = build_service_report(filters)
    try:
        buffer = export_report_to_pdf(report)
    except RuntimeError as exc:
        messages.error(request, str(exc))
        return redirect('informe_servicio:index')

    empresa_slug = slugify(report['empresa'].nombre) if report['empresa'] else 'empresa'
    filename = f"informe_servicio_{empresa_slug}_{report['fecha_desde']}_{report['fecha_hasta']}.pdf"
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/pdf',
    )
