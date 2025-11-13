#!/usr/bin/env node

/**
 * Script de configuración inicial para las pruebas de diseño de EcoPuntos
 * Automatiza la instalación y configuración de dependencias
 */

const { spawn, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colores para la consola
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
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

// Ejecutar comando con promesa
function runCommand(command, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, [], {
      stdio: options.silent ? 'pipe' : 'inherit',
      shell: true,
      ...options
    });
    
    let output = '';
    if (options.silent) {
      child.stdout.on('data', (data) => {
        output += data.toString();
      });
      child.stderr.on('data', (data) => {
        output += data.toString();
      });
    }
    
    child.on('close', (code) => {
      if (code === 0) {
        resolve(output);
      } else {
        reject(new Error(`Command failed with exit code ${code}: ${output}`));
      }
    });
    
    child.on('error', (error) => {
      reject(error);
    });
  });
}

// Verificar si Node.js tiene la versión correcta
function checkNodeVersion() {
  const version = process.version;
  const majorVersion = parseInt(version.slice(1).split('.')[0]);
  
  if (majorVersion < 14) {
    logError(`Node.js versión ${version} detectada. Se requiere versión 14 o superior.`);
    return false;
  }
  
  logSuccess(`Node.js versión ${version} es compatible`);
  return true;
}

// Verificar si npm está disponible
async function checkNpm() {
  try {
    const output = await runCommand('npm --version', { silent: true });
    logSuccess(`npm versión ${output.trim()} detectado`);
    return true;
  } catch (error) {
    logError('npm no está disponible');
    return false;
  }
}

// Verificar si package.json existe
function checkPackageJson() {
  if (fs.existsSync('package.json')) {
    logSuccess('package.json encontrado');
    return true;
  } else {
    logError('package.json no encontrado');
    return false;
  }
}

// Instalar dependencias de npm
async function installDependencies() {
  logInfo('Instalando dependencias de npm...');
  try {
    await runCommand('npm install');
    logSuccess('Dependencias de npm instaladas');
    return true;
  } catch (error) {
    logError(`Error instalando dependencias: ${error.message}`);
    return false;
  }
}

// Instalar navegadores de Playwright
async function installPlaywrightBrowsers() {
  logInfo('Instalando navegadores de Playwright...');
  try {
    await runCommand('npx playwright install');
    logSuccess('Navegadores de Playwright instalados');
    return true;
  } catch (error) {
    logError(`Error instalando navegadores: ${error.message}`);
    return false;
  }
}

// Verificar estructura de directorios
function checkDirectoryStructure() {
  const requiredDirs = ['tests'];
  const requiredFiles = [
    'playwright.config.js',
    'run-design-tests.js',
    'tests/visual-regression.spec.js',
    'tests/responsive-design.spec.js',
    'tests/accessibility.spec.js',
    'tests/javascript-components.spec.js',
    'tests/css-validation.spec.js',
    'tests/README.md'
  ];
  
  let allExists = true;
  
  // Verificar directorios
  requiredDirs.forEach(dir => {
    if (fs.existsSync(dir)) {
      logSuccess(`Directorio '${dir}' existe`);
    } else {
      logError(`Directorio '${dir}' no encontrado`);
      allExists = false;
    }
  });
  
  // Verificar archivos
  requiredFiles.forEach(file => {
    if (fs.existsSync(file)) {
      logSuccess(`Archivo '${file}' existe`);
    } else {
      logError(`Archivo '${file}' no encontrado`);
      allExists = false;
    }
  });
  
  return allExists;
}

// Verificar servidor Django
async function checkDjangoSetup() {
  logInfo('Verificando configuración de Django...');
  
  const djangoFiles = ['manage.py', 'requirements.txt'];
  let djangoOk = true;
  
  djangoFiles.forEach(file => {
    if (fs.existsSync(file)) {
      logSuccess(`Archivo Django '${file}' encontrado`);
    } else {
      logWarning(`Archivo Django '${file}' no encontrado`);
      djangoOk = false;
    }
  });
  
  if (djangoOk) {
    logInfo('Para ejecutar las pruebas, asegúrate de tener el servidor Django corriendo:');
    log('  python manage.py runserver 8000', 'yellow');
  }
  
  return djangoOk;
}

