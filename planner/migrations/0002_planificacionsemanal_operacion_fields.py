from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='planificacionsemanal',
            name='max_horas_jornada',
            field=models.DecimalField(decimal_places=1, default=8, max_digits=4, verbose_name='Maximo horas por jornada'),
        ),
        migrations.AddField(
            model_name='planificacionsemanal',
            name='max_km_diario',
            field=models.DecimalField(decimal_places=1, default=120, help_text='Limite diario de kilometros estimados para controlar gasto de combustible.', max_digits=6, verbose_name='Maximo km por dia'),
        ),
        migrations.AddField(
            model_name='planificacionsemanal',
            name='minutos_servicio_por_cliente',
            field=models.PositiveIntegerField(default=12, help_text='Tiempo medio para atender un cliente (estacionar, entregar, validar).', verbose_name='Minutos por atencion'),
        ),
        migrations.AddField(
            model_name='planificacionsemanal',
            name='velocidad_promedio_kmh',
            field=models.DecimalField(decimal_places=1, default=28, help_text='Velocidad promedio esperada en ruta para estimar tiempos.', max_digits=5, verbose_name='Velocidad promedio (km/h)'),
        ),
    ]
