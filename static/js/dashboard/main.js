/* ============================================
   📊 DASHBOARD MAIN - ECOPUNTOS
   ============================================ */

// Import all CSS files in the correct order
import '../css/dashboard/variables.css';
import '../css/dashboard/base.css';
import '../css/dashboard/components.css';
import '../css/dashboard/responsive.css';

// Import JavaScript modules
import { MobileNavigation } from './navigation.js';
import { NotificationSystem } from './navigation.js';
import { FloatingActionButton } from './fab.js';

// Dashboard Main Class
class EcoDashboard {
    constructor() {
        this.modules = {
            mobileNav: null,
            notifications: null,
            fab: null,
            analytics: null
        };
        
        this.isInitialized = false;
        this.loadingState = 'loading';
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing EcoDashboard...');
        
        try {
            // Set loading state
            this.setLoadingState('loading');
            
            // Initialize critical modules first
            await this.initCriticalModules();
            
            // Initialize non-critical modules
            await this.initNonCriticalModules();
            
            // Setup global event listeners
            this.setupGlobalEvents();
            
            // Mark as initialized
            this.isInitialized = true;
            this.setLoadingState('ready');
            
            console.log('✅ EcoDashboard initialized successfully');
            
            // Dispatch ready event
            this.dispatchReadyEvent();
            
        } catch (error) {
            console.error('❌ Error initializing dashboard:', error);
            this.setLoadingState('error');
        }
    }

    async initCriticalModules() {
        // Mobile Navigation
        this.modules.mobileNav = new MobileNavigation();
        
        // Notification System
        this.modules.notifications = new NotificationSystem();
        
        console.log('✅ Critical modules initialized');
    }

    async initNonCriticalModules() {
        // Floating Action Button
        this.modules.fab = new FloatingActionButton();
        
        // Lazy load analytics
        setTimeout(() => this.loadAnalytics(), 2000);
        
        console.log('✅ Non-critical modules initialized');
    }

    async loadAnalytics() {
        try {
            const { EcoAnalytics } = await import('./analytics.js');
            this.modules.analytics = new EcoAnalytics();
            console.log('📊 Analytics module loaded');
        } catch (error) {
            console.warn('Analytics module failed to load:', error);
        }
    }

    setupGlobalEvents() {
        // Performance monitoring
        this.setupPerformanceMonitoring();
        
        // Error handling
        this.setupErrorHandling();
        
        // Visibility API
        this.setupVisibilityAPI();
        
        // Responsive handling
        this.setupResponsiveHandling();
    }

