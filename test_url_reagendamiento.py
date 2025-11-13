#!/usr/bin/env python
"""
Script para probar el reagendamiento completo incluyendo acceso por URL
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import Usuario, Ruta
from django.utils import timezone
from datetime import datetime, date, time

def test_url_reagendamiento():
    """Probar el acceso a URL de reagendamiento"""
    
    print("🔗 Iniciando prueba de URL de reagendamiento...")
    
    # 1. Obtener un usuario con rutas
    usuario = Usuario.objects.filter(email__isnull=False).exclude(email='').first()
    
    if not usuario:
        print("❌ No hay usuarios con email configurado")
        return False
    
    print(f"✅ Usuario encontrado: {usuario.username} ({usuario.email})")
    
    # 2. Obtener o crear una ruta que SÍ pertenezca al usuario
    ruta = Ruta.objects.filter(usuario=usuario).first()
    
    if not ruta:
        # Crear ruta de prueba
        ruta = Ruta.objects.create(
            usuario=usuario,
            fecha=date(2025, 10, 25),
            hora=time(15, 30),
            direccion='Calle de Prueba 456, Bogotá',
            barrio='Barrio Usuario',
            materiales='Papel: 3kg',
            estado='pendiente',
            referencia='Casa roja, primer piso'
        )
        print(f"✅ Ruta creada para usuario: ID {ruta.id}")
    else:
        print(f"✅ Ruta encontrada para usuario: ID {ruta.id}")
    
    # 3. Probar simulación de reagendamiento
    try:
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        from core.views import rutasusuario_reagendada
        
        # Crear request simulado
        factory = RequestFactory()
        request = factory.get(f'/rutasusuario/reagendada/{ruta.id}/')
        request.user = usuario  # Simular usuario autenticado
        
        print(f"🔗 Probando URL: /rutasusuario/reagendada/{ruta.id}/")
        print(f"👤 Usuario en request: {request.user.username}")
        print(f"🎯 Ruta objetivo: {ruta.id} (pertenece a {ruta.usuario.username})")
        
        # Llamar a la vista
        response = rutasusuario_reagendada(request, ruta.id)
        
        print(f"✅ Vista ejecutada exitosamente")
        print(f"📍 Tipo de respuesta: {type(response).__name__}")
        
        if hasattr(response, 'url'):
            print(f"🔄 Redirigiendo a: {response.url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de URL: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_usuario_incorrecto():
    """Probar acceso con usuario incorrecto (debe fallar graciosamente)"""
    
    print("\n🚫 Iniciando prueba de acceso con usuario incorrecto...")
    
    # Obtener dos usuarios diferentes
    usuarios = Usuario.objects.all()[:2]
    
    if len(usuarios) < 2:
        print("❌ Se necesitan al menos 2 usuarios para esta prueba")
        return False
    
    usuario1 = usuarios[0]
    usuario2 = usuarios[1]
    
    # Obtener ruta del usuario1
    ruta = Ruta.objects.filter(usuario=usuario1).first()
    
    if not ruta:
        print("❌ No hay rutas para realizar la prueba")
        return False
    
    try:
        from django.test import RequestFactory
        from core.views import rutasusuario_reagendada
        
        # Crear request con usuario2 intentando acceder a ruta de usuario1
        factory = RequestFactory()
        request = factory.get(f'/rutasusuario/reagendada/{ruta.id}/')
        request.user = usuario2  # Usuario diferente
        
        print(f"🔗 Probando acceso incorrecto:")
        print(f"   - Ruta {ruta.id} pertenece a: {ruta.usuario.username}")
        print(f"   - Usuario intentando acceder: {usuario2.username}")
        
        # Llamar a la vista
        response = rutasusuario_reagendada(request, ruta.id)
        
        if hasattr(response, 'url') and '/rutasusuario/' in response.url and 'reagendada' not in response.url:
            print("✅ Acceso denegado correctamente - redirigido a rutasusuario sin modal")
            return True
        else:
            print("❌ El acceso no fue denegado correctamente")
            return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Ejecutando tests de URL de reagendamiento...\n")
    
    test1 = test_url_reagendamiento()
    test2 = test_usuario_incorrecto()
    
    print(f"\n📊 Resultados:")
    print(f"   - Test URL correcta: {'✅ PASÓ' if test1 else '❌ FALLÓ'}")
    print(f"   - Test seguridad: {'✅ PASÓ' if test2 else '❌ FALLÓ'}")
    
    if test1 and test2:
        print("\n🎉 ¡Todos los tests pasaron! El sistema está funcionando correctamente.")
    else:
        print("\n⚠️  Algunos tests fallaron. Revisar los errores.")
        sys.exit(1)