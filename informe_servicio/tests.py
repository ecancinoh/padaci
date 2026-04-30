from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clients.models import Cliente
from companies.models import Empresa
from rendiciones.models import RendicionReparto
from routes.models import Entrega, RutaDia


class InformeServicioAccessTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin = self.user_model.objects.create_user(username='admin_test', password='1234', rol='admin')
        self.supervisor = self.user_model.objects.create_user(username='supervisor_test', password='1234', rol='supervisor')
        self.operador = self.user_model.objects.create_user(username='operador_test', password='1234', rol='operador')

    def test_admin_can_access_report(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('informe_servicio:index'))
        self.assertEqual(response.status_code, 200)

    def test_supervisor_can_access_report(self):
        self.client.force_login(self.supervisor)
        response = self.client.get(reverse('informe_servicio:index'))
        self.assertEqual(response.status_code, 200)

    def test_operador_is_redirected(self):
        self.client.force_login(self.operador)
        response = self.client.get(reverse('informe_servicio:index'))
        self.assertRedirects(response, reverse('dashboard:index'))


class InformeServicioMetricsTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.admin = self.user_model.objects.create_user(username='admin_metrics', password='1234', rol='admin', first_name='Ana', last_name='Admin')
        self.conductor = self.user_model.objects.create_user(username='conductor_metrics', password='1234', rol='conductor', first_name='Carlos', last_name='Ruta')
        self.peoneta = self.user_model.objects.create_user(username='peoneta_metrics', password='1234', rol='peoneta', first_name='Paula', last_name='Apoyo')
        self.empresa = Empresa.objects.create(
            nombre='Distribuidora Central',
            razon_social='Distribuidora Central SPA',
            rut='76.111.111-1',
            direccion='Av. Principal 123',
        )
        self.cliente_1 = Cliente.objects.create(nombre='Cliente Uno', comuna='Santiago', empresa=self.empresa)
        self.cliente_2 = Cliente.objects.create(nombre='Cliente Dos', comuna='Providencia', empresa=self.empresa)
        Entrega.objects.create(
            cliente=self.cliente_1,
            empresa=self.empresa,
            conductor=self.conductor,
            estado='entregado',
            fecha_programada='2026-04-10',
        )
        Entrega.objects.create(
            cliente=self.cliente_2,
            empresa=self.empresa,
            conductor=self.conductor,
            estado='fallido',
            fecha_programada='2026-04-11',
        )
        self.ruta = RutaDia.objects.create(
            fecha='2026-04-10',
            empresa=self.empresa,
            conductor=self.conductor,
            peoneta=self.peoneta,
            estado='completada',
            total_consolidado=Decimal('150000'),
        )
        RendicionReparto.objects.create(
            ruta=self.ruta,
            fecha='2026-04-10',
            distribuidora='Distribuidora Central',
            nombre_repartidor='Carlos Ruta',
            nombre_peoneta='Paula Apoyo',
            total_consolidado=Decimal('150000'),
                kilometraje_inicial=Decimal('0'),
                kilometraje_final=Decimal('42.5'),
            facturas_entregadas=12,
            facturas_nulas=1,
        )

    def test_report_shows_metrics_for_period(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse('informe_servicio:index'),
            {
                'empresa': self.empresa.pk,
                'fecha_desde': '2026-04-01',
                'fecha_hasta': '2026-04-30',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Distribuidora Central')
        self.assertContains(response, '150.000')
        self.assertContains(response, '50.0%')
        self.assertContains(response, '42,5 km')

    def test_pdf_export_returns_pdf(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse('informe_servicio:pdf'),
            {
                'empresa': self.empresa.pk,
                'fecha_desde': '2026-04-01',
                'fecha_hasta': '2026-04-30',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
