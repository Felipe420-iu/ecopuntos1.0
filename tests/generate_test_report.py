#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para generar un informe consolidado de todas las pruebas

Este script recopila los resultados de todas las pruebas (manuales, automatizadas y de diseño)
y genera un informe consolidado con estadísticas y gráficos.
"""

import os
import sys
import json
import glob
import csv
import datetime
import argparse
from pathlib import Path
import pandas as pd

# Configuración de rutas
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TESTS_DIR = PROJECT_ROOT / 'tests'
RESULTS_DIR = PROJECT_ROOT / 'tests' / 'results'
REPORTS_DIR = PROJECT_ROOT / 'tests' / 'reports'

# Asegurar que los directorios existan
RESULTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Tipos de pruebas
TEST_TYPES = {
    'manual': 'Pruebas Manuales',
    'automated': 'Pruebas Automatizadas',
    'design': 'Pruebas de Diseño',
    'api': 'Pruebas de API'
}

# Módulos del proyecto
PROJECT_MODULES = [
    'Usuarios',
    'Puntos y Recompensas',
    'Rutas y Materiales',
    'Notificaciones',
    'Chatbot IA',
    'Estadísticas',
    'Configuración',
    'Interfaz de Usuario',
    'Seguridad y Sesiones',
    'API REST'
]


def collect_manual_test_results():
    """Recopila los resultados de las pruebas manuales"""
    results = []
    
    # Buscar archivos CSV de resultados de pruebas manuales
    csv_files = list(RESULTS_DIR.glob('manual_test_results_*.csv'))
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            file_results = df.to_dict('records')
            
            # Agregar metadatos
            for result in file_results:
                result['test_type'] = 'manual'
                result['source_file'] = str(csv_file)
            
            results.extend(file_results)
        except Exception as e:
            print(f"Error al leer {csv_file}: {str(e)}")
    
    return results


def collect_automated_test_results():
    """Recopila los resultados de las pruebas automatizadas"""
    results = []
    
    # Buscar archivos de resultados de pruebas automatizadas
    # Asumimos que los resultados están en formato de texto
    txt_files = list(RESULTS_DIR.glob('test_modules_*.txt')) + list(RESULTS_DIR.glob('automated_*.txt'))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer información básica del archivo
            # Esto es un ejemplo simple, se puede mejorar con expresiones regulares
            # para extraer información más detallada
            passed = content.count('PASS') or content.count('OK')
            failed = content.count('FAIL') or content.count('ERROR')
            skipped = content.count('SKIP')
            
            # Crear un resultado para este archivo
            result = {
                'test_type': 'automated',
                'source_file': str(txt_file),
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'total': passed + failed + skipped,
                'fecha': datetime.datetime.fromtimestamp(txt_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            results.append(result)
        except Exception as e:
            print(f"Error al leer {txt_file}: {str(e)}")
    
    return results


def collect_design_test_results():
    """Recopila los resultados de las pruebas de diseño"""
    results = []
    
    # Buscar archivos de resultados de pruebas de diseño
    txt_files = list(RESULTS_DIR.glob('visual_*.txt')) + \
               list(RESULTS_DIR.glob('responsive_*.txt')) + \
               list(RESULTS_DIR.glob('accessibility_*.txt')) + \
               list(RESULTS_DIR.glob('components_*.txt')) + \
               list(RESULTS_DIR.glob('css_*.txt'))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determinar el tipo de prueba de diseño
            design_type = 'unknown'
            if 'visual' in txt_file.name:
                design_type = 'visual'
            elif 'responsive' in txt_file.name:
                design_type = 'responsive'
            elif 'accessibility' in txt_file.name:
                design_type = 'accessibility'
            elif 'components' in txt_file.name:
                design_type = 'components'
            elif 'css' in txt_file.name:
                design_type = 'css'
            
            # Extraer información básica del archivo
            success = 'ÉXITO' in content or 'SUCCESS' in content
            
            # Crear un resultado para este archivo
            result = {
                'test_type': 'design',
                'design_type': design_type,
                'source_file': str(txt_file),
                'success': success,
                'fecha': datetime.datetime.fromtimestamp(txt_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            results.append(result)
        except Exception as e:
            print(f"Error al leer {txt_file}: {str(e)}")
    
    return results


def collect_api_test_results():
    """Recopila los resultados de las pruebas de API"""
    results = []
    
    # Buscar archivos de resultados de pruebas de API
    txt_files = list(RESULTS_DIR.glob('api_*.txt'))
    
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraer información básica del archivo
            passed = content.count('PASS') or content.count('OK')
            failed = content.count('FAIL') or content.count('ERROR')
            
            # Crear un resultado para este archivo
            result = {
                'test_type': 'api',
                'source_file': str(txt_file),
                'passed': passed,
                'failed': failed,
                'total': passed + failed,
                'fecha': datetime.datetime.fromtimestamp(txt_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
            
            results.append(result)
        except Exception as e:
            print(f"Error al leer {txt_file}: {str(e)}")
    
    return results


def generate_consolidated_report(manual_results, automated_results, design_results, api_results):
    """Genera un informe consolidado con todos los resultados"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = REPORTS_DIR / f"consolidated_test_report_{timestamp}.html"
    
    # Calcular estadísticas generales
    total_manual = len(manual_results)
    manual_passed = sum(1 for r in manual_results if r.get('estado') == 'Pasado')
    manual_failed = sum(1 for r in manual_results if r.get('estado') == 'Fallido')
    manual_other = total_manual - manual_passed - manual_failed
    
    total_automated = sum(r.get('total', 0) for r in automated_results)
    automated_passed = sum(r.get('passed', 0) for r in automated_results)
    automated_failed = sum(r.get('failed', 0) for r in automated_results)
    automated_skipped = sum(r.get('skipped', 0) for r in automated_results)
    
    total_design = len(design_results)
    design_passed = sum(1 for r in design_results if r.get('success', False))
    design_failed = total_design - design_passed
    
    total_api = sum(r.get('total', 0) for r in api_results)
    api_passed = sum(r.get('passed', 0) for r in api_results)
    api_failed = sum(r.get('failed', 0) for r in api_results)
    
    # Calcular totales generales
    total_tests = total_manual + total_automated + total_design + total_api
    total_passed = manual_passed + automated_passed + design_passed + api_passed
    total_failed = manual_failed + automated_failed + design_failed + api_failed
    total_other = manual_other + automated_skipped
    
    success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
    
    # Crear el contenido del informe
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Informe Consolidado de Pruebas - EcoPuntos</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            h1 {{ text-align: center; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .test-section {{ margin-bottom: 30px; border: 1px solid #ddd; border-radius: 5px; overflow: hidden; }}
            .test-header {{ padding: 10px 15px; background-color: #e9ecef; font-weight: bold; }}
            .test-content {{ padding: 15px; }}
            .status-passed {{ color: #28a745; }}
            .status-failed {{ color: #dc3545; }}
            .status-other {{ color: #6c757d; }}
            .timestamp {{ color: #6c757d; font-size: 0.9em; text-align: center; margin-top: 30px; }}
            .progress-bar {{ height: 20px; background-color: #e9ecef; border-radius: 5px; margin-bottom: 20px; overflow: hidden; }}
            .progress {{ height: 100%; background-color: #28a745; text-align: center; line-height: 20px; color: white; }}
            .chart-container {{ display: flex; flex-wrap: wrap; justify-content: space-around; margin: 20px 0; }}
            .chart-item {{ width: 45%; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #e9ecef; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            @media (max-width: 768px) {{ .chart-item {{ width: 100%; }} }}
        </style>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>Informe Consolidado de Pruebas - EcoPuntos</h1>
        <div class="timestamp">Generado el {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</div>
        
        <div class="summary">
            <h2>Resumen General</h2>
            <p>Total de pruebas: <strong>{total_tests}</strong></p>
            <p>Pruebas exitosas: <strong class="status-passed">{total_passed}</strong></p>
            <p>Pruebas fallidas: <strong class="status-failed">{total_failed}</strong></p>
            <p>Otras (omitidas/bloqueadas): <strong class="status-other">{total_other}</strong></p>
            <div class="progress-bar">
                <div class="progress" style="width: {success_rate}%">{success_rate:.1f}%</div>
            </div>
            
            <div class="chart-container">
                <div class="chart-item">
                    <canvas id="overallStatusChart"></canvas>
                </div>
                <div class="chart-item">
                    <canvas id="testTypeChart"></canvas>
                </div>
            </div>
        </div>
    """
    
    # Sección de pruebas manuales
    html_content += f"""
        <div class="test-section">
            <div class="test-header">Pruebas Manuales</div>
            <div class="test-content">
                <p>Total de pruebas: <strong>{total_manual}</strong></p>
                <p>Pruebas exitosas: <strong class="status-passed">{manual_passed}</strong></p>
                <p>Pruebas fallidas: <strong class="status-failed">{manual_failed}</strong></p>
                <p>Otras (bloqueadas/omitidas/NA): <strong class="status-other">{manual_other}</strong></p>
                
                <div class="chart-container">
                    <div class="chart-item">
                        <canvas id="manualStatusChart"></canvas>
                    </div>
                    <div class="chart-item">
                        <canvas id="manualModuleChart"></canvas>
                    </div>
                </div>
    """
    
    # Tabla de pruebas manuales fallidas
    failed_manual = [r for r in manual_results if r.get('estado') == 'Fallido']
    if failed_manual:
        html_content += """
                <h3>Pruebas Manuales Fallidas</h3>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Descripción</th>
                            <th>Módulo</th>
                            <th>Resultado</th>
                            <th>Observaciones</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for result in failed_manual:
            html_content += f"""
                        <tr>
                            <td>{result.get('id', '')}</td>
                            <td>{result.get('descripcion', '')}</td>
                            <td>{result.get('modulo', '')}</td>
                            <td>{result.get('resultado', '')}</td>
                            <td>{result.get('observaciones', '')}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
        """
    
    html_content += """
            </div>
        </div>
    """
    
    # Sección de pruebas automatizadas
    html_content += f"""
        <div class="test-section">
            <div class="test-header">Pruebas Automatizadas</div>
            <div class="test-content">
                <p>Total de pruebas: <strong>{total_automated}</strong></p>
                <p>Pruebas exitosas: <strong class="status-passed">{automated_passed}</strong></p>
                <p>Pruebas fallidas: <strong class="status-failed">{automated_failed}</strong></p>
                <p>Pruebas omitidas: <strong class="status-other">{automated_skipped}</strong></p>
                
                <div class="chart-container">
                    <div class="chart-item">
                        <canvas id="automatedStatusChart"></canvas>
                    </div>
                </div>
                
                <h3>Resultados por Archivo</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Archivo</th>
                            <th>Total</th>
                            <th>Pasadas</th>
                            <th>Fallidas</th>
                            <th>Omitidas</th>
                            <th>Fecha</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for result in automated_results:
        file_name = os.path.basename(result.get('source_file', ''))
        html_content += f"""
                        <tr>
                            <td>{file_name}</td>
                            <td>{result.get('total', 0)}</td>
                            <td class="status-passed">{result.get('passed', 0)}</td>
                            <td class="status-failed">{result.get('failed', 0)}</td>
                            <td class="status-other">{result.get('skipped', 0)}</td>
                            <td>{result.get('fecha', '')}</td>
                        </tr>
        """
    
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    """
    
    # Sección de pruebas de diseño
    html_content += f"""
        <div class="test-section">
            <div class="test-header">Pruebas de Diseño</div>
            <div class="test-content">
                <p>Total de pruebas: <strong>{total_design}</strong></p>
                <p>Pruebas exitosas: <strong class="status-passed">{design_passed}</strong></p>
                <p>Pruebas fallidas: <strong class="status-failed">{design_failed}</strong></p>
                
                <div class="chart-container">
                    <div class="chart-item">
                        <canvas id="designStatusChart"></canvas>
                    </div>
                    <div class="chart-item">
                        <canvas id="designTypeChart"></canvas>
                    </div>
                </div>
                
                <h3>Resultados por Tipo</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Tipo</th>
                            <th>Estado</th>
                            <th>Archivo</th>
                            <th>Fecha</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    design_types = {
        'visual': 'Regresión Visual',
        'responsive': 'Diseño Responsive',
        'accessibility': 'Accesibilidad',
        'components': 'Componentes JavaScript',
        'css': 'Validación CSS',
        'unknown': 'Desconocido'
    }
    
    for result in design_results:
        file_name = os.path.basename(result.get('source_file', ''))
        design_type = result.get('design_type', 'unknown')
        status = "ÉXITO" if result.get('success', False) else "FALLO"
        status_class = "status-passed" if result.get('success', False) else "status-failed"
        
        html_content += f"""
                        <tr>
                            <td>{design_types.get(design_type, 'Desconocido')}</td>
                            <td class="{status_class}">{status}</td>
                            <td>{file_name}</td>
                            <td>{result.get('fecha', '')}</td>
                        </tr>
        """
    
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    """
    
    # Sección de pruebas de API
    html_content += f"""
        <div class="test-section">
            <div class="test-header">Pruebas de API</div>
            <div class="test-content">
                <p>Total de pruebas: <strong>{total_api}</strong></p>
                <p>Pruebas exitosas: <strong class="status-passed">{api_passed}</strong></p>
                <p>Pruebas fallidas: <strong class="status-failed">{api_failed}</strong></p>
                
                <div class="chart-container">
                    <div class="chart-item">
                        <canvas id="apiStatusChart"></canvas>
                    </div>
                </div>
                
                <h3>Resultados por Archivo</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Archivo</th>
                            <th>Total</th>
                            <th>Pasadas</th>
                            <th>Fallidas</th>
                            <th>Fecha</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for result in api_results:
        file_name = os.path.basename(result.get('source_file', ''))
        html_content += f"""
                        <tr>
                            <td>{file_name}</td>
                            <td>{result.get('total', 0)}</td>
                            <td class="status-passed">{result.get('passed', 0)}</td>
                            <td class="status-failed">{result.get('failed', 0)}</td>
                            <td>{result.get('fecha', '')}</td>
                        </tr>
        """
    
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    """
    
    # Calcular datos para gráficos
    # Contar pruebas manuales por módulo
    manual_by_module = {}
    for module in PROJECT_MODULES:
        manual_by_module[module] = sum(1 for r in manual_results if module.lower() in str(r.get('modulo', '')).lower())
    
    # Contar pruebas de diseño por tipo
    design_by_type = {}
    for design_type in design_types.keys():
        if design_type != 'unknown':
            design_by_type[design_types[design_type]] = sum(1 for r in design_results if r.get('design_type') == design_type)
    
    # Agregar scripts para gráficos
    html_content += f"""
        <script>
            // Gráfico de estado general
            const overallStatusCtx = document.getElementById('overallStatusChart').getContext('2d');
            new Chart(overallStatusCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Exitosas', 'Fallidas', 'Otras'],
                    datasets: [{{
                        data: [{total_passed}, {total_failed}, {total_other}],
                        backgroundColor: ['#28a745', '#dc3545', '#6c757d']
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
                            text: 'Estado General de Pruebas'
                        }}
                    }}
                }}
            }});
            
            // Gráfico por tipo de prueba
            const testTypeCtx = document.getElementById('testTypeChart').getContext('2d');
            new Chart(testTypeCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Manuales', 'Automatizadas', 'Diseño', 'API'],
                    datasets: [{{
                        data: [{total_manual}, {total_automated}, {total_design}, {total_api}],
                        backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e']
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
                            text: 'Distribución por Tipo de Prueba'
                        }}
                    }}
                }}
            }});
            
            // Gráfico de pruebas manuales
            const manualStatusCtx = document.getElementById('manualStatusChart').getContext('2d');
            new Chart(manualStatusCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Exitosas', 'Fallidas', 'Otras'],
                    datasets: [{{
                        data: [{manual_passed}, {manual_failed}, {manual_other}],
                        backgroundColor: ['#28a745', '#dc3545', '#6c757d']
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
                            text: 'Estado de Pruebas Manuales'
                        }}
                    }}
                }}
            }});
            
            // Gráfico de pruebas manuales por módulo
            const manualModuleCtx = document.getElementById('manualModuleChart').getContext('2d');
            new Chart(manualModuleCtx, {{
                type: 'bar',
                data: {{
                    labels: [{', '.join([f"'{m}'" for m in manual_by_module.keys()])}],
                    datasets: [{{
                        label: 'Pruebas',
                        data: [{', '.join([str(c) for c in manual_by_module.values()])}],
                        backgroundColor: '#4e73df'
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        title: {{
                            display: true,
                            text: 'Pruebas Manuales por Módulo'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true
                        }}
                    }}
                }}
            }});
            
            // Gráfico de pruebas automatizadas
            const automatedStatusCtx = document.getElementById('automatedStatusChart').getContext('2d');
            new Chart(automatedStatusCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Exitosas', 'Fallidas', 'Omitidas'],
                    datasets: [{{
                        data: [{automated_passed}, {automated_failed}, {automated_skipped}],
                        backgroundColor: ['#28a745', '#dc3545', '#6c757d']
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
                            text: 'Estado de Pruebas Automatizadas'
                        }}
                    }}
                }}
            }});
            
            // Gráfico de pruebas de diseño
            const designStatusCtx = document.getElementById('designStatusChart').getContext('2d');
            new Chart(designStatusCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Exitosas', 'Fallidas'],
                    datasets: [{{
                        data: [{design_passed}, {design_failed}],
                        backgroundColor: ['#28a745', '#dc3545']
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
                            text: 'Estado de Pruebas de Diseño'
                        }}
                    }}
                }}
            }});
            
            // Gráfico de pruebas de diseño por tipo
            const designTypeCtx = document.getElementById('designTypeChart').getContext('2d');
            new Chart(designTypeCtx, {{
                type: 'pie',
                data: {{
                    labels: [{', '.join([f"'{t}'" for t in design_by_type.keys()])}],
                    datasets: [{{
                        data: [{', '.join([str(c) for c in design_by_type.values()])}],
                        backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b']
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
                            text: 'Pruebas de Diseño por Tipo'
                        }}
                    }}
                }}
            }});
            
            // Gráfico de pruebas de API
            const apiStatusCtx = document.getElementById('apiStatusChart').getContext('2d');
            new Chart(apiStatusCtx, {{
                type: 'pie',
                data: {{
                    labels: ['Exitosas', 'Fallidas'],
                    datasets: [{{
                        data: [{api_passed}, {api_failed}],
                        backgroundColor: ['#28a745', '#dc3545']
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
                            text: 'Estado de Pruebas de API'
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
    
    print(f"Informe consolidado generado en: {report_file}")
    
    return report_file


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Generar informe consolidado de pruebas para EcoPuntos')
    parser.add_argument('-o', '--output', help='Ruta del archivo de salida')
    
    args = parser.parse_args()
    
    print("Recopilando resultados de pruebas...")
    
    # Recopilar resultados
    manual_results = collect_manual_test_results()
    print(f"Se encontraron {len(manual_results)} resultados de pruebas manuales")
    
    automated_results = collect_automated_test_results()
    print(f"Se encontraron {len(automated_results)} archivos de resultados de pruebas automatizadas")
    
    design_results = collect_design_test_results()
    print(f"Se encontraron {len(design_results)} archivos de resultados de pruebas de diseño")
    
    api_results = collect_api_test_results()
    print(f"Se encontraron {len(api_results)} archivos de resultados de pruebas de API")
    
    # Generar informe
    report_file = generate_consolidated_report(manual_results, automated_results, design_results, api_results)
    
    # Si se especificó una ruta de salida, copiar el informe allí
    if args.output:
        import shutil
        output_path = Path(args.output)
        shutil.copy2(report_file, output_path)
        print(f"Informe copiado a: {output_path}")
    
    print(f"Puede abrir el informe en su navegador: file://{report_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())