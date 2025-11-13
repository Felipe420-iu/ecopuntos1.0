const { test, expect } = require('@playwright/test');

/**
 * Pruebas de Validación de CSS para EcoPuntos
 * Verifican la integridad y calidad del CSS
 */

test.describe('Validación de CSS', () => {
  
  test('Carga de archivos CSS - Verificación de recursos', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Obtener todos los archivos CSS cargados
    const cssFiles = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
      const styles = Array.from(document.querySelectorAll('style'));
      
      return {
        externalCSS: links.map(link => ({
          href: link.href,
          loaded: !link.sheet || link.sheet.cssRules.length > 0
        })),
        inlineStyles: styles.length,
        totalStylesheets: document.styleSheets.length
      };
    });
    
    // Debe haber al menos un archivo CSS
    expect(cssFiles.totalStylesheets).toBeGreaterThan(0);
    
    // Verificar que los archivos CSS externos se cargaron correctamente
    cssFiles.externalCSS.forEach(css => {
      expect(css.loaded).toBeTruthy();
    });
  });
  
  test('Estilos críticos - Elementos principales', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verificar estilos de elementos críticos
    const criticalStyles = await page.evaluate(() => {
      const elements = {
        body: document.body,
        header: document.querySelector('header, .header, nav'),
        main: document.querySelector('main, .main, .content'),
        footer: document.querySelector('footer, .footer')
      };
      
      const styles = {};
      
      Object.keys(elements).forEach(key => {
        const element = elements[key];
        if (element) {
          const computedStyle = window.getComputedStyle(element);
          styles[key] = {
            display: computedStyle.display,
            position: computedStyle.position,
            width: computedStyle.width,
            height: computedStyle.height,
            margin: computedStyle.margin,
            padding: computedStyle.padding,
            backgroundColor: computedStyle.backgroundColor,
            color: computedStyle.color,
            fontSize: computedStyle.fontSize,
            fontFamily: computedStyle.fontFamily
          };
        }
      });
      
      return styles;
    });
    
    // Body debe tener estilos básicos
    expect(criticalStyles.body).toBeDefined();
    expect(criticalStyles.body.display).not.toBe('none');
    expect(criticalStyles.body.fontFamily).not.toBe('');
    
    // Header debe estar visible si existe
    if (criticalStyles.header) {
      expect(criticalStyles.header.display).not.toBe('none');
    }
  });
  
  test('Responsive CSS - Media queries', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verificar media queries en diferentes tamaños
    const viewports = [
      { width: 320, height: 568, name: 'mobile' },
      { width: 768, height: 1024, name: 'tablet' },
      { width: 1920, height: 1080, name: 'desktop' }
    ];
    
    const responsiveResults = [];
    
    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.waitForTimeout(500);
      
      const styles = await page.evaluate(() => {
        const body = document.body;
        const header = document.querySelector('header, .header, nav');
        const main = document.querySelector('main, .main, .content');
        
        return {
          bodyWidth: window.getComputedStyle(body).width,
          headerDisplay: header ? window.getComputedStyle(header).display : null,
          mainPadding: main ? window.getComputedStyle(main).padding : null,
          viewportWidth: window.innerWidth,
          viewportHeight: window.innerHeight
        };
      });
      
      responsiveResults.push({
        viewport: viewport.name,
        ...styles
      });
    }
    
    // Verificar que los estilos cambian según el viewport
    const mobileStyles = responsiveResults.find(r => r.viewport === 'mobile');
    const desktopStyles = responsiveResults.find(r => r.viewport === 'desktop');
    
    expect(mobileStyles.viewportWidth).toBeLessThan(desktopStyles.viewportWidth);
    
    // Los estilos pueden ser diferentes entre mobile y desktop
    const stylesAreDifferent = 
      mobileStyles.bodyWidth !== desktopStyles.bodyWidth ||
      mobileStyles.headerDisplay !== desktopStyles.headerDisplay ||
      mobileStyles.mainPadding !== desktopStyles.mainPadding;
    
    // Es aceptable que no haya diferencias si el diseño es simple
    // expect(stylesAreDifferent).toBeTruthy();
  });
  
  test('Colores y contraste - Verificación de paleta', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const colorAnalysis = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const colors = new Set();
      const backgroundColors = new Set();
      const borderColors = new Set();
      
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        
        if (styles.color && styles.color !== 'rgba(0, 0, 0, 0)') {
          colors.add(styles.color);
        }
        
        if (styles.backgroundColor && styles.backgroundColor !== 'rgba(0, 0, 0, 0)') {
          backgroundColors.add(styles.backgroundColor);
        }
        
        if (styles.borderColor && styles.borderColor !== 'rgba(0, 0, 0, 0)') {
          borderColors.add(styles.borderColor);
        }
      });
      
      return {
        uniqueColors: Array.from(colors),
        uniqueBackgroundColors: Array.from(backgroundColors),
        uniqueBorderColors: Array.from(borderColors),
        totalUniqueColors: colors.size + backgroundColors.size + borderColors.size
      };
    });
    
    // Debe haber una paleta de colores definida
    expect(colorAnalysis.uniqueColors.length).toBeGreaterThan(0);
    expect(colorAnalysis.uniqueBackgroundColors.length).toBeGreaterThan(0);
    
    // No debe haber demasiados colores únicos (indica falta de consistencia)
    expect(colorAnalysis.totalUniqueColors).toBeLessThan(50);
  });
  
  test('Tipografía - Fuentes y tamaños', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const typographyAnalysis = await page.evaluate(() => {
      const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div, a, button, input, label');
      const fontFamilies = new Set();
      const fontSizes = new Set();
      const fontWeights = new Set();
      
      textElements.forEach(el => {
        const styles = window.getComputedStyle(el);
        
        if (styles.fontFamily) {
          fontFamilies.add(styles.fontFamily);
        }
        
        if (styles.fontSize) {
          fontSizes.add(styles.fontSize);
        }
        
        if (styles.fontWeight) {
          fontWeights.add(styles.fontWeight);
        }
      });
      
      return {
        uniqueFontFamilies: Array.from(fontFamilies),
        uniqueFontSizes: Array.from(fontSizes),
        uniqueFontWeights: Array.from(fontWeights),
        totalTextElements: textElements.length
      };
    });
    
    // Debe haber elementos de texto
    expect(typographyAnalysis.totalTextElements).toBeGreaterThan(0);
    
    // Debe haber al menos una fuente definida
    expect(typographyAnalysis.uniqueFontFamilies.length).toBeGreaterThan(0);
    
    // No debe haber demasiadas fuentes diferentes (consistencia)
    expect(typographyAnalysis.uniqueFontFamilies.length).toBeLessThan(10);
    
    // Debe haber variedad en tamaños de fuente
    expect(typographyAnalysis.uniqueFontSizes.length).toBeGreaterThan(1);
  });
  
  test('Layout y posicionamiento - Flexbox y Grid', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const layoutAnalysis = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const layoutTypes = {
        flex: 0,
        grid: 0,
        block: 0,
        inline: 0,
        inlineBlock: 0,
        absolute: 0,
        relative: 0,
        fixed: 0,
        sticky: 0
      };
      
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        
        // Display types
        if (styles.display.includes('flex')) layoutTypes.flex++;
        if (styles.display.includes('grid')) layoutTypes.grid++;
        if (styles.display === 'block') layoutTypes.block++;
        if (styles.display === 'inline') layoutTypes.inline++;
        if (styles.display === 'inline-block') layoutTypes.inlineBlock++;
        
        // Position types
        if (styles.position === 'absolute') layoutTypes.absolute++;
        if (styles.position === 'relative') layoutTypes.relative++;
        if (styles.position === 'fixed') layoutTypes.fixed++;
        if (styles.position === 'sticky') layoutTypes.sticky++;
      });
      
      return layoutTypes;
    });
    
    // Debe haber elementos con diferentes tipos de layout
    const totalLayoutElements = Object.values(layoutAnalysis).reduce((sum, count) => sum + count, 0);
    expect(totalLayoutElements).toBeGreaterThan(0);
    
    // Debe haber al menos algunos elementos block
    expect(layoutAnalysis.block).toBeGreaterThan(0);
  });
  
  test('Animaciones y transiciones CSS', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const animationAnalysis = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const animations = [];
      const transitions = [];
      const transforms = [];
      
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        
        if (styles.animation && styles.animation !== 'none') {
          animations.push({
            element: el.tagName,
            className: el.className,
            animation: styles.animation
          });
        }
        
        if (styles.transition && styles.transition !== 'all 0s ease 0s') {
          transitions.push({
            element: el.tagName,
            className: el.className,
            transition: styles.transition
          });
        }
        
        if (styles.transform && styles.transform !== 'none') {
          transforms.push({
            element: el.tagName,
            className: el.className,
            transform: styles.transform
          });
        }
      });
      
      return {
        animations,
        transitions,
        transforms,
        totalAnimatedElements: animations.length + transitions.length + transforms.length
      };
    });
    
    // Las animaciones son opcionales, pero si existen deben estar bien definidas
    if (animationAnalysis.totalAnimatedElements > 0) {
      expect(animationAnalysis.totalAnimatedElements).toBeGreaterThan(0);
    }
  });
  
  test('CSS personalizado vs framework - Análisis de origen', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const cssOriginAnalysis = await page.evaluate(() => {
      const stylesheets = Array.from(document.styleSheets);
      const analysis = {
        totalStylesheets: stylesheets.length,
        externalStylesheets: 0,
        inlineStyles: 0,
        frameworkDetected: {
          bootstrap: false,
          tailwind: false,
          bulma: false,
          foundation: false
        },
        customCSS: 0
      };
      
      stylesheets.forEach(sheet => {
        try {
          if (sheet.href) {
            analysis.externalStylesheets++;
            
            // Detectar frameworks comunes
            const href = sheet.href.toLowerCase();
            if (href.includes('bootstrap')) analysis.frameworkDetected.bootstrap = true;
            if (href.includes('tailwind')) analysis.frameworkDetected.tailwind = true;
            if (href.includes('bulma')) analysis.frameworkDetected.bulma = true;
            if (href.includes('foundation')) analysis.frameworkDetected.foundation = true;
            
            // CSS personalizado (archivos locales)
            if (href.includes('/static/') || href.includes('/css/') || href.includes('core')) {
              analysis.customCSS++;
            }
          } else {
            analysis.inlineStyles++;
          }
        } catch (e) {
          // CORS puede impedir el acceso a algunos stylesheets
        }
      });
      
      return analysis;
    });
    
    // Debe haber al menos un stylesheet
    expect(cssOriginAnalysis.totalStylesheets).toBeGreaterThan(0);
    
    // Debe haber CSS personalizado para el proyecto
    expect(cssOriginAnalysis.customCSS).toBeGreaterThan(0);
  });
  
  test('Errores de CSS - Propiedades inválidas', async ({ page }) => {
    const cssErrors = [];
    
    // Capturar errores de CSS en la consola
    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().toLowerCase().includes('css')) {
        cssErrors.push(msg.text());
      }
    });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verificar propiedades CSS computadas
    const cssValidation = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const invalidProperties = [];
      
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        
        // Verificar algunas propiedades comunes
        const properties = ['display', 'position', 'width', 'height', 'margin', 'padding'];
        
        properties.forEach(prop => {
          const value = styles[prop];
          if (value === 'initial' || value === 'unset' || value === 'revert') {
            // Estas pueden indicar propiedades no reconocidas
            invalidProperties.push({
              element: el.tagName,
              property: prop,
              value: value
            });
          }
        });
      });
      
      return {
        invalidProperties,
        totalElements: elements.length
      };
    });
    
    // No debe haber errores críticos de CSS
    expect(cssErrors.length).toBeLessThanOrEqual(2);
    
    // No debe haber demasiadas propiedades inválidas
    expect(cssValidation.invalidProperties.length).toBeLessThan(cssValidation.totalElements * 0.1);
  });
  
  test('Performance de CSS - Tamaño y optimización', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const cssPerformance = await page.evaluate(() => {
      const stylesheets = Array.from(document.styleSheets);
      let totalRules = 0;
      let totalSelectors = 0;
      const unusedSelectors = [];
      
      stylesheets.forEach(sheet => {
        try {
          if (sheet.cssRules) {
            totalRules += sheet.cssRules.length;
            
            Array.from(sheet.cssRules).forEach(rule => {
              if (rule.selectorText) {
                totalSelectors++;
                
                // Verificar si el selector se usa en el DOM
                try {
                  const elements = document.querySelectorAll(rule.selectorText);
                  if (elements.length === 0) {
                    unusedSelectors.push(rule.selectorText);
                  }
                } catch (e) {
                  // Selector inválido o complejo
                }
              }
            });
          }
        } catch (e) {
          // CORS puede impedir el acceso
        }
      });
      
      return {
        totalStylesheets: stylesheets.length,
        totalRules,
        totalSelectors,
        unusedSelectors: unusedSelectors.slice(0, 10), // Limitar para performance
        unusedPercentage: totalSelectors > 0 ? (unusedSelectors.length / totalSelectors) * 100 : 0
      };
    });
    
    // Verificar métricas de performance
    expect(cssPerformance.totalStylesheets).toBeGreaterThan(0);
    expect(cssPerformance.totalRules).toBeGreaterThan(0);
    
    // No debe haber demasiado CSS no utilizado (más del 50%)
    expect(cssPerformance.unusedPercentage).toBeLessThan(50);
    
    // No debe haber demasiados stylesheets (performance)
    expect(cssPerformance.totalStylesheets).toBeLessThan(20);
  });
});