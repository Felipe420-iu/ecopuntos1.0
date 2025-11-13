#!/usr/bin/env python
"""
Script de prueba para verificar el sistema de términos y condiciones
"""

import os
import sys
import django

# Configurar Django
if __name__ == "__main__":
    project_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_path)
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
    django.setup()
    
    from core.models import Usuario
    from django.utils import timezone
    
    print("🧪 PRUEBA DEL SISTEMA DE TÉRMINOS Y CONDICIONES")
    print("=" * 50)
    
    try:
        # Estadísticas actuales
        total_usuarios = Usuario.objects.count()
        usuarios_con_terminos = Usuario.objects.filter(terminos_aceptados=True).count()
        usuarios_sin_terminos = Usuario.objects.filter(terminos_aceptados=False).count()
        
        print(f"📊 ESTADÍSTICAS ACTUALES:")
        print(f"   • Total de usuarios: {total_usuarios}")
        print(f"   • Han aceptado términos: {usuarios_con_terminos}")
        print(f"   • Necesitan aceptar términos: {usuarios_sin_terminos}")
        
        # Mostrar algunos usuarios de ejemplo
        print(f"\n👥 USUARIOS QUE VERÁN EL MODAL:")
        usuarios_ejemplo = Usuario.objects.filter(terminos_aceptados=False)[:5]
        for usuario in usuarios_ejemplo:
            print(f"   • {usuario.username} ({usuario.email or 'sin email'})")
        
        if usuarios_sin_terminos > 5:
            print(f"   ... y {usuarios_sin_terminos - 5} más")
        
        # URLs a probar
        print(f"\n🔗 URLs PARA PROBAR:")
        print(f"   • Login: http://127.0.0.1:8000/iniciosesion/")
        print(f"   • Dashboard: http://127.0.0.1:8000/dashusuario/")
        print(f"   • Términos: http://127.0.0.1:8000/terminos-condiciones/")
        print(f"   • Privacidad: http://127.0.0.1:8000/politica-privacidad/")
        
        # Flujo de prueba
        print(f"\n🎯 FLUJO DE PRUEBA:")
        print(f"   1. Inicia sesión con cualquier usuario existente")
        print(f"   2. Serás redirigido al dashboard")
        print(f"   3. Debería aparecer el modal de términos automáticamente")
        print(f"   4. Marca la casilla 'Acepto los términos'")
        print(f"   5. Haz clic en 'Aceptar y Continuar'")
        print(f"   6. El modal se cierra y aparece un mensaje de éxito")
        print(f"   7. Refresca la página - el modal NO debe aparecer")
        print(f"   8. El usuario ya tiene terminos_aceptados=True")
        
        print(f"\n🆕 PARA USUARIOS NUEVOS:")
        print(f"   1. Regístrate desde: http://127.0.0.1:8000/registrate/")
        print(f"   2. Después del registro exitoso, inicia sesión")
        print(f"   3. Al acceder al dashboard, verás el modal de términos")
        print(f"   4. Acepta los términos (solo aparece una vez)")
        
        # Verificar configuración del sistema
        print(f"\n⚙️ VERIFICACIÓN DEL SISTEMA:")
        
        # Verificar URLs
        try:
            from django.urls import reverse
            terminos_url = reverse('aceptar_terminos')
            verificar_url = reverse('verificar_terminos')
            print(f"   ✅ URLs configuradas correctamente")
            print(f"      - Aceptar: {terminos_url}")
            print(f"      - Verificar: {verificar_url}")
        except Exception as e:
            print(f"   ❌ Error en URLs: {e}")
        
        # Verificar modelo
        try:
            test_user = Usuario.objects.first()
            if test_user:
                print(f"   ✅ Campos del modelo disponibles:")
                print(f"      - terminos_aceptados: {test_user.terminos_aceptados}")
                print(f"      - fecha_aceptacion_terminos: {test_user.fecha_aceptacion_terminos}")
            else:
                print(f"   ⚠️ No hay usuarios para probar")
        except Exception as e:
            print(f"   ❌ Error en modelo: {e}")
        
        print(f"\n✅ SISTEMA LISTO PARA PRUEBAS")
        print(f"   El modal aparecerá para todos los usuarios existentes")
        print(f"   Una vez aceptado, no volverá a aparecer")
        print(f"   Los nuevos usuarios también lo verán una sola vez")
        
    except Exception as e:
        print(f"❌ Error en el sistema: {e}")
        import traceback
        traceback.print_exc()
