from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0015_paradafalabellameta_cantidad_pedidos'),
    ]

    operations = [
        migrations.AddField(
            model_name='paradafalabellameta',
            name='observacion_importada',
            field=models.TextField(blank=True, default='', verbose_name='Observación importada del Excel'),
        ),
    ]
