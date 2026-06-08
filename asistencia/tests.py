from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser

from .models import Asistencia


class AsistenciaViewsTests(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='admin',
            password='secret123',
            rol='admin',
            first_name='Admin',
            last_name='Padaci',
            activo=True,
        )
        self.supervisor = CustomUser.objects.create_user(
            username='supervisor',
            password='secret123',
            rol='supervisor',
            first_name='Super',
            last_name='Visor',
            activo=True,
        )
        self.conductor = CustomUser.objects.create_user(
            username='conductor1',
            password='secret123',
            rol='conductor',
            first_name='Juan',
            last_name='Perez',
            activo=True,
        )
        self.peoneta = CustomUser.objects.create_user(
            username='peoneta1',
            password='secret123',
            rol='peoneta',
            first_name='Ana',
            last_name='Soto',
            activo=True,
        )

    def test_admin_puede_registrar_asistencia_diaria(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('asistencia:diaria'),
            data={
                'fecha': '2026-06-01',
                f'estado_{self.conductor.pk}': Asistencia.ESTADO_PRESENTE,
                f'observacion_{self.conductor.pk}': '',
                f'estado_{self.peoneta.pk}': Asistencia.ESTADO_AUSENTE,
                f'observacion_{self.peoneta.pk}': 'Licencia médica',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Asistencia.objects.filter(fecha='2026-06-01').count(), 2)
        self.assertEqual(
            Asistencia.objects.get(fecha='2026-06-01', usuario=self.peoneta).estado,
            Asistencia.ESTADO_AUSENTE,
        )

    def test_supervisor_puede_crear_o_actualizar_individual(self):
        self.client.force_login(self.supervisor)

        response = self.client.post(
            reverse('asistencia:individual'),
            data={
                'usuario': self.conductor.pk,
                'fecha': '2026-06-03',
                'estado': Asistencia.ESTADO_PRESENTE,
                'observacion': '',
            },
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.post(
            reverse('asistencia:individual'),
            data={
                'usuario': self.conductor.pk,
                'fecha': '2026-06-03',
                'estado': Asistencia.ESTADO_AUSENTE,
                'observacion': 'Inasistencia',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Asistencia.objects.filter(usuario=self.conductor, fecha='2026-06-03').count(), 1)
        self.assertEqual(Asistencia.objects.get(usuario=self.conductor, fecha='2026-06-03').estado, Asistencia.ESTADO_AUSENTE)

    def test_conductor_no_tiene_acceso_a_modulo(self):
        self.client.force_login(self.conductor)
        response = self.client.get(reverse('asistencia:list'))
        self.assertEqual(response.status_code, 302)

    def test_reporte_mensual_muestra_resumen(self):
        Asistencia.objects.create(
            usuario=self.conductor,
            fecha=date(2026, 6, 2),
            estado=Asistencia.ESTADO_PRESENTE,
            registrado_por=self.admin,
        )
        Asistencia.objects.create(
            usuario=self.conductor,
            fecha=date(2026, 6, 3),
            estado=Asistencia.ESTADO_AUSENTE,
            registrado_por=self.admin,
        )

        self.client.force_login(self.admin)
        response = self.client.get(reverse('asistencia:reporte_mensual'), {'mes': '6', 'anio': '2026'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporte mensual')
        self.assertContains(response, self.conductor.get_full_name())

    def test_vista_semanal_con_checkbox_crea_7_registros_por_trabajador(self):
        self.client.force_login(self.admin)

        fecha_base = date(2026, 6, 10)
        inicio_semana = fecha_base - timedelta(days=fecha_base.weekday())
        fechas_semana = [inicio_semana + timedelta(days=i) for i in range(7)]

        data = {
            'fecha': fecha_base.isoformat(),
            'vista': 'semana',
            f'presente_{self.conductor.pk}_{fechas_semana[0].strftime("%Y%m%d")}': '1',
        }

        response = self.client.post(reverse('asistencia:diaria'), data=data)

        self.assertEqual(response.status_code, 302)
        self.assertIn('vista=semana', response.url)

        self.assertEqual(Asistencia.objects.filter(usuario=self.conductor, fecha__in=fechas_semana).count(), 7)
        self.assertEqual(Asistencia.objects.filter(usuario=self.peoneta, fecha__in=fechas_semana).count(), 7)

        for fecha_dia in fechas_semana:
            estado_conductor = Asistencia.objects.get(usuario=self.conductor, fecha=fecha_dia).estado
            estado_peoneta = Asistencia.objects.get(usuario=self.peoneta, fecha=fecha_dia).estado

            if fecha_dia == fechas_semana[0]:
                self.assertEqual(estado_conductor, Asistencia.ESTADO_PRESENTE)
            else:
                self.assertEqual(estado_conductor, Asistencia.ESTADO_AUSENTE)

            self.assertEqual(estado_peoneta, Asistencia.ESTADO_AUSENTE)
