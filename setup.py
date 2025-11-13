#!/usr/bin/env python
"""
Script de configuración e instalación para EcoPuntos
Este script automatiza la instalación y configuración inicial del proyecto.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, description=""):
    """Ejecutar comando y manejar errores"""
    print(f"\n{'='*50}")
    print(f"Ejecutando: {description or command}")
    print(f"{'='*50}")
    
    try:
        if platform.system() == "Windows":
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command.split(), check=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando: {command}")
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def check_python_version():
    """Verificar versión de Python"""
    print("Verificando versión de Python...")
    if sys.version_info < (3, 8):
        print("Error: Se requiere Python 3.8 o superior")
        sys.exit(1)
    print(f"✓ Python {sys.version} detectado")


def create_virtual_environment():
    """Crear entorno virtual"""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✓ Entorno virtual ya existe")
        return True
    
    print("Creando entorno virtual...")
    return run_command("python -m venv venv", "Crear entorno virtual")


def activate_virtual_environment():
    """Activar entorno virtual"""
    if platform.system() == "Windows":
        activate_script = "venv\\Scripts\\activate"
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:
        activate_script = "source venv/bin/activate"
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    print(f"Para activar el entorno virtual manualmente, ejecuta: {activate_script}")
    return pip_path, python_path


def install_dependencies(pip_path):
    """Instalar dependencias"""
    print("Instalando dependencias...")
    
    # Actualizar pip
    if not run_command(f"{pip_path} install --upgrade pip", "Actualizar pip"):
        return False
    
    # Instalar dependencias principales
    if not run_command(f"{pip_path} install -r requirements.txt", "Instalar dependencias del proyecto"):
        return False
    
    return True


def setup_database(python_path):
    """Configurar base de datos"""
    print("Configurando base de datos...")
    
    # Crear migraciones
    if not run_command(f"{python_path} manage.py makemigrations", "Crear migraciones"):
        return False
    
    # Aplicar migraciones
    if not run_command(f"{python_path} manage.py migrate", "Aplicar migraciones"):
        return False
    
    return True


def create_superuser(python_path):
    """Crear superusuario"""
    print("\n¿Deseas crear un superusuario? (s/n): ", end="")
    response = input().lower().strip()
    
    if response in ['s', 'si', 'y', 'yes']:
        print("Creando superusuario...")
        print("Nota: Se te pedirá ingresar username, email y password")
        
        if platform.system() == "Windows":
            os.system(f"{python_path} manage.py createsuperuser")
        else:
            subprocess.run([python_path, "manage.py", "createsuperuser"])
    
    return True


def collect_static_files(python_path):
    """Recopilar archivos estáticos"""
    print("Recopilando archivos estáticos...")
    return run_command(f"{python_path} manage.py collectstatic --noinput", "Recopilar archivos estáticos")


def create_directories():
    """Crear directorios necesarios"""
    directories = ['logs', 'media', 'staticfiles']
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Directorio '{directory}' creado")
        else:
            print(f"✓ Directorio '{directory}' ya existe")


def check_env_file():
    """Verificar archivo .env"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Archivo .env no encontrado")
        print("Copiando .env.example a .env...")
        
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ Archivo .env creado desde .env.example")
            print("⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones reales")
        else:
            print("❌ Archivo .env.example no encontrado")
            return False
    else:
        print("✓ Archivo .env encontrado")
    
    return True


def show_next_steps():
    """Mostrar pasos siguientes"""
    print("\n" + "="*60)
    print("🎉 INSTALACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        python_cmd = "venv\\Scripts\\python"
    else:
        activate_cmd = "source venv/bin/activate"
        python_cmd = "venv/bin/python"
    
    print("\n📋 PASOS SIGUIENTES:")
    print("\n1. Activar el entorno virtual:")
    print(f"   {activate_cmd}")
    
    print("\n2. Configurar variables de entorno:")
    print("   - Edita el archivo .env con tus configuraciones")
    print("   - Configura tu base de datos Supabase")
    print("   - Configura tu email para notificaciones")
    
    print("\n3. Ejecutar el servidor de desarrollo:")
    print(f"   {python_cmd} manage.py runserver")
    
    print("\n4. Acceder a la aplicación:")
    print("   - Aplicación web: http://localhost:8000")
    print("   - Panel de administración: http://localhost:8000/admin")
    print("   - API REST: http://localhost:8000/api/v1/")
    
    print("\n5. Para ejecutar tests:")
    print("   pytest")
    
    print("\n📚 DOCUMENTACIÓN ADICIONAL:")
    print("   - README.md: Información general del proyecto")
    print("   - requirements.txt: Lista de dependencias")
    print("   - .env.example: Ejemplo de configuración")
    
    print("\n⚠️  IMPORTANTE PARA PRODUCCIÓN:")
    print("   - Cambiar SECRET_KEY en .env")
    print("   - Configurar DEBUG=False")
    print("   - Configurar ALLOWED_HOSTS apropiadamente")
    print("   - Usar PostgreSQL en lugar de SQLite")
    print("   - Configurar HTTPS")
    
    print("\n" + "="*60)


def main():
    """Función principal"""
    print("🚀 CONFIGURACIÓN DE ECOPUNTOS")
    print("Este script configurará automáticamente el proyecto EcoPuntos")
    print("\n" + "="*60)
    
    # Verificaciones iniciales
    check_python_version()
    
    # Verificar archivo .env
    if not check_env_file():
        print("❌ Error en la configuración del archivo .env")
        sys.exit(1)
    
    # Crear directorios necesarios
    create_directories()
    
    # Crear entorno virtual
    if not create_virtual_environment():
        print("❌ Error creando entorno virtual")
        sys.exit(1)
    
    # Obtener rutas del entorno virtual
    pip_path, python_path = activate_virtual_environment()
    
    # Instalar dependencias
    if not install_dependencies(pip_path):
        print("❌ Error instalando dependencias")
        sys.exit(1)
    
    # Configurar base de datos
    if not setup_database(python_path):
        print("❌ Error configurando base de datos")
        sys.exit(1)
    
    # Recopilar archivos estáticos
    if not collect_static_files(python_path):
        print("⚠️  Advertencia: Error recopilando archivos estáticos")
    
    # Crear superusuario
    create_superuser(python_path)
    
    # Mostrar pasos siguientes
    show_next_steps()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Instalación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        sys.exit(1)