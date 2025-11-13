#!/usr/bin/env python
"""
Script para probar el estado "aprobado" en pagos
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import Usuario, RedencionPuntos
from datetime import datetime

def test_estado_aprobado():
    """Probar el estado aprobado en redenciones"""
    
    print("🧪 PROBANDO ESTADO 'APROBADO' EN PAGOS")
    print("=" * 50)
    
    # Obtener un usuario
    usuario = Usuario.objects.filter(email__isnull=False).exclude(email='').first()
    if not usuario:
        print("❌ No se encontró usuario para el test")
        return
    
    print(f"👤 Usuario seleccionado: {usuario.username}")
    
    # Verificar si hay redenciones existentes
    redenciones = RedencionPuntos.objects.filter(usuario=usuario).order_by('-id')
    
    if redenciones.exists():
        print(f"\n💰 REDENCIONES EXISTENTES:")
        for redencion in redenciones[:5]:  # Mostrar solo las últimas 5
            print(f"   📋 ID: {redencion.id}")
            print(f"   💰 Valor: ${redencion.valor_cop} COP")
            print(f"   📊 Estado: {redencion.estado}")
            print(f"   📅 Fecha: {redencion.fecha_solicitud}")
            print(f"   ---")
        
        # Cambiar el estado de la primera a "aprobado" para testing
        primera_redencion = redenciones.first()
        estado_anterior = primera_redencion.estado
        
        primera_redencion.estado = 'aprobado'
        primera_redencion.save()
        
        print(f"\n✅ PRUEBA REALIZADA:")
        print(f"   🔄 Cambié redencion ID {primera_redencion.id}")
        print(f"   📊 Estado anterior: {estado_anterior}")
        print(f"   📊 Estado nuevo: aprobado")
        print(f"\n📱 RESULTADO ESPERADO EN LA WEB:")
        print(f"   🎨 Debería mostrar clase CSS: 'status-aprobado'")
        print(f"   📝 Texto: 'Aprobado' (o el valor de get_estado_display)")
        print(f"   🎪 Modal: 'Canje Aprobado' con mensaje de 24 horas")
        
        return primera_redencion.id
        
    else:
        # Crear una redención de prueba
        nueva_redencion = RedencionPuntos.objects.create(
            usuario=usuario,
            puntos=1000,
            valor_cop=500,
            metodo_pago='nequi',
            numero_cuenta='3001234567',
            estado='aprobado'  # Directamente con estado aprobado
        )
        
        print(f"\n✅ REDENCIÓN DE PRUEBA CREADA:")
        print(f"   📋 ID: {nueva_redencion.id}")
        print(f"   💰 Valor: ${nueva_redencion.valor_cop} COP")
        print(f"   📊 Estado: {nueva_redencion.estado}")
        print(f"   📅 Fecha: {nueva_redencion.fecha_solicitud}")
        
        return nueva_redencion.id

def mostrar_instrucciones(redencion_id):
    """Mostrar instrucciones para probar en el navegador"""
    
    print(f"\n🔧 INSTRUCCIONES PARA PROBAR:")
    print("=" * 50)
    print("1. 🌐 Ve a: http://127.0.0.1:8000/pagos/")
    print("2. 👀 Busca la transacción con estado 'Aprobado'")
    print("3. 🎨 Debería tener fondo verde claro")
    print("4. 👆 Haz clic en el ícono del ojo (👁️) para ver detalles")
    print("5. 🎪 Debería aparecer modal con:")
    print("   • ✅ Ícono verde de check")
    print("   • 📝 Título: 'Canje Aprobado'")
    print("   • 💬 Mensaje: 'en las próximas 24 horas'")
    print("")
    print("🎯 SI NO VES EL ESTADO 'APROBADO':")
    print("   • Recarga la página (F5)")
    print("   • Verifica que el usuario tenga redenciones")
    print("   • Checa que el estado en la BD sea 'aprobado'")

if __name__ == "__main__":
    redencion_id = test_estado_aprobado()
    if redencion_id:
        mostrar_instrucciones(redencion_id)
        print(f"\n🎉 ¡Test completado! Redencion ID: {redencion_id}")
    else:
        print("\n❌ Test falló - No se pudo crear/encontrar redención")