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
    numero_factura_ref = models.CharField(
        max_length=40,
        blank=True,
        default='',
        db_index=True,
        verbose_name='N° factura (referencia)'
    )
    total_factura_ref = models.DecimalField(
        max_digits=14,
        decimal_places=0,
        default=0,
        verbose_name='Total factura (referencia)',
    )
    dia_factura_ref = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Día factura (referencia)',
    )
    mes_factura_ref = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Mes factura (referencia)',
    )
    condicion_pago_ref = models.CharField(
        max_length=120,
        blank=True,
        default='',
        verbose_name='Condición pago (referencia)',
    )
    direccion_factura_ref = models.TextField(
        blank=True,
        default='',
        verbose_name='Dirección factura (referencia)',
    )
    comuna_factura_ref = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Comuna factura (referencia)',
    )
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

    MODALIDAD_CHOICES = [
        ('estandar', 'Estandar'),
        ('falabella', 'Falabella'),
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
    modalidad = models.CharField(
        max_length=20,
        choices=MODALIDAD_CHOICES,
        default='estandar',
        verbose_name='Modalidad de ruta',
        db_index=True,
    )
    patente = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name='Patente',
        help_text='Patente asociada a la ruta importada.',
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
    ocr_facturas_raw = models.JSONField(
        blank=True,
        null=True,
        verbose_name='OCR facturas (raw)',
        help_text='Respuesta estructurada del OCR de facturas para revisión.',
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


class ParadaFalabellaMeta(models.Model):
    """Metadatos Falabella por parada para resolución de direcciones."""

    ESTADO_DIRECCION_CHOICES = [
        ('pendiente_busqueda', 'Pendiente de busqueda'),
        ('candidatos_disponibles', 'Candidatos disponibles'),
        ('requiere_llamada_cliente', 'Requiere llamada al cliente'),
        ('confirmada_manual', 'Confirmada manualmente'),
    ]

    parada = models.OneToOneField(
        ParadaRuta,
        on_delete=models.CASCADE,
        related_name='falabella_meta',
        verbose_name='Parada',
    )
    direccion_importada = models.TextField(blank=True, default='', verbose_name='Direccion importada de Falabella')
    localidad_importada = models.CharField(max_length=140, blank=True, default='', verbose_name='Localidad importada de Falabella')
    direccion_original = models.TextField(blank=True, default='', verbose_name='Direccion original')
    localidad_original = models.CharField(max_length=140, blank=True, default='', verbose_name='Localidad original')
    contacto_original = models.CharField(max_length=80, blank=True, default='', verbose_name='Contacto original')
    estado_direccion = models.CharField(
        max_length=30,
        choices=ESTADO_DIRECCION_CHOICES,
        default='pendiente_busqueda',
        verbose_name='Estado direccion',
    )
    observacion_llamada = models.CharField(max_length=240, blank=True, default='', verbose_name='Observacion llamada')
    cantidad_pedidos = models.PositiveSmallIntegerField(default=1, verbose_name='Cantidad de pedidos en esta parada')
    coordenada_manual_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Latitud manual')
    coordenada_manual_lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name='Longitud manual')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Parada Falabella (meta)'
        verbose_name_plural = 'Paradas Falabella (meta)'

    def __str__(self):
        return f'Meta parada {self.parada_id}'


class ParadaUbicacionCandidata(models.Model):
    """Candidatos de ubicación de una parada provenientes de geocodificación."""

    parada = models.ForeignKey(
        ParadaRuta,
        on_delete=models.CASCADE,
        related_name='ubicaciones_candidatas',
        verbose_name='Parada',
    )
    proveedor = models.CharField(max_length=40, default='nominatim', verbose_name='Proveedor')
    etiqueta = models.CharField(max_length=240, blank=True, default='', verbose_name='Etiqueta')
    direccion_formateada = models.TextField(blank=True, default='', verbose_name='Direccion formateada')
    latitud = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Latitud')
    longitud = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Longitud')
    score = models.DecimalField(max_digits=6, decimal_places=4, default=0, verbose_name='Score')
    orden = models.PositiveSmallIntegerField(default=1, verbose_name='Orden sugerencia')
    seleccionada = models.BooleanField(default=False, verbose_name='Seleccionada')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ubicacion candidata de parada'
        verbose_name_plural = 'Ubicaciones candidatas de parada'
        ordering = ['parada_id', 'orden', 'id']
        indexes = [
            models.Index(fields=['parada', 'seleccionada']),
        ]

    def __str__(self):
        return f'Parada {self.parada_id} - {self.proveedor} #{self.orden}'


class FacturaOCRLinea(models.Model):
    """Línea OCR de factura detectada desde hoja de ruta."""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente validación'),
        ('confirmada', 'Confirmada'),
        ('omitida', 'Omitida'),
    ]

    ruta = models.ForeignKey(
        RutaDia,
        on_delete=models.CASCADE,
        related_name='facturas_ocr',
        verbose_name='Ruta',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas_ocr_asociadas',
        verbose_name='Cliente asociado',
    )
    entrega = models.ForeignKey(
        Entrega,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lineas_factura_ocr',
        verbose_name='Entrega asociada',
    )

    numero_factura = models.CharField(max_length=40, blank=True, default='', verbose_name='N° factura')
    nombre_cliente_ocr = models.CharField(max_length=240, blank=True, default='', verbose_name='Cliente OCR')
    direccion_ocr = models.TextField(blank=True, default='', verbose_name='Dirección OCR')
    comuna_ocr = models.CharField(max_length=120, blank=True, default='', verbose_name='Comuna OCR')
    dia_factura = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Día factura')
    mes_factura = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Mes factura')
    total_factura = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Total factura')
    transportista = models.CharField(max_length=140, blank=True, default='', verbose_name='Transportista')
    condicion_pago = models.CharField(max_length=140, blank=True, default='', verbose_name='Condición pago')

    estado_validacion = models.CharField(
        max_length=12,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado validación',
    )
    requiere_revision = models.BooleanField(default=False, verbose_name='Requiere revisión')
    observacion_validacion = models.CharField(max_length=240, blank=True, default='', verbose_name='Observación validación')
    audit_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facturas_ocr_validadas',
        verbose_name='Validado por',
    )
    fecha_validacion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha validación')

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Línea OCR de factura'
        verbose_name_plural = 'Líneas OCR de factura'
        ordering = ['ruta', 'id']
        indexes = [
            models.Index(fields=['ruta', 'numero_factura']),
        ]

    def __str__(self):
        factura = self.numero_factura or f'linea-{self.pk}'
        return f'Ruta {self.ruta_id} - Factura {factura}'


