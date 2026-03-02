from django.db import models
from django.conf import settings
from clients.models import Cliente
from companies.models import Empresa


class Entrega(models.Model):
    """Registro individual de entrega de paquete."""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_ruta', 'En Ruta'),
        ('entregado', 'Entregado'),
        ('fallido', 'Intento Fallido'),
        ('reprogramado', 'Reprogramado'),
        ('devuelto', 'Devuelto'),
    ]

    # Relaciones
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='entregas',
        verbose_name='Cliente',
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name='entregas',
        verbose_name='Empresa Solicitante',
        null=True,
        blank=True,
    )
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entregas_asignadas',
        verbose_name='Conductor',
        limit_choices_to={'rol': 'conductor'},
    )

    # Datos del paquete
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción del paquete')

    # Estado
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    fecha_programada = models.DateField(verbose_name='Fecha Programada')
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name='Fecha/Hora Entrega Real')
    observacion = models.TextField(blank=True, null=True, verbose_name='Observación')

    # Firma y evidencia
    foto_evidencia = models.ImageField(upload_to='entregas/evidencia/', blank=True, null=True, verbose_name='Foto Evidencia')

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'
        ordering = ['-fecha_programada', 'cliente']

    def __str__(self):
        return f'Entrega {self.cliente} – {self.fecha_programada} [{self.get_estado_display()}]'

    def esta_completada(self):
        return self.estado == 'entregado'
