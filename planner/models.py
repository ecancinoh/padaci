from django.db import models

from clients.models import Cliente
from companies.models import Empresa


class PlanificacionSemanal(models.Model):
    DIAS = [
        ('lun', 'Lunes'),
        ('mar', 'Martes'),
        ('mie', 'Miercoles'),
        ('jue', 'Jueves'),
        ('vie', 'Viernes'),
    ]

    nombre = models.CharField(max_length=120, verbose_name='Nombre del plan')
    clientes_reparto = models.ManyToManyField(
        Cliente,
        blank=True,
        related_name='planes_reparto_semanal',
        verbose_name='Clientes para reparto',
        help_text='Selecciona los clientes que tendran reparto en esta planificacion.',
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planes_semanales',
        verbose_name='Empresa',
    )
    solo_clientes_activos = models.BooleanField(default=True, verbose_name='Solo clientes activos')
    incluir_clientes_sin_coordenadas = models.BooleanField(
        default=True,
        verbose_name='Incluir clientes sin coordenadas',
    )

    capacidad_lunes = models.PositiveIntegerField(null=True, blank=True, verbose_name='Capacidad lunes')
    capacidad_martes = models.PositiveIntegerField(null=True, blank=True, verbose_name='Capacidad martes')
    capacidad_miercoles = models.PositiveIntegerField(null=True, blank=True, verbose_name='Capacidad miercoles')
    capacidad_jueves = models.PositiveIntegerField(null=True, blank=True, verbose_name='Capacidad jueves')
    capacidad_viernes = models.PositiveIntegerField(null=True, blank=True, verbose_name='Capacidad viernes')

    max_km_diario = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=90,
        verbose_name='Maximo km por dia',
        help_text='Limite diario de kilometros estimados para controlar gasto de combustible.',
    )
    velocidad_promedio_kmh = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=25,
        verbose_name='Velocidad promedio (km/h)',
        help_text='Velocidad promedio esperada en ruta para estimar tiempos.',
    )
    minutos_servicio_por_cliente = models.PositiveIntegerField(
        default=14,
        verbose_name='Minutos por atencion',
        help_text='Tiempo medio para atender un cliente (estacionar, entregar, validar).',
    )
    max_horas_jornada = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=8.5,
        verbose_name='Maximo horas por jornada',
    )
    comunas_dia_exclusivo = models.TextField(
        blank=True,
        default='',
        verbose_name='Comunas de dia exclusivo',
        help_text='Lista de comunas separadas por coma. Esas comunas se agendan solo en el dia definido para zonas alejadas.',
    )
    dia_reparto_zonas_alejadas = models.CharField(
        max_length=3,
        choices=DIAS,
        default='vie',
        verbose_name='Dia reparto zonas alejadas',
    )

    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Planificacion semanal'
        verbose_name_plural = 'Planificaciones semanales'
        ordering = ['-fecha_actualizacion', '-id']

    def __str__(self):
        return self.nombre

    def capacidades_por_dia(self):
        return {
            'lun': self.capacidad_lunes,
            'mar': self.capacidad_martes,
            'mie': self.capacidad_miercoles,
            'jue': self.capacidad_jueves,
            'vie': self.capacidad_viernes,
        }


class RecomendacionCliente(models.Model):
    ORIGEN_CHOICES = [
        ('auto', 'Automatico'),
        ('manual', 'Manual'),
    ]

    plan = models.ForeignKey(
        PlanificacionSemanal,
        on_delete=models.CASCADE,
        related_name='recomendaciones',
        verbose_name='Planificacion',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='recomendaciones_semanales',
        verbose_name='Cliente',
    )
    dia_semana = models.CharField(max_length=3, choices=PlanificacionSemanal.DIAS, verbose_name='Dia')
    orden = models.PositiveIntegerField(default=1, verbose_name='Orden')
    origen = models.CharField(max_length=10, choices=ORIGEN_CHOICES, default='auto', verbose_name='Origen')
    bloqueado = models.BooleanField(
        default=False,
        verbose_name='Bloqueado',
        help_text='Si esta activo, no se mueve automaticamente al regenerar.',
    )
    observacion = models.CharField(max_length=255, blank=True, default='', verbose_name='Observacion')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Recomendacion de cliente'
        verbose_name_plural = 'Recomendaciones de clientes'
        ordering = ['dia_semana', 'orden', 'id']
        unique_together = [('plan', 'cliente')]
        indexes = [
            models.Index(fields=['plan', 'dia_semana']),
            models.Index(fields=['plan', 'bloqueado']),
        ]

    def __str__(self):
        return f'{self.plan} - {self.get_dia_semana_display()} - {self.cliente.nombre}'
