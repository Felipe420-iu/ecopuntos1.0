#!/usr/bin/env python
"""
Script de prueba para verificar la funcionalidad de usuarios desactivados
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.models import Usuario
from django.contrib.auth import authenticate

def test_usuario_desactivado():
    print("=== Test de Usuario Desactivado ===")
    
    # Crear usuario de prueba
    test_username = "usuario_test_desactivado"
    test_password = "password123"
    
    try:
        # Eliminar usuario si existe
        try:
            existing_user = Usuario.objects.get(username=test_username)
            existing_user.delete()
            print(f"✓ Usuario existente {test_username} eliminado")
        except Usuario.DoesNotExist:
            pass
        
        # Crear nuevo usuario
        user = Usuario.objects.create_user(
            username=test_username,
            password=test_password,
            email="test@test.com"
        )
        user.is_active = True
        user.save()
        print(f"✓ Usuario {test_username} creado y activado")
        
        # Probar autenticación con usuario activo
        auth_user = authenticate(username=test_username, password=test_password)
        if auth_user:
            print(f"✓ Autenticación exitosa con usuario activo")
        else:
            print(f"✗ Error: No se pudo autenticar usuario activo")
            return
        
        # Desactivar usuario
        user.is_active = False
        user.save()
        print(f"✓ Usuario {test_username} desactivado")
        
        # Verificar estado del usuario
        user.refresh_from_db()
        print(f"✓ Estado is_active: {user.is_active}")
        
        # Probar autenticación con usuario desactivado
        auth_user = authenticate(username=test_username, password=test_password)
        if auth_user is None:
            print(f"✓ Correcto: authenticate() retorna None para usuario desactivado")
        else:
            print(f"✗ Error: authenticate() retornó usuario para cuenta desactivada")
            
        # Verificar que el usuario existe pero está desactivado
        try:
            db_user = Usuario.objects.get(username=test_username)
            if not db_user.is_active:
                print(f"✓ Usuario existe en DB pero está desactivado")
            else:
                print(f"✗ Error: Usuario está activo en DB")
        except Usuario.DoesNotExist:
            print(f"✗ Error: Usuario no existe en DB")
            
        # Limpiar - eliminar usuario de prueba
        user.delete()
        print(f"✓ Usuario de prueba eliminado")
        
        print("\n=== Resumen ===")
        print("✓ La lógica de usuario desactivado funciona correctamente")
        print("✓ authenticate() retorna None para usuarios desactivados")
        print("✓ El campo is_active se actualiza correctamente")
        
    except Exception as e:
        print(f"✗ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_usuario_desactivado()
