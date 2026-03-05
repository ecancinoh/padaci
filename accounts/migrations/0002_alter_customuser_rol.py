from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='rol',
            field=models.CharField(
                choices=[
                    ('admin', 'Administrador'),
                    ('supervisor', 'Supervisor'),
                    ('conductor', 'Conductor'),
                    ('peoneta', 'Peoneta'),
                    ('operador', 'Operador'),
                ],
                default='operador',
                max_length=20,
                verbose_name='Rol',
            ),
        ),
    ]
