#!/usr/bin/env node

/**
 * Script para ejecutar todas las pruebas de diseño de EcoPuntos
 * Uso: node run-design-tests.js [opciones]
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Configuración de pruebas
const testSuites = {
  'visual': {
    file: 'tests/visual-regression.spec.js',
    description: 'Pruebas de regresión visual',
    priority: 'alta'
  },
  'responsive': {
    file: 'tests/responsive-design.spec.js',
    description: 'Pruebas de diseño responsive',
    priority: 'alta'
  },
  'accessibility': {
    file: 'tests/accessibility.spec.js',
    description: 'Pruebas de accesibilidad',
    priority: 'media'
  },
  'components': {
    file: 'tests/javascript-components.spec.js',
    description: 'Pruebas de componentes JavaScript',
    priority: 'media'
  },
  'css': {
    file: 'tests/css-validation.spec.js',
    description: 'Validación de CSS',
    priority: 'baja'
  }
};

// Colores para la consola
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logHeader(message) {
  log('\n' + '='.repeat(60), 'cyan');
  log(`  ${message}`, 'bright');
  log('='.repeat(60), 'cyan');
}

function logSuccess(message) {
  log(`✓ ${message}`, 'green');
}

function logError(message) {
  log(`✗ ${message}`, 'red');
}

function logWarning(message) {
  log(`⚠ ${message}`, 'yellow');
}

function logInfo(message) {
  log(`ℹ ${message}`, 'blue');
}

// Verificar si Playwright está instalado
function checkPlaywrightInstallation() {
  try {
    require.resolve('@playwright/test');
    return true;
  } catch (error) {
    return false;
  }
}

// Verificar si el servidor Django está corriendo
function checkDjangoServer() {
  return new Promise((resolve) => {
    const http = require('http');
    const req = http.request({
      hostname: 'localhost',
      port: 8000,
      path: '/',
      method: 'GET',
      timeout: 2000
    }, (res) => {
      resolve(true);
    });
    
    req.on('error', () => {
      resolve(false);
    });
    
    req.on('timeout', () => {
      resolve(false);
    });
    
    req.end();
  });
}

// Ejecutar comando de Playwright
function runPlaywrightTest(testFile, options = {}) {
  return new Promise((resolve, reject) => {
    const args = ['test', testFile];
    
    // Agregar opciones
    if (options.headed) args.push('--headed');
    if (options.debug) args.push('--debug');
    if (options.reporter) args.push('--reporter', options.reporter);
    if (options.project) args.push('--project', options.project);
    if (options.workers) args.push('--workers', options.workers.toString());
    
    const child = spawn('npx', ['playwright', ...args], {
      stdio: 'inherit',
      shell: true
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Test failed with exit code ${code}`));
      }
    });
    
    child.on('error', (error) => {
      reject(error);
    });
  });
}

// Función principal
async function main() {
  const args = process.argv.slice(2);
  
  logHeader('ECOPUNTOS - PRUEBAS DE DISEÑO');
  
  // Verificar instalación de Playwright
  if (!checkPlaywrightInstallation()) {
    logError('Playwright no está instalado.');
    logInfo('Ejecuta: npm install @playwright/test');
    process.exit(1);
  }
  
  logSuccess('Playwright está instalado');
  
  // Verificar servidor Django
  const serverRunning = await checkDjangoServer();
  if (!serverRunning) {
    logWarning('El servidor Django no está corriendo en localhost:8000');
    logInfo('Asegúrate de ejecutar: python manage.py runserver');
    logInfo('Las pruebas intentarán iniciar el servidor automáticamente...');
  } else {
    logSuccess('Servidor Django detectado en localhost:8000');
  }
  
  // Parsear argumentos
  const options = {
    headed: args.includes('--headed'),
    debug: args.includes('--debug'),
    reporter: args.includes('--reporter') ? args[args.indexOf('--reporter') + 1] : 'list',
    workers: args.includes('--workers') ? parseInt(args[args.indexOf('--workers') + 1]) : 1,
    suite: null
  };
  
  // Verificar si se especificó una suite específica
  const suiteArg = args.find(arg => Object.keys(testSuites).includes(arg));
  if (suiteArg) {
    options.suite = suiteArg;
  }
  
  // Mostrar ayuda
  if (args.includes('--help') || args.includes('-h')) {
    logInfo('Uso: node run-design-tests.js [opciones] [suite]');
    log('\nSuites disponibles:');
    Object.entries(testSuites).forEach(([key, suite]) => {
      log(`  ${key.padEnd(12)} - ${suite.description} (Prioridad: ${suite.priority})`);
    });
    log('\nOpciones:');
    log('  --headed      Ejecutar en modo visual (no headless)');
    log('  --debug       Modo debug con pausa en fallos');
    log('  --reporter    Reporter a usar (list, html, json)');
    log('  --workers N   Número de workers paralelos');
    log('  --help, -h    Mostrar esta ayuda');
    log('\nEjemplos:');
    log('  node run-design-tests.js                    # Ejecutar todas las pruebas');
    log('  node run-design-tests.js visual             # Solo pruebas visuales');
    log('  node run-design-tests.js --headed           # Modo visual');
    log('  node run-design-tests.js --reporter html    # Reporte HTML');
    return;
  }
  
  // Determinar qué pruebas ejecutar
  const suitesToRun = options.suite ? 
    { [options.suite]: testSuites[options.suite] } : 
    testSuites;
  
  logHeader('CONFIGURACIÓN DE PRUEBAS');
  log(`Modo: ${options.headed ? 'Visual (headed)' : 'Headless'}`);
  log(`Reporter: ${options.reporter}`);
  log(`Workers: ${options.workers}`);
  log(`Suites a ejecutar: ${Object.keys(suitesToRun).join(', ')}`);
  
  // Ejecutar pruebas
  let totalTests = 0;
  let passedTests = 0;
  let failedTests = 0;
  
  for (const [suiteKey, suite] of Object.entries(suitesToRun)) {
    logHeader(`EJECUTANDO: ${suite.description.toUpperCase()}`);
    logInfo(`Archivo: ${suite.file}`);
    logInfo(`Prioridad: ${suite.priority}`);
    
    try {
      // Verificar que el archivo existe
      if (!fs.existsSync(suite.file)) {
        logError(`Archivo de prueba no encontrado: ${suite.file}`);
        failedTests++;
        continue;
      }
      
      await runPlaywrightTest(suite.file, options);
      logSuccess(`Suite '${suiteKey}' completada exitosamente`);
      passedTests++;
    } catch (error) {
      logError(`Suite '${suiteKey}' falló: ${error.message}`);
      failedTests++;
    }
    
    totalTests++;
  }
  
  // Resumen final
  logHeader('RESUMEN DE EJECUCIÓN');
  log(`Total de suites: ${totalTests}`);
  logSuccess(`Exitosas: ${passedTests}`);
  if (failedTests > 0) {
    logError(`Fallidas: ${failedTests}`);
  }
  
  if (failedTests === 0) {
    logSuccess('¡Todas las pruebas de diseño pasaron exitosamente!');
    process.exit(0);
  } else {
    logError('Algunas pruebas fallaron. Revisa los logs anteriores.');
    process.exit(1);
  }
}

// Manejo de errores no capturados
process.on('uncaughtException', (error) => {
  logError(`Error no capturado: ${error.message}`);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logError(`Promesa rechazada no manejada: ${reason}`);
  process.exit(1);
});

// Manejo de interrupción (Ctrl+C)
process.on('SIGINT', () => {
  logWarning('\nEjecución interrumpida por el usuario');
  process.exit(0);
});

// Ejecutar función principal
if (require.main === module) {
  main().catch((error) => {
    logError(`Error en la ejecución: ${error.message}`);
    process.exit(1);
  });
}

module.exports = { main, testSuites };