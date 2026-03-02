from django.contrib import admin
from .models import Entrega


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'empresa', 'estado', 'fecha_programada', 'conductor')
    list_filter = ('estado', 'fecha_programada', 'empresa')
    search_fields = ('cliente__nombre', 'empresa__nombre')
    date_hierarchy = 'fecha_programada'
    raw_id_fields = ('cliente', 'empresa', 'conductor')
