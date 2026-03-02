from django.contrib import admin
from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'telefono', 'email', 'contacto', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre', 'razon_social', 'rut', 'email')
