const { test, expect } = require('@playwright/test');

/**
 * Pruebas de Diseño Responsive para EcoPuntos
 * Verifican que el diseño se adapte correctamente a diferentes tamaños de pantalla
 */

const viewports = {
  mobile: { width: 375, height: 667, name: 'Mobile' },
  tablet: { width: 768, height: 1024, name: 'Tablet' },
  desktop: { width: 1920, height: 1080, name: 'Desktop' },
  smallDesktop: { width: 1366, height: 768, name: 'Small Desktop' }
};

const pages = [
  { url: '/', name: 'Homepage' },
  { url: '/iniciosesion/', name: 'Login' },
  { url: '/registrate/', name: 'Register' }
];

test.describe('Pruebas de Diseño Responsive', () => {
  
  // Probar cada página en cada viewport
  for (const pageInfo of pages) {
    for (const [viewportKey, viewport] of Object.entries(viewports)) {
      test(`${pageInfo.name} - ${viewport.name} (${viewport.width}x${viewport.height})`, async ({ page }) => {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await page.goto(pageInfo.url);
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000);
        
        // Verificar que no hay scroll horizontal
        const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
        expect(bodyWidth).toBeLessThanOrEqual(viewport.width + 20); // 20px de tolerancia
        
        // Verificar elementos críticos visibles
        await test.step('Verificar elementos críticos', async () => {
          // Header/Navigation
          const nav = page.locator('nav, header, .navbar');
          if (await nav.count() > 0) {
            await expect(nav.first()).toBeVisible();
          }
          
          // Main content
          const main = page.locator('main, .main-content, .container');
          if (await main.count() > 0) {
            await expect(main.first()).toBeVisible();
          }
          
          // Footer
          const footer = page.locator('footer, .footer');
          if (await footer.count() > 0) {
            await expect(footer.first()).toBeVisible();
          }
        });
        
        // Capturar screenshot para comparación visual
        await expect(page).toHaveScreenshot(`${pageInfo.name.toLowerCase()}-${viewportKey}.png`, {
          fullPage: true,
          animations: 'disabled'
        });
      });
    }
  }
  
  test('Navegación móvil - Menú hamburguesa', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Buscar menú hamburguesa o botón de menú móvil
    const mobileMenu = page.locator('.hamburger, .mobile-menu, .menu-toggle, [aria-label*="menu"]');
    
    if (await mobileMenu.count() > 0) {
      // Verificar que el menú está visible
      await expect(mobileMenu.first()).toBeVisible();
      
      // Hacer clic en el menú
      await mobileMenu.first().click();
      await page.waitForTimeout(500);
      
      // Verificar que se abre el menú
      const menuItems = page.locator('.menu-item, .nav-item, nav a');
      if (await menuItems.count() > 0) {
        await expect(menuItems.first()).toBeVisible();
      }
    }
  });
  
  test('Formularios responsive - Campos y botones', async ({ page }) => {
    await page.goto('/iniciosesion/');
    await page.waitForLoadState('networkidle');
    
    for (const [viewportKey, viewport] of Object.entries(viewports)) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(500);
      
      // Verificar campos de formulario
      const inputs = page.locator('input[type="text"], input[type="email"], input[type="password"]');
      const inputCount = await inputs.count();
      
      for (let i = 0; i < inputCount; i++) {
        const input = inputs.nth(i);
        await expect(input).toBeVisible();
        
        // Verificar que el campo es clickeable
        const box = await input.boundingBox();
        if (box) {
          expect(box.width).toBeGreaterThan(0);
          expect(box.height).toBeGreaterThan(0);
        }
      }
      
      // Verificar botones
      const buttons = page.locator('button, input[type="submit"], .btn');
      const buttonCount = await buttons.count();
      
      for (let i = 0; i < buttonCount; i++) {
        const button = buttons.nth(i);
        if (await button.isVisible()) {
          const box = await button.boundingBox();
          if (box) {
            // En móvil, los botones deben ser al menos 44px de alto (recomendación de accesibilidad)
            if (viewport.width <= 768) {
              expect(box.height).toBeGreaterThanOrEqual(40);
            }
          }
        }
      }
    }
  });
  
  test('Imágenes responsive - Escalado correcto', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    for (const [viewportKey, viewport] of Object.entries(viewports)) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(500);
      
      const images = page.locator('img');
      const imageCount = await images.count();
      
      for (let i = 0; i < Math.min(5, imageCount); i++) {
        const img = images.nth(i);
        if (await img.isVisible()) {
          const box = await img.boundingBox();
          if (box) {
            // Las imágenes no deben exceder el ancho del viewport
            expect(box.width).toBeLessThanOrEqual(viewport.width);
            
            // Las imágenes deben tener dimensiones válidas
            expect(box.width).toBeGreaterThan(0);
            expect(box.height).toBeGreaterThan(0);
          }
        }
      }
    }
  });
  
  test('Texto responsive - Legibilidad en diferentes tamaños', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    for (const [viewportKey, viewport] of Object.entries(viewports)) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(500);
      
      // Verificar títulos principales
      const headings = page.locator('h1, h2, h3');
      const headingCount = await headings.count();
      
      for (let i = 0; i < Math.min(3, headingCount); i++) {
        const heading = headings.nth(i);
        if (await heading.isVisible()) {
          const fontSize = await heading.evaluate(el => {
            return window.getComputedStyle(el).fontSize;
          });
          
          const fontSizeNum = parseInt(fontSize);
          
          // En móvil, los títulos deben ser al menos 16px
          if (viewport.width <= 768) {
            expect(fontSizeNum).toBeGreaterThanOrEqual(16);
          }
        }
      }
      
      // Verificar texto del cuerpo
      const bodyText = page.locator('p, .text, .content');
      const textCount = await bodyText.count();
      
      for (let i = 0; i < Math.min(3, textCount); i++) {
        const text = bodyText.nth(i);
        if (await text.isVisible()) {
          const fontSize = await text.evaluate(el => {
            return window.getComputedStyle(el).fontSize;
          });
          
          const fontSizeNum = parseInt(fontSize);
          
          // El texto del cuerpo debe ser al menos 14px en móvil
          if (viewport.width <= 768) {
            expect(fontSizeNum).toBeGreaterThanOrEqual(14);
          }
        }
      }
    }
  });
  
  test('Breakpoints CSS - Verificación de media queries', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Probar breakpoints comunes
    const breakpoints = [
      { width: 320, name: 'Small Mobile' },
      { width: 480, name: 'Large Mobile' },
      { width: 768, name: 'Tablet' },
      { width: 1024, name: 'Small Desktop' },
      { width: 1200, name: 'Large Desktop' }
    ];
    
    for (const breakpoint of breakpoints) {
      await page.setViewportSize({ width: breakpoint.width, height: 800 });
      await page.waitForTimeout(300);
      
      // Verificar que no hay elementos que se salgan del viewport
      const overflowElements = await page.evaluate((viewportWidth) => {
        const elements = document.querySelectorAll('*');
        const overflowing = [];
        
        elements.forEach(el => {
          const rect = el.getBoundingClientRect();
          if (rect.right > viewportWidth + 10) { // 10px de tolerancia
            overflowing.push({
              tag: el.tagName,
              class: el.className,
              right: rect.right
            });
          }
        });
        
        return overflowing;
      }, breakpoint.width);
      
      // Reportar elementos que se salen del viewport
      if (overflowElements.length > 0) {
        console.warn(`Elementos que se salen del viewport en ${breakpoint.name} (${breakpoint.width}px):`, overflowElements);
      }
      
      // No debe haber más de 2 elementos menores que se salgan (tolerancia para elementos decorativos)
      expect(overflowElements.length).toBeLessThanOrEqual(2);
    }
  });
});