from django.db import models
from django.conf import settings
from companies.models import Empresa
from clients.models import Cliente


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

    ESTADO_PAGO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado_completo', 'Pagado completo'),
        ('pagado_parcial', 'Pagado parcial'),
        ('sin_pago', 'Sin pago'),
        ('credito', 'Credito'),
    ]

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

    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción del paquete')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    fecha_programada = models.DateField(verbose_name='Fecha Programada')
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name='Fecha/Hora Entrega Real')
    observacion = models.TextField(blank=True, null=True, verbose_name='Observación')
    foto_evidencia = models.ImageField(upload_to='entregas/evidencia/', blank=True, null=True, verbose_name='Foto Evidencia')
    estado_pago = models.CharField(
        max_length=20,
        choices=ESTADO_PAGO_CHOICES,
        default='pendiente',
        verbose_name='Estado de pago',
    )
    pago_registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entregas_pago_registradas',
        verbose_name='Pago registrado por',
    )
    fecha_registro_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha registro pago',
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'
        ordering = ['-fecha_programada', 'cliente']
        db_table = 'deliveries_entrega'

    def __str__(self):
        return f'Entrega {self.cliente} – {self.fecha_programada} [{self.get_estado_display()}]'

    def esta_completada(self):
        return self.estado == 'entregado'

    @property
    def total_pagado(self):
        total = self.pagos.aggregate(total=models.Sum('monto'))['total']
        return total or 0


class EntregaPago(models.Model):
    """Linea de pago individual asociada a una entrega."""

    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('credito', 'Credito'),
        ('transferencia', 'Transferencia'),
        ('descuento', 'Descuento'),
        ('nula', 'Nula'),
    ]

    entrega = models.ForeignKey(
        Entrega,
        on_delete=models.CASCADE,
        related_name='pagos',
        verbose_name='Entrega',
    )
    metodo = models.CharField(
        max_length=15,
        choices=METODO_CHOICES,
        verbose_name='Metodo de pago',
    )
    monto = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name='Monto',
    )
    tiene_documento_credito = models.BooleanField(
        default=False,
        verbose_name='Credito con documento',
        help_text='Solo aplica para pagos con metodo credito.',
    )
    observacion = models.CharField(
        max_length=240,
        blank=True,
        verbose_name='Observacion pago',
    )
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lineas_pago_entrega_registradas',
        verbose_name='Registrado por',
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha registro',
    )

    class Meta:
        verbose_name = 'Linea de pago de entrega'
        verbose_name_plural = 'Lineas de pago de entrega'
        ordering = ['id']

    def __str__(self):
        return f'{self.entrega_id} - {self.get_metodo_display()} - {self.monto}'


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
    peoneta = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='rutas_peoneta',
        verbose_name='Peoneta',
        null=True,
        blank=True,
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='planificada', verbose_name='Estado')
    total_consolidado = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name='Total consolidado (CLP)',
        help_text='Monto total consolidado en pesos chilenos.',
    )
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
