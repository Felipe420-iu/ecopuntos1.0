#!/usr/bin/env python
"""
Test del reagendamiento desde la interfaz web de rutas
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import Usuario, Ruta, Notificacion
from django.test import Client
from django.contrib.auth import login
import json

def test_reagendamiento_desde_interfaz():
    """Test del reagendamiento desde la interfaz web"""
    
    print("🌐 TEST REAGENDAMIENTO DESDE INTERFAZ WEB")
    print("=" * 60)
    
    # 1. Configurar cliente de prueba
    client = Client()
    
    # 2. Obtener usuario con rutas
    usuario = Usuario.objects.filter(email__isnull=False).exclude(email='').first()
    if not usuario:
        print("❌ No hay usuarios con email")
        return False
        
    ruta = Ruta.objects.filter(usuario=usuario).first()
    if not ruta:
        print("❌ No hay rutas para el usuario")
        return False
    
    # 3. Obtener usuario admin/conductor para realizar el reagendamiento
    admin_user = Usuario.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = Usuario.objects.filter(role='conductor').first()
    
    if not admin_user:
        print("❌ No hay admin o conductor para realizar reagendamiento")
        return False
    
    print(f"👤 Usuario con ruta: {usuario.username} ({usuario.email})")
    print(f"🛣️ Ruta ID: {ruta.id}")
    print(f"👮 Admin/Conductor: {admin_user.username}")
    
    # 4. Limpiar notificaciones anteriores
    notificaciones_antes = Notificacion.objects.filter(
        usuario=usuario,
        titulo="Recolección Reagendada",
        leida=False
    ).count()
    
    Notificacion.objects.filter(
        usuario=usuario,
        titulo="Recolección Reagendada"
    ).delete()
    
    print(f"🧹 Limpiadas {notificaciones_antes} notificaciones anteriores")
    
    # 5. Hacer login como admin/conductor
    client.force_login(admin_user)
    
    # 6. Simular reagendamiento desde la interfaz web
    print(f"\n🔧 REAGENDAMIENTO DESDE INTERFAZ WEB:")
    
    try:
        # Datos del formulario como los enviaría la interfaz
        form_data = {
            'fecha': '2025-12-30',
            'hora': '14:30',
            'notas_admin': 'Reagendado desde interfaz web - test automático'
        }
        
        # Hacer POST al endpoint de reagendamiento
        response = client.post(f'/reagendar_ruta/{ruta.id}/', form_data)
        
        print(f"   📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = json.loads(response.content.decode())
            print(f"   📊 Respuesta: {data}")
            
            if data.get('success'):
                print("   ✅ Reagendamiento exitoso desde interfaz")
                
                # 7. Verificar que se creó la notificación
                notificaciones_nuevas = Notificacion.objects.filter(
                    usuario=usuario,
                    titulo="Recolección Reagendada",
                    leida=False
                )
                
                print(f"\n🔔 VERIFICACIÓN DE NOTIFICACIÓN:")
                print(f"   📊 Notificaciones creadas: {notificaciones_nuevas.count()}")
                
                if notificaciones_nuevas.exists():
                    notif = notificaciones_nuevas.first()
                    print(f"   ✅ NOTIFICACIÓN CREADA:")
                    print(f"      🆔 ID: {notif.id}")
                    print(f"      📖 Estado: {'LEÍDA' if notif.leida else 'NO LEÍDA'}")
                    print(f"      📝 Mensaje: {notif.mensaje}")
                    print(f"      📅 Creada: {notif.fecha_creacion}")
                    
                    # 8. Verificar actualización de ruta
                    ruta.refresh_from_db()
                    print(f"\n🛣️ VERIFICACIÓN DE RUTA ACTUALIZADA:")
                    print(f"   📅 Nueva fecha: {ruta.fecha}")
                    print(f"   🕐 Nueva hora: {ruta.hora}")
                    print(f"   📝 Notas: {ruta.notas_admin}")
                    
                    return True
                else:
                    print("   ❌ NO se creó la notificación")
                    return False
            else:
                print(f"   ❌ Error en reagendamiento: {data.get('message')}")
                return False
        else:
            print(f"   ❌ Error HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def mostrar_instrucciones_uso():
    """Instrucciones para el usuario"""
    
    print(f"\n🎯 INSTRUCCIONES DE USO:")
    print("=" * 50)
    print("✅ El sistema está funcionando correctamente")
    print("")
    print("🔄 PARA REAGENDAR UNA RUTA:")
    print("   1. 🌐 Ve a la página de Gestión de Rutas")
    print("   2. 🔍 Busca la ruta que quieres reagendar")
    print("   3. 📅 Presiona el botón azul 'Reagendar' (ícono de calendario)")
    print("   4. 📋 Llena el formulario con:")
    print("      - Nueva fecha")
    print("      - Nueva hora")
    print("      - Motivo del reagendamiento")
    print("   5. ✅ Presiona 'Reagendar'")
    print("")
    print("🎪 QUE PASARÁ AUTOMÁTICAMENTE:")
    print("   1. 📧 Se envía correo al usuario")
    print("   2. 🔔 Se crea notificación en BD")
    print("   3. 🎪 Cuando el usuario entre a /rutasusuario/")
    print("      aparecerá el modal automáticamente")
    print("   4. ✅ Usuario puede aceptar o rechazar")

if __name__ == "__main__":
    resultado = test_reagendamiento_desde_interfaz()
    
    if resultado:
        print(f"\n🎉 ¡REAGENDAMIENTO DESDE INTERFAZ FUNCIONA!")
        mostrar_instrucciones_uso()
    else:
        print(f"\n❌ HAY PROBLEMAS EN EL REAGENDAMIENTO")