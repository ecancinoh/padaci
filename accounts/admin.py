from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'email', 'rol', 'activo', 'date_joined')
    list_filter = ('rol', 'activo', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'rut')
    fieldsets = UserAdmin.fieldsets + (
        ('Datos PADACI', {
            'fields': ('rol', 'telefono', 'rut', 'foto', 'activo'),
        }),
    )
