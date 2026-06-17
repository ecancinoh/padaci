from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0014_paradafalabellameta_direccion_importada'),
    ]

    operations = [
        migrations.AddField(
            model_name='paradafalabellameta',
            name='cantidad_pedidos',
            field=models.PositiveSmallIntegerField(default=1, verbose_name='Cantidad de pedidos en esta parada'),
        ),
    ]
