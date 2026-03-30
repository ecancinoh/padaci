from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'empresa', 'ciudad', 'tiempo_estimado_atencion', 'telefono', 'activo')
    list_filter = ('activo', 'ciudad', 'empresa')
    search_fields = ('nombre', 'apellido', 'rut', 'email', 'direccion')
    raw_id_fields = ('empresa',)

    def has_delete_permission(self, request, obj=None):
        # Solo permite eliminar si el usuario NO es conductor ni peoneta
        return request.user.rol not in {'conductor', 'peoneta'} and super().has_delete_permission(request, obj)
