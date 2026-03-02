from django.contrib import admin
from .models import HistorialDia, DetalleHistorial


class DetalleHistorialInline(admin.TabularInline):
    model = DetalleHistorial
    extra = 0


@admin.register(HistorialDia)
class HistorialDiaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'conductor', 'total_entregas', 'entregadas', 'fallidas', 'porcentaje_exito')
    list_filter = ('fecha', 'conductor')
    date_hierarchy = 'fecha'
    inlines = [DetalleHistorialInline]
