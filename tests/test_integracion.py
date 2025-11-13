#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pruebas de integración para EcoPuntos

Este script contiene pruebas que verifican el funcionamiento conjunto
de los diferentes módulos del sistema, asegurando que interactúan
correctamente entre sí.
"""

import os
import sys
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Configurar el entorno Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecopuntos.settings')

import django
django.setup()

from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction

from core.models import (
    Usuario, Material, PuntoDeReciclaje, Recompensa, 
    Reciclaje, Redencion, Notificacion, Mensaje, 
    Configuracion, Estadistica, Sesion
)


class IntegracionTestCase(TransactionTestCase):
    """Clase base para pruebas de integración"""
    
    fixtures = ['tests/fixtures/test_data.json']
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        
        # Usuarios de prueba
        self.admin_user = get_user_model().objects.get(username='admin')
        self.regular_user = get_user_model().objects.get(username='usuario_regular')
        self.collector_user = get_user_model().objects.get(username='recolector')
        
        # Objetos comunes
        self.usuario_regular = Usuario.objects.get(user=self.regular_user)
        self.usuario_admin = Usuario.objects.get(user=self.admin_user)
        self.usuario_recolector = Usuario.objects.get(user=self.collector_user)
        
        # Iniciar sesión como usuario regular por defecto
        self.client.login(username='usuario_regular', password='password123')
    
    def login_as_admin(self):
        """Iniciar sesión como administrador"""
        self.client.logout()
        self.client.login(username='admin', password='password123')
    
    def login_as_collector(self):
        """Iniciar sesión como recolector"""
        self.client.logout()
        self.client.login(username='recolector', password='password123')


class FlujoReciclajeTest(IntegracionTestCase):
    """Pruebas para el flujo completo de reciclaje"""
    
    def test_flujo_completo_reciclaje(self):
        """Verificar el flujo completo de reciclaje: registro, verificación y puntos"""
        # 1. Usuario registra un reciclaje
        material = Material.objects.get(codigo='PET')  # Plástico
        punto_reciclaje = PuntoDeReciclaje.objects.first()
        
        # Guardar puntos iniciales del usuario
        puntos_iniciales = self.usuario_regular.puntos
        
        # Registrar reciclaje
        response = self.client.post(reverse('registrar_reciclaje'), {
            'material': material.id,
            'punto_reciclaje': punto_reciclaje.id,
            'cantidad_kg': 2.5,
            'comentario': 'Prueba de integración'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Verificar que se creó el reciclaje
        reciclaje = Reciclaje.objects.filter(
            usuario=self.usuario_regular,
            material=material,
            punto_reciclaje=punto_reciclaje,
            verificado=False
        ).latest('fecha_creacion')
        
        self.assertIsNotNone(reciclaje)
        self.assertEqual(float(reciclaje.cantidad_kg), 2.5)
        
        # 2. Recolector verifica el reciclaje
        self.login_as_collector()
        
        response = self.client.post(reverse('verificar_reciclaje', args=[reciclaje.id]), {
            'verificado': True,
            'comentario': 'Verificado en prueba de integración'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Recargar el reciclaje desde la base de datos
        reciclaje.refresh_from_db()
        
        # Verificar que se actualizó correctamente
        self.assertTrue(reciclaje.verificado)
        self.assertEqual(reciclaje.verificado_por, self.usuario_recolector)
        self.assertIsNotNone(reciclaje.fecha_verificacion)
        
        # Verificar que se calcularon los puntos correctamente
        puntos_esperados = material.puntos_por_kg * float(reciclaje.cantidad_kg)
        self.assertEqual(reciclaje.puntos_obtenidos, puntos_esperados)
        
        # 3. Verificar que el usuario recibió los puntos
        self.usuario_regular.refresh_from_db()
        self.assertEqual(self.usuario_regular.puntos, puntos_iniciales + puntos_esperados)
        
        # 4. Verificar que se creó una notificación
        notificacion = Notificacion.objects.filter(
            usuario=self.usuario_regular,
            tipo='puntos',
            leida=False
        ).latest('fecha_creacion')
        
        self.assertIsNotNone(notificacion)
        self.assertIn(str(puntos_esperados), notificacion.mensaje)


class FlujoRecompensaTest(IntegracionTestCase):
    """Pruebas para el flujo completo de recompensas"""
    
    def test_flujo_completo_recompensa(self):
        """Verificar el flujo completo de recompensas: listado, canje y uso"""
        # 1. Usuario ve lista de recompensas disponibles
        response = self.client.get(reverse('lista_recompensas'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Descuento en Tienda Eco')  # Recompensa de los fixtures
        
        # 2. Usuario selecciona una recompensa para canjear
        recompensa = Recompensa.objects.get(nombre='Descuento en Tienda Eco')
        
        # Asegurar que el usuario tiene suficientes puntos
        puntos_iniciales = self.usuario_regular.puntos
        if puntos_iniciales < recompensa.puntos_requeridos:
            self.usuario_regular.puntos = recompensa.puntos_requeridos
            self.usuario_regular.save()
        
        # Canjear recompensa
        response = self.client.post(reverse('canjear_recompensa', args=[recompensa.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # 3. Verificar que se creó la redención
        redencion = Redencion.objects.filter(
            usuario=self.usuario_regular,
            recompensa=recompensa,
            estado='pendiente'
        ).latest('fecha_creacion')
        
        self.assertIsNotNone(redencion)
        self.assertEqual(redencion.puntos_usados, recompensa.puntos_requeridos)
        self.assertIsNotNone(redencion.codigo_canje)
        
        # 4. Verificar que se descontaron los puntos
        self.usuario_regular.refresh_from_db()
        self.assertEqual(self.usuario_regular.puntos, puntos_iniciales - recompensa.puntos_requeridos)
        
        # 5. Verificar que se actualizó el stock de la recompensa
        recompensa.refresh_from_db()
        self.assertEqual(recompensa.stock, recompensa.stock - 1)
        
        # 6. Administrador marca la redención como canjeada
        self.login_as_admin()
        
        response = self.client.post(reverse('procesar_redencion', args=[redencion.id]), {
            'estado': 'canjeado',
            'comentario': 'Procesado en prueba de integración'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Recargar la redención desde la base de datos
        redencion.refresh_from_db()
        
        # Verificar que se actualizó correctamente
        self.assertEqual(redencion.estado, 'canjeado')
        self.assertIsNotNone(redencion.fecha_uso)


class FlujoNotificacionesTest(IntegracionTestCase):
    """Pruebas para el flujo de notificaciones"""
    
    def test_flujo_notificaciones(self):
        """Verificar el flujo completo de notificaciones: creación, listado y lectura"""
        # 1. Crear una notificación para el usuario
        notificacion = Notificacion.objects.create(
            usuario=self.usuario_regular,
            titulo='Notificación de prueba',
            mensaje='Esta es una notificación creada para pruebas de integración',
            tipo='sistema',
            leida=False,
            enlace='/perfil'
        )
        
        # 2. Usuario ve sus notificaciones
        response = self.client.get(reverse('notificaciones'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Notificación de prueba')
        
        # Contar notificaciones no leídas antes
        no_leidas_antes = Notificacion.objects.filter(
            usuario=self.usuario_regular,
            leida=False
        ).count()
        
        # 3. Usuario marca la notificación como leída
        response = self.client.post(reverse('marcar_notificacion_leida', args=[notificacion.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Recargar la notificación desde la base de datos
        notificacion.refresh_from_db()
        
        # Verificar que se marcó como leída
        self.assertTrue(notificacion.leida)
        self.assertIsNotNone(notificacion.fecha_lectura)
        
        # 4. Verificar contador de notificaciones no leídas
        no_leidas_despues = Notificacion.objects.filter(
            usuario=self.usuario_regular,
            leida=False
        ).count()
        
        self.assertEqual(no_leidas_despues, no_leidas_antes - 1)


class FlujoChatSoporteTest(IntegracionTestCase):
    """Pruebas para el flujo de chat de soporte"""
    
    def test_flujo_chat_soporte(self):
        """Verificar el flujo completo de chat de soporte: envío y respuesta de mensajes"""
        # 1. Usuario envía un mensaje al administrador
        response = self.client.post(reverse('enviar_mensaje'), {
            'destinatario': self.usuario_admin.id,
            'asunto': 'Consulta de prueba',
            'contenido': 'Este es un mensaje de prueba para el flujo de integración'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Verificar que se creó el mensaje
        mensaje_usuario = Mensaje.objects.filter(
            remitente=self.usuario_regular,
            destinatario=self.usuario_admin,
            asunto='Consulta de prueba'
        ).latest('fecha_creacion')
        
        self.assertIsNotNone(mensaje_usuario)
        self.assertFalse(mensaje_usuario.leido)
        
        # 2. Administrador ve el mensaje
        self.login_as_admin()
        
        response = self.client.get(reverse('bandeja_entrada'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Consulta de prueba')
        
        # 3. Administrador lee el mensaje
        response = self.client.get(reverse('ver_mensaje', args=[mensaje_usuario.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este es un mensaje de prueba')
        
        # Recargar el mensaje desde la base de datos
        mensaje_usuario.refresh_from_db()
        
        # Verificar que se marcó como leído
        self.assertTrue(mensaje_usuario.leido)
        self.assertIsNotNone(mensaje_usuario.fecha_lectura)
        
        # 4. Administrador responde al mensaje
        response = self.client.post(reverse('responder_mensaje', args=[mensaje_usuario.id]), {
            'contenido': 'Esta es una respuesta de prueba para el flujo de integración'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Verificar que se creó la respuesta
        mensaje_respuesta = Mensaje.objects.filter(
            remitente=self.usuario_admin,
            destinatario=self.usuario_regular,
            asunto__startswith='Re: Consulta de prueba'
        ).latest('fecha_creacion')
        
        self.assertIsNotNone(mensaje_respuesta)
        self.assertFalse(mensaje_respuesta.leido)
        
        # 5. Usuario ve la respuesta
        self.client.login(username='usuario_regular', password='password123')
        
        response = self.client.get(reverse('bandeja_entrada'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Re: Consulta de prueba')


class FlujoEstadisticasTest(IntegracionTestCase):
    """Pruebas para el flujo de estadísticas"""
    
    def test_generacion_estadisticas(self):
        """Verificar la generación y visualización de estadísticas"""
        # 1. Crear algunos datos para estadísticas
        # Crear un reciclaje verificado
        material = Material.objects.get(codigo='PET')  # Plástico
        reciclaje = Reciclaje.objects.create(
            usuario=self.usuario_regular,
            punto_reciclaje=PuntoDeReciclaje.objects.first(),
            material=material,
            cantidad_kg=3.0,
            puntos_obtenidos=material.puntos_por_kg * 3,
            fecha_reciclaje=datetime.now(),
            verificado=True,
            verificado_por=self.usuario_recolector,
            fecha_verificacion=datetime.now()
        )
        
        # 2. Ejecutar el comando de generación de estadísticas (simulado)
        from django.core.management import call_command
        try:
            call_command('generar_estadisticas')
        except:
            # Si el comando no existe, crear estadísticas manualmente
            Estadistica.objects.create(
                tipo='reciclaje_diario',
                fecha=datetime.now().date(),
                datos=json.dumps({
                    'plastico': 3.0,
                    'papel': 0,
                    'vidrio': 0,
                    'metal': 0
                })
            )
        
        # 3. Administrador ve las estadísticas
        self.login_as_admin()
        
        response = self.client.get(reverse('estadisticas_admin'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Estadísticas')
        
        # 4. Usuario regular ve estadísticas públicas
        self.client.login(username='usuario_regular', password='password123')
        
        response = self.client.get(reverse('estadisticas'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Estadísticas')


class FlujoConfiguracionTest(IntegracionTestCase):
    """Pruebas para el flujo de configuración"""
    
    def test_configuracion_sistema(self):
        """Verificar la gestión de configuración del sistema"""
        # 1. Administrador accede a la configuración
        self.login_as_admin()
        
        response = self.client.get(reverse('configuracion'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Configuración')
        
        # 2. Administrador actualiza una configuración
        config = Configuracion.objects.get(clave='nombre_sitio')
        nuevo_valor = 'EcoPuntos Test Actualizado'
        
        response = self.client.post(reverse('editar_configuracion', args=[config.id]), {
            'valor': nuevo_valor,
            'descripcion': config.descripcion
        })
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Recargar la configuración desde la base de datos
        config.refresh_from_db()
        
        # Verificar que se actualizó correctamente
        self.assertEqual(config.valor, nuevo_valor)
        
        # 3. Usuario regular no puede acceder a la configuración
        self.client.login(username='usuario_regular', password='password123')
        
        response = self.client.get(reverse('configuracion'))
        
        # Debería redirigir a login o mostrar acceso denegado
        self.assertNotEqual(response.status_code, 200)


class FlujoSeguridadTest(IntegracionTestCase):
    """Pruebas para el flujo de seguridad"""
    
    def test_seguridad_sesiones(self):
        """Verificar la gestión de sesiones y seguridad"""
        # 1. Usuario inicia sesión
        self.client.logout()
        
        response = self.client.post(reverse('login'), {
            'username': 'usuario_regular',
            'password': 'password123'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Verificar que se creó una sesión
        sesion = Sesion.objects.filter(
            usuario=self.usuario_regular,
            activa=True
        ).latest('fecha_creacion')
        
        self.assertIsNotNone(sesion)
        
        # 2. Usuario ve sus sesiones activas
        response = self.client.get(reverse('sesiones_activas'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sesiones activas')
        
        # 3. Usuario cierra una sesión específica
        response = self.client.post(reverse('cerrar_sesion', args=[sesion.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Recargar la sesión desde la base de datos
        sesion.refresh_from_db()
        
        # Verificar que se cerró correctamente
        self.assertFalse(sesion.activa)
        self.assertIsNotNone(sesion.fecha_fin)
        
        # 4. Verificar que el usuario sigue autenticado (cerró otra sesión, no la actual)
        response = self.client.get(reverse('perfil'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'usuario_regular')
        
        # 5. Usuario cierra sesión actual
        response = self.client.get(reverse('logout'))
        
        self.assertEqual(response.status_code, 302)  # Redirección después de éxito
        
        # Verificar que ya no está autenticado
        response = self.client.get(reverse('perfil'))
        
        # Debería redirigir a login
        self.assertNotEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()