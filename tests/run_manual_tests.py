#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para ejecutar y registrar casos de prueba manuales

Este script permite al tester ejecutar casos de prueba manuales definidos en el archivo
de casos de prueba, registrar los resultados y generar informes.
"""

import os
import sys
import csv
import json
import datetime
import argparse
from pathlib import Path
from termcolor import colored
import pandas as pd
import re

# Configuración de rutas
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCS_DIR = PROJECT_ROOT / 'docs'
TESTS_DIR = PROJECT_ROOT / 'tests'
RESULTS_DIR = PROJECT_ROOT / 'tests' / 'results'
REPORTS_DIR = PROJECT_ROOT / 'tests' / 'reports'

# Asegurar que los directorios existan
RESULTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Archivos de casos de prueba
CASOS_PRUEBA_MD = DOCS_DIR / 'casos_de_prueba.md'
CASOS_PRUEBA_CSV = DOCS_DIR / 'plantilla_casos_prueba.csv'
CASOS_PRUEBA_EXCEL = DOCS_DIR / 'Plantilla de Casos de Prueba.xlsx'

# Estados de prueba
TEST_STATES = {
    'P': {'name': 'Pasado', 'color': 'green'},
    'F': {'name': 'Fallido', 'color': 'red'},
    'B': {'name': 'Bloqueado', 'color': 'yellow'},
    'N': {'name': 'No Aplicable', 'color': 'blue'},
    'S': {'name': 'Omitido', 'color': 'cyan'}
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


def load_test_cases_from_csv():
    """Carga los casos de prueba desde el archivo CSV"""
    if not CASOS_PRUEBA_CSV.exists():
        print(colored(f"Error: No se encontró el archivo CSV en {CASOS_PRUEBA_CSV}", 'red'))
        return []
    
    try:
        df = pd.read_csv(CASOS_PRUEBA_CSV, encoding='utf-8')
        test_cases = df.to_dict('records')
        print(f"Se cargaron {len(test_cases)} casos de prueba desde {CASOS_PRUEBA_CSV}")
        return test_cases
    except Exception as e:
        print(colored(f"Error al cargar el archivo CSV: {str(e)}", 'red'))
        return []


def load_test_cases_from_excel():
    """Carga los casos de prueba desde el archivo Excel"""
    if not CASOS_PRUEBA_EXCEL.exists():
        print(colored(f"Error: No se encontró el archivo Excel en {CASOS_PRUEBA_EXCEL}", 'red'))
        return []
    
    try:
        df = pd.read_excel(CASOS_PRUEBA_EXCEL, sheet_name='Plantilla de Casos de Prueba')
        test_cases = df.to_dict('records')
        print(f"Se cargaron {len(test_cases)} casos de prueba desde {CASOS_PRUEBA_EXCEL}")
        return test_cases
    except Exception as e:
        print(colored(f"Error al cargar el archivo Excel: {str(e)}", 'red'))
        return []


def load_test_cases_from_markdown():
    """Carga los casos de prueba desde el archivo Markdown"""
    if not CASOS_PRUEBA_MD.exists():
        print(colored(f"Error: No se encontró el archivo Markdown en {CASOS_PRUEBA_MD}", 'red'))
        return []
    
    try:
        with open(CASOS_PRUEBA_MD, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer casos de prueba usando expresiones regulares
        # Patrón para encontrar casos de prueba en formato markdown
        pattern = r'### Caso de Prueba: ([\w-]+)\s*\n\s*\*\*Descripción\*\*: (.+?)\s*\n\s*\*\*Módulo\*\*: (.+?)\s*\n\s*\*\*Prioridad\*\*: (.+?)\s*\n\s*\*\*Precondiciones\*\*:\s*\n(.+?)\s*\n\s*\*\*Pasos\*\*:\s*\n(.+?)\s*\n\s*\*\*Resultado Esperado\*\*:\s*\n(.+?)\s*\n\s*\*\*Datos de Prueba\*\*:\s*\n(.+?)(?=\n\s*###|$)'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        test_cases = []
        for match in matches:
            test_case = {
                'id': match.group(1).strip(),
                'descripcion': match.group(2).strip(),
                'modulo': match.group(3).strip(),
                'prioridad': match.group(4).strip(),
                'precondiciones': match.group(5).strip(),
                'pasos': match.group(6).strip(),
                'resultado_esperado': match.group(7).strip(),
                'datos_prueba': match.group(8).strip()
            }
            test_cases.append(test_case)
        
        print(f"Se cargaron {len(test_cases)} casos de prueba desde {CASOS_PRUEBA_MD}")
        return test_cases
    
    except Exception as e:
        print(colored(f"Error al cargar el archivo Markdown: {str(e)}", 'red'))
        return []


def filter_test_cases(test_cases, module=None, priority=None):
    """Filtra los casos de prueba por módulo y/o prioridad"""
    filtered_cases = test_cases
    
    if module:
        filtered_cases = [tc for tc in filtered_cases if module.lower() in str(tc.get('modulo', '')).lower() or 
                          module.lower() in str(tc.get('Área Funcional / Sub-módulo', '')).lower()]
    
    if priority:
        filtered_cases = [tc for tc in filtered_cases if priority.lower() in str(tc.get('prioridad', '')).lower() or 
                          priority.lower() in str(tc.get('Prioridad', '')).lower()]
    
    return filtered_cases


def run_manual_test(test_case):
    """Ejecuta un caso de prueba manual y registra el resultado"""
    # Determinar qué campos usar según el formato del caso de prueba
    id_field = test_case.get('id') or test_case.get('Caso de Prueba')
    desc_field = test_case.get('descripcion') or test_case.get('Descripción')
    module_field = test_case.get('modulo') or test_case.get('Área Funcional / Sub-módulo')
    steps_field = test_case.get('pasos') or test_case.get('Procedimiento específico')
    expected_field = test_case.get('resultado_esperado') or test_case.get('Resultado Esperado')
    precond_field = test_case.get('precondiciones') or test_case.get('Precondiciones / Configuración')
    data_field = test_case.get('datos_prueba') or test_case.get('Datos Necesarios de Entrada')
    
    print_header(f"CASO DE PRUEBA: {id_field}")
    print(f"Descripción: {desc_field}")
    print(f"Módulo: {module_field}")
    
    print_section("Precondiciones")
    print(precond_field)
    
    print_section("Datos de Prueba")
    print(data_field)
    
    print_section("Pasos")
    print(steps_field)
    
    print_section("Resultado Esperado")
    print(expected_field)
    
    # Solicitar resultado al tester
    print_section("Resultado de la Prueba")
    print("Opciones de estado:")
    for key, state in TEST_STATES.items():
        print(f"  {key} - {colored(state['name'], state['color'])}")
    
    while True:
        state = input("\nIngrese el estado de la prueba (P/F/B/N/S): ").upper()
        if state in TEST_STATES:
            break
        print(colored("Estado no válido. Intente de nuevo.", 'red'))
    
    result = input("Ingrese el resultado obtenido: ")
    observations = input("Ingrese observaciones (opcional): ")
    
    # Registrar el resultado
    test_result = {
        'id': id_field,
        'descripcion': desc_field,
        'modulo': module_field,
        'estado': TEST_STATES[state]['name'],
        'resultado': result,
        'observaciones': observations,
        'fecha': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'tester': os.environ.get('USERNAME', 'unknown')
    }
    
    return test_result


def save_results(results):
    """Guarda los resultados en un archivo CSV"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = RESULTS_DIR / f"manual_test_results_{timestamp}.csv"
    
    try:
        with open(result_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        
        print_section("Resultados guardados")
        print(f"Resultados guardados en: {result_file}")
        return result_file
    
    except Exception as e:
        print(colored(f"Error al guardar los resultados: {str(e)}", 'red'))
        return None


def generate_report(results):
    """Genera un informe HTML con los resultados de las pruebas"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"manual_test_report_{timestamp}.html"
    
    # Calcular estadísticas
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['estado'] == 'Pasado')
    failed_tests = sum(1 for r in results if r['estado'] == 'Fallido')
    blocked_tests = sum(1 for r in results if r['estado'] == 'Bloqueado')
    na_tests = sum(1 for r in results if r['estado'] == 'No Aplicable')
    skipped_tests = sum(1 for r in results if r['estado'] == 'Omitido')
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # Agrupar por módulo
    modules = {}
    for result in results:
        module = result['modulo']
        if module not in modules:
            modules[module] = {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'blocked': 0,
                'na': 0,
                'skipped': 0
            }
        
        modules[module]['total'] += 1
        
        if result['estado'] == 'Pasado':
            modules[module]['passed'] += 1
        elif result['estado'] == 'Fallido':
            modules[module]['failed'] += 1
        elif result['estado'] == 'Bloqueado':
            modules[module]['blocked'] += 1
        elif result['estado'] == 'No Aplicable':
            modules[module]['na'] += 1
        elif result['estado'] == 'Omitido':
            modules[module]['skipped'] += 1
    
    # Crear el contenido del informe
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Informe de Pruebas Manuales - EcoPuntos</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            h1 {{ text-align: center; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .module-section {{ margin-bottom: 30px; }}
            .test-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .test-table th, .test-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .test-table th {{ background-color: #e9ecef; }}
            .test-table tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .status-passed {{ color: #28a745; }}
            .status-failed {{ color: #dc3545; }}
            .status-blocked {{ color: #ffc107; }}
            .status-na {{ color: #17a2b8; }}
            .status-skipped {{ color: #6c757d; }}
            .timestamp {{ color: #6c757d; font-size: 0.9em; text-align: center; margin-top: 30px; }}
            .progress-bar {{ height: 20px; background-color: #e9ecef; border-radius: 5px; margin-bottom: 20px; overflow: hidden; }}
            .progress {{ height: 100%; background-color: #28a745; text-align: center; line-height: 20px; color: white; }}
            .chart-container {{ display: flex; justify-content: space-around; margin: 20px 0; }}
            .pie-chart {{ width: 200px; height: 200px; position: relative; }}
            .module-chart {{ width: 100%; height: 300px; margin-top: 20px; }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>Informe de Pruebas Manuales - EcoPuntos</h1>
        <div class="timestamp">Generado el {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
        
        <div class="summary">
            <h2>Resumen</h2>
            <p>Total de pruebas: <strong>{total_tests}</strong></p>
            <p>Pruebas exitosas: <strong class="status-passed">{passed_tests}</strong></p>
            <p>Pruebas fallidas: <strong class="status-failed">{failed_tests}</strong></p>
            <p>Pruebas bloqueadas: <strong class="status-blocked">{blocked_tests}</strong></p>
            <p>Pruebas no aplicables: <strong class="status-na">{na_tests}</strong></p>
            <p>Pruebas omitidas: <strong class="status-skipped">{skipped_tests}</strong></p>
            <div class="progress-bar">
                <div class="progress" style="width: {success_rate}%">{success_rate:.1f}%</div>
            </div>
            
            <div class="chart-container">
                <div class="pie-chart">
                    <canvas id="statusChart"></canvas>
                </div>
                <div class="pie-chart">
                    <canvas id="moduleChart"></canvas>
                </div>
            </div>
        </div>
        
        <h2>Resultados por Módulo</h2>
        <div class="module-chart">
            <canvas id="moduleBarChart"></canvas>
        </div>
    """
    
    # Agregar secciones por módulo
    for module, stats in modules.items():
        module_success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
        
        html_content += f"""
        <div class="module-section">
            <h3>{module}</h3>
            <p>Total de pruebas: <strong>{stats['total']}</strong></p>
            <p>Tasa de éxito: <strong class="status-passed">{module_success_rate:.1f}%</strong></p>
            
            <table class="test-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Descripción</th>
                        <th>Estado</th>
                        <th>Resultado</th>
                        <th>Observaciones</th>
                        <th>Fecha</th>
                        <th>Tester</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Filtrar resultados por módulo
        module_results = [r for r in results if r['modulo'] == module]
        
        for result in module_results:
            status_class = "status-passed"
            if result['estado'] == 'Fallido':
                status_class = "status-failed"
            elif result['estado'] == 'Bloqueado':
                status_class = "status-blocked"
            elif result['estado'] == 'No Aplicable':
                status_class = "status-na"
            elif result['estado'] == 'Omitido':
                status_class = "status-skipped"
            
            html_content += f"""
                    <tr>
                        <td>{result['id']}</td>
                        <td>{result['descripcion']}</td>
                        <td class="{status_class}">{result['estado']}</td>
                        <td>{result['resultado']}</td>
                        <td>{result['observaciones']}</td>
                        <td>{result['fecha']}</td>
                        <td>{result['tester']}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </div>
        """
    
    # Agregar scripts para gráficos
    html_content += f"""
        <script>
            // Gráfico de estado general
            const statusCtx = document.getElementById('statusChart').getContext('2d');
            new Chart(statusCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Pasado', 'Fallido', 'Bloqueado', 'No Aplicable', 'Omitido'],
                    datasets: [{{
                        data: [{passed_tests}, {failed_tests}, {blocked_tests}, {na_tests}, {skipped_tests}],
                        backgroundColor: ['#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6c757d']
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                        }},
                        title: {{
                            display: true,
                            text: 'Distribución por Estado'
                        }}
                    }}
                }}
            }});
            
            // Gráfico por módulo
            const moduleCtx = document.getElementById('moduleChart').getContext('2d');
            new Chart(moduleCtx, {{
                type: 'pie',
                data: {{
                    labels: [{', '.join([f"'{m}'" for m in modules.keys()])}],
                    datasets: [{{
                        data: [{', '.join([str(m['total']) for m in modules.values()])}],
                        backgroundColor: [
                            '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
                            '#5a5c69', '#858796', '#f8f9fc', '#d1d3e2', '#b7b9cc'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                        }},
                        title: {{
                            display: true,
                            text: 'Distribución por Módulo'
                        }}
                    }}
                }}
            }});
            
            // Gráfico de barras por módulo
            const moduleBarCtx = document.getElementById('moduleBarChart').getContext('2d');
            new Chart(moduleBarCtx, {{
                type: 'bar',
                data: {{
                    labels: [{', '.join([f"'{m}'" for m in modules.keys()])}],
                    datasets: [
                        {{
                            label: 'Pasado',
                            data: [{', '.join([str(m['passed']) for m in modules.values()])}],
                            backgroundColor: '#28a745'
                        }},
                        {{
                            label: 'Fallido',
                            data: [{', '.join([str(m['failed']) for m in modules.values()])}],
                            backgroundColor: '#dc3545'
                        }},
                        {{
                            label: 'Bloqueado',
                            data: [{', '.join([str(m['blocked']) for m in modules.values()])}],
                            backgroundColor: '#ffc107'
                        }},
                        {{
                            label: 'No Aplicable',
                            data: [{', '.join([str(m['na']) for m in modules.values()])}],
                            backgroundColor: '#17a2b8'
                        }},
                        {{
                            label: 'Omitido',
                            data: [{', '.join([str(m['skipped']) for m in modules.values()])}],
                            backgroundColor: '#6c757d'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        x: {{
                            stacked: true,
                        }},
                        y: {{
                            stacked: true
                        }}
                    }},
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Resultados por Módulo'
                        }}
                    }}
                }}
            }});
        </script>
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
    parser = argparse.ArgumentParser(description='Ejecutar pruebas manuales para EcoPuntos')
    parser.add_argument('-s', '--source', choices=['csv', 'excel', 'markdown'], default='markdown',
                        help='Fuente de los casos de prueba (por defecto: markdown)')
    parser.add_argument('-m', '--module', help='Filtrar por módulo')
    parser.add_argument('-p', '--priority', help='Filtrar por prioridad')
    parser.add_argument('-r', '--report', action='store_true', help='Generar informe HTML')
    
    args = parser.parse_args()
    
    print_header("EJECUCIÓN DE PRUEBAS MANUALES - ECOPUNTOS")
    print(f"Fecha y hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Directorio del proyecto: {PROJECT_ROOT}")
    
    # Cargar casos de prueba
    if args.source == 'csv':
        test_cases = load_test_cases_from_csv()
    elif args.source == 'excel':
        test_cases = load_test_cases_from_excel()
    else:  # markdown
        test_cases = load_test_cases_from_markdown()
    
    if not test_cases:
        print(colored("No se encontraron casos de prueba. Saliendo.", 'red'))
        return 1
    
    # Filtrar casos de prueba
    filtered_cases = filter_test_cases(test_cases, args.module, args.priority)
    
    if not filtered_cases:
        print(colored("No se encontraron casos de prueba que coincidan con los filtros. Saliendo.", 'red'))
        return 1
    
    print(f"Se ejecutarán {len(filtered_cases)} casos de prueba")
    
    # Ejecutar casos de prueba
    results = []
    for i, test_case in enumerate(filtered_cases, 1):
        print(f"\nCaso de prueba {i} de {len(filtered_cases)}")
        result = run_manual_test(test_case)
        results.append(result)
        
        # Preguntar si desea continuar después de cada caso
        if i < len(filtered_cases):
            continue_testing = input("\n¿Continuar con el siguiente caso? (s/n): ").lower()
            if continue_testing != 's':
                print("Ejecución de pruebas interrumpida por el usuario.")
                break
    
    # Guardar resultados
    if results:
        result_file = save_results(results)
        
        # Generar informe si se solicita
        if args.report and result_file:
            report_file = generate_report(results)
            print(f"Puede abrir el informe en su navegador: file://{report_file}")
    
    print_header("RESUMEN DE RESULTADOS")
    print(f"Total de casos ejecutados: {len(results)}")
    print(f"Casos exitosos: {sum(1 for r in results if r['estado'] == 'Pasado')}")
    print(f"Casos fallidos: {sum(1 for r in results if r['estado'] == 'Fallido')}")
    print(f"Casos bloqueados: {sum(1 for r in results if r['estado'] == 'Bloqueado')}")
    print(f"Casos no aplicables: {sum(1 for r in results if r['estado'] == 'No Aplicable')}")
    print(f"Casos omitidos: {sum(1 for r in results if r['estado'] == 'Omitido')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())