from django.db import models
from companies.models import Empresa


class Cliente(models.Model):
    """Cliente receptor de los paquetes."""

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clientes',
        verbose_name='Empresa asociada',
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre del Cliente')
    apellido = models.CharField(max_length=200, blank=True, default='', verbose_name='Apellido')
    rut = models.CharField(max_length=12, blank=True, null=True, verbose_name='RUT')
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, null=True, verbose_name='Correo')

    # Dirección
    comuna = models.CharField(max_length=100, blank=True, default='', verbose_name='Comuna')
    direccion = models.TextField(blank=True, default='', verbose_name='Dirección')
    ciudad = models.CharField(max_length=100, blank=True, default='', verbose_name='Ciudad')
    region = models.CharField(max_length=100, blank=True, default='', verbose_name='Región')
    codigo_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name='Código Postal')

    # Geolocalización para el mapa
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Latitud')
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Longitud')

    notas = models.TextField(blank=True, null=True, verbose_name='Notas')
    observaciones = models.TextField(blank=True, default='', verbose_name='Observaciones', help_text='Indicaciones especiales de entrega, acceso, horarios, etc.')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def nombre_completo(self):
        return self.nombre

    def tiene_coordenadas(self):
        return self.latitud is not None and self.longitud is not None

    @property
    def url_google_maps(self):
        """URL universal que abre Google Maps en la ubicación exacta."""
        if self.tiene_coordenadas():
            return f'https://maps.google.com/?q={self.latitud},{self.longitud}'
        return ''

    @property
    def url_waze(self):
        """URL universal que abre Waze navegando hacia la ubicación."""
        if self.tiene_coordenadas():
            return f'https://waze.com/ul?ll={self.latitud},{self.longitud}&navigate=yes'
        return ''
