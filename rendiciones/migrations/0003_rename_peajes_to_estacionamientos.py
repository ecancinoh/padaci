from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rendiciones', '0002_remove_campos_resumen'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rendicionreparto',
            old_name='peajes',
            new_name='estacionamientos',
        ),
    ]
