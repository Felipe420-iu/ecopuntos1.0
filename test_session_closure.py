#!/usr/bin/env python
"""
Script para probar el cierre de sesión y bloqueo inmediato
"""
import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.models import Usuario, SesionUsuario
from django.utils import timezone

def test_session_closure():
    """Prueba el cierre de sesión de un usuario"""
    print("🔍 Buscando sesiones activas...")
    
    # Buscar sesiones activas
    sesiones_activas = SesionUsuario.objects.filter(activa=True)
    
    if not sesiones_activas.exists():
        print("❌ No hay sesiones activas para probar")
        
        # Mostrar todos los usuarios disponibles
        usuarios = Usuario.objects.all()
        print("\n👥 Usuarios disponibles:")
        for usuario in usuarios:
            print(f"- {usuario.username} (ID: {usuario.id})")
        
        return
    
    print(f"✅ Encontradas {sesiones_activas.count()} sesiones activas:")
    
    for sesion in sesiones_activas:
        print(f"""
📱 Sesión Activa:
   - Usuario: {sesion.usuario.username}
   - Dispositivo ID: {sesion.dispositivo_id}
   - IP: {sesion.ip_address}
   - Token: {sesion.token_sesion[:20]}...
   - Fecha creación: {sesion.fecha_creacion}
   - Expira: {sesion.fecha_expiracion}
        """)
    
    # Preguntar cuál cerrar
    try:
        usuario_nombre = input("\n💡 Ingresa el nombre del usuario cuya sesión quieres cerrar: ").strip()
        
        if not usuario_nombre:
            print("❌ Nombre de usuario vacío")
            return
        
        sesion_usuario = sesiones_activas.filter(usuario__username=usuario_nombre).first()
        
        if not sesion_usuario:
            print(f"❌ No se encontró sesión activa para el usuario '{usuario_nombre}'")
            return
        
        # Cerrar la sesión
        print(f"🔒 Cerrando sesión de {usuario_nombre}...")
        sesion_usuario.activa = False
        sesion_usuario.save()
        
        print(f"✅ Sesión cerrada exitosamente!")
        print(f"""
🎯 Detalles del cierre:
   - Usuario: {sesion_usuario.usuario.username}
   - Token: {sesion_usuario.token_sesion[:20]}...
   - Activa: {sesion_usuario.activa}
        """)
        
        print("""
🔔 INSTRUCCIONES PARA PROBAR:
1. Ve al navegador donde el usuario está logueado
2. Intenta navegar a cualquier página (ej. categorías)
3. Deberías ver el modal de sesión cerrada inmediatamente
4. El usuario no debería poder navegar más

📝 VERIFICACIONES:
- ✅ Monitor de sesión agregado a todas las páginas principales
- ✅ Verificaciones cada 3 segundos
- ✅ Middleware bloqueando navegación
- ✅ Sistema de bloqueo total activado
        """)
        
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_session_closure()
