from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deliveries', '0004_move_entrega_to_routes'),
        ('routes', '0005_rutadia_peoneta'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0003_cliente_observaciones'),
        ('companies', '0002_alter_empresa_email_alter_empresa_telefono'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Entrega',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('descripcion', models.TextField(blank=True, null=True, verbose_name='Descripción del paquete')),
                        ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('en_ruta', 'En Ruta'), ('entregado', 'Entregado'), ('fallido', 'Intento Fallido'), ('reprogramado', 'Reprogramado'), ('devuelto', 'Devuelto')], default='pendiente', max_length=15, verbose_name='Estado')),
                        ('fecha_programada', models.DateField(verbose_name='Fecha Programada')),
                        ('fecha_entrega', models.DateTimeField(blank=True, null=True, verbose_name='Fecha/Hora Entrega Real')),
                        ('observacion', models.TextField(blank=True, null=True, verbose_name='Observación')),
                        ('foto_evidencia', models.ImageField(blank=True, null=True, upload_to='entregas/evidencia/', verbose_name='Foto Evidencia')),
                        ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                        ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                        ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='entregas', to='clients.cliente', verbose_name='Cliente')),
                        ('conductor', models.ForeignKey(blank=True, limit_choices_to={'rol': 'conductor'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='entregas_asignadas', to=settings.AUTH_USER_MODEL, verbose_name='Conductor')),
                        ('empresa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='entregas', to='companies.empresa', verbose_name='Empresa Solicitante')),
                    ],
                    options={
                        'verbose_name': 'Entrega',
                        'verbose_name_plural': 'Entregas',
                        'ordering': ['-fecha_programada', 'cliente'],
                        'db_table': 'deliveries_entrega',
                    },
                ),
                migrations.AlterField(
                    model_name='paradaruta',
                    name='entrega',
                    field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='paradas', to='routes.entrega', verbose_name='Entrega'),
                ),
            ],
        ),
    ]
