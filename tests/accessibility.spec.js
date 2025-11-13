const { test, expect } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright').default;

/**
 * Pruebas de Accesibilidad para EcoPuntos
 * Utilizan axe-core para verificar estándares WCAG
 */

test.describe('Pruebas de Accesibilidad', () => {
  
  test('Página de inicio - Accesibilidad completa', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('Página de login - Accesibilidad de formularios', async ({ page }) => {
    await page.goto('/iniciosesion/');
    await page.waitForLoadState('networkidle');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('Página de registro - Accesibilidad de formularios', async ({ page }) => {
    await page.goto('/registrate/');
    await page.waitForLoadState('networkidle');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('Navegación por teclado - Elementos interactivos', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verificar que se puede navegar con Tab
    await page.keyboard.press('Tab');
    
    // Obtener el elemento enfocado
    let focusedElement = await page.evaluate(() => {
      const focused = document.activeElement;
      return {
        tagName: focused.tagName,
        type: focused.type,
        role: focused.getAttribute('role'),
        ariaLabel: focused.getAttribute('aria-label'),
        tabIndex: focused.tabIndex
      };
    });
    
    // Verificar que hay un elemento enfocado
    expect(focusedElement.tagName).toBeDefined();
    
    // Continuar navegando y verificar que el foco es visible
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      
      const currentFocus = await page.evaluate(() => {
        const focused = document.activeElement;
        const styles = window.getComputedStyle(focused);
        return {
          tagName: focused.tagName,
          outline: styles.outline,
          outlineWidth: styles.outlineWidth,
          boxShadow: styles.boxShadow,
          border: styles.border
        };
      });
      
      // Verificar que el elemento enfocado tiene algún indicador visual
      const hasFocusIndicator = 
        currentFocus.outline !== 'none' ||
        currentFocus.outlineWidth !== '0px' ||
        currentFocus.boxShadow !== 'none' ||
        currentFocus.border.includes('rgb');
      
      if (currentFocus.tagName !== 'BODY') {
        expect(hasFocusIndicator).toBeTruthy();
      }
    }
  });
  
  test('Contraste de colores - Elementos de texto', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Usar axe-core específicamente para contraste
    const contrastResults = await new AxeBuilder({ page })
      .withRules(['color-contrast'])
      .analyze();
    
    expect(contrastResults.violations).toEqual([]);
  });
  
  test('Etiquetas de formulario - Asociación correcta', async ({ page }) => {
    await page.goto('/iniciosesion/');
    await page.waitForLoadState('networkidle');
    
    // Verificar que todos los inputs tienen labels asociados
    const inputsWithoutLabels = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea, select');
      const problematicInputs = [];
      
      inputs.forEach(input => {
        const hasLabel = 
          input.labels && input.labels.length > 0 ||
          input.getAttribute('aria-label') ||
          input.getAttribute('aria-labelledby') ||
          input.getAttribute('title');
        
        if (!hasLabel) {
          problematicInputs.push({
            tagName: input.tagName,
            type: input.type,
            id: input.id,
            name: input.name,
            placeholder: input.placeholder
          });
        }
      });
      
      return problematicInputs;
    });
    
    expect(inputsWithoutLabels).toEqual([]);
  });
  
  test('Imágenes - Texto alternativo', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const imagesWithoutAlt = await page.evaluate(() => {
      const images = document.querySelectorAll('img');
      const problematicImages = [];
      
      images.forEach(img => {
        const hasAlt = 
          img.getAttribute('alt') !== null ||
          img.getAttribute('aria-label') ||
          img.getAttribute('role') === 'presentation' ||
          img.getAttribute('role') === 'none';
        
        if (!hasAlt) {
          problematicImages.push({
            src: img.src,
            className: img.className,
            id: img.id
          });
        }
      });
      
      return problematicImages;
    });
    
    // Permitir hasta 2 imágenes decorativas sin alt (tolerancia)
    expect(imagesWithoutAlt.length).toBeLessThanOrEqual(2);
  });
  
  test('Estructura semántica - Encabezados jerárquicos', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const headingStructure = await page.evaluate(() => {
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      const structure = [];
      
      headings.forEach(heading => {
        structure.push({
          level: parseInt(heading.tagName.charAt(1)),
          text: heading.textContent.trim().substring(0, 50),
          hasContent: heading.textContent.trim().length > 0
        });
      });
      
      return structure;
    });
    
    // Verificar que hay al menos un H1
    const h1Count = headingStructure.filter(h => h.level === 1).length;
    expect(h1Count).toBeGreaterThanOrEqual(1);
    expect(h1Count).toBeLessThanOrEqual(1); // Solo un H1 por página
    
    // Verificar que todos los encabezados tienen contenido
    headingStructure.forEach(heading => {
      expect(heading.hasContent).toBeTruthy();
    });
    
    // Verificar jerarquía (no saltar niveles)
    for (let i = 1; i < headingStructure.length; i++) {
      const current = headingStructure[i];
      const previous = headingStructure[i - 1];
      
      // No se debe saltar más de un nivel
      if (current.level > previous.level) {
        expect(current.level - previous.level).toBeLessThanOrEqual(1);
      }
    }
  });
  
  test('ARIA - Roles y propiedades', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Usar axe-core para verificar ARIA
    const ariaResults = await new AxeBuilder({ page })
      .withRules(['aria-valid-attr', 'aria-valid-attr-value', 'aria-roles'])
      .analyze();
    
    expect(ariaResults.violations).toEqual([]);
  });
  
  test('Elementos interactivos - Tamaño mínimo táctil', async ({ page }) => {
    // Configurar viewport móvil
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const smallInteractiveElements = await page.evaluate(() => {
      const interactiveElements = document.querySelectorAll(
        'button, a, input[type="button"], input[type="submit"], [role="button"], [tabindex="0"]'
      );
      
      const smallElements = [];
      
      interactiveElements.forEach(element => {
        const rect = element.getBoundingClientRect();
        const isVisible = rect.width > 0 && rect.height > 0;
        
        if (isVisible && (rect.width < 44 || rect.height < 44)) {
          smallElements.push({
            tagName: element.tagName,
            className: element.className,
            width: rect.width,
            height: rect.height,
            text: element.textContent.trim().substring(0, 30)
          });
        }
      });
      
      return smallElements;
    });
    
    // Permitir hasta 3 elementos pequeños (iconos, etc.)
    expect(smallInteractiveElements.length).toBeLessThanOrEqual(3);
  });
  
  test('Formularios - Estados de error accesibles', async ({ page }) => {
    await page.goto('/iniciosesion/');
    await page.waitForLoadState('networkidle');
    
    // Intentar enviar formulario vacío para generar errores
    const submitButton = page.locator('input[type="submit"], button[type="submit"]');
    if (await submitButton.count() > 0) {
      await submitButton.click();
      await page.waitForTimeout(1000);
      
      // Verificar que los errores son accesibles
      const errorAccessibility = await page.evaluate(() => {
        const errorElements = document.querySelectorAll('.error, .invalid, [aria-invalid="true"]');
        const errors = [];
        
        errorElements.forEach(error => {
          const hasAriaDescribedBy = error.getAttribute('aria-describedby');
          const hasAriaLabel = error.getAttribute('aria-label');
          const hasRole = error.getAttribute('role');
          
          errors.push({
            hasAriaDescribedBy: !!hasAriaDescribedBy,
            hasAriaLabel: !!hasAriaLabel,
            hasRole: !!hasRole,
            text: error.textContent.trim().substring(0, 50)
          });
        });
        
        return errors;
      });
      
      // Si hay errores, deben ser accesibles
      errorAccessibility.forEach(error => {
        const isAccessible = error.hasAriaDescribedBy || error.hasAriaLabel || error.hasRole;
        if (error.text.length > 0) {
          expect(isAccessible).toBeTruthy();
        }
      });
    }
  });
  
  test('Accesibilidad móvil - Orientación y zoom', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verificar que el contenido es accesible en orientación vertical
    const verticalAccessibility = await new AxeBuilder({ page })
      .withTags(['wcag21aa'])
      .analyze();
    
    expect(verticalAccessibility.violations).toEqual([]);
    
    // Cambiar a orientación horizontal
    await page.setViewportSize({ width: 667, height: 375 });
    await page.waitForTimeout(500);
    
    // Verificar que el contenido sigue siendo accesible
    const horizontalAccessibility = await new AxeBuilder({ page })
      .withTags(['wcag21aa'])
      .analyze();
    
    expect(horizontalAccessibility.violations).toEqual([]);
  });
});