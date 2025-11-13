#!/usr/bin/env python
"""
Script para probar la lógica de suspensión de usuarios
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from core.models import Usuario
from django.contrib.auth import authenticate

def test_suspension_logic():
    print("=== PROBANDO LÓGICA DE SUSPENSIÓN DE USUARIOS ===\n")
    
    # Crear un usuario de prueba
    test_username = "usuario_test_suspension"
    test_password = "password123"
    test_email = "test_suspension@example.com"
    
    # Limpiar usuario de prueba si existe
    try:
        existing_user = Usuario.objects.get(username=test_username)
        existing_user.delete()
        print(f"✓ Usuario de prueba anterior eliminado")
    except Usuario.DoesNotExist:
        pass
    
    # Crear nuevo usuario
    user = Usuario.objects.create_user(
        username=test_username,
        email=test_email,
        password=test_password,
        nombres="Usuario",
        apellidos="De Prueba",
        cedula="1234567890"
    )
    print(f"✓ Usuario creado: {user.username}")
    print(f"  - is_active: {user.is_active}")
    print(f"  - suspended: {user.suspended}")
    
    # Probar autenticación normal
    auth_user = authenticate(username=test_username, password=test_password)
    if auth_user:
        print(f"✓ Autenticación normal exitosa")
    else:
        print(f"✗ Error en autenticación normal")
    
    # Suspender usuario
    user.suspended = True
    user.save()
    print(f"\n✓ Usuario suspendido")
    print(f"  - is_active: {user.is_active}")
    print(f"  - suspended: {user.suspended}")
    
    # Probar autenticación con usuario suspendido
    auth_user = authenticate(username=test_username, password=test_password)
    if auth_user:
        print(f"✓ Autenticación con usuario suspendido funciona (contraseña correcta)")
        print(f"  - El middleware debería redirigir a usuario_suspendido")
    else:
        print(f"✗ Error en autenticación con usuario suspendido")
    
    # Desactivar usuario (mantener suspensión)
    user.is_active = False
    user.save()
    print(f"\n✓ Usuario desactivado (y suspendido)")
    print(f"  - is_active: {user.is_active}")
    print(f"  - suspended: {user.suspended}")
    
    # Probar autenticación con usuario desactivado y suspendido
    auth_user = authenticate(username=test_username, password=test_password)
    if auth_user:
        print(f"✓ Autenticación con usuario desactivado funciona")
        print(f"  - Debería redirigir a usuario_suspendido (prioridad)")
    else:
        print(f"✗ Error en autenticación con usuario desactivado")
    
    # Reactivar usuario (quitar suspensión)
    user.is_active = True
    user.suspended = False
    user.save()
    print(f"\n✓ Usuario reactivado")
    print(f"  - is_active: {user.is_active}")
    print(f"  - suspended: {user.suspended}")
    
    # Probar autenticación con usuario reactivado
    auth_user = authenticate(username=test_username, password=test_password)
    if auth_user:
        print(f"✓ Autenticación con usuario reactivado exitosa")
    else:
        print(f"✗ Error en autenticación con usuario reactivado")
    
    # Limpiar
    user.delete()
    print(f"\n✓ Usuario de prueba eliminado")
    print(f"\n=== PRUEBA COMPLETADA ===")

if __name__ == "__main__":
    test_suspension_logic()
