from django.contrib import admin
from .models import RutaDia, ParadaRuta


class ParadaRutaInline(admin.TabularInline):
    model = ParadaRuta
    extra = 0
    fields = ('orden', 'entrega', 'hora_estimada', 'hora_real', 'distancia_anterior_km')


@admin.register(RutaDia)
class RutaDiaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'conductor', 'estado', 'total_paradas')
    list_filter = ('estado', 'fecha', 'conductor')
    date_hierarchy = 'fecha'
    inlines = [ParadaRutaInline]
