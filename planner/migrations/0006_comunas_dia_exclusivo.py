from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0005_zonas_alejadas_policy'),
    ]

    operations = [
        migrations.AddField(
            model_name='planificacionsemanal',
            name='comunas_dia_exclusivo',
            field=models.TextField(blank=True, default='', help_text='Lista de comunas separadas por coma. Esas comunas se agendan solo en el dia definido para zonas alejadas.', verbose_name='Comunas de dia exclusivo'),
        ),
    ]
