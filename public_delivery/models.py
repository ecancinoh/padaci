import uuid

from django.conf import settings
from django.db import models


def _generate_tracking_code():
    return 'RC-' + uuid.uuid4().hex[:6].upper()


class EntregaPublica(models.Model):
    VEHICLE_JAC = 'jac_x200'
    VEHICLE_MAXUS = 'maxus_c35l'
    VEHICLE_CHOICES = [
        (VEHICLE_JAC, 'JAC X200 (hasta 1.7 ton)'),
        (VEHICLE_MAXUS, 'Maxus C35L (hasta 3.5 ton)'),
    ]

    STATUS_SCHEDULED = 'scheduled'
    STATUS_PICKED_UP = 'picked_up'
    STATUS_IN_ROUTE = 'in_route'
    STATUS_DELIVERED = 'delivered'
    STATUS_ISSUE = 'issue'
    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Programada'),
        (STATUS_PICKED_UP, 'Retirada'),
        (STATUS_IN_ROUTE, 'En ruta'),
        (STATUS_DELIVERED, 'Entregada'),
        (STATUS_ISSUE, 'Incidencia'),
    ]

    tracking_code = models.CharField(
        max_length=20, unique=True, default=_generate_tracking_code,
        verbose_name='Código de seguimiento',
    )
    vehicle = models.CharField(
        max_length=20, choices=VEHICLE_CHOICES, default=VEHICLE_JAC,
        verbose_name='Vehículo',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED,
        verbose_name='Estado',
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='entregas_publicas',
        limit_choices_to={'rol': 'conductor'},
        verbose_name='Conductor',
    )
    driver_name = models.CharField(max_length=100, blank=True, verbose_name='Nombre conductor')
    scheduled_for = models.DateField(null=True, blank=True, verbose_name='Fecha programada')
    client_name = models.CharField(max_length=200, blank=True, verbose_name='Cliente')
    client_phone = models.CharField(max_length=30, blank=True, verbose_name='Teléfono cliente')
    notes = models.TextField(blank=True, verbose_name='Notas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Entrega pública'
        verbose_name_plural = 'Entregas públicas'

    def __str__(self):
        return f'{self.tracking_code} — {self.get_status_display()}'

    def save(self, *args, **kwargs):
        if self.driver and not self.driver_name:
            self.driver_name = self.driver.get_full_name() or self.driver.username
        super().save(*args, **kwargs)


class ParadaPublica(models.Model):
    STATUS_CHOICES = EntregaPublica.STATUS_CHOICES

    entrega = models.ForeignKey(
        EntregaPublica, on_delete=models.CASCADE, related_name='paradas',
        verbose_name='Entrega',
    )
    stop_order = models.PositiveSmallIntegerField(verbose_name='Orden')
    label = models.CharField(max_length=200, verbose_name='Descripción del punto')
    address = models.CharField(max_length=300, verbose_name='Dirección')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=EntregaPublica.STATUS_SCHEDULED,
        verbose_name='Estado',
    )
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Hora entrega')
    notes = models.CharField(max_length=300, blank=True, verbose_name='Notas')

    class Meta:
        ordering = ['stop_order']
        unique_together = ('entrega', 'stop_order')
        verbose_name = 'Parada'
        verbose_name_plural = 'Paradas'

    def __str__(self):
        return f'{self.entrega.tracking_code} · Parada {self.stop_order}: {self.label}'


class EventoParada(models.Model):
    entrega = models.ForeignKey(
        EntregaPublica, on_delete=models.CASCADE, related_name='eventos',
        verbose_name='Entrega',
    )
    parada = models.ForeignKey(
        ParadaPublica, on_delete=models.CASCADE, related_name='eventos',
        null=True, blank=True, verbose_name='Parada',
    )
    note = models.CharField(max_length=500, verbose_name='Nota')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Registrado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'

    def __str__(self):
        return f'{self.entrega.tracking_code} · {self.note[:50]}'
