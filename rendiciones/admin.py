from django.contrib import admin
from .models import (
    RendicionReparto,
    CreditoDocumentoItem,
    DevolucionParcialItem,
    CreditoConfianzaItem,
    FacturaNulaItem,
    DepositoTransferenciaItem,
)


class CreditoDocumentoInline(admin.TabularInline):
    model = CreditoDocumentoItem
    extra = 0


class DevolucionParcialInline(admin.TabularInline):
    model = DevolucionParcialItem
    extra = 0


class CreditoConfianzaInline(admin.TabularInline):
    model = CreditoConfianzaItem
    extra = 0


class FacturaNulaInline(admin.TabularInline):
    model = FacturaNulaItem
    extra = 0


class DepositoTransferenciaInline(admin.TabularInline):
    model = DepositoTransferenciaItem
    extra = 0


@admin.register(RendicionReparto)
class RendicionRepartoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'ruta', 'nombre_repartidor', 'total_consolidado', 'total_dinero_recibir')
    search_fields = ('nombre_repartidor', 'distribuidora', 'ruta__conductor__first_name', 'ruta__conductor__last_name')
    list_filter = ('fecha',)
    inlines = [
        CreditoDocumentoInline,
        DevolucionParcialInline,
        CreditoConfianzaInline,
        FacturaNulaInline,
        DepositoTransferenciaInline,
    ]
