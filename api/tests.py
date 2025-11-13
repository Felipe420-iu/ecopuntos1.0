import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import MaterialTasa, Canje, RedencionPuntos, Notificacion
from decimal import Decimal

User = get_user_model()


class APIAuthenticationTest(APITestCase):
    """Tests para autenticación de la API"""
    
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_login_success(self):
        """Test de login exitoso"""
        url = reverse('api:token_obtain_pair')
        data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_invalid_credentials(self):
        """Test de login con credenciales inválidas"""
        url = reverse('api:token_obtain_pair')
        data = {
            'username': self.user_data['username'],
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_protected_endpoint_without_token(self):
        """Test de acceso a endpoint protegido sin token"""
        url = reverse('api:usuario-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_protected_endpoint_with_token(self):
        """Test de acceso a endpoint protegido con token"""
        # Obtener token
        login_url = reverse('api:token_obtain_pair')
        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }
        login_response = self.client.post(login_url, login_data)
        token = login_response.data['access']
        
        # Usar token para acceder a endpoint protegido
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse('api:usuario-perfil')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user_data['username'])


class UsuarioAPITest(APITestCase):
    """Tests para la API de usuarios"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='usuario'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            role='admin'
        )
        
        # Autenticar usuario
        self.client.force_authenticate(user=self.user)
    
    def test_get_user_profile(self):
        """Test para obtener perfil de usuario"""
        url = reverse('api:usuario-perfil')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)
    
    def test_update_user_profile(self):
        """Test para actualizar perfil de usuario"""
        url = reverse('api:usuario-actualizar-perfil')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'telefono': '1234567890'
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.telefono, '1234567890')
    
    def test_user_statistics(self):
        """Test para obtener estadísticas de usuario"""
        # Crear algunos datos de prueba
        material = MaterialTasa.objects.create(
            nombre='Plástico',
            puntos_por_kg=10
        )
        Canje.objects.create(
            usuario=self.user,
            material=material,
            cantidad=Decimal('5.0'),
            puntos_ganados=50
        )
        
        url = reverse('api:usuario-estadisticas', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_puntos', response.data)
        self.assertIn('total_canjes', response.data)
        self.assertIn('materiales_reciclados', response.data)


class CanjeAPITest(APITestCase):
    """Tests para la API de canjes"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='usuario'
        )
        self.recolector = User.objects.create_user(
            username='recolector',
            email='recolector@example.com',
            password='recolectorpass123',
            role='recolector'
        )
        self.material = MaterialTasa.objects.create(
            nombre='Plástico',
            puntos_por_kg=10
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_create_canje(self):
        """Test para crear un canje"""
        url = reverse('api:canje-list')
        data = {
            'material': self.material.id,
            'cantidad': '5.0',
            'observaciones': 'Botellas de plástico'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Canje.objects.count(), 1)
        canje = Canje.objects.first()
        self.assertEqual(canje.usuario, self.user)
        self.assertEqual(canje.material, self.material)
        self.assertEqual(canje.cantidad, Decimal('5.0'))
    
    def test_approve_canje_as_recolector(self):
        """Test para aprobar un canje como recolector"""
        # Crear canje
        canje = Canje.objects.create(
            usuario=self.user,
            material=self.material,
            cantidad=Decimal('5.0'),
            estado='pendiente'
        )
        
        # Autenticar como recolector
        self.client.force_authenticate(user=self.recolector)
        
        url = reverse('api:canje-aprobar', kwargs={'pk': canje.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        canje.refresh_from_db()
        self.assertEqual(canje.estado, 'aprobado')
        self.assertEqual(canje.puntos_ganados, 50)  # 5.0 * 10 puntos
    
    def test_approve_canje_as_user_forbidden(self):
        """Test para verificar que usuarios normales no pueden aprobar canjes"""
        canje = Canje.objects.create(
            usuario=self.user,
            material=self.material,
            cantidad=Decimal('5.0'),
            estado='pendiente'
        )
        
        url = reverse('api:canje-aprobar', kwargs={'pk': canje.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class NotificacionAPITest(APITestCase):
    """Tests para la API de notificaciones"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Crear notificaciones de prueba
        self.notification1 = Notificacion.objects.create(
            usuario=self.user,
            titulo='Notificación 1',
            mensaje='Mensaje de prueba 1',
            tipo='info'
        )
        self.notification2 = Notificacion.objects.create(
            usuario=self.user,
            titulo='Notificación 2',
            mensaje='Mensaje de prueba 2',
            tipo='success',
            leida=True
        )
        # Notificación de otro usuario
        self.other_notification = Notificacion.objects.create(
            usuario=self.other_user,
            titulo='Notificación de otro usuario',
            mensaje='No debería aparecer',
            tipo='info'
        )
        
        self.client.force_authenticate(user=self.user)
    
    def test_get_user_notifications(self):
        """Test para obtener notificaciones del usuario"""
        url = reverse('api:notificacion-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Solo las del usuario autenticado
    
    def test_get_unread_notifications(self):
        """Test para obtener notificaciones no leídas"""
        url = reverse('api:notificaciones-no-leidas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Solo la no leída
        self.assertEqual(response.data[0]['id'], self.notification1.id)
    
    def test_mark_notification_read(self):
        """Test para marcar notificación como leída"""
        url = reverse('api:notificacion-marcar-leida', kwargs={'pk': self.notification1.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.leida)
    
    def test_mark_all_notifications_read(self):
        """Test para marcar todas las notificaciones como leídas"""
        url = reverse('api:notificaciones-marcar-todas-leidas')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todas las notificaciones del usuario están marcadas como leídas
        user_notifications = Notificacion.objects.filter(usuario=self.user)
        for notification in user_notifications:
            self.assertTrue(notification.leida)


class EstadisticasAPITest(APITestCase):
    """Tests para la API de estadísticas"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_general_statistics(self):
        """Test para obtener estadísticas generales"""
        url = reverse('api:estadisticas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('usuarios_activos', response.data)
        self.assertIn('total_canjes_mes', response.data)
        self.assertIn('total_puntos_otorgados', response.data)
    
    def test_get_ranking(self):
        """Test para obtener ranking de usuarios"""
        # Crear usuarios con diferentes puntos
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123',
            puntos=100
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123',
            puntos=200
        )
        
        url = reverse('api:ranking')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Verificar que está ordenado por puntos (descendente)
        if len(response.data) >= 2:
            self.assertGreaterEqual(
                response.data[0]['puntos'],
                response.data[1]['puntos']
            )
    
    def test_get_dashboard_data(self):
        """Test para obtener datos del dashboard"""
        url = reverse('api:dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('puntos_totales', response.data)
        self.assertIn('canjes_mes', response.data)
        self.assertIn('notificaciones_no_leidas', response.data)


@pytest.mark.integration
class IntegrationTest(APITestCase):
    """Tests de integración para flujos completos"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='usuario'
        )
        self.recolector = User.objects.create_user(
            username='recolector',
            email='recolector@example.com',
            password='recolectorpass123',
            role='recolector'
        )
        self.material = MaterialTasa.objects.create(
            nombre='Plástico',
            puntos_por_kg=10
        )
    
    def test_complete_canje_flow(self):
        """Test del flujo completo de canje: crear -> aprobar -> verificar puntos"""
        # 1. Usuario crea canje
        self.client.force_authenticate(user=self.user)
        
        create_url = reverse('api:canje-list')
        canje_data = {
            'material': self.material.id,
            'cantidad': '5.0',
            'observaciones': 'Botellas de plástico'
        }
        create_response = self.client.post(create_url, canje_data)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        
        canje_id = create_response.data['id']
        
        # 2. Recolector aprueba canje
        self.client.force_authenticate(user=self.recolector)
        
        approve_url = reverse('api:canje-aprobar', kwargs={'pk': canje_id})
        approve_response = self.client.post(approve_url)
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        
        # 3. Verificar que se otorgaron los puntos
        self.user.refresh_from_db()
        self.assertEqual(self.user.puntos, 50)  # 5.0 * 10 puntos
        
        # 4. Verificar estado del canje
        canje = Canje.objects.get(id=canje_id)
        self.assertEqual(canje.estado, 'aprobado')
        self.assertEqual(canje.puntos_ganados, 50)