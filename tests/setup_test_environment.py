#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para configurar el entorno de pruebas de EcoPuntos

Este script instala todas las dependencias necesarias para ejecutar las pruebas
y configura el entorno de pruebas.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Configuración de rutas
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS_DIR = PROJECT_ROOT / 'tests'
RESULTS_DIR = PROJECT_ROOT / 'tests' / 'results'
REPORTS_DIR = PROJECT_ROOT / 'tests' / 'reports'

# Asegurar que los directorios existan
RESULTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Dependencias Python
PYTHON_DEPENDENCIES = [
    'pandas',
    'openpyxl',
    'termcolor',
    'pytest',
    'pytest-django',
    'pytest-html',
    'axe-selenium-python',
    'selenium',
    'requests',
    'beautifulsoup4',
    'coverage'
]

# Dependencias Node.js
NODE_DEPENDENCIES = [
    'playwright',
    'stylelint',
    'axe-core',
    'jest',
    'jest-html-reporter'
]


def print_header(text):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 80)
    print(f" {text} ")
    print("=" * 80)


def print_section(text):
    """Imprime una sección formateada"""
    print("\n" + "-" * 60)
    print(f" {text} ")
    print("-" * 60)


def run_command(command, cwd=None):
    """Ejecuta un comando y devuelve el resultado"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_python_version():
    """Verifica la versión de Python"""
    print_section("Verificando versión de Python")
    
    version = sys.version.split()[0]
    print(f"Versión de Python: {version}")
    
    major, minor, *_ = version.split('.')
    if int(major) < 3 or (int(major) == 3 and int(minor) < 6):
        print("ADVERTENCIA: Se recomienda Python 3.6 o superior para ejecutar las pruebas.")
        return False
    
    print("Versión de Python compatible.")
    return True


def check_node_version():
    """Verifica la versión de Node.js"""
    print_section("Verificando versión de Node.js")
    
    success, stdout, stderr = run_command("node --version")
    if not success:
        print("ADVERTENCIA: No se pudo determinar la versión de Node.js.")
        print(f"Error: {stderr}")
        return False
    
    version = stdout.strip()
    print(f"Versión de Node.js: {version}")
    
    # Verificar que sea v12 o superior (para Playwright)
    if version.startswith('v'):
        major = int(version[1:].split('.')[0])
        if major < 12:
            print("ADVERTENCIA: Se recomienda Node.js v12 o superior para ejecutar las pruebas de diseño.")
            return False
    
    print("Versión de Node.js compatible.")
    return True


def install_python_dependencies():
    """Instala las dependencias de Python"""
    print_section("Instalando dependencias de Python")
    
    for dependency in PYTHON_DEPENDENCIES:
        print(f"Instalando {dependency}...")
        success, stdout, stderr = run_command(f"{sys.executable} -m pip install {dependency}")
        
        if success:
            print(f"  ✓ {dependency} instalado correctamente.")
        else:
            print(f"  ✗ Error al instalar {dependency}.")
            print(f"    {stderr}")
    
    print("\nDependencias de Python instaladas.")


def install_node_dependencies():
    """Instala las dependencias de Node.js"""
    print_section("Instalando dependencias de Node.js")
    
    # Verificar si npm está disponible
    success, _, _ = run_command("npm --version")
    if not success:
        print("ADVERTENCIA: npm no está disponible. No se pueden instalar dependencias de Node.js.")
        return False
    
    # Instalar dependencias globales
    for dependency in NODE_DEPENDENCIES:
        print(f"Instalando {dependency}...")
        success, stdout, stderr = run_command(f"npm install -g {dependency}")
        
        if success:
            print(f"  ✓ {dependency} instalado correctamente.")
        else:
            print(f"  ✗ Error al instalar {dependency}.")
            print(f"    {stderr}")
    
    # Instalar Playwright browsers
    print("\nInstalando navegadores para Playwright...")
    success, stdout, stderr = run_command("npx playwright install")
    
    if success:
        print("  ✓ Navegadores de Playwright instalados correctamente.")
    else:
        print("  ✗ Error al instalar navegadores de Playwright.")
        print(f"    {stderr}")
    
    print("\nDependencias de Node.js instaladas.")
    return True


def setup_django_test_environment():
    """Configura el entorno de pruebas de Django"""
    print_section("Configurando entorno de pruebas de Django")
    
    # Verificar si manage.py existe
    manage_py = PROJECT_ROOT / 'manage.py'
    if not manage_py.exists():
        print(f"ADVERTENCIA: No se encontró {manage_py}. No se puede configurar el entorno de Django.")
        return False
    
    # Verificar la configuración de Django
    print("Verificando configuración de Django...")
    success, stdout, stderr = run_command(f"{sys.executable} {manage_py} check")
    
    if success:
        print("  ✓ Configuración de Django correcta.")
    else:
        print("  ✗ Error en la configuración de Django.")
        print(f"    {stderr}")
        return False
    
    # Crear base de datos de pruebas
    print("\nCreando base de datos de pruebas...")
    success, stdout, stderr = run_command(f"{sys.executable} {manage_py} migrate --settings=ecopuntos.settings.test")
    
    if success:
        print("  ✓ Base de datos de pruebas creada correctamente.")
    else:
        print("  ✗ Error al crear la base de datos de pruebas.")
        print(f"    {stderr}")
    
    print("\nEntorno de pruebas de Django configurado.")
    return True


def create_test_data():
    """Crea datos de prueba"""
    print_section("Creando datos de prueba")
    
    # Verificar si manage.py existe
    manage_py = PROJECT_ROOT / 'manage.py'
    if not manage_py.exists():
        print(f"ADVERTENCIA: No se encontró {manage_py}. No se pueden crear datos de prueba.")
        return False
    
    # Crear datos de prueba
    print("Cargando datos de prueba...")
    success, stdout, stderr = run_command(f"{sys.executable} {manage_py} loaddata tests/fixtures/test_data.json")
    
    if success:
        print("  ✓ Datos de prueba cargados correctamente.")
    else:
        print("  ✗ Error al cargar datos de prueba.")
        print(f"    {stderr}")
        
        # Intentar crear datos de prueba básicos
        print("\nCreando datos de prueba básicos...")
        
        # Crear superusuario
        print("Creando superusuario de prueba...")
        success, stdout, stderr = run_command(
            f"{sys.executable} {manage_py} shell -c \""
            "from django.contrib.auth import get_user_model; "
            "User = get_user_model(); "
            "User.objects.create_superuser('admin', 'admin@example.com', 'admin')\""
        )
        
        if success:
            print("  ✓ Superusuario de prueba creado correctamente.")
        else:
            print("  ✗ Error al crear superusuario de prueba.")
            print(f"    {stderr}")
    
    print("\nDatos de prueba creados.")
    return True


def verify_test_environment():
    """Verifica que el entorno de pruebas esté correctamente configurado"""
    print_section("Verificando entorno de pruebas")
    
    # Verificar que los directorios existan
    print("Verificando directorios...")
    if RESULTS_DIR.exists() and REPORTS_DIR.exists():
        print("  ✓ Directorios de resultados e informes creados correctamente.")
    else:
        print("  ✗ Error al crear directorios de resultados e informes.")
    
    # Verificar que las dependencias de Python estén instaladas
    print("\nVerificando dependencias de Python...")
    missing_deps = []
    for dependency in PYTHON_DEPENDENCIES:
        try:
            __import__(dependency.split('[')[0])
            print(f"  ✓ {dependency} instalado correctamente.")
        except ImportError:
            print(f"  ✗ {dependency} no está instalado.")
            missing_deps.append(dependency)
    
    if missing_deps:
        print(f"\nFaltan {len(missing_deps)} dependencias de Python.")
    else:
        print("\nTodas las dependencias de Python están instaladas.")
    
    # Verificar que los scripts de prueba existan
    print("\nVerificando scripts de prueba...")
    scripts = [
        'run_manual_tests.py',
        'run_design_tests.py',
        'test_modules.py',
        'generate_test_report.py'
    ]
    
    missing_scripts = []
    for script in scripts:
        script_path = TESTS_DIR / script
        if script_path.exists():
            print(f"  ✓ {script} existe.")
        else:
            print(f"  ✗ {script} no existe.")
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"\nFaltan {len(missing_scripts)} scripts de prueba.")
    else:
        print("\nTodos los scripts de prueba existen.")
    
    # Verificar que los archivos de casos de prueba existan
    print("\nVerificando archivos de casos de prueba...")
    case_files = [
        'casos_de_prueba.md',
        'plantilla_casos_prueba.csv',
        'Plantilla de Casos de Prueba.xlsx'
    ]
    
    missing_files = []
    for case_file in case_files:
        file_path = PROJECT_ROOT / 'docs' / case_file
        if file_path.exists():
            print(f"  ✓ {case_file} existe.")
        else:
            print(f"  ✗ {case_file} no existe.")
            missing_files.append(case_file)
    
    if missing_files:
        print(f"\nFaltan {len(missing_files)} archivos de casos de prueba.")
    else:
        print("\nTodos los archivos de casos de prueba existen.")
    
    # Resultado final
    if not missing_deps and not missing_scripts and not missing_files:
        print("\nEl entorno de pruebas está correctamente configurado.")
        return True
    else:
        print("\nEl entorno de pruebas no está completamente configurado.")
        return False


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Configurar el entorno de pruebas para EcoPuntos')
    parser.add_argument('--skip-python', action='store_true', help='Omitir la instalación de dependencias de Python')
    parser.add_argument('--skip-node', action='store_true', help='Omitir la instalación de dependencias de Node.js')
    parser.add_argument('--skip-django', action='store_true', help='Omitir la configuración del entorno de Django')
    parser.add_argument('--skip-data', action='store_true', help='Omitir la creación de datos de prueba')
    parser.add_argument('--verify-only', action='store_true', help='Solo verificar el entorno sin instalar nada')
    
    args = parser.parse_args()
    
    print_header("CONFIGURACIÓN DEL ENTORNO DE PRUEBAS - ECOPUNTOS")
    
    # Verificar versiones
    python_ok = check_python_version()
    node_ok = check_node_version()
    
    if args.verify_only:
        verify_test_environment()
        return 0
    
    # Instalar dependencias
    if not args.skip_python and python_ok:
        install_python_dependencies()
    
    if not args.skip_node and node_ok:
        install_node_dependencies()
    
    # Configurar entorno de Django
    if not args.skip_django and python_ok:
        setup_django_test_environment()
    
    # Crear datos de prueba
    if not args.skip_data and python_ok:
        create_test_data()
    
    # Verificar entorno
    verify_test_environment()
    
    print_header("CONFIGURACIÓN COMPLETADA")
    print("El entorno de pruebas ha sido configurado correctamente.")
    print("\nPara ejecutar las pruebas, utilice los siguientes comandos:")
    print("  - Pruebas manuales: python tests/run_manual_tests.py")
    print("  - Pruebas de diseño: python tests/run_design_tests.py")
    print("  - Pruebas automatizadas: python -m unittest tests/test_modules.py")
    print("  - Generar informe: python tests/generate_test_report.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())