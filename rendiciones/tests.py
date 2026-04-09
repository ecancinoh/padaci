from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from clients.models import Cliente
from companies.models import Empresa
from rendiciones.models import RendicionReparto
from routes.models import Entrega, EntregaPago, ParadaRuta, RutaDia


class RendicionCreateTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			username='admin',
			password='secret123',
			rol='admin',
			first_name='Admin',
			last_name='Padaci',
			activo=True,
		)
		self.conductor = CustomUser.objects.create_user(
			username='conductor',
			password='secret123',
			rol='conductor',
			first_name='Conductor',
			last_name='Uno',
			activo=True,
		)
		self.empresa = Empresa.objects.create(
			nombre='Distribuidora Demo',
			razon_social='Distribuidora Demo SPA',
			rut='76000000-1',
			direccion='Calle 123',
			activa=True,
		)
		self.cliente = Cliente.objects.create(
			empresa=self.empresa,
			nombre='Cliente Demo',
			direccion='Direccion Cliente',
		)
		self.ruta = RutaDia.objects.create(
			fecha='2026-04-09',
			empresa=self.empresa,
			conductor=self.conductor,
			total_consolidado=Decimal('100000'),
		)
		self.client.force_login(self.user)

	def _crear_entrega(self, orden, estado='entregado', metodo_pago=None, monto='0', observacion=''):
		entrega = Entrega.objects.create(
			cliente=self.cliente,
			empresa=self.empresa,
			conductor=self.conductor,
			estado=estado,
			fecha_programada=self.ruta.fecha,
		)
		ParadaRuta.objects.create(ruta=self.ruta, entrega=entrega, orden=orden)
		if metodo_pago:
			EntregaPago.objects.create(
				entrega=entrega,
				metodo=metodo_pago,
				monto=Decimal(monto),
				observacion=observacion,
			)
		return entrega

	def test_create_preserves_manual_invoice_numbers_for_all_items(self):
		self._crear_entrega(1, metodo_pago='cheque', monto='1000')
		self._crear_entrega(2, metodo_pago='descuento', monto='2000', observacion='Motivo descuento')
		self._crear_entrega(3, metodo_pago='credito', monto='3000')
		self._crear_entrega(4, estado='fallido')
		self._crear_entrega(5, metodo_pago='transferencia', monto='5000')

		response = self.client.post(
			reverse('rendiciones:create'),
			data={
				'ruta': str(self.ruta.pk),
				'fecha': '2026-04-09',
				'distribuidora': str(self.empresa.pk),
				'nombre_repartidor': str(self.conductor.pk),
				'nombre_peoneta': '',
				'estacionamientos': '0',
				'diferencia_menos': '0',
				'diferencia_mas': '0',
				'facturas_totales': '5',
				'facturas_entregadas': '4',
				'facturas_nulas': '1',
				'kilometraje_inicial': '0',
				'kilometraje_final': '10',
				'total_kilometros_recorridos': '10',
				'a-TOTAL_FORMS': '1',
				'a-INITIAL_FORMS': '0',
				'a-MIN_NUM_FORMS': '0',
				'a-MAX_NUM_FORMS': '1000',
				'a-0-numero_factura': 'A-MANUAL-001',
				'a-0-nombre_cliente': 'Cliente Demo',
				'a-0-monto': '1000',
				'a-0-banco': 'Chile',
				'b-TOTAL_FORMS': '1',
				'b-INITIAL_FORMS': '0',
				'b-MIN_NUM_FORMS': '0',
				'b-MAX_NUM_FORMS': '1000',
				'b-0-numero_factura': 'B-MANUAL-001',
				'b-0-motivo': 'Motivo descuento',
				'b-0-monto': '2000',
				'c-TOTAL_FORMS': '1',
				'c-INITIAL_FORMS': '0',
				'c-MIN_NUM_FORMS': '0',
				'c-MAX_NUM_FORMS': '1000',
				'c-0-numero_factura': 'C-MANUAL-001',
				'c-0-autoriza_credito': 'Cliente Demo',
				'c-0-monto': '3000',
				'd-TOTAL_FORMS': '1',
				'd-INITIAL_FORMS': '0',
				'd-MIN_NUM_FORMS': '0',
				'd-MAX_NUM_FORMS': '1000',
				'd-0-numero_factura': 'D-MANUAL-001',
				'd-0-monto': '0',
				'e-TOTAL_FORMS': '1',
				'e-INITIAL_FORMS': '0',
				'e-MIN_NUM_FORMS': '0',
				'e-MAX_NUM_FORMS': '1000',
				'e-0-numero_factura': 'E-MANUAL-001',
				'e-0-monto': '5000',
			},
		)

		self.assertEqual(response.status_code, 302)

		rendicion = RendicionReparto.objects.get(ruta=self.ruta)
		self.assertEqual(rendicion.creditos_documentos.count(), 1)
		self.assertEqual(rendicion.devoluciones_parciales.count(), 1)
		self.assertEqual(rendicion.creditos_confianza.count(), 1)
		self.assertEqual(rendicion.facturas_nulas_detalle.count(), 1)
		self.assertEqual(rendicion.depositos_transferencias.count(), 1)

		self.assertEqual(rendicion.creditos_documentos.get().numero_factura, 'A-MANUAL-001')
		self.assertEqual(rendicion.devoluciones_parciales.get().numero_factura, 'B-MANUAL-001')
		self.assertEqual(rendicion.creditos_confianza.get().numero_factura, 'C-MANUAL-001')
		self.assertEqual(rendicion.facturas_nulas_detalle.get().numero_factura, 'D-MANUAL-001')
		self.assertEqual(rendicion.depositos_transferencias.get().numero_factura, 'E-MANUAL-001')
		self.assertEqual(rendicion.menos_items, Decimal('11000'))
		self.assertEqual(rendicion.total_dinero_recibir, Decimal('89000'))
