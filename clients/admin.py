from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'empresa', 'ciudad', 'telefono', 'activo')
    list_filter = ('activo', 'ciudad', 'empresa')
    search_fields = ('nombre', 'apellido', 'rut', 'email', 'direccion')
    raw_id_fields = ('empresa',)
