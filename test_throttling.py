#!/usr/bin/env python
"""
Script de prueba para el sistema de throttling
Simula múltiples requests para probar los límites
"""

import requests
import time
import sys
from datetime import datetime

def test_throttling():
    """Prueba el sistema de throttling haciendo múltiples requests"""
    
    # URL base de tu aplicación
    base_url = "http://127.0.0.1:8000"
    
    # Endpoints para probar
    endpoints = [
        "/",  # Página principal
        "/iniciosesion/",  # Login (debería tener límite de 5/minuto)
        "/dashboard/",  # Dashboard (debería tener límite)
    ]
    
    print("🎯 Iniciando prueba de Rate Limiting/Throttling")
    print("=" * 60)
    
    for endpoint in endpoints:
        print(f"\n📍 Probando endpoint: {endpoint}")
        url = base_url + endpoint
        
        success_count = 0
        throttled_count = 0
        
        # Hacer 10 requests rápidos
        for i in range(1, 11):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=5)
                response_time = time.time() - start_time
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"   Request {i:2d}: ✅ 200 OK ({response_time:.2f}s) - {timestamp}")
                elif response.status_code == 429:
                    throttled_count += 1
                    print(f"   Request {i:2d}: ⚠️  429 THROTTLED! - {timestamp}")
                    
                    # Verificar headers de rate limiting
                    if 'X-RateLimit-Limit' in response.headers:
                        print(f"                   Rate Limit: {response.headers['X-RateLimit-Limit']}")
                    if 'X-RateLimit-Remaining' in response.headers:
                        print(f"                   Remaining: {response.headers['X-RateLimit-Remaining']}")
                    if 'Retry-After' in response.headers:
                        print(f"                   Retry After: {response.headers['Retry-After']}s")
                        
                else:
                    print(f"   Request {i:2d}: ❌ {response.status_code} - {timestamp}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   Request {i:2d}: 💥 ERROR: {str(e)}")
            
            # Pequeña pausa entre requests
            time.sleep(0.1)
        
        print(f"\n   📊 Resumen para {endpoint}:")
        print(f"       ✅ Exitosos: {success_count}")
        print(f"       ⚠️  Throttled: {throttled_count}")
        
        # Esperar antes del siguiente endpoint
        if endpoint != endpoints[-1]:
            print("\n   ⏳ Esperando 3 segundos antes del siguiente endpoint...")
            time.sleep(3)
    
    print("\n" + "=" * 60)
    print("🏁 Prueba completada!")
    
    if throttled_count > 0:
        print("✅ El throttling está funcionando correctamente!")
    else:
        print("ℹ️  No se detectó throttling. Esto puede significar:")
        print("   - El sistema no está configurado")
        print("   - Los límites son muy altos")
        print("   - Necesitas hacer más requests")

def test_login_throttling():
    """Prueba específica para el throttling de login"""
    print("\n🔐 Prueba específica de Login Throttling")
    print("=" * 50)
    
    login_url = "http://127.0.0.1:8000/iniciosesion/"
    
    for i in range(1, 8):  # Intentar 7 logins (debería fallar después del 5to)
        try:
            response = requests.post(login_url, data={
                'username': 'test_user',
                'password': 'wrong_password'
            }, timeout=5)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if response.status_code == 429:
                print(f"   Login {i}: ⚠️  429 THROTTLED! - {timestamp}")
                break
            else:
                print(f"   Login {i}: ✅ {response.status_code} - {timestamp}")
                
        except requests.exceptions.RequestException as e:
            print(f"   Login {i}: 💥 ERROR: {str(e)}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    try:
        print("🚀 Verificando que el servidor esté corriendo...")
        response = requests.get("http://127.0.0.1:8000", timeout=5)
        print("✅ Servidor detectado!")
        
        test_throttling()
        test_login_throttling()
        
    except requests.exceptions.RequestException:
        print("❌ Error: No se puede conectar al servidor")
        print("   Asegúrate de que Django esté corriendo en http://127.0.0.1:8000")
        sys.exit(1)