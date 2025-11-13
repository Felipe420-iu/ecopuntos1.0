#!/usr/bin/env python
"""
Script de verificación del sistema de chat directo
Verifica que todos los componentes estén funcionando correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.models import *
from django.contrib.auth import get_user_model

def verificar_chat_system():
    """Verifica el sistema de chat directo"""
    print("🔍 Verificando sistema de chat directo...")
    
    # 1. Verificar que los modelos existen
    try:
        print("\n1. ✅ Verificando modelos...")
        print(f"   - ConversacionDirecta: {ConversacionDirecta.objects.count()} conversaciones")
        print(f"   - MensajeDirecto: {MensajeDirecto.objects.count()} mensajes")
        print(f"   - SolicitudSoporte: {SolicitudSoporte.objects.count()} solicitudes")
    except Exception as e:
        print(f"   ❌ Error con modelos: {e}")
        return False
    
    # 2. Verificar que hay usuarios admin
    try:
        print("\n2. ✅ Verificando usuarios administrativos...")
        admins = Usuario.objects.filter(role__in=['admin', 'superuser'])
        print(f"   - Usuarios admin encontrados: {admins.count()}")
        for admin in admins[:3]:
            print(f"     - {admin.username} ({admin.role})")
    except Exception as e:
        print(f"   ❌ Error verificando admins: {e}")
        return False
    
    # 3. Verificar URLs
    try:
        print("\n3. ✅ Verificando URLs...")
        from django.urls import reverse
        urls_chat = [
            'conversaciones_activas',
            'listar_solicitudes_soporte',
        ]
        for url_name in urls_chat:
            try:
                url = reverse(url_name)
                print(f"   - {url_name}: {url}")
            except Exception as e:
                print(f"   ❌ URL {url_name}: {e}")
    except Exception as e:
        print(f"   ❌ Error verificando URLs: {e}")
    
    # 4. Verificar templates
    try:
        print("\n4. ✅ Verificando templates...")
        import os
        template_base = "core/templates/core/chatbot"
        templates = [
            'chat_directo.html',
            'conversaciones_activas.html',
            'listar_solicitudes.html'
        ]
        
        for template in templates:
            template_path = os.path.join(template_base, template)
            if os.path.exists(template_path):
                size = os.path.getsize(template_path)
                print(f"   ✅ {template}: {size} bytes")
            else:
                print(f"   ❌ {template}: No encontrado")
    except Exception as e:
        print(f"   ❌ Error verificando templates: {e}")
    
    # 5. Crear datos de prueba si es necesario
    print("\n5. 🧪 Creando datos de prueba...")
    try:
        # Buscar un usuario regular
        usuario_regular = Usuario.objects.filter(role='user').first()
        admin_user = Usuario.objects.filter(role__in=['admin', 'superuser']).first()
        
        if not usuario_regular:
            print("   ⚠️  No hay usuarios regulares para pruebas")
        elif not admin_user:
            print("   ⚠️  No hay usuarios admin para pruebas")
        else:
            # Verificar si ya existe una solicitud de prueba
            solicitud_test = SolicitudSoporte.objects.filter(
                usuario=usuario_regular,
                mensaje__contains="Prueba del sistema de chat"
            ).first()
            
            if not solicitud_test:
                solicitud_test = SolicitudSoporte.objects.create(
                    usuario=usuario_regular,
                    mensaje="Prueba del sistema de chat directo - generada automáticamente",
                    estado='pendiente'
                )
                print(f"   ✅ Solicitud de prueba creada: ID {solicitud_test.id}")
            else:
                print(f"   ℹ️  Solicitud de prueba existente: ID {solicitud_test.id}")
        
    except Exception as e:
        print(f"   ❌ Error creando datos de prueba: {e}")
    
    print("\n🎉 Verificación completada!")
    print("\n📋 Próximos pasos para probar:")
    print("1. Ve a /admin/solicitudes-soporte/ para ver solicitudes")
    print("2. Acepta una solicitud para crear un chat")
    print("3. Ve a /admin/conversaciones-activas/ para ver chats activos")
    print("4. Prueba el chat directo entre usuario y admin")
    
    return True

if __name__ == "__main__":
    verificar_chat_system()