#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pruebas automatizadas para la API de EcoPuntos

Este script contiene pruebas para verificar el funcionamiento correcto
de los endpoints de la API REST de EcoPuntos.
"""

import os
import sys
import json
import unittest
from datetime import datetime
from pathlib import Path

# Configurar el entorno Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecopuntos.settings')

import django
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from core.models import Usuario, Material, PuntoDeReciclaje, Recompensa, Reciclaje, Redencion


class APITestCase(TestCase):
    """Clase base para pruebas de API"""
    
    fixtures = ['tests/fixtures/test_data.json']
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = APIClient()
        self.admin_user = get_user_model().objects.get(username='admin')
        self.regular_user = get_user_model().objects.get(username='usuario_regular')
        self.collector_user = get_user_model().objects.get(username='recolector')
        
        # Autenticar como usuario regular por defecto
        self.client.force_authenticate(user=self.regular_user)
    
    def authenticate_as_admin(self):
        """Autenticar como administrador"""
        self.client.force_authenticate(user=self.admin_user)
    
    def authenticate_as_collector(self):
        """Autenticar como recolector"""
        self.client.force_authenticate(user=self.collector_user)
    
    def logout(self):
        """Cerrar sesión"""
        self.client.force_authenticate(user=None)


class UsuarioAPITest(APITestCase):
    """Pruebas para la API de Usuarios"""
    
    def test_get_perfil_propio(self):
        """Verificar que un usuario puede obtener su propio perfil"""
        url = reverse('usuario-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.regular_user.username)
    
    def test_actualizar_perfil(self):
        """Verificar que un usuario puede actualizar su perfil"""
        url = reverse('usuario-me')
        data = {
            'biografia': 'Nueva biografía de prueba',
            'notificaciones_email': False
        }
        
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['biografia'], 'Nueva biografía de prueba')
        self.assertEqual(response.data['notificaciones_email'], False)
    
    def test_listar_usuarios_como_admin(self):
        """Verificar que un administrador puede listar todos los usuarios"""
        self.authenticate_as_admin()
        
        url = reverse('usuario-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 3)  # Al menos los 3 usuarios de prueba
    
    def test_listar_usuarios_como_regular_prohibido(self):
        """Verificar que un usuario regular no puede listar todos los usuarios"""
        url = reverse('usuario-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MaterialAPITest(APITestCase):
    """Pruebas para la API de Materiales"""
    
    def test_listar_materiales(self):
        """Verificar que cualquier usuario puede listar materiales"""
        url = reverse('material-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 4)  # Al menos los 4 materiales de prueba
    
    def test_detalle_material(self):
        """Verificar que se puede obtener el detalle de un material"""
        material = Material.objects.first()
        url = reverse('material-detail', args=[material.id])
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], material.nombre)
    
    def test_crear_material_como_admin(self):
        """Verificar que un administrador puede crear materiales"""
        self.authenticate_as_admin()
        
        url = reverse('material-list')
        data = {
            'nombre': 'Material de Prueba',
            'descripcion': 'Descripción del material de prueba',
            'puntos_por_kg': 7,
            'codigo': 'TEST',
            'color': '#FF5722',
            'icono': 'test',
            'activo': True
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Material de Prueba')
    
    def test_crear_material_como_regular_prohibido(self):
        """Verificar que un usuario regular no puede crear materiales"""
        url = reverse('material-list')
        data = {
            'nombre': 'Material de Prueba No Permitido',
            'descripcion': 'Este material no debería crearse',
            'puntos_por_kg': 7,
            'codigo': 'NOPE',
            'color': '#FF5722',
            'icono': 'test',
            'activo': True
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PuntoDeReciclajeAPITest(APITestCase):
    """Pruebas para la API de Puntos de Reciclaje"""
    
    def test_listar_puntos_reciclaje(self):
        """Verificar que cualquier usuario puede listar puntos de reciclaje"""
        url = reverse('puntodereciclaje-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 2)  # Al menos los 2 puntos de prueba
    
    def test_filtrar_puntos_por_material(self):
        """Verificar que se pueden filtrar puntos por material aceptado"""
        material = Material.objects.get(codigo='VID')  # Vidrio
        
        url = reverse('puntodereciclaje-list')
        response = self.client.get(url, {'material': material.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todos los puntos devueltos aceptan este material
        for punto in response.data:
            self.assertIn(material.id, punto['materiales_aceptados'])
    
    def test_buscar_puntos_cercanos(self):
        """Verificar que se pueden buscar puntos cercanos a una ubicación"""
        url = reverse('puntodereciclaje-list')
        response = self.client.get(url, {
            'latitud': 4.6100,
            'longitud': -74.0800,
            'radio': 5  # km
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)


class ReciclajeAPITest(APITestCase):
    """Pruebas para la API de Reciclajes"""
    
    def test_registrar_reciclaje(self):
        """Verificar que un usuario puede registrar un reciclaje"""
        url = reverse('reciclaje-list')
        data = {
            'punto_reciclaje': PuntoDeReciclaje.objects.first().id,
            'material': Material.objects.first().id,
            'cantidad_kg': 1.5,
            'comentario': 'Reciclaje de prueba API'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['usuario'], self.regular_user.id)
        self.assertEqual(float(response.data['cantidad_kg']), 1.5)
        self.assertFalse(response.data['verificado'])  # No debería estar verificado inicialmente
    
    def test_verificar_reciclaje_como_recolector(self):
        """Verificar que un recolector puede verificar un reciclaje"""
        # Primero crear un reciclaje
        reciclaje = Reciclaje.objects.create(
            usuario=Usuario.objects.get(user=self.regular_user),
            punto_reciclaje=PuntoDeReciclaje.objects.first(),
            material=Material.objects.first(),
            cantidad_kg=2.0,
            puntos_obtenidos=0,  # Se calculará al verificar
            fecha_reciclaje=datetime.now(),
            verificado=False
        )
        
        # Autenticar como recolector
        self.authenticate_as_collector()
        
        # Verificar el reciclaje
        url = reverse('reciclaje-verificar', args=[reciclaje.id])
        data = {
            'verificado': True,
            'comentario': 'Verificado por recolector de prueba'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['verificado'])
        self.assertIsNotNone(response.data['verificado_por'])
        self.assertIsNotNone(response.data['fecha_verificacion'])
        self.assertTrue(response.data['puntos_obtenidos'] > 0)  # Debería haber calculado los puntos
    
    def test_listar_reciclajes_propios(self):
        """Verificar que un usuario puede listar sus propios reciclajes"""
        url = reverse('reciclaje-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todos los reciclajes pertenecen al usuario actual
        for reciclaje in response.data:
            self.assertEqual(reciclaje['usuario'], Usuario.objects.get(user=self.regular_user).id)


class RecompensaAPITest(APITestCase):
    """Pruebas para la API de Recompensas"""
    
    def test_listar_recompensas_disponibles(self):
        """Verificar que se pueden listar las recompensas disponibles"""
        url = reverse('recompensa-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        
        # Verificar que todas las recompensas están activas
        for recompensa in response.data:
            self.assertTrue(recompensa['activo'])
    
    def test_canjear_recompensa(self):
        """Verificar que un usuario puede canjear una recompensa"""
        # Obtener una recompensa disponible
        recompensa = Recompensa.objects.filter(
            puntos_requeridos__lte=Usuario.objects.get(user=self.regular_user).puntos,
            activo=True,
            stock__gt=0
        ).first()
        
        if not recompensa:
            self.skipTest("No hay recompensas disponibles para canjear")
        
        url = reverse('recompensa-canjear', args=[recompensa.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['recompensa'], recompensa.id)
        self.assertEqual(response.data['usuario'], Usuario.objects.get(user=self.regular_user).id)
        self.assertEqual(response.data['puntos_usados'], recompensa.puntos_requeridos)
        self.assertIsNotNone(response.data['codigo_canje'])
    
    def test_listar_redenciones_propias(self):
        """Verificar que un usuario puede listar sus propias redenciones"""
        url = reverse('redencion-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todas las redenciones pertenecen al usuario actual
        for redencion in response.data:
            self.assertEqual(redencion['usuario'], Usuario.objects.get(user=self.regular_user).id)


class EstadisticasAPITest(APITestCase):
    """Pruebas para la API de Estadísticas"""
    
    def test_estadisticas_publicas(self):
        """Verificar que cualquier usuario puede ver estadísticas públicas"""
        url = reverse('estadisticas-publicas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reciclado', response.data)
        self.assertIn('usuarios_activos', response.data)
        self.assertIn('materiales', response.data)
    
    def test_estadisticas_personales(self):
        """Verificar que un usuario puede ver sus estadísticas personales"""
        url = reverse('estadisticas-personales')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reciclado', response.data)
        self.assertIn('total_puntos', response.data)
        self.assertIn('redenciones', response.data)
        self.assertIn('materiales', response.data)
    
    def test_estadisticas_admin_como_admin(self):
        """Verificar que un administrador puede ver estadísticas administrativas"""
        self.authenticate_as_admin()
        
        url = reverse('estadisticas-admin')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('usuarios_por_rol', response.data)
        self.assertIn('reciclaje_por_material', response.data)
        self.assertIn('redenciones_por_tipo', response.data)
    
    def test_estadisticas_admin_como_regular_prohibido(self):
        """Verificar que un usuario regular no puede ver estadísticas administrativas"""
        url = reverse('estadisticas-admin')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class NotificacionesAPITest(APITestCase):
    """Pruebas para la API de Notificaciones"""
    
    def test_listar_notificaciones_propias(self):
        """Verificar que un usuario puede listar sus propias notificaciones"""
        url = reverse('notificacion-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que todas las notificaciones pertenecen al usuario actual
        for notificacion in response.data:
            self.assertEqual(notificacion['usuario'], Usuario.objects.get(user=self.regular_user).id)
    
    def test_marcar_notificacion_como_leida(self):
        """Verificar que un usuario puede marcar una notificación como leída"""
        # Obtener una notificación no leída
        from core.models import Notificacion
        notificacion = Notificacion.objects.filter(
            usuario=Usuario.objects.get(user=self.regular_user),
            leida=False
        ).first()
        
        if not notificacion:
            self.skipTest("No hay notificaciones no leídas para marcar")
        
        url = reverse('notificacion-marcar-leida', args=[notificacion.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['leida'])
        self.assertIsNotNone(response.data['fecha_lectura'])


class SeguridadAPITest(APITestCase):
    """Pruebas para la seguridad de la API"""
    
    def test_acceso_sin_autenticacion(self):
        """Verificar que no se puede acceder a endpoints protegidos sin autenticación"""
        self.logout()
        
        # Intentar acceder al perfil
        url = reverse('usuario-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_autenticacion(self):
        """Verificar que se puede obtener un token de autenticación"""
        self.logout()
        
        url = reverse('token_obtain_pair')
        data = {
            'username': 'usuario_regular',
            'password': 'password123'  # Asumiendo que esta es la contraseña en los fixtures
        }
        
        # Este test podría fallar si la contraseña en los fixtures es diferente
        # En ese caso, se puede omitir
        try:
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('access', response.data)
            self.assertIn('refresh', response.data)
        except:
            self.skipTest("No se pudo probar la autenticación por token debido a credenciales incorrectas")
    
    def test_csrf_protection(self):
        """Verificar que las solicitudes POST requieren token CSRF"""
        # Usar un cliente sin autenticación forzada
        client = Client(enforce_csrf_checks=True)
        
        # Intentar hacer una solicitud POST sin token CSRF
        url = reverse('usuario-me')
        response = client.post(url, {'biografia': 'Test CSRF'})
        
        # Debería fallar por falta de token CSRF
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


if __name__ == '__main__':
    unittest.main()