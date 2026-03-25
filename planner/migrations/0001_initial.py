from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clients', '0003_cliente_observaciones'),
        ('companies', '0002_alter_empresa_email_alter_empresa_telefono'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanificacionSemanal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=120, verbose_name='Nombre del plan')),
                ('solo_clientes_activos', models.BooleanField(default=True, verbose_name='Solo clientes activos')),
                ('incluir_clientes_sin_coordenadas', models.BooleanField(default=True, verbose_name='Incluir clientes sin coordenadas')),
                ('capacidad_lunes', models.PositiveIntegerField(blank=True, null=True, verbose_name='Capacidad lunes')),
                ('capacidad_martes', models.PositiveIntegerField(blank=True, null=True, verbose_name='Capacidad martes')),
                ('capacidad_miercoles', models.PositiveIntegerField(blank=True, null=True, verbose_name='Capacidad miercoles')),
                ('capacidad_jueves', models.PositiveIntegerField(blank=True, null=True, verbose_name='Capacidad jueves')),
                ('capacidad_viernes', models.PositiveIntegerField(blank=True, null=True, verbose_name='Capacidad viernes')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='planes_semanales', to='companies.empresa', verbose_name='Empresa')),
            ],
            options={
                'verbose_name': 'Planificacion semanal',
                'verbose_name_plural': 'Planificaciones semanales',
                'ordering': ['-fecha_actualizacion', '-id'],
            },
        ),
        migrations.CreateModel(
            name='RecomendacionCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia_semana', models.CharField(choices=[('lun', 'Lunes'), ('mar', 'Martes'), ('mie', 'Miercoles'), ('jue', 'Jueves'), ('vie', 'Viernes')], max_length=3, verbose_name='Dia')),
                ('orden', models.PositiveIntegerField(default=1, verbose_name='Orden')),
                ('origen', models.CharField(choices=[('auto', 'Automatico'), ('manual', 'Manual')], default='auto', max_length=10, verbose_name='Origen')),
                ('bloqueado', models.BooleanField(default=False, help_text='Si esta activo, no se mueve automaticamente al regenerar.', verbose_name='Bloqueado')),
                ('observacion', models.CharField(blank=True, default='', max_length=255, verbose_name='Observacion')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recomendaciones_semanales', to='clients.cliente', verbose_name='Cliente')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recomendaciones', to='planner.planificacionsemanal', verbose_name='Planificacion')),
            ],
            options={
                'verbose_name': 'Recomendacion de cliente',
                'verbose_name_plural': 'Recomendaciones de clientes',
                'ordering': ['dia_semana', 'orden', 'id'],
                'unique_together': {('plan', 'cliente')},
            },
        ),
        migrations.AddIndex(
            model_name='recomendacioncliente',
            index=models.Index(fields=['plan', 'dia_semana'], name='planner_rec_plan_id_b05665_idx'),
        ),
        migrations.AddIndex(
            model_name='recomendacioncliente',
            index=models.Index(fields=['plan', 'bloqueado'], name='planner_rec_plan_id_99996e_idx'),
        ),
    ]
