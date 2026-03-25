from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_cliente_tiempo_estimado_atencion'),
        ('planner', '0003_ajuste_defaults_urbanos'),
    ]

    operations = [
        migrations.AddField(
            model_name='planificacionsemanal',
            name='clientes_reparto',
            field=models.ManyToManyField(blank=True, help_text='Selecciona los clientes que tendran reparto en esta planificacion.', related_name='planes_reparto_semanal', to='clients.cliente', verbose_name='Clientes para reparto'),
        ),
    ]
