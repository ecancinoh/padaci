from django.contrib import admin

from .models import Asistencia


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'estado', 'registrado_por', 'fecha_actualizacion')
    list_filter = ('fecha', 'estado', 'usuario__rol')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'observacion')
    date_hierarchy = 'fecha'
