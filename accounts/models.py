from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """Usuario personalizado del sistema PADACI."""

    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('supervisor', 'Supervisor'),
        ('conductor', 'Conductor'),
        ('operador', 'Operador'),
    ]

    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='operador', verbose_name='Rol')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    rut = models.CharField(max_length=12, blank=True, null=True, unique=True, verbose_name='RUT')
    foto = models.ImageField(upload_to='usuarios/', blank=True, null=True, verbose_name='Foto')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.get_full_name()} ({self.get_rol_display()})'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username
