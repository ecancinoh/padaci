from django.test import TestCase
from django.urls import reverse

from .models import CustomUser


class AdminPasswordResetTests(TestCase):
	def setUp(self):
		self.admin = CustomUser.objects.create_user(
			username='admin-test',
			password='Admin1234!',
			rol='admin',
			activo=True,
		)
		self.operador = CustomUser.objects.create_user(
			username='operador-test',
			password='Operador1234!',
			rol='operador',
			activo=True,
		)
		self.supervisor = CustomUser.objects.create_user(
			username='supervisor-test',
			password='Supervisor1234!',
			rol='supervisor',
			activo=True,
		)

	def test_admin_can_change_other_user_password(self):
		self.client.force_login(self.admin)
		url = reverse('accounts:set_password', kwargs={'pk': self.operador.pk})
		response = self.client.post(
			url,
			{
				'new_password1': 'NuevaClaveSegura2026*',
				'new_password2': 'NuevaClaveSegura2026*',
			},
		)
		self.assertEqual(response.status_code, 302)
		self.operador.refresh_from_db()
		self.assertTrue(self.operador.check_password('NuevaClaveSegura2026*'))

	def test_non_admin_cannot_change_other_user_password(self):
		self.client.force_login(self.supervisor)
		url = reverse('accounts:set_password', kwargs={'pk': self.operador.pk})
		response = self.client.post(
			url,
			{
				'new_password1': 'ClaveNoDebeAplicar2026*',
				'new_password2': 'ClaveNoDebeAplicar2026*',
			},
		)
		self.assertEqual(response.status_code, 302)
		self.operador.refresh_from_db()
		self.assertFalse(self.operador.check_password('ClaveNoDebeAplicar2026*'))
