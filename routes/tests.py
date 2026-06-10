import json
from io import BytesIO
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import CustomUser
from clients.models import Cliente
from companies.models import Empresa
from routes.models import Entrega, RutaDia, ParadaRuta, ClienteOCRAlias, ParadaFalabellaMeta, ParadaUbicacionCandidata
from routes.views import _safe_total, _match_clients_from_facturas, _build_ocr_alias_key, _falabella_optimizar_con_anclas, _read_excel_rows


class SafeTotalTests(TestCase):
	"""Tests para validar que _safe_total() parsea correctamente diferentes formatos de monto."""

	def test_safe_total_formatos_basicos(self):
		"""Validar parsing de formatos variados."""
		# Números sin separadores
		self.assertEqual(_safe_total('50000'), Decimal('50000'))
		self.assertEqual(_safe_total(50000), Decimal('50000'))
		self.assertEqual(_safe_total(50000.0), Decimal('50000'))
		self.assertEqual(_safe_total(Decimal('50000')), Decimal('50000'))
		
		# Con símbolo de moneda
		self.assertEqual(_safe_total('$50000'), Decimal('50000'))
		self.assertEqual(_safe_total('$ 50000'), Decimal('50000'))
		
		# Formato chileno: $50.000 (punto como miles)
		self.assertEqual(_safe_total('50.000'), Decimal('50000'))
		self.assertEqual(_safe_total('$50.000'), Decimal('50000'))
		self.assertEqual(_safe_total('$50.000.000'), Decimal('50000000'))
		
		# Formato con decimal - quantize redondea al entero más cercano
		self.assertEqual(_safe_total('50000.00'), Decimal('50000'))
		self.assertEqual(_safe_total('50000.4'), Decimal('50000'))   # < 0.5 redondea hacia abajo
		self.assertEqual(_safe_total('50000.5'), Decimal('50000'))   # .5 usa banker's rounding (hacia par)
		self.assertEqual(_safe_total('50001.5'), Decimal('50002'))   # .5 hacia par
		
		# Formato americano: 50,000.00
		self.assertEqual(_safe_total('50,000.00'), Decimal('50000'))
		self.assertEqual(_safe_total('$50,000.00'), Decimal('50000'))
		self.assertEqual(_safe_total('50,000'), Decimal('50000'))
		
		# Formato europeo: 50.000,00 (punto miles, coma decimal)
		self.assertEqual(_safe_total('50.000,00'), Decimal('50000'))
		self.assertEqual(_safe_total('50.000,4'), Decimal('50000'))  # < 0.5 redondea hacia abajo
		
		# Valores especiales
		self.assertEqual(_safe_total(''), Decimal('0'))
		self.assertEqual(_safe_total(None), Decimal('0'))
		self.assertEqual(_safe_total('0'), Decimal('0'))
		self.assertEqual(_safe_total('-100'), Decimal('0'))  # Negativo → 0


class FalabellaExcelParserTests(TestCase):
	def test_usa_hoja_planificacion_no_activa_y_no_exige_cliente_contacto(self):
		from openpyxl import Workbook

		wb = Workbook()
		ws_activa = wb.active
		ws_activa.title = 'Resumen'
		ws_activa.append(['cualquier', 'columna'])

		ws_plan = wb.create_sheet(title='PLANIFICACION DEFINITIVA')
		ws_plan.append(['empresa', 'patente', 'direccion', 'localidad'])
		ws_plan.append(['Falabella', 'ABCD11', 'Av. Test 123', 'Rancagua'])

		stream = BytesIO()
		wb.save(stream)
		stream.seek(0)

		uploaded = SimpleUploadedFile(
			'planificacion.xlsx',
			stream.getvalue(),
			content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
		)

		rows, empresas, patentes = _read_excel_rows(uploaded)

		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]['empresa'], 'Falabella')
		self.assertEqual(rows[0]['patente'], 'ABCD11')
		self.assertEqual(rows[0]['direccion'], 'Av. Test 123')
		self.assertEqual(rows[0]['localidad'], 'Rancagua')
		self.assertNotIn('cliente', rows[0])
		self.assertNotIn('contacto', rows[0])
		self.assertEqual(empresas, ['Falabella'])
		self.assertEqual(patentes, ['ABCD11'])


