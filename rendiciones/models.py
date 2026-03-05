from django.db import models
from decimal import Decimal
from django.db.models import Sum
from routes.models import RutaDia


class RendicionReparto(models.Model):
    ruta = models.OneToOneField(RutaDia, on_delete=models.CASCADE, related_name='rendicion', verbose_name='Ruta del día')
    fecha = models.DateField(verbose_name='Fecha')
    distribuidora = models.CharField(max_length=120, blank=True, verbose_name='Distribuidora')
    nombre_repartidor = models.CharField(max_length=140, verbose_name='Nombre del repartidor')
    nombre_peoneta = models.CharField(max_length=140, blank=True, verbose_name='Nombre del peoneta')

    estacionamientos = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Estacionamientos')
    diferencia_menos = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Diferencia menos')
    diferencia_mas = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Diferencia más')

    total_consolidado = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Total consolidado')
    menos_items = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Menos ítems (A,B,C,D,E)')
    total_dinero_recibir = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Total dinero a recibir')

    facturas_totales = models.PositiveIntegerField(default=0, verbose_name='Facturas totales')
    facturas_entregadas = models.PositiveIntegerField(default=0, verbose_name='Facturas entregadas')
    facturas_nulas = models.PositiveIntegerField(default=0, verbose_name='Facturas nulas')

    kilometraje_inicial = models.DecimalField(max_digits=8, decimal_places=1, default=0, verbose_name='Kilometraje inicial')
    kilometraje_final = models.DecimalField(max_digits=8, decimal_places=1, default=0, verbose_name='Kilometraje final')
    total_kilometros_recorridos = models.DecimalField(max_digits=8, decimal_places=1, default=0, verbose_name='Total kilómetros recorridos')

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rendición de reparto'
        verbose_name_plural = 'Rendiciones de reparto'
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f'Rendición {self.fecha} - {self.nombre_repartidor}'

    def calcular_menos_items(self):
        total_a = self.creditos_documentos.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        total_b = self.devoluciones_parciales.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        total_c = self.creditos_confianza.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        total_d = self.facturas_nulas_detalle.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        total_e = self.depositos_transferencias.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        return total_a + total_b + total_c + total_d + total_e

    def calcular_total_dinero_recibir(self):
        return (self.total_consolidado or Decimal('0')) - (self.menos_items or Decimal('0'))

    def recalcular_totales(self):
        self.menos_items = self.calcular_menos_items()
        self.total_dinero_recibir = self.calcular_total_dinero_recibir()

    def save(self, *args, **kwargs):
        if not getattr(self, '_preserve_total_km_manual', False):
            km_inicial = self.kilometraje_inicial or Decimal('0')
            km_final = self.kilometraje_final or Decimal('0')
            self.total_kilometros_recorridos = km_final - km_inicial
        super().save(*args, **kwargs)


class BaseFacturaMonto(models.Model):
    numero_factura = models.CharField(max_length=40, blank=True, verbose_name='N° factura')
    monto = models.DecimalField(max_digits=14, decimal_places=0, default=0, verbose_name='Monto')

    class Meta:
        abstract = True


class CreditoDocumentoItem(BaseFacturaMonto):
    rendicion = models.ForeignKey(RendicionReparto, on_delete=models.CASCADE, related_name='creditos_documentos')
    nombre_cliente = models.CharField(max_length=140, blank=True, verbose_name='Nombre cliente')
    banco = models.CharField(max_length=120, blank=True, verbose_name='Banco')

    class Meta:
        verbose_name = 'Crédito con documento (A)'
        verbose_name_plural = 'Créditos con documentos (A)'


class DevolucionParcialItem(BaseFacturaMonto):
    rendicion = models.ForeignKey(RendicionReparto, on_delete=models.CASCADE, related_name='devoluciones_parciales')
    motivo = models.CharField(max_length=200, blank=True, verbose_name='Motivo')

    class Meta:
        verbose_name = 'Devolución parcial (B)'
        verbose_name_plural = 'Devoluciones parciales (B)'


class CreditoConfianzaItem(BaseFacturaMonto):
    rendicion = models.ForeignKey(RendicionReparto, on_delete=models.CASCADE, related_name='creditos_confianza')
    autoriza_credito = models.CharField(max_length=140, blank=True, verbose_name='Quién autoriza el crédito')

    class Meta:
        verbose_name = 'Crédito de confianza (C)'
        verbose_name_plural = 'Créditos de confianza (C)'


class FacturaNulaItem(BaseFacturaMonto):
    rendicion = models.ForeignKey(RendicionReparto, on_delete=models.CASCADE, related_name='facturas_nulas_detalle')

    class Meta:
        verbose_name = 'Factura nula (D)'
        verbose_name_plural = 'Facturas nulas (D)'


class DepositoTransferenciaItem(BaseFacturaMonto):
    rendicion = models.ForeignKey(RendicionReparto, on_delete=models.CASCADE, related_name='depositos_transferencias')

    class Meta:
        verbose_name = 'Depósito o transferencia (E)'
        verbose_name_plural = 'Depósitos o transferencias (E)'
