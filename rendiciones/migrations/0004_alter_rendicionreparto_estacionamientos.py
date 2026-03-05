from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rendiciones', '0003_rename_peajes_to_estacionamientos'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rendicionreparto',
            name='estacionamientos',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Estacionamientos'),
        ),
    ]