    setupPerformanceMonitoring() {
        // Monitor page load performance
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            console.log(`⚡ Page loaded in ${Math.round(loadTime)}ms`);
            
            // Report to analytics
            if (this.modules.analytics) {
                this.modules.analytics.trackEvent('page_performance', {
                    loadTime: Math.round(loadTime),
                    timestamp: Date.now()
                });
            }
        });
        
        // Monitor LCP (Largest Contentful Paint)
        if ('PerformanceObserver' in window) {
            const lcpObserver = new PerformanceObserver((entryList) => {
                for (const entry of entryList.getEntries()) {
                    console.log('LCP:', Math.round(entry.startTime));
                }
            });
            
            try {
                lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            } catch (e) {
                // LCP not supported
            }
        }
    }

    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            console.error('JavaScript Error:', {
                message: event.message,
                filename: event.filename,
                line: event.lineno,
                column: event.colno,
                stack: event.error?.stack
            });
            
            // Report to analytics
            if (this.modules.analytics) {
                this.modules.analytics.trackEvent('javascript_error', {
                    message: event.message,
                    filename: event.filename,
                    line: event.lineno
                });
            }
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled Promise Rejection:', event.reason);
            
            // Report to analytics
            if (this.modules.analytics) {
                this.modules.analytics.trackEvent('promise_rejection', {
                    reason: event.reason?.toString()
                });
            }
        });
    }

    setupVisibilityAPI() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page is hidden
                console.log('📱 Page hidden');
                
                // Pause non-essential operations
                if (this.modules.notifications) {
                    this.modules.notifications.stopPolling();
                }
            } else {
                // Page is visible
                console.log('👀 Page visible');
                
                // Resume operations
                if (this.modules.notifications) {
                    this.modules.notifications.startPolling();
                }
            }
        });
    }

    setupResponsiveHandling() {
        const mediaQuery = window.matchMedia('(max-width: 768px)');
        
        const handleResponsive = (e) => {
            if (e.matches) {
                // Mobile view
                document.body.classList.add('mobile-view');
                console.log('📱 Switched to mobile view');
            } else {
                // Desktop view
                document.body.classList.remove('mobile-view');
                console.log('🖥️ Switched to desktop view');
                
                // Close mobile sidebar if open
                if (this.modules.mobileNav && this.modules.mobileNav.isOpened()) {
                    this.modules.mobileNav.forceClose();
                }
            }
        };
        
        // Initial check
        handleResponsive(mediaQuery);
        
        // Listen for changes
        mediaQuery.addEventListener('change', handleResponsive);
    }

    setLoadingState(state) {
        this.loadingState = state;
        document.body.setAttribute('data-loading-state', state);
        
        // Update UI based on loading state
        const loadingIndicator = document.querySelector('.loading-indicator');
        if (loadingIndicator) {
            switch (state) {
                case 'loading':
                    loadingIndicator.style.display = 'flex';
                    break;
                case 'ready':
                case 'error':
                    loadingIndicator.style.display = 'none';
                    break;
            }
        }
    }

    dispatchReadyEvent() {
        const event = new CustomEvent('dashboard:ready', {
            detail: {
                modules: this.modules,
                loadTime: performance.now()
            }
        });
        
        document.dispatchEvent(event);
    }

    // Public API methods
    getModule(name) {
        return this.modules[name];
    }

    isReady() {
        return this.isInitialized && this.loadingState === 'ready';
    }

    reload() {
        window.location.reload();
    }

    // Theme management
    setTheme(theme) {
        if (this.modules.fab) {
            this.modules.fab.setTheme(theme);
        }
        
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('ecopuntos_theme', theme);
    }

    getTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    // Notification management
    showNotification(title, message, type = 'info') {
        if (this.modules.notifications) {
            this.modules.notifications.addNotification({
                id: 'local_' + Date.now(),
                tipo: type,
                titulo: title,
                mensaje: message,
                leido: false,
                created_at: new Date().toISOString()
            });
        }
    }

    // Analytics shortcuts
    trackEvent(eventName, data = {}) {
        if (this.modules.analytics) {
            this.modules.analytics.trackEvent(eventName, data);
        }
    }

    trackPageView(page = 'dashboard') {
        if (this.modules.analytics) {
            this.modules.analytics.trackPageView();
        }
    }
}

// Module loader with dependency management
class ModuleLoader {
    constructor() {
        this.loadedModules = new Set();
        this.loadingPromises = new Map();
    }

    async loadModule(moduleName, moduleUrl) {
        if (this.loadedModules.has(moduleName)) {
            return;
        }

        if (this.loadingPromises.has(moduleName)) {
            return this.loadingPromises.get(moduleName);
        }

        const loadingPromise = this.importModule(moduleUrl);
        this.loadingPromises.set(moduleName, loadingPromise);

        try {
            const module = await loadingPromise;
            this.loadedModules.add(moduleName);
            console.log(`✅ Module "${moduleName}" loaded successfully`);
            return module;
        } catch (error) {
            console.error(`❌ Failed to load module "${moduleName}":`, error);
            this.loadingPromises.delete(moduleName);
            throw error;
        }
    }

    async importModule(url) {
        // Dynamic import with retry logic
        let attempts = 0;
        const maxAttempts = 3;

        while (attempts < maxAttempts) {
            try {
                return await import(url);
            } catch (error) {
                attempts++;
                if (attempts >= maxAttempts) {
                    throw error;
                }
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, 1000 * attempts));
            }
        }
    }

    async loadCSS(href) {
        if (document.querySelector(`link[href="${href}"]`)) {
            return; // Already loaded
        }

        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.onload = () => resolve();
            link.onerror = () => reject(new Error(`Failed to load CSS: ${href}`));
            document.head.appendChild(link);
        });
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.ecoDashboard = new EcoDashboard();
    window.moduleLoader = new ModuleLoader();
    
    // Global dashboard API
    window.EcoPuntos = {
        dashboard: window.ecoDashboard,
        moduleLoader: window.moduleLoader,
        
        // Utility methods
        showMessage: (title, message, type) => {
            window.ecoDashboard.showNotification(title, message, type);
        },
        
        trackEvent: (event, data) => {
            window.ecoDashboard.trackEvent(event, data);
        },
        
        setTheme: (theme) => {
            window.ecoDashboard.setTheme(theme);
        },
        
        getTheme: () => {
            return window.ecoDashboard.getTheme();
        }
    };
    
    console.log('🌍 EcoPuntos Global API available');
});

// Export for module systems
export { EcoDashboard, ModuleLoader };