from django.db import migrations, models


def aplicar_defaults_urbanos(apps, schema_editor):
    PlanificacionSemanal = apps.get_model('planner', 'PlanificacionSemanal')

    # Solo ajusta planes que siguen con valores antiguos del primer rollout.
    PlanificacionSemanal.objects.filter(
        max_km_diario=120,
        velocidad_promedio_kmh=28,
        minutos_servicio_por_cliente=12,
        max_horas_jornada=8,
    ).update(
        max_km_diario=90,
        velocidad_promedio_kmh=25,
        minutos_servicio_por_cliente=14,
        max_horas_jornada=8.5,
    )


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0002_planificacionsemanal_operacion_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='planificacionsemanal',
            name='max_horas_jornada',
            field=models.DecimalField(decimal_places=1, default=8.5, max_digits=4, verbose_name='Maximo horas por jornada'),
        ),
        migrations.AlterField(
            model_name='planificacionsemanal',
            name='max_km_diario',
            field=models.DecimalField(decimal_places=1, default=90, help_text='Limite diario de kilometros estimados para controlar gasto de combustible.', max_digits=6, verbose_name='Maximo km por dia'),
        ),
        migrations.AlterField(
            model_name='planificacionsemanal',
            name='minutos_servicio_por_cliente',
            field=models.PositiveIntegerField(default=14, help_text='Tiempo medio para atender un cliente (estacionar, entregar, validar).', verbose_name='Minutos por atencion'),
        ),
        migrations.AlterField(
            model_name='planificacionsemanal',
            name='velocidad_promedio_kmh',
            field=models.DecimalField(decimal_places=1, default=25, help_text='Velocidad promedio esperada en ruta para estimar tiempos.', max_digits=5, verbose_name='Velocidad promedio (km/h)'),
        ),
        migrations.RunPython(aplicar_defaults_urbanos, noop_reverse),
    ]
