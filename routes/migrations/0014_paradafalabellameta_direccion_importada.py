from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0013_rename_routes_clie_bloquea_6a8fd4_idx_routes_clie_bloquea_9057d5_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='paradafalabellameta',
            name='direccion_importada',
            field=models.TextField(blank=True, default='', verbose_name='Direccion importada de Falabella'),
        ),
        migrations.AddField(
            model_name='paradafalabellameta',
            name='localidad_importada',
            field=models.CharField(blank=True, default='', max_length=140, verbose_name='Localidad importada de Falabella'),
        ),
    ]
