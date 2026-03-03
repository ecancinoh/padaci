from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_alter_cliente_options_cliente_comuna_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='observaciones',
            field=models.TextField(blank=True, default='', help_text='Indicaciones especiales de entrega, acceso, horarios, etc.', verbose_name='Observaciones'),
        ),
    ]
