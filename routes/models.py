from django.db import models
from django.conf import settings
from companies.models import Empresa
from deliveries.models import Entrega


class RutaDia(models.Model):
    """Ruta de reparto diaria asignada a un conductor."""

    ESTADO_CHOICES = [
        ('planificada', 'Planificada'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    fecha = models.DateField(verbose_name='Fecha de Ruta')
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='rutas',
        verbose_name='Empresa',
        null=True,
        blank=True,
    )
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='rutas',
        verbose_name='Conductor',
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='planificada', verbose_name='Estado')
    foto_hoja_ruta = models.ImageField(
        upload_to='rutas/fotos/',
        blank=True,
        null=True,
        verbose_name='Foto Hoja de Ruta',
        help_text='Sube una foto de la hoja de ruta para extraer los clientes automáticamente con IA.',
    )
    texto_extraido = models.TextField(
        blank=True, null=True,
        verbose_name='Texto extraído OCR',
        help_text='Texto detectado automáticamente en la foto.',
    )
    observacion = models.TextField(blank=True, null=True, verbose_name='Observación')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ruta del Día'
        verbose_name_plural = 'Rutas del Día'
        ordering = ['-fecha']
        unique_together = ('fecha', 'conductor')

    def __str__(self):
        return f'Ruta {self.fecha} – {self.conductor.get_full_name()}'

    def total_paradas(self):
        return self.paradas.count()


class ParadaRuta(models.Model):
    """Parada individual dentro de una ruta diaria."""

    ruta = models.ForeignKey(
        RutaDia,
        on_delete=models.CASCADE,
        related_name='paradas',
        verbose_name='Ruta',
    )
    entrega = models.ForeignKey(
        Entrega,
        on_delete=models.CASCADE,
        related_name='paradas',
        verbose_name='Entrega',
    )
    orden = models.PositiveSmallIntegerField(verbose_name='Orden de visita')
    distancia_anterior_km = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name='Distancia desde parada anterior (km)',
    )
    hora_estimada = models.TimeField(null=True, blank=True, verbose_name='Hora Estimada')
    hora_real = models.TimeField(null=True, blank=True, verbose_name='Hora Real')

    class Meta:
        verbose_name = 'Parada de Ruta'
        verbose_name_plural = 'Paradas de Ruta'
        ordering = ['ruta', 'orden']
        unique_together = ('ruta', 'orden')

    def __str__(self):
        return f'{self.ruta} – Parada {self.orden}: {self.entrega.cliente}'
