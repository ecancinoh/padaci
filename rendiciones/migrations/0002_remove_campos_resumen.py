from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rendiciones', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rendicionreparto',
            name='combustible',
        ),
        migrations.RemoveField(
            model_name='rendicionreparto',
            name='total_consolidado_iva',
        ),
        migrations.RemoveField(
            model_name='rendicionreparto',
            name='total_efectivo',
        ),
        migrations.RemoveField(
            model_name='rendicionreparto',
            name='total_facturas_agregadas',
        ),
    ]
