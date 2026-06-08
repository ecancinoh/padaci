from django.conf import settings
from django.db import models
from django.utils import timezone


class Asistencia(models.Model):
    ESTADO_PRESENTE = 'presente'
    ESTADO_AUSENTE = 'ausente'

    ESTADO_CHOICES = [
        (ESTADO_PRESENTE, 'Presente'),
        (ESTADO_AUSENTE, 'Ausente'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='asistencias',
        verbose_name='Trabajador',
    )
    fecha = models.DateField(default=timezone.localdate, verbose_name='Fecha')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ESTADO_PRESENTE, verbose_name='Estado')
    observacion = models.CharField(max_length=255, blank=True, verbose_name='Observación')
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asistencias_registradas',
        verbose_name='Registrado por',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        ordering = ['-fecha', 'usuario__last_name', 'usuario__first_name']
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'fecha'], name='uq_asistencia_usuario_fecha'),
        ]

    def __str__(self):
        return f'{self.usuario.get_full_name()} - {self.fecha} - {self.get_estado_display()}'
