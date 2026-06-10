from django.contrib import admin
from .models import RutaDia, ParadaRuta, Entrega, EntregaPago, FacturaOCRLinea, ClienteOCRAlias


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
    list_display = (
        'cliente',
        'numero_factura_ref',
        'total_factura_ref',
        'empresa',
        'estado',
        'estado_pago',
        'fecha_programada',
        'conductor',
    )
    list_filter = ('estado', 'estado_pago', 'fecha_programada', 'empresa')
    search_fields = ('cliente__nombre', 'empresa__nombre', 'numero_factura_ref')
    date_hierarchy = 'fecha_programada'
    raw_id_fields = ('cliente', 'empresa', 'conductor')


@admin.register(EntregaPago)
class EntregaPagoAdmin(admin.ModelAdmin):
    list_display = ('entrega', 'metodo', 'monto', 'tiene_documento_credito', 'registrado_por', 'fecha_registro')
    list_filter = ('metodo', 'tiene_documento_credito', 'fecha_registro')
    search_fields = ('entrega__cliente__nombre', 'observacion')


@admin.register(FacturaOCRLinea)
class FacturaOCRLineaAdmin(admin.ModelAdmin):
    list_display = (
        'ruta',
        'numero_factura',
        'nombre_cliente_ocr',
        'cliente',
        'total_factura',
        'estado_validacion',
        'requiere_revision',
    )
    list_filter = ('estado_validacion', 'requiere_revision', 'ruta__fecha')
    search_fields = ('numero_factura', 'nombre_cliente_ocr', 'cliente__nombre', 'direccion_ocr', 'comuna_ocr')
    raw_id_fields = ('ruta', 'cliente', 'entrega', 'audit_usuario')


@admin.register(ClienteOCRAlias)
class ClienteOCRAliasAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_ocr',
        'comuna_ocr',
        'cliente',
        'bloqueado_por_conflicto',
        'fecha_actualizacion',
    )
    list_filter = ('bloqueado_por_conflicto', 'comuna_ocr')
    search_fields = ('nombre_ocr', 'direccion_ocr', 'comuna_ocr', 'cliente__nombre', 'clave_normalizada')
    raw_id_fields = ('cliente', 'audit_usuario')
