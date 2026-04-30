from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deliveries', '0003_remove_entrega_numero_guia_remove_entrega_peso_kg_and_more'),
        ('routes', '0003_alter_paradaruta_entrega'),
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='Entrega'),
            ],
        ),
    ]
