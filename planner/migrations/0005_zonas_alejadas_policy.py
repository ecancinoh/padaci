from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0004_planificacionsemanal_clientes_reparto'),
    ]

    operations = [
        migrations.AddField(
            model_name='planificacionsemanal',
            name='dia_reparto_zonas_alejadas',
            field=models.CharField(choices=[('lun', 'Lunes'), ('mar', 'Martes'), ('mie', 'Miercoles'), ('jue', 'Jueves'), ('vie', 'Viernes')], default='vie', max_length=3, verbose_name='Dia reparto zonas alejadas'),
        ),
        migrations.AddField(
            model_name='planificacionsemanal',
            name='distancia_zona_alejada_km',
            field=models.DecimalField(decimal_places=1, default=40, help_text='Si un cliente supera esta distancia desde Rancagua, se agenda solo en el dia definido para zonas alejadas.', max_digits=6, verbose_name='Distancia zona alejada (km)'),
        ),
    ]
