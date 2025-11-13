#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para ejecutar las pruebas de diseño y generar informes

Este script ejecuta las pruebas de diseño definidas en el proyecto EcoPuntos,
incluidas las pruebas de regresión visual, diseño responsive, accesibilidad,
componentes JavaScript y validación CSS.
"""

import os
import sys
import json
import subprocess
import datetime
import argparse
from pathlib import Path
from termcolor import colored

# Configuración de rutas
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS_DIR = PROJECT_ROOT / 'tests'
RESULTS_DIR = PROJECT_ROOT / 'tests' / 'results'
REPORTS_DIR = PROJECT_ROOT / 'tests' / 'reports'

# Asegurar que los directorios existan
RESULTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Configuración de pruebas
TEST_TYPES = {
    'visual': {
        'name': 'Regresión Visual',
        'command': 'npx playwright test tests/visual-regression',
        'description': 'Pruebas de regresión visual para verificar que los cambios no afecten el diseño'
    },
    'responsive': {
        'name': 'Diseño Responsive',
        'command': 'npx playwright test tests/responsive-design',
        'description': 'Pruebas de diseño responsive para móvil/tablet/desktop'
    },
    'accessibility': {
        'name': 'Accesibilidad',
        'command': 'npx playwright test tests/accessibility',
        'description': 'Pruebas de accesibilidad usando axe-core'
    },
    'components': {
        'name': 'Componentes JavaScript',
        'command': 'npx playwright test tests/js-components',
        'description': 'Pruebas de componentes JavaScript'
    },
    'css': {
        'name': 'Validación CSS',
        'command': 'npx stylelint "**/*.css"',
        'description': 'Validación automática de CSS y detección de estilos no utilizados'
    },
    'all': {
        'name': 'Todas las pruebas',
        'command': None,  # Se ejecutarán todas las pruebas individualmente
        'description': 'Ejecutar todas las pruebas de diseño'
    }
}


def print_header(text):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 80)
    print(colored(f" {text} ", 'white', 'on_blue', attrs=['bold']))
    print("=" * 80)


def print_section(text):
    """Imprime una sección formateada"""
    print("\n" + "-" * 60)
    print(colored(f" {text} ", 'blue', attrs=['bold']))
    print("-" * 60)


def run_test(test_type, verbose=False):
    """Ejecuta un tipo específico de prueba"""
    if test_type not in TEST_TYPES:
        print(colored(f"Error: Tipo de prueba '{test_type}' no reconocido", 'red'))
        return False

    test_info = TEST_TYPES[test_type]
    
    if test_type == 'all':
        results = {}
        for t_type, t_info in TEST_TYPES.items():
            if t_type != 'all':
                print_section(f"Ejecutando pruebas de {t_info['name']}")
                success = run_test(t_type, verbose)
                results[t_type] = success
        return all(results.values())
    
    print_section(f"Ejecutando pruebas de {test_info['name']}")
    print(f"Descripción: {test_info['description']}")
    
    # Crear el comando con opciones adicionales
    command = test_info['command']
    if verbose:
        if 'playwright' in command:
            command += ' --debug'
        elif 'stylelint' in command:
            command += ' --verbose'
    
    # Ejecutar el comando
    print(colored(f"Comando: {command}", 'cyan'))
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        # Guardar la salida en un archivo de resultados
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = RESULTS_DIR / f"{test_type}_{timestamp}.txt"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"Comando: {command}\n")
            f.write(f"Código de salida: {result.returncode}\n")
            f.write("\nSTDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)
        
        # Mostrar la salida si es verbose
        if verbose:
            print("\nSalida:")
            print(result.stdout)
            if result.stderr:
                print(colored("Errores:", 'red'))
                print(result.stderr)
        
        # Verificar si la prueba fue exitosa
        success = result.returncode == 0
        status = colored("ÉXITO", 'green') if success else colored("FALLO", 'red')
        print(f"Estado: {status}")
        print(f"Resultados guardados en: {result_file}")
        
        return success
    
    except Exception as e:
        print(colored(f"Error al ejecutar la prueba: {str(e)}", 'red'))
        return False


def generate_report(test_results):
    """Genera un informe HTML con los resultados de las pruebas"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"design_test_report_{timestamp}.html"
    
    # Crear el contenido del informe
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Informe de Pruebas de Diseño - EcoPuntos</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .test-section {{ margin-bottom: 30px; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }}
            .test-header {{ padding: 10px 15px; background-color: #e9ecef; font-weight: bold; display: flex; justify-content: space-between; }}
            .test-details {{ padding: 15px; }}
            .success {{ color: #28a745; }}
            .failure {{ color: #dc3545; }}
            .timestamp {{ color: #6c757d; font-size: 0.9em; text-align: center; margin-top: 30px; }}
            .progress-bar {{ height: 20px; background-color: #e9ecef; border-radius: 5px; margin-bottom: 20px; overflow: hidden; }}
            .progress {{ height: 100%; background-color: #28a745; text-align: center; line-height: 20px; color: white; }}
        </style>
    </head>
    <body>
        <h1>Informe de Pruebas de Diseño - EcoPuntos</h1>
        <div class="timestamp">Generado el {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
        
        <div class="summary">
            <h2>Resumen</h2>
    """
    
    # Calcular estadísticas
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result['success'])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    html_content += f"""
            <p>Total de pruebas: <strong>{total_tests}</strong></p>
            <p>Pruebas exitosas: <strong class="success">{passed_tests}</strong></p>
            <p>Pruebas fallidas: <strong class="failure">{failed_tests}</strong></p>
            <div class="progress-bar">
                <div class="progress" style="width: {success_rate}%">{success_rate:.1f}%</div>
            </div>
        </div>
    """
    
    # Detalles de cada prueba
    html_content += "<h2>Detalles de las Pruebas</h2>"
    
    for test_type, result in test_results.items():
        test_info = TEST_TYPES[test_type]
        status_class = "success" if result['success'] else "failure"
        status_text = "ÉXITO" if result['success'] else "FALLO"
        
        html_content += f"""
        <div class="test-section">
            <div class="test-header">
                <span>{test_info['name']}</span>
                <span class="{status_class}">{status_text}</span>
            </div>
            <div class="test-details">
                <p><strong>Descripción:</strong> {test_info['description']}</p>
                <p><strong>Comando:</strong> <code>{test_info['command']}</code></p>
                <p><strong>Archivo de resultados:</strong> {result['result_file']}</p>
            </div>
        </div>
        """
    
    # Cerrar el HTML
    html_content += """
    </body>
    </html>
    """
    
    # Escribir el informe
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print_section("Informe generado")
    print(f"Informe HTML guardado en: {report_file}")
    
    return report_file


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Ejecutar pruebas de diseño para EcoPuntos')
    parser.add_argument('test_type', nargs='?', default='all', choices=list(TEST_TYPES.keys()),
                        help='Tipo de prueba a ejecutar (por defecto: all)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mostrar salida detallada')
    parser.add_argument('-r', '--report', action='store_true', help='Generar informe HTML')
    
    args = parser.parse_args()
    
    print_header("EJECUCIÓN DE PRUEBAS DE DISEÑO - ECOPUNTOS")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Directorio del proyecto: {PROJECT_ROOT}")
    
    # Ejecutar las pruebas
    if args.test_type == 'all':
        test_results = {}
        for test_type in TEST_TYPES:
            if test_type != 'all':
                test_results[test_type] = {
                    'success': run_test(test_type, args.verbose),
                    'result_file': str(RESULTS_DIR / f"{test_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                }
    else:
        test_results = {
            args.test_type: {
                'success': run_test(args.test_type, args.verbose),
                'result_file': str(RESULTS_DIR / f"{args.test_type}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            }
        }
    
    # Generar informe si se solicita
    if args.report:
        report_file = generate_report(test_results)
        print(f"Puede abrir el informe en su navegador: file://{report_file}")
    
    # Determinar el código de salida
    success = all(result['success'] for result in test_results.values())
    
    print_header("RESUMEN DE RESULTADOS")
    for test_type, result in test_results.items():
        status = colored("ÉXITO", 'green') if result['success'] else colored("FALLO", 'red')
        print(f"{TEST_TYPES[test_type]['name']}: {status}")
    
    overall_status = colored("TODAS LAS PRUEBAS EXITOSAS", 'green') if success else colored("ALGUNAS PRUEBAS FALLARON", 'red')
    print(f"\nEstado general: {overall_status}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())