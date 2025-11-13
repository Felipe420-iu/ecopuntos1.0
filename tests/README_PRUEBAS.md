# Guía de Pruebas para EcoPuntos

Este documento proporciona instrucciones detalladas sobre cómo ejecutar y gestionar las pruebas del proyecto EcoPuntos.

## Contenido

1. [Estructura de Pruebas](#estructura-de-pruebas)
2. [Casos de Prueba](#casos-de-prueba)
3. [Ejecución de Pruebas](#ejecución-de-pruebas)
   - [Pruebas Manuales](#pruebas-manuales)
   - [Pruebas Automatizadas](#pruebas-automatizadas)
   - [Pruebas de Diseño](#pruebas-de-diseño)
4. [Generación de Informes](#generación-de-informes)
5. [Conversión de Formatos](#conversión-de-formatos)

## Estructura de Pruebas

El proyecto EcoPuntos utiliza una estructura organizada para las pruebas:

```
ecopuntos1.00/
├── docs/
│   ├── casos_de_prueba.md       # Documentación de casos de prueba en formato Markdown
│   ├── plantilla_casos_prueba.csv # Plantilla de casos de prueba en formato CSV
│   └── Plantilla de Casos de Prueba.xlsx # Plantilla en formato Excel
├── tests/
│   ├── run_manual_tests.py      # Script para ejecutar pruebas manuales
│   ├── run_design_tests.py      # Script para ejecutar pruebas de diseño
│   ├── test_modules.py          # Pruebas automatizadas para módulos del proyecto
│   ├── generate_test_report.py  # Generador de informes consolidados
│   ├── results/                 # Resultados de las pruebas
│   └── reports/                 # Informes generados
```

## Casos de Prueba

Los casos de prueba están documentados en tres formatos:

1. **Markdown** (`docs/casos_de_prueba.md`): Formato principal con todos los casos de prueba organizados por módulos.
2. **CSV** (`docs/plantilla_casos_prueba.csv`): Formato tabular para importar/exportar casos de prueba.
3. **Excel** (`docs/Plantilla de Casos de Prueba.xlsx`): Formato visual con estilos y colores para presentaciones.

Para convertir entre formatos, utilice el script `docs/convertir_csv_a_excel.py`.

## Ejecución de Pruebas

### Pruebas Manuales

Las pruebas manuales se ejecutan con el script `run_manual_tests.py`, que guía al tester a través de cada caso de prueba y registra los resultados.

```bash
# Ejecutar todas las pruebas manuales desde el archivo Markdown
python tests/run_manual_tests.py

# Ejecutar pruebas de un módulo específico
python tests/run_manual_tests.py -m "Usuarios"

# Ejecutar pruebas de alta prioridad
python tests/run_manual_tests.py -p "Alta"

# Usar fuente CSV o Excel
python tests/run_manual_tests.py -s csv
python tests/run_manual_tests.py -s excel

# Generar informe HTML
python tests/run_manual_tests.py -r
```

Durante la ejecución, se le pedirá que ingrese el resultado de cada prueba con las siguientes opciones:

- **P**: Pasado - La prueba fue exitosa
- **F**: Fallido - La prueba falló
- **B**: Bloqueado - No se pudo ejecutar por dependencias
- **N**: No Aplicable - No aplica en el contexto actual
- **S**: Omitido - Se decidió omitir la prueba

### Pruebas Automatizadas

Las pruebas automatizadas están implementadas en `test_modules.py` y cubren los principales módulos del proyecto.

```bash
# Ejecutar todas las pruebas automatizadas
python -m unittest tests/test_modules.py

# Ejecutar pruebas de un módulo específico
python -m unittest tests.test_modules.UsuariosTestCase
```

### Pruebas de Diseño

Las pruebas de diseño verifican aspectos visuales, responsive, accesibilidad y componentes JavaScript.

```bash
# Ejecutar todas las pruebas de diseño
python tests/run_design_tests.py

# Ejecutar un tipo específico de prueba
python tests/run_design_tests.py visual
python tests/run_design_tests.py responsive
python tests/run_design_tests.py accessibility
python tests/run_design_tests.py components
python tests/run_design_tests.py css

# Mostrar salida detallada
python tests/run_design_tests.py -v

# Generar informe HTML
python tests/run_design_tests.py -r
```

## Generación de Informes

Para generar un informe consolidado de todas las pruebas (manuales, automatizadas y de diseño), utilice el script `generate_test_report.py`:

```bash
# Generar informe consolidado
python tests/generate_test_report.py

# Especificar ruta de salida
python tests/generate_test_report.py -o ruta/al/informe.html
```

El informe incluye:

- Resumen general de todas las pruebas
- Estadísticas por tipo de prueba
- Gráficos y visualizaciones
- Detalles de pruebas fallidas
- Distribución por módulos

## Conversión de Formatos

Para convertir la plantilla CSV a formato Excel con estilos:

```bash
# Convertir CSV a Excel
python docs/convertir_csv_a_excel.py
```

Esto generará un archivo Excel con formato similar al mostrado en la imagen de referencia, incluyendo colores, bordes y una hoja de instrucciones.

## Recomendaciones para Pruebas

1. **Pruebas Manuales**: Ejecute primero las pruebas de alta prioridad y documente detalladamente los resultados.
2. **Pruebas Automatizadas**: Ejecute regularmente para detectar regresiones.
3. **Pruebas de Diseño**: Ejecute después de cambios significativos en la interfaz de usuario.
4. **Informes**: Genere informes consolidados antes de cada entrega o sprint review.

## Solución de Problemas

Si encuentra errores durante la ejecución de las pruebas:

1. Verifique que todas las dependencias estén instaladas:
   ```bash
   pip install pandas openpyxl termcolor
   ```

2. Asegúrese de que los directorios `tests/results` y `tests/reports` existan.

3. Para problemas con las pruebas de diseño, verifique que Playwright esté instalado:
   ```bash
   npm install -g playwright
   npx playwright install
   ```

4. Si las pruebas automatizadas fallan, verifique la configuración de la base de datos y las credenciales.

---

Para cualquier consulta adicional, contacte al equipo de desarrollo de EcoPuntos.