class ClienteOCRAlias(models.Model):
    """Memoria global para asociar texto OCR a un cliente real."""

    clave_normalizada = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Clave OCR normalizada',
    )
    nombre_ocr = models.CharField(max_length=240, blank=True, default='', verbose_name='Cliente OCR')
    direccion_ocr = models.TextField(blank=True, default='', verbose_name='Dirección OCR')
    comuna_ocr = models.CharField(max_length=120, blank=True, default='', verbose_name='Comuna OCR')
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='alias_ocr',
        verbose_name='Cliente asociado',
    )
    bloqueado_por_conflicto = models.BooleanField(
        default=False,
        verbose_name='Bloqueado por conflicto',
        help_text='Si se detectaron asociaciones distintas para la misma clave OCR, no se autoselecciona.',
    )
    audit_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alias_ocr_actualizados',
        verbose_name='Actualizado por',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Alias OCR de cliente'
        verbose_name_plural = 'Alias OCR de clientes'
        ordering = ['-fecha_actualizacion']
        indexes = [
            models.Index(fields=['bloqueado_por_conflicto']),
            models.Index(fields=['cliente']),
        ]

    def __str__(self):
        estado = 'conflicto' if self.bloqueado_por_conflicto else 'activo'
        return f'{self.nombre_ocr or self.clave_normalizada} -> {self.cliente} ({estado})'