class CrearEntregasFacturaTests(TestCase):
	def setUp(self):
		self.admin = CustomUser.objects.create_user(
			username='admin-routes',
			password='secret123',
			rol='admin',
			first_name='Admin',
			last_name='Routes',
			activo=True,
		)
		self.conductor = CustomUser.objects.create_user(
			username='conductor-routes',
			password='secret123',
			rol='conductor',
			first_name='Conductor',
			last_name='Routes',
			activo=True,
		)
		self.empresa = Empresa.objects.create(
			nombre='Distribuidora Routes',
			razon_social='Distribuidora Routes SPA',
			rut='76000000-2',
			direccion='Calle 321',
			activa=True,
		)
		self.cliente = Cliente.objects.create(
			empresa=self.empresa,
			nombre='Cliente OCR',
			comuna='Requinoa',
			direccion='Direccion anterior',
			equivalencia_entregas=10,
		)
		self.ruta = RutaDia.objects.create(
			fecha='2026-05-01',
			empresa=self.empresa,
			conductor=self.conductor,
			total_consolidado=Decimal('250000'),
		)
		self.client.force_login(self.admin)

	def test_rechaza_facturas_duplicadas_en_misma_ruta(self):
		payload = {
			'lineas': [
				{
					'documento': '87029',
					'nombre_cliente': 'Cliente OCR',
					'direccion_cliente': 'Dirección 1',
					'dia': 12,
					'mes': 5,
					'total': 10000,
					'cond_pago': 'CONTADO',
					'comuna': 'Requinoa',
					'cliente_id': self.cliente.pk,
				},
				{
					'documento': '87029',
					'nombre_cliente': 'Cliente OCR',
					'direccion_cliente': 'Dirección 2',
					'dia': 12,
					'mes': 5,
					'total': 12000,
					'cond_pago': 'CONTADO',
					'comuna': 'Requinoa',
					'cliente_id': self.cliente.pk,
				},
			]
		}

		response = self.client.post(
			reverse('routes:crear_entregas', kwargs={'pk': self.ruta.pk}),
			data=payload,
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 400)
		self.assertEqual(Entrega.objects.count(), 0)

	def test_crea_entrega_por_factura_y_actualiza_cliente(self):
		payload = {
			'lineas': [
				{
					'documento': '87030',
					'nombre_cliente': 'Cliente OCR',
					'direccion_cliente': 'Ruta validada 123',
					'dia': 12,
					'mes': 5,
					'total': 25357,
					'cond_pago': 'CONTADO',
					'comuna': 'Olivar',
					'cliente_id': self.cliente.pk,
				}
			]
		}

		response = self.client.post(
			reverse('routes:crear_entregas', kwargs={'pk': self.ruta.pk}),
			data=payload,
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		body = response.json()
		self.assertEqual(body['creadas'], 1)
		self.assertEqual(body['pendientes'], 0)

		entrega = Entrega.objects.get(numero_factura_ref='87030')
		self.assertEqual(entrega.total_factura_ref, Decimal('25357'))
		self.assertEqual(entrega.dia_factura_ref, 12)
		self.assertEqual(entrega.mes_factura_ref, 5)

		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.direccion, 'Ruta validada 123')
		self.assertEqual(self.cliente.comuna, 'Olivar')

	def test_crear_cliente_rapido_desde_ruta(self):
		payload = {
			'nombre': 'Cliente Nuevo Modal',
			'direccion': 'Calle Modal 456',
			'comuna': 'Rancagua',
		}

		response = self.client.post(
			reverse('routes:crear_cliente_rapido', kwargs={'pk': self.ruta.pk}),
			data=json.dumps(payload),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		body = response.json()
		self.assertTrue(body.get('ok'))
		self.assertIn('cliente', body)

		cliente = Cliente.objects.get(pk=body['cliente']['id'])
		self.assertEqual(cliente.nombre, 'Cliente Nuevo Modal')
		self.assertEqual(cliente.direccion, 'Calle Modal 456')
		self.assertEqual(cliente.comuna, 'Rancagua')
		self.assertEqual(cliente.empresa, self.ruta.empresa)

	def test_guardar_entregas_persiste_alias_ocr(self):
		payload = {
			'lineas': [
				{
					'documento': '88001',
					'nombre_cliente': 'Cliente OCR Alias',
					'direccion_cliente': 'Av Alias 100',
					'dia': 10,
					'mes': 5,
					'total': 5000,
					'cond_pago': 'CONTADO',
					'comuna': 'Rancagua',
					'cliente_id': self.cliente.pk,
				}
			]
		}

		response = self.client.post(
			reverse('routes:crear_entregas', kwargs={'pk': self.ruta.pk}),
			data=payload,
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		alias_key = _build_ocr_alias_key('Cliente OCR Alias', 'Av Alias 100', 'Rancagua')
		alias = ClienteOCRAlias.objects.get(clave_normalizada=alias_key)
		self.assertEqual(alias.cliente_id, self.cliente.pk)
		self.assertFalse(alias.bloqueado_por_conflicto)

	def test_match_con_alias_en_conflicto_requiere_revision_manual(self):
		cliente_2 = Cliente.objects.create(
			empresa=self.empresa,
			nombre='Cliente OCR Dos',
			comuna='Rancagua',
			direccion='Av Alias 101',
		)
		alias_key = _build_ocr_alias_key('Alias conflictivo', 'Av Alias', 'Rancagua')
		ClienteOCRAlias.objects.create(
			clave_normalizada=alias_key,
			nombre_ocr='Alias conflictivo',
			direccion_ocr='Av Alias',
			comuna_ocr='Rancagua',
			cliente=cliente_2,
			bloqueado_por_conflicto=True,
		)

		resultados, _clientes, _no_encontrados = _match_clients_from_facturas([
			{
				'documento': '9001',
				'nombre_cliente': 'Alias conflictivo',
				'direccion_cliente': 'Av Alias',
				'dia': 12,
				'mes': 5,
				'total': 12000,
				'cond_pago': 'CONTADO',
				'comuna': 'Rancagua',
			}
		])

		self.assertEqual(len(resultados), 1)
		self.assertEqual(resultados[0]['cliente_id'], None)
		self.assertTrue(resultados[0]['requiere_revision'])


class FalabellaRutaTests(TestCase):
	def setUp(self):
		self.admin = CustomUser.objects.create_user(
			username='admin-falabella',
			password='secret123',
			rol='admin',
			activo=True,
		)
		self.conductor = CustomUser.objects.create_user(
			username='conductor-falabella',
			password='secret123',
			rol='conductor',
			activo=True,
		)
		self.empresa = Empresa.objects.create(
			nombre='Falabella',
			razon_social='Falabella Retail SA',
			rut='76000000-3',
			direccion='Rengo',
			activa=True,
		)
		self.ruta = RutaDia.objects.create(
			fecha='2026-06-10',
			empresa=self.empresa,
			conductor=self.conductor,
			modalidad='falabella',
			patente='ABCD11',
		)
		self.client.force_login(self.admin)

	def _crear_parada(self, nombre, lat=None, lon=None):
		cliente = Cliente.objects.create(
			nombre=nombre,
			empresa=self.empresa,
			comuna='Rancagua',
			direccion='Direccion test',
			latitud=lat,
			longitud=lon,
		)
		entrega = Entrega.objects.create(
			cliente=cliente,
			empresa=self.empresa,
			conductor=self.conductor,
			fecha_programada=self.ruta.fecha,
		)
		return ParadaRuta.objects.create(ruta=self.ruta, entrega=entrega, orden=self.ruta.paradas.count() + 1)

	def test_optimizar_anclas_mantiene_paradas_sin_coordenadas_al_final(self):
		self._crear_parada('Cliente cerca Rengo', Decimal('-34.40'), Decimal('-70.86'))
		self._crear_parada('Cliente centro', Decimal('-34.28'), Decimal('-70.77'))
		self._crear_parada('Cliente sin coords', None, None)

		con_coords, pendientes = _falabella_optimizar_con_anclas(self.ruta)

		self.assertEqual(con_coords, 2)
		self.assertEqual(pendientes, 1)
		ultima = self.ruta.paradas.select_related('entrega__cliente').order_by('-orden').first()
		self.assertEqual(ultima.entrega.cliente.nombre, 'Cliente sin coords')

	def test_optimizar_anclas_reordena_sin_colision_unique_orden(self):
		# Crea en orden inverso para forzar swap de ordenes 1<->2.
		self._crear_parada('Cliente mas lejos', Decimal('-34.10'), Decimal('-70.70'))
		self._crear_parada('Cliente cerca Rengo', Decimal('-34.40'), Decimal('-70.86'))

		con_coords, pendientes = _falabella_optimizar_con_anclas(self.ruta)

		self.assertEqual(con_coords, 2)
		self.assertEqual(pendientes, 0)
		paradas = list(self.ruta.paradas.select_related('entrega__cliente').order_by('orden'))
		self.assertEqual(len(paradas), 2)
		self.assertEqual(paradas[0].entrega.cliente.nombre, 'Cliente cerca Rengo')
		self.assertEqual(paradas[1].entrega.cliente.nombre, 'Cliente mas lejos')

	def test_endpoint_marcar_entregado_simple_toggle(self):
		parada = self._crear_parada('Cliente toggle', Decimal('-34.20'), Decimal('-70.74'))

		url = reverse('routes:falabella_marcar_entregado', kwargs={'pk': self.ruta.pk, 'parada_id': parada.pk})
		response = self.client.post(url, data='{}', content_type='application/json')
		self.assertEqual(response.status_code, 200)
		parada.entrega.refresh_from_db()
		self.assertEqual(parada.entrega.estado, 'entregado')

		response_2 = self.client.post(url, data='{}', content_type='application/json')
		self.assertEqual(response_2.status_code, 200)
		parada.entrega.refresh_from_db()
		self.assertEqual(parada.entrega.estado, 'pendiente')

	@patch('routes.views._geocode_nominatim', return_value=[])
	def test_import_create_reutiliza_ruta_falabella_existente(self, _mock_geocode):
		# Deja una parada previa para verificar que el flujo la reemplaza.
		self._crear_parada('Parada antigua', Decimal('-34.20'), Decimal('-70.74'))

		token = 'token-prueba-falabella'
		session = self.client.session
		session[f'falabella_upload_{token}'] = {
			'rows': [
				{
					'row_number': 2,
					'empresa': 'Falabella',
					'patente': 'ABCD11',
					'direccion': 'Arturo Prat 116',
					'localidad': 'Machali',
				}
			],
			'empresas': ['Falabella'],
			'patentes': ['ABCD11'],
			'form_data': {
				'fecha': '2026-06-10',
				'conductor': self.conductor.pk,
				'peoneta': '',
			},
		}
		session.save()

		response = self.client.post(
			reverse('routes:falabella_import'),
			data={
				'action': 'create',
				'upload_token': token,
				'fecha': '2026-06-10',
				'conductor': self.conductor.pk,
				'peoneta': '',
				'empresa_archivo': 'Falabella',
				'patente_archivo': 'ABCD11',
				'empresa_objetivo': self.empresa.pk,
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(
			RutaDia.objects.filter(fecha='2026-06-10', conductor=self.conductor).count(),
			1,
		)
		ruta = RutaDia.objects.get(fecha='2026-06-10', conductor=self.conductor)
		self.assertEqual(ruta.modalidad, 'falabella')
		self.assertEqual(ruta.patente, 'ABCD11')
		self.assertEqual(ruta.paradas.count(), 1)

	@patch('routes.views._geocode_nominatim', return_value=[])
	def test_import_create_repetido_no_falla_por_orden_duplicado(self, _mock_geocode):
		token = 'token-prueba-repetido'
		session = self.client.session
		session[f'falabella_upload_{token}'] = {
			'rows': [
				{
					'row_number': 2,
					'empresa': 'Falabella',
					'patente': 'ABCD11',
					'direccion': 'Arturo Prat 116',
					'localidad': 'Machali',
				}
			],
			'empresas': ['Falabella'],
			'patentes': ['ABCD11'],
			'form_data': {
				'fecha': '2026-06-10',
				'conductor': self.conductor.pk,
				'peoneta': '',
			},
		}
		session.save()

		payload = {
			'action': 'create',
			'upload_token': token,
			'fecha': '2026-06-10',
			'conductor': self.conductor.pk,
			'peoneta': '',
			'empresa_archivo': 'Falabella',
			'patente_archivo': 'ABCD11',
			'empresa_objetivo': self.empresa.pk,
		}

		response_1 = self.client.post(reverse('routes:falabella_import'), data=payload)
		self.assertEqual(response_1.status_code, 302)

		response_2 = self.client.post(reverse('routes:falabella_import'), data=payload)
		self.assertEqual(response_2.status_code, 302)

		ruta = RutaDia.objects.get(fecha='2026-06-10', conductor=self.conductor)
		self.assertEqual(ruta.paradas.count(), 1)

	def test_endpoint_seleccionar_candidato_actualiza_coordenadas(self):
		parada = self._crear_parada('Cliente candidato', Decimal('-34.20'), Decimal('-70.74'))
		ParadaFalabellaMeta.objects.create(
			parada=parada,
			direccion_original='Mojica 123',
			localidad_original='Machali',
		)
		cand_1 = ParadaUbicacionCandidata.objects.create(
			parada=parada,
			orden=1,
			latitud=Decimal('-34.100000'),
			longitud=Decimal('-70.700000'),
		)
		cand_2 = ParadaUbicacionCandidata.objects.create(
			parada=parada,
			orden=2,
			latitud=Decimal('-34.200000'),
			longitud=Decimal('-70.800000'),
		)

		url = reverse(
			'routes:falabella_select_candidate',
			kwargs={'pk': self.ruta.pk, 'parada_id': parada.pk, 'candidato_id': cand_2.pk},
		)
		response = self.client.post(url, data='{}', content_type='application/json')

		self.assertEqual(response.status_code, 200)
		cand_1.refresh_from_db()
		cand_2.refresh_from_db()
		self.assertFalse(cand_1.seleccionada)
		self.assertTrue(cand_2.seleccionada)
		parada.entrega.cliente.refresh_from_db()
		self.assertEqual(parada.entrega.cliente.latitud, Decimal('-34.200000'))
		self.assertEqual(parada.entrega.cliente.longitud, Decimal('-70.800000'))

	@patch('routes.views._geocode_free_address', return_value=(Decimal('-34.165432'), Decimal('-70.740123')))
	def test_endpoint_actualizar_direccion_sin_generar_candidatos(self, _mock_google):
		parada = self._crear_parada('Cliente direccion', Decimal('-34.20'), Decimal('-70.74'))
		ParadaFalabellaMeta.objects.create(
			parada=parada,
			direccion_original='Mojica 123',
			localidad_original='Machali',
		)

		url = reverse('routes:falabella_update_address', kwargs={'pk': self.ruta.pk, 'parada_id': parada.pk})
		response = self.client.post(
			url,
			data=json.dumps({'direccion': 'Mujica 120', 'localidad': 'Machali'}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		parada.entrega.cliente.refresh_from_db()
		self.assertEqual(parada.entrega.cliente.direccion, 'Mujica 120')
		self.assertEqual(parada.entrega.cliente.comuna, 'Machali')
		self.assertEqual(parada.ubicaciones_candidatas.count(), 0)
		self.assertEqual(parada.entrega.cliente.latitud, Decimal('-34.165432'))
		self.assertEqual(parada.entrega.cliente.longitud, Decimal('-70.740123'))
		meta = ParadaFalabellaMeta.objects.get(parada=parada)
		self.assertEqual(meta.direccion_original, 'Mujica 120')
		self.assertEqual(meta.estado_direccion, 'confirmada_manual')
		payload = response.json()
		self.assertEqual(payload.get('candidatos'), 0)
		self.assertTrue(payload.get('google_maps_busqueda'))

	@patch('routes.views._geocode_free_address', return_value=None)
	def test_endpoint_actualizar_direccion_sin_match_conserva_coordenadas(self, _mock_google):
		parada = self._crear_parada('Cliente con pin', Decimal('-34.200000'), Decimal('-70.740000'))
		ParadaFalabellaMeta.objects.create(
			parada=parada,
			direccion_original='Direccion inicial 100',
			localidad_original='Rancagua',
		)

		url = reverse('routes:falabella_update_address', kwargs={'pk': self.ruta.pk, 'parada_id': parada.pk})
		response = self.client.post(
			url,
			data=json.dumps({'direccion': 'Lourdes 37', 'localidad': 'Rancagua'}),
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 200)
		parada.entrega.cliente.refresh_from_db()
		self.assertEqual(parada.entrega.cliente.latitud, Decimal('-34.200000'))
		self.assertEqual(parada.entrega.cliente.longitud, Decimal('-70.740000'))
		meta = ParadaFalabellaMeta.objects.get(parada=parada)
		self.assertEqual(meta.estado_direccion, 'confirmada_manual')

	@patch('routes.views._geocode_nominatim')
	def test_geocode_free_address_fallback_por_calle_y_localidad(self, mock_nominatim):
		from routes.views import _geocode_free_address

		mock_nominatim.return_value = [
			{
				'latitud': Decimal('-34.180000'),
				'longitud': Decimal('-70.760000'),
				'etiqueta': 'Lourdes',
				'direccion_formateada': 'Lourdes, Rancagua, Chile',
				'score': Decimal('0.8000'),
				'orden': 1,
			},
		]

		coords = _geocode_free_address('Lourdes 37', 'Rancagua')

		self.assertEqual(coords, (Decimal('-34.180000'), Decimal('-70.760000')))
