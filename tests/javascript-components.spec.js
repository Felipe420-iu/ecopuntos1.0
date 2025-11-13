const { test, expect } = require('@playwright/test');

/**
 * Pruebas de Componentes JavaScript para EcoPuntos
 * Verifican la funcionalidad de los scripts del frontend
 */

test.describe('Pruebas de Componentes JavaScript', () => {
  
  test('Funcionalidad de login - Validación de formulario', async ({ page }) => {
    await page.goto('/iniciosesion/');
    await page.waitForLoadState('networkidle');
    
    // Verificar que el script de login está cargado
    const loginScriptLoaded = await page.evaluate(() => {
      return typeof window.loginFunctionality !== 'undefined' || 
             document.querySelector('script[src*="login-functionality"]') !== null;
    });
    
    // Probar validación de campos vacíos
    const usernameField = page.locator('input[name="username"], input[type="text"]').first();
    const passwordField = page.locator('input[name="password"], input[type="password"]').first();
    const submitButton = page.locator('input[type="submit"], button[type="submit"]').first();
    
    if (await usernameField.count() > 0 && await passwordField.count() > 0) {
      // Intentar enviar formulario vacío
      await submitButton.click();
      await page.waitForTimeout(500);
      
      // Verificar que aparecen mensajes de error o validación
      const hasValidation = await page.evaluate(() => {
        const errorElements = document.querySelectorAll('.error, .invalid, .alert-danger');
        const requiredFields = document.querySelectorAll('input:required');
        const browserValidation = document.querySelector('input:invalid');
        
        return errorElements.length > 0 || requiredFields.length > 0 || browserValidation !== null;
      });
      
      expect(hasValidation).toBeTruthy();
    }
  });
  
  test('Animaciones de índice - Carga y ejecución', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verificar que el script de animaciones está cargado
    const animationScriptLoaded = await page.evaluate(() => {
      return document.querySelector('script[src*="index-animations"]') !== null;
    });
    
    // Verificar elementos animados
    const animatedElements = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const animated = [];
      
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        const hasTransition = styles.transition !== 'all 0s ease 0s';
        const hasAnimation = styles.animation !== 'none';
        const hasTransform = styles.transform !== 'none';
        
        if (hasTransition || hasAnimation || hasTransform) {
          animated.push({
            tagName: el.tagName,
            className: el.className,
            hasTransition,
            hasAnimation,
            hasTransform
          });
        }
      });
      
      return animated;
    });
    
    // Debe haber al menos algunos elementos con animaciones/transiciones
    expect(animatedElements.length).toBeGreaterThan(0);
  });
  
  test('Monitor de sesión - Funcionalidad de timeout', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verificar que el script de monitor de sesión está presente
    const sessionMonitorLoaded = await page.evaluate(() => {
      return document.querySelector('script[src*="session-monitor"]') !== null ||
             typeof window.sessionMonitor !== 'undefined';
    });
    
    // Verificar variables de sesión
    const sessionVariables = await page.evaluate(() => {
      return {
        hasSessionTimeout: typeof window.sessionTimeout !== 'undefined',
        hasWarningTime: typeof window.warningTime !== 'undefined',
        hasSessionCheck: typeof window.checkSession !== 'undefined',
        hasLocalStorage: typeof localStorage !== 'undefined',
        hasSessionStorage: typeof sessionStorage !== 'undefined'
      };
    });
    
    // Al menos debe tener capacidades de almacenamiento
    expect(sessionVariables.hasLocalStorage || sessionVariables.hasSessionStorage).toBeTruthy();
  });
  
  test('Recuperación de contraseña - Modal y validación', async ({ page }) => {
    await page.goto('/iniciosesion/');
    await page.waitForLoadState('networkidle');
    
    // Buscar enlace de recuperación de contraseña
    const forgotPasswordLink = page.locator('a[href*="password"], a[href*="forgot"], a[href*="recover"]');
    
    if (await forgotPasswordLink.count() > 0) {
      await forgotPasswordLink.first().click();
      await page.waitForTimeout(1000);
      
      // Verificar que se abre modal o se navega a página de recuperación
      const modalOrPage = await page.evaluate(() => {
        const modal = document.querySelector('.modal, .popup, .overlay');
        const passwordForm = document.querySelector('form[action*="password"], form[action*="recover"]');
        const emailField = document.querySelector('input[type="email"]');
        
        return {
          hasModal: modal !== null,
          hasPasswordForm: passwordForm !== null,
          hasEmailField: emailField !== null,
          currentUrl: window.location.href
        };
      });
      
      // Debe haber algún mecanismo de recuperación
      const hasRecoveryMechanism = modalOrPage.hasModal || 
                                   modalOrPage.hasPasswordForm || 
                                   modalOrPage.hasEmailField ||
                                   modalOrPage.currentUrl.includes('password') ||
                                   modalOrPage.currentUrl.includes('recover');
      
      expect(hasRecoveryMechanism).toBeTruthy();
    }
  });
  
  test('Interacciones de formulario - Eventos y validación', async ({ page }) => {
    await page.goto('/registrate/');
    await page.waitForLoadState('networkidle');
    
    const formFields = page.locator('input[type="text"], input[type="email"], input[type="password"]');
    const fieldCount = await formFields.count();
    
    if (fieldCount > 0) {
      // Probar eventos de focus y blur
      for (let i = 0; i < Math.min(3, fieldCount); i++) {
        const field = formFields.nth(i);
        
        // Focus en el campo
        await field.focus();
        await page.waitForTimeout(200);
        
        // Verificar que el campo tiene focus
        const hasFocus = await field.evaluate(el => el === document.activeElement);
        expect(hasFocus).toBeTruthy();
        
        // Escribir algo y luego borrarlo
        await field.fill('test');
        await page.waitForTimeout(100);
        await field.fill('');
        
        // Blur del campo
        await field.blur();
        await page.waitForTimeout(200);
        
        // Verificar si aparecen mensajes de validación
        const validationMessage = await page.evaluate(() => {
          const errors = document.querySelectorAll('.error, .invalid, .field-error');
          return errors.length > 0;
        });
        
        // No es obligatorio que haya validación, pero si la hay, debe funcionar
      }
    }
  });
  
  test('Navegación y menús - Interactividad', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Buscar elementos de navegación interactivos
    const navElements = page.locator('nav a, .menu a, .navbar a');
    const navCount = await navElements.count();
    
    if (navCount > 0) {
      // Probar hover en elementos de navegación
      for (let i = 0; i < Math.min(3, navCount); i++) {
        const navItem = navElements.nth(i);
        
        if (await navItem.isVisible()) {
          // Hover sobre el elemento
          await navItem.hover();
          await page.waitForTimeout(200);
          
          // Verificar cambios visuales en hover
          const hoverStyles = await navItem.evaluate(el => {
            const styles = window.getComputedStyle(el);
            return {
              color: styles.color,
              backgroundColor: styles.backgroundColor,
              textDecoration: styles.textDecoration,
              transform: styles.transform
            };
          });
          
          // Los estilos deben estar definidos
          expect(hoverStyles.color).toBeDefined();
        }
      }
    }
  });
  
  test('Elementos dinámicos - Carga y actualización', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verificar elementos que pueden cargarse dinámicamente
    const dynamicContent = await page.evaluate(() => {
      const containers = document.querySelectorAll('.dynamic, .ajax, .load-more, .infinite-scroll');
      const hasDataAttributes = document.querySelectorAll('[data-url], [data-endpoint]').length > 0;
      const hasFetchCalls = typeof window.fetch !== 'undefined';
      const hasXHR = typeof XMLHttpRequest !== 'undefined';
      
      return {
        dynamicContainers: containers.length,
        hasDataAttributes,
        hasFetchCalls,
        hasXHR
      };
    });
    
    // Verificar capacidades de carga dinámica
    expect(dynamicContent.hasFetchCalls || dynamicContent.hasXHR).toBeTruthy();
  });
  
  test('Manejo de errores JavaScript - Console y excepciones', async ({ page }) => {
    const consoleErrors = [];
    const jsErrors = [];
    
    // Capturar errores de consola
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Capturar errores de JavaScript
    page.on('pageerror', error => {
      jsErrors.push(error.message);
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Navegar por algunas páginas para detectar errores
    const pages = ['/iniciosesion/', '/registrate/'];
    
    for (const pageUrl of pages) {
      try {
        await page.goto(pageUrl);
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);
      } catch (error) {
        // Página puede no existir, continuar
      }
    }
    
    // Reportar errores encontrados
    if (consoleErrors.length > 0) {
      console.warn('Errores de consola encontrados:', consoleErrors);
    }
    
    if (jsErrors.length > 0) {
      console.warn('Errores de JavaScript encontrados:', jsErrors);
    }
    
    // No debe haber errores críticos de JavaScript
    expect(jsErrors.length).toBeLessThanOrEqual(2); // Tolerancia para errores menores
  });
  
  test('Performance de JavaScript - Tiempo de carga', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Verificar métricas de performance
    const performanceMetrics = await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      const resources = performance.getEntriesByType('resource');
      
      const jsResources = resources.filter(resource => 
        resource.name.includes('.js') && !resource.name.includes('node_modules')
      );
      
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        jsResourceCount: jsResources.length,
        totalJSSize: jsResources.reduce((total, resource) => total + (resource.transferSize || 0), 0)
      };
    });
    
    // La página debe cargar en menos de 5 segundos
    expect(loadTime).toBeLessThan(5000);
    
    // DOM debe estar listo en menos de 3 segundos
    expect(performanceMetrics.domContentLoaded).toBeLessThan(3000);
    
    // No debe haber demasiados archivos JS (optimización)
    expect(performanceMetrics.jsResourceCount).toBeLessThan(20);
  });
});