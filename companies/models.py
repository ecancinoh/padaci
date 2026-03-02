from django.db import models


class Empresa(models.Model):
    """Empresa distribuidora solicitante de las entregas."""

    nombre = models.CharField(max_length=200, verbose_name='Nombre Empresa')
    razon_social = models.CharField(max_length=200, verbose_name='Razón Social')
    rut = models.CharField(max_length=12, unique=True, verbose_name='RUT Empresa')
    direccion = models.TextField(verbose_name='Dirección')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, null=True, verbose_name='Correo')
    contacto = models.CharField(max_length=100, blank=True, null=True, verbose_name='Persona de Contacto')
    logo = models.ImageField(upload_to='empresas/', blank=True, null=True, verbose_name='Logo')
    activa = models.BooleanField(default=True, verbose_name='Activa')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.rut})'
