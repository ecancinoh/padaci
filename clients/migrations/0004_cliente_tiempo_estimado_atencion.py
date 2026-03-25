from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0003_cliente_observaciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='tiempo_estimado_atencion',
            field=models.PositiveIntegerField(default=10, help_text='Minutos estimados para atender este cliente en una visita.', verbose_name='Tiempo estimado de atencion (min)'),
        ),
    ]
