from django.contrib import admin
from .models import RutaDia, ParadaRuta, Entrega, EntregaPago


class ParadaRutaInline(admin.TabularInline):
    model = ParadaRuta
    extra = 0
    fields = ('orden', 'entrega', 'hora_estimada', 'hora_real', 'distancia_anterior_km')


@admin.register(RutaDia)
class RutaDiaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'conductor', 'peoneta', 'estado', 'total_consolidado', 'total_paradas')
    list_filter = ('estado', 'fecha', 'conductor', 'peoneta')
    date_hierarchy = 'fecha'
    inlines = [ParadaRutaInline]


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'empresa', 'estado', 'estado_pago', 'fecha_programada', 'conductor')
    list_filter = ('estado', 'estado_pago', 'fecha_programada', 'empresa')
    search_fields = ('cliente__nombre', 'empresa__nombre')
    date_hierarchy = 'fecha_programada'
    raw_id_fields = ('cliente', 'empresa', 'conductor')


@admin.register(EntregaPago)
class EntregaPagoAdmin(admin.ModelAdmin):
    list_display = ('entrega', 'metodo', 'monto', 'tiene_documento_credito', 'registrado_por', 'fecha_registro')
    list_filter = ('metodo', 'tiene_documento_credito', 'fecha_registro')
    search_fields = ('entrega__cliente__nombre', 'observacion')
