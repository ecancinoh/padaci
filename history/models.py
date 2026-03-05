from django.db import models
from django.conf import settings
from routes.models import Entrega


class HistorialDia(models.Model):
    """Resumen de entregas agrupadas por día."""

    fecha = models.DateField(unique=True, verbose_name='Fecha')
    total_entregas = models.PositiveIntegerField(default=0, verbose_name='Total Entregas')
    entregadas = models.PositiveIntegerField(default=0, verbose_name='Entregadas')
    fallidas = models.PositiveIntegerField(default=0, verbose_name='Fallidas')
    reprogramadas = models.PositiveIntegerField(default=0, verbose_name='Reprogramadas')
    devueltas = models.PositiveIntegerField(default=0, verbose_name='Devueltas')
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historiales',
        verbose_name='Conductor',
    )
    observacion = models.TextField(blank=True, null=True, verbose_name='Observación del día')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial del Día'
        verbose_name_plural = 'Historial de Días'
        ordering = ['-fecha']

    def __str__(self):
        return f'Historial {self.fecha} – {self.entregadas}/{self.total_entregas} entregadas'

    def porcentaje_exito(self):
        if self.total_entregas == 0:
            return 0
        return round((self.entregadas / self.total_entregas) * 100, 1)


class DetalleHistorial(models.Model):
    """Detalle de cada entrega incluida en el historial diario."""

    historial = models.ForeignKey(
        HistorialDia,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='Historial',
    )
    entrega = models.ForeignKey(
        Entrega,
        on_delete=models.CASCADE,
        related_name='detalles_historial',
        verbose_name='Entrega',
    )
    estado_final = models.CharField(max_length=15, verbose_name='Estado Final')
    hora_registro = models.TimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Detalle de Historial'
        verbose_name_plural = 'Detalles de Historial'
        unique_together = ('historial', 'entrega')

    def __str__(self):
        return f'{self.historial.fecha} – {self.entrega.numero_guia}'
