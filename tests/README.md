# Pruebas de Diseño - EcoPuntos

Este directorio contiene todas las pruebas de diseño implementadas para el proyecto EcoPuntos, utilizando Playwright como framework principal de testing.

## 📋 Suites de Pruebas Implementadas

### 🔴 Prioridad Alta

#### 1. Pruebas de Regresión Visual (`visual-regression.spec.js`)
- **Propósito**: Detectar cambios visuales no deseados en la interfaz
- **Cobertura**:
  - Capturas de pantalla de páginas principales
  - Comparación pixel por pixel
  - Detección de cambios en layout
  - Verificación de elementos críticos (header, footer, formularios)
  - Pruebas en diferentes resoluciones

#### 2. Pruebas de Diseño Responsive (`responsive-design.spec.js`)
- **Propósito**: Verificar la adaptabilidad del diseño en diferentes dispositivos
- **Cobertura**:
  - Viewports móvil, tablet y desktop
  - Visibilidad de elementos críticos
  - Navegación móvil
  - Escalado de imágenes
  - Legibilidad del texto
  - Breakpoints de CSS

### 🟡 Prioridad Media

#### 3. Pruebas de Accesibilidad (`accessibility.spec.js`)
- **Propósito**: Garantizar cumplimiento de estándares WCAG
- **Cobertura**:
  - Navegación por teclado
  - Contraste de colores
  - Etiquetas de formularios
  - Texto alternativo en imágenes
  - Estructura semántica
  - Roles ARIA
  - Tamaño de elementos táctiles

#### 4. Pruebas de Componentes JavaScript (`javascript-components.spec.js`)
- **Propósito**: Verificar funcionalidad de scripts del frontend
- **Cobertura**:
  - Validación de formularios
  - Animaciones e interacciones
  - Monitor de sesión
  - Recuperación de contraseña
  - Eventos de formulario
  - Navegación interactiva
  - Manejo de errores
  - Performance de JavaScript

### 🟢 Prioridad Baja

#### 5. Validación de CSS (`css-validation.spec.js`)
- **Propósito**: Verificar calidad e integridad del CSS
- **Cobertura**:
  - Carga de archivos CSS
  - Estilos críticos
  - Media queries responsive
  - Paleta de colores
  - Tipografía
  - Layout (Flexbox/Grid)
  - Animaciones y transiciones
  - Detección de CSS no utilizado
  - Performance de CSS

## 🚀 Configuración y Ejecución

### Prerrequisitos

1. **Node.js** (versión 14 o superior)
2. **Playwright** instalado:
   ```bash
   npm install @playwright/test
   npx playwright install
   ```
3. **Servidor Django** corriendo en `localhost:8000`:
   ```bash
   python manage.py runserver
   ```

### Métodos de Ejecución

#### Opción 1: Script Automatizado (Recomendado)
```bash
# Ejecutar todas las pruebas
node run-design-tests.js

# Ejecutar suite específica
node run-design-tests.js visual
node run-design-tests.js responsive
node run-design-tests.js accessibility
node run-design-tests.js components
node run-design-tests.js css

# Opciones adicionales
node run-design-tests.js --headed          # Modo visual
node run-design-tests.js --debug           # Modo debug
node run-design-tests.js --reporter html   # Reporte HTML
node run-design-tests.js --workers 2       # Paralelización
```

#### Opción 2: Playwright Directo
```bash
# Ejecutar todas las pruebas
npx playwright test tests/

# Ejecutar suite específica
npx playwright test tests/visual-regression.spec.js
npx playwright test tests/responsive-design.spec.js
npx playwright test tests/accessibility.spec.js
npx playwright test tests/javascript-components.spec.js
npx playwright test tests/css-validation.spec.js

# Con opciones
npx playwright test --headed
npx playwright test --debug
npx playwright test --reporter=html
```

#### Opción 3: Scripts NPM
Agregar al `package.json`:
```json
{
  "scripts": {
    "test:design": "node run-design-tests.js",
    "test:visual": "npx playwright test tests/visual-regression.spec.js",
    "test:responsive": "npx playwright test tests/responsive-design.spec.js",
    "test:accessibility": "npx playwright test tests/accessibility.spec.js",
    "test:components": "npx playwright test tests/javascript-components.spec.js",
    "test:css": "npx playwright test tests/css-validation.spec.js"
  }
}
```

