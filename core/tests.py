
from django.test import TestCase
from django.utils import timezone
from .models import Usuario, Configuracion

class UsuarioModelTest(TestCase):
	def setUp(self):
		self.user = Usuario.objects.create_user(
			username='testuser',
			email='test@example.com',
			password='testpass123',
			first_name='Test',
			last_name='User',
			role='user',
			puntos=100
		)

	def test_usuario_str(self):
		self.assertEqual(str(self.user), 'testuser')

	def test_usuario_puntos(self):
		self.assertEqual(self.user.puntos, 100)

	def test_usuario_role(self):
		self.assertEqual(self.user.role, 'user')


class ConfiguracionModelTest(TestCase):
	def setUp(self):
		self.config = Configuracion.objects.create(
			categoria='general',
			nombre='test_config',
			valor='valor_prueba',
			descripcion='config de prueba'
		)

	def test_configuracion_str(self):
		self.assertEqual(str(self.config), 'general - test_config')

	def test_get_configs_by_category(self):
		configs = Configuracion.get_configs_by_category('general')
		self.assertIn(self.config, configs)