// Ejecutar prueba de ejemplo
async function runSampleTest() {
  logInfo('Ejecutando prueba de ejemplo...');
  try {
    // Verificar si el servidor está corriendo
    const http = require('http');
    const serverRunning = await new Promise((resolve) => {
      const req = http.request({
        hostname: 'localhost',
        port: 8000,
        path: '/',
        method: 'GET',
        timeout: 2000
      }, (res) => {
        resolve(true);
      });
      
      req.on('error', () => resolve(false));
      req.on('timeout', () => resolve(false));
      req.end();
    });
    
    if (!serverRunning) {
      logWarning('Servidor Django no está corriendo. Saltando prueba de ejemplo.');
      logInfo('Para ejecutar pruebas, inicia el servidor con: python manage.py runserver');
      return true;
    }
    
    // Ejecutar una prueba simple
    await runCommand('npx playwright test tests/visual-regression.spec.js --grep "Homepage" --reporter=list');
    logSuccess('Prueba de ejemplo ejecutada exitosamente');
    return true;
  } catch (error) {
    logWarning(`Prueba de ejemplo falló (esto es normal si el servidor no está corriendo): ${error.message}`);
    return true; // No es crítico
  }
}

// Mostrar resumen de comandos útiles
function showUsageInstructions() {
  logHeader('COMANDOS ÚTILES');
  
  log('Ejecutar todas las pruebas de diseño:', 'bright');
  log('  npm run test:design');
  log('  node run-design-tests.js');
  
  log('\nEjecutar pruebas específicas:', 'bright');
  log('  npm run test:visual        # Pruebas visuales');
  log('  npm run test:responsive    # Pruebas responsive');
  log('  npm run test:accessibility # Pruebas de accesibilidad');
  log('  npm run test:components    # Pruebas de componentes JS');
  log('  npm run test:css          # Validación de CSS');
  
  log('\nOpciones adicionales:', 'bright');
  log('  npm run test:design:headed # Modo visual');
  log('  npm run test:design:html   # Reporte HTML');
  log('  npm run test:visual:update # Actualizar capturas');
  
  log('\nAntes de ejecutar pruebas:', 'bright');
  log('  python manage.py runserver # Iniciar servidor Django');
  
  log('\nDocumentación:', 'bright');
  log('  tests/README.md           # Documentación completa');
}

// Función principal
async function main() {
  logHeader('CONFIGURACIÓN DE PRUEBAS DE DISEÑO - ECOPUNTOS');
  
  let setupSuccess = true;
  
  // Verificaciones previas
  logHeader('VERIFICACIONES PREVIAS');
  
  if (!checkNodeVersion()) setupSuccess = false;
  if (!(await checkNpm())) setupSuccess = false;
  if (!checkPackageJson()) setupSuccess = false;
  
  if (!setupSuccess) {
    logError('Verificaciones previas fallaron. Corrige los errores antes de continuar.');
    process.exit(1);
  }
  
  // Instalación de dependencias
  logHeader('INSTALACIÓN DE DEPENDENCIAS');
  
  if (!(await installDependencies())) setupSuccess = false;
  if (!(await installPlaywrightBrowsers())) setupSuccess = false;
  
  // Verificación de estructura
  logHeader('VERIFICACIÓN DE ESTRUCTURA');
  
  if (!checkDirectoryStructure()) {
    logError('Algunos archivos de prueba no se encontraron.');
    logInfo('Asegúrate de que todos los archivos de prueba estén en su lugar.');
    setupSuccess = false;
  }
  
  // Verificación de Django
  logHeader('VERIFICACIÓN DE DJANGO');
  await checkDjangoSetup();
  
  // Prueba de ejemplo (opcional)
  logHeader('PRUEBA DE EJEMPLO');
  await runSampleTest();
  
  // Resumen final
  logHeader('RESUMEN DE CONFIGURACIÓN');
  
  if (setupSuccess) {
    logSuccess('¡Configuración completada exitosamente!');
    logInfo('Las pruebas de diseño están listas para usar.');
  } else {
    logWarning('Configuración completada con advertencias.');
    logInfo('Revisa los errores anteriores antes de ejecutar pruebas.');
  }
  
  showUsageInstructions();
}

// Manejo de errores
process.on('uncaughtException', (error) => {
  logError(`Error no capturado: ${error.message}`);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logError(`Promesa rechazada: ${reason}`);
  process.exit(1);
});

process.on('SIGINT', () => {
  logWarning('\nConfiguración interrumpida por el usuario');
  process.exit(0);
});

// Ejecutar si es el módulo principal
if (require.main === module) {
  main().catch((error) => {
    logError(`Error en la configuración: ${error.message}`);
    process.exit(1);
  });
}

module.exports = { main };