from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deliveries', '0003_remove_entrega_numero_guia_remove_entrega_peso_kg_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='Entrega'),
            ],
        ),
    ]
