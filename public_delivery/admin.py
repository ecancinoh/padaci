from django.contrib import admin
from .models import EntregaPublica, EventoParada, ParadaPublica


class ParadaInline(admin.TabularInline):
    model = ParadaPublica
    extra = 0
    fields = ('stop_order', 'label', 'address', 'status', 'delivered_at')


class EventoInline(admin.TabularInline):
    model = EventoParada
    extra = 0
    fields = ('note', 'parada', 'created_by', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(EntregaPublica)
class EntregaPublicaAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'vehicle', 'status', 'driver_name', 'scheduled_for', 'created_at')
    list_filter = ('status', 'vehicle')
    search_fields = ('tracking_code', 'client_name', 'driver_name')
    inlines = [ParadaInline, EventoInline]
    readonly_fields = ('tracking_code', 'created_at', 'updated_at')
