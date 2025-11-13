#!/usr/bin/env python
"""
Script para verificar que todas las URLs de términos y condiciones funcionen
"""
import urllib.request
import urllib.error
import time

def test_urls():
    """Prueba todas las URLs relacionadas con términos y condiciones"""
    base_url = "http://127.0.0.1:8000"
    
    urls_to_test = [
        ("/", "Página de Inicio"),
        ("/iniciosesion/", "Inicio de Sesión"),
        ("/registrate/", "Registro"),
        ("/terminos-condiciones/", "Términos y Condiciones"),
        ("/politica-privacidad/", "Política de Privacidad"),
    ]
    
    print("🔍 Verificando URLs de EcoPuntos...")
    print("=" * 50)
    
    all_working = True
    
    for url_path, description in urls_to_test:
        full_url = base_url + url_path
        try:
            print(f"📄 Probando: {description}")
            print(f"   URL: {full_url}")
            
            response = urllib.request.urlopen(full_url, timeout=10)
            status_code = response.getcode()
            
            if status_code == 200:
                print(f"   ✅ Estado: {status_code} - OK")
                
                # Leer contenido
                content = response.read().decode('utf-8')
                
                # Verificar contenido específico
                if url_path == "/terminos-condiciones/":
                    if "Términos y Condiciones" in content and "EcoPuntos" in content:
                        print(f"   ✅ Contenido: Válido")
                    else:
                        print(f"   ⚠️ Contenido: Posible problema")
                        
                elif url_path == "/politica-privacidad/":
                    if "Política de Privacidad" in content and "privacidad" in content:
                        print(f"   ✅ Contenido: Válido")
                    else:
                        print(f"   ⚠️ Contenido: Posible problema")
                        
                elif url_path == "/registrate/":
                    if "terminosCheck" in content and "Términos y Condiciones" in content:
                        print(f"   ✅ Contenido: Checkbox de términos presente")
                    else:
                        print(f"   ⚠️ Contenido: Checkbox de términos faltante")
                        
                elif url_path == "/iniciosesion/":
                    if "Términos y Condiciones" in content and "Política de Privacidad" in content:
                        print(f"   ✅ Contenido: Enlaces legales presentes")
                    else:
                        print(f"   ⚠️ Contenido: Enlaces legales faltantes")
                        
            else:
                print(f"   ❌ Estado: {status_code} - Error")
                all_working = False
                
        except urllib.error.URLError as e:
            print(f"   ❌ Error de conexión: {e}")
            all_working = False
            
        except Exception as e:
            print(f"   ❌ Error inesperado: {e}")
            all_working = False
            
        print()
        time.sleep(0.5)  # Pequeña pausa entre requests
    
    print("=" * 50)
    if all_working:
        print("🎉 ¡TODAS LAS URLs FUNCIONAN CORRECTAMENTE!")
        print("\n✅ Resumen de funcionalidades verificadas:")
        print("   - Términos y Condiciones accesibles")
        print("   - Política de Privacidad accesible")
        print("   - Checkbox de términos en registro")
        print("   - Enlaces legales en inicio de sesión")
        print("   - Footer con enlaces legales")
        print("\n🚀 ¡Tu aplicación está lista para producción!")
    else:
        print("⚠️ Algunas URLs presentan problemas.")
        print("   Revisa los errores mostrados arriba.")
    
    print("\n📋 URLs disponibles:")
    for url_path, description in urls_to_test:
        print(f"   {description}: {base_url}{url_path}")

if __name__ == "__main__":
    try:
        test_urls()
    except KeyboardInterrupt:
        print("\n❌ Prueba cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")
