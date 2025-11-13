const { test, expect } = require('@playwright/test');

/**
 * Pruebas de Regresión Visual para EcoPuntos
 * Estas pruebas capturan screenshots y los comparan con imágenes de referencia
 */

test.describe('Pruebas de Regresión Visual', () => {
  
  test('Página de inicio - Vista completa', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Esperar a que las imágenes se carguen
    await page.waitForTimeout(2000);
    
    // Capturar screenshot de la página completa
    await expect(page).toHaveScreenshot('homepage-full.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Página de login - Vista completa', async ({ page }) => {
    await page.goto('/iniciosesion/');
    await page.waitForLoadState('networkidle');
    
    // Capturar screenshot del formulario de login
    await expect(page).toHaveScreenshot('login-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Página de registro - Vista completa', async ({ page }) => {
    await page.goto('/registrate/');
    await page.waitForLoadState('networkidle');
    
    // Capturar screenshot del formulario de registro
    await expect(page).toHaveScreenshot('register-page.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Header y navegación principal', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Capturar solo el header
    const header = page.locator('header, nav, .navbar');
    if (await header.count() > 0) {
      await expect(header.first()).toHaveScreenshot('header-navigation.png');
    }
  });

  test('Footer - Elementos legales', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Capturar el footer
    const footer = page.locator('footer, .footer');
    if (await footer.count() > 0) {
      await expect(footer.first()).toHaveScreenshot('footer-legal.png');
    }
  });

  test('Formularios - Estados de validación', async ({ page }) => {
    await page.goto('/iniciosesion/');
    await page.waitForLoadState('networkidle');
    
    // Intentar enviar formulario vacío para mostrar errores
    const submitButton = page.locator('input[type="submit"], button[type="submit"]');
    if (await submitButton.count() > 0) {
      await submitButton.click();
      await page.waitForTimeout(1000);
      
      // Capturar formulario con errores de validación
      await expect(page.locator('form').first()).toHaveScreenshot('form-validation-errors.png');
    }
  });

  test('Elementos interactivos - Botones y enlaces', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Capturar botones principales
    const buttons = page.locator('button, .btn, input[type="submit"]');
    const buttonCount = await buttons.count();
    
    if (buttonCount > 0) {
      // Capturar los primeros 3 botones
      for (let i = 0; i < Math.min(3, buttonCount); i++) {
        await expect(buttons.nth(i)).toHaveScreenshot(`button-${i + 1}.png`);
      }
    }
  });

  test('Categorías de materiales - Vista de tarjetas', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Buscar sección de categorías
    const categories = page.locator('.categoria, .category, .material-card');
    const categoryCount = await categories.count();
    
    if (categoryCount > 0) {
      await expect(categories.first()).toHaveScreenshot('material-category-card.png');
    }
  });

  test('Responsive - Elementos críticos en móvil', async ({ page }) => {
    // Configurar viewport móvil
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Capturar vista móvil
    await expect(page).toHaveScreenshot('mobile-homepage.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });

  test('Responsive - Elementos críticos en tablet', async ({ page }) => {
    // Configurar viewport tablet
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Capturar vista tablet
    await expect(page).toHaveScreenshot('tablet-homepage.png', {
      fullPage: true,
      animations: 'disabled'
    });
  });
});