from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0003_alter_paradaruta_entrega'),
    ]

    operations = [
        migrations.AddField(
            model_name='rutadia',
            name='total_consolidado',
            field=models.DecimalField(decimal_places=0, default=0, help_text='Monto total consolidado en pesos chilenos.', max_digits=14, verbose_name='Total consolidado (CLP)'),
        ),
    ]