## 📊 Reportes y Resultados

### Tipos de Reportes Disponibles

1. **Lista (por defecto)**: Salida en consola
2. **HTML**: Reporte interactivo en navegador
3. **JSON**: Datos estructurados para integración
4. **JUnit**: Compatible con CI/CD

### Generar Reporte HTML
```bash
node run-design-tests.js --reporter html
# o
npx playwright test --reporter=html
```

### Ubicación de Resultados
- **Screenshots**: `test-results/`
- **Videos**: `test-results/` (en caso de fallos)
- **Reportes HTML**: `playwright-report/`
- **Capturas de referencia**: `tests/visual-regression.spec.js-snapshots/`

## 🔧 Configuración Avanzada

### Archivo de Configuración (`playwright.config.js`)

El archivo de configuración incluye:
- Configuración de navegadores (Chrome, Firefox, Safari)
- Viewports para diferentes dispositivos
- Configuración de red y timeouts
- Integración con servidor Django
- Configuración de reportes

### Personalización de Pruebas

#### Agregar Nuevas Páginas a Probar
Editar los archivos `.spec.js` correspondientes y agregar nuevas URLs:

```javascript
test('Nueva página - Verificación visual', async ({ page }) => {
  await page.goto('/nueva-pagina/');
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveScreenshot('nueva-pagina.png');
});
```

#### Configurar Nuevos Viewports
Editar `playwright.config.js`:

```javascript
projects: [
  {
    name: 'nuevo-dispositivo',
    use: {
      ...devices['iPhone 13'],
      viewport: { width: 390, height: 844 }
    }
  }
]
```

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Error: "Server not running"**
   - Verificar que Django esté corriendo en puerto 8000
   - Ejecutar: `python manage.py runserver`

2. **Fallos en pruebas visuales**
   - Las capturas pueden diferir entre sistemas operativos
   - Regenerar capturas de referencia: `npx playwright test --update-snapshots`

3. **Timeouts en pruebas**
   - Aumentar timeout en `playwright.config.js`
   - Verificar velocidad de red y servidor

4. **Errores de accesibilidad**
   - Revisar elementos sin etiquetas
   - Verificar contraste de colores
   - Asegurar navegación por teclado

### Logs y Debugging

```bash
# Modo debug con pausa en fallos
node run-design-tests.js --debug

# Ejecutar con logs detallados
DEBUG=pw:api npx playwright test

# Modo headed para ver ejecución
node run-design-tests.js --headed
```

## 📈 Integración con CI/CD

### GitHub Actions
```yaml
name: Design Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npx playwright install
      - run: python manage.py runserver &
      - run: node run-design-tests.js
```

### Jenkins
```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'npm install'
                sh 'npx playwright install'
            }
        }
        stage('Start Server') {
            steps {
                sh 'python manage.py runserver &'
                sleep 10
            }
        }
        stage('Run Tests') {
            steps {
                sh 'node run-design-tests.js --reporter junit'
            }
        }
    }
    post {
        always {
            publishTestResults testResultsPattern: 'test-results.xml'
        }
    }
}
```

## 📝 Mantenimiento

### Actualización Regular

1. **Capturas de referencia**: Actualizar cuando hay cambios intencionales en el diseño
2. **Nuevas páginas**: Agregar pruebas para nuevas funcionalidades
3. **Dependencias**: Mantener Playwright actualizado
4. **Configuración**: Revisar y ajustar timeouts y configuraciones

### Mejores Prácticas

1. **Ejecutar antes de cada deploy**
2. **Revisar fallos inmediatamente**
3. **Mantener capturas actualizadas**
4. **Documentar cambios en pruebas**
5. **Monitorear performance de pruebas**

## 🤝 Contribución

Para agregar nuevas pruebas:

1. Crear archivo `.spec.js` en el directorio `tests/`
2. Seguir la estructura existente
3. Agregar documentación
4. Probar localmente
5. Actualizar este README si es necesario

## 📞 Soporte

Para problemas o preguntas:
- Revisar logs de ejecución
- Consultar documentación de Playwright
- Verificar configuración del servidor Django
- Revisar este README para soluciones comunes