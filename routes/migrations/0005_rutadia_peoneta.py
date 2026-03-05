from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0004_rutadia_total_consolidado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='rutadia',
            name='peoneta',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='rutas_peoneta',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Peoneta',
            ),
        ),
    ]
