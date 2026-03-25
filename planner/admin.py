from django.contrib import admin

from .models import PlanificacionSemanal, RecomendacionCliente


@admin.register(PlanificacionSemanal)
class PlanificacionSemanalAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'empresa',
        'activo',
        'solo_clientes_activos',
        'incluir_clientes_sin_coordenadas',
        'fecha_actualizacion',
    )
    list_filter = ('activo', 'solo_clientes_activos', 'incluir_clientes_sin_coordenadas', 'empresa')
    search_fields = ('nombre',)


@admin.register(RecomendacionCliente)
class RecomendacionClienteAdmin(admin.ModelAdmin):
    list_display = ('plan', 'cliente', 'dia_semana', 'orden', 'origen', 'bloqueado')
    list_filter = ('dia_semana', 'origen', 'bloqueado', 'plan')
    search_fields = ('cliente__nombre', 'plan__nombre')
