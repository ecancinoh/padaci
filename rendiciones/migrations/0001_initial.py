from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('routes', '0004_rutadia_total_consolidado'),
    ]

    operations = [
        migrations.CreateModel(
            name='RendicionReparto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(verbose_name='Fecha')),
                ('distribuidora', models.CharField(blank=True, max_length=120, verbose_name='Distribuidora')),
                ('nombre_repartidor', models.CharField(max_length=140, verbose_name='Nombre del repartidor')),
                ('nombre_peoneta', models.CharField(blank=True, max_length=140, verbose_name='Nombre del peoneta')),
                ('total_consolidado_iva', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Total consolidado con IVA')),
                ('total_facturas_agregadas', models.PositiveIntegerField(default=0, verbose_name='Total facturas agregadas a la ruta')),
                ('peajes', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Peajes')),
                ('combustible', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Combustible')),
                ('total_efectivo', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Total efectivo')),
                ('diferencia_menos', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Diferencia menos')),
                ('diferencia_mas', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Diferencia más')),
                ('total_consolidado', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Total consolidado')),
                ('menos_items', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Menos ítems (A,B,C,D,E)')),
                ('total_dinero_recibir', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Total dinero a recibir')),
                ('facturas_totales', models.PositiveIntegerField(default=0, verbose_name='Facturas totales')),
                ('facturas_entregadas', models.PositiveIntegerField(default=0, verbose_name='Facturas entregadas')),
                ('facturas_nulas', models.PositiveIntegerField(default=0, verbose_name='Facturas nulas')),
                ('kilometraje_inicial', models.DecimalField(decimal_places=1, default=0, max_digits=8, verbose_name='Kilometraje inicial')),
                ('kilometraje_final', models.DecimalField(decimal_places=1, default=0, max_digits=8, verbose_name='Kilometraje final')),
                ('total_kilometros_recorridos', models.DecimalField(decimal_places=1, default=0, max_digits=8, verbose_name='Total kilómetros recorridos')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('ruta', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rendicion', to='routes.rutadia', verbose_name='Ruta del día')),
            ],
            options={
                'verbose_name': 'Rendición de reparto',
                'verbose_name_plural': 'Rendiciones de reparto',
                'ordering': ['-fecha', '-id'],
            },
        ),
        migrations.CreateModel(
            name='FacturaNulaItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_factura', models.CharField(blank=True, max_length=40, verbose_name='N° factura')),
                ('monto', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Monto')),
                ('rendicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facturas_nulas_detalle', to='rendiciones.rendicionreparto')),
            ],
            options={
                'verbose_name': 'Factura nula (D)',
                'verbose_name_plural': 'Facturas nulas (D)',
            },
        ),
        migrations.CreateModel(
            name='DepositoTransferenciaItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_factura', models.CharField(blank=True, max_length=40, verbose_name='N° factura')),
                ('monto', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Monto')),
                ('rendicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='depositos_transferencias', to='rendiciones.rendicionreparto')),
            ],
            options={
                'verbose_name': 'Depósito o transferencia (E)',
                'verbose_name_plural': 'Depósitos o transferencias (E)',
            },
        ),
        migrations.CreateModel(
            name='DevolucionParcialItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_factura', models.CharField(blank=True, max_length=40, verbose_name='N° factura')),
                ('monto', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Monto')),
                ('motivo', models.CharField(blank=True, max_length=200, verbose_name='Motivo')),
                ('rendicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devoluciones_parciales', to='rendiciones.rendicionreparto')),
            ],
            options={
                'verbose_name': 'Devolución parcial (B)',
                'verbose_name_plural': 'Devoluciones parciales (B)',
            },
        ),
        migrations.CreateModel(
            name='CreditoConfianzaItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_factura', models.CharField(blank=True, max_length=40, verbose_name='N° factura')),
                ('monto', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Monto')),
                ('autoriza_credito', models.CharField(blank=True, max_length=140, verbose_name='Quién autoriza el crédito')),
                ('rendicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='creditos_confianza', to='rendiciones.rendicionreparto')),
            ],
            options={
                'verbose_name': 'Crédito de confianza (C)',
                'verbose_name_plural': 'Créditos de confianza (C)',
            },
        ),
        migrations.CreateModel(
            name='CreditoDocumentoItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_factura', models.CharField(blank=True, max_length=40, verbose_name='N° factura')),
                ('monto', models.DecimalField(decimal_places=0, default=0, max_digits=14, verbose_name='Monto')),
                ('nombre_cliente', models.CharField(blank=True, max_length=140, verbose_name='Nombre cliente')),
                ('banco', models.CharField(blank=True, max_length=120, verbose_name='Banco')),
                ('rendicion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='creditos_documentos', to='rendiciones.rendicionreparto')),
            ],
            options={
                'verbose_name': 'Crédito con documento (A)',
                'verbose_name_plural': 'Créditos con documentos (A)',
            },
        ),
    ]
