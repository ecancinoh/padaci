from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
        ('routes', '0006_move_entrega_from_deliveries'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='detallehistorial',
                    name='entrega',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles_historial', to='routes.entrega', verbose_name='Entrega'),
                ),
            ],
        ),
    ]
