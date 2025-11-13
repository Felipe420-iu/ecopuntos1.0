/**
 * Monitor de Sesión - EcoPuntos
 * Verifica periódicamente si la sesión del usuario sigue activa
 * y muestra notificaciones cuando la sesión es cerrada externamente
 */

class SessionMonitor {
    constructor() {
        this.checkInterval = 3000; // Verificar cada 3 segundos
        this.warningShown = false;
        this.sessionClosed = false;
        this.intervalId = null;
        this.startTime = Date.now(); // Tiempo de inicio del monitor
        this.gracePeroid = 5000; // Período de gracia de 5 segundos para sesiones nuevas
        
        console.log('🔍 SessionMonitor inicializado');
        
        // Iniciar monitoreo automáticamente
        this.startMonitoring();
        
        // Detectar actividad del usuario para verificar sesión
        this.bindActivityEvents();
    }
    
    /**
     * Inicia el monitoreo automático de la sesión
     */
    startMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        console.log('🔄 Iniciando verificaciones inmediatas cada 3 segundos');
        
        // Primera verificación inmediata
        this.checkSessionStatus();
        
        // Configurar verificaciones periódicas cada 3 segundos
        this.intervalId = setInterval(() => {
            this.checkSessionStatus();
        }, 3000); // Verificar cada 3 segundos para detección más rápida
    }
    
    /**
     * Detiene el monitoreo de la sesión
     */
    stopMonitoring() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    
    /**
     * Verifica el estado de la sesión mediante AJAX
     */
    async checkSessionStatus() {
        if (this.sessionClosed) {
            return; // Ya se cerró la sesión, no verificar más
        }
        
        console.log('🔍 Verificando estado de sesión...');
        
        try {
            const response = await fetch('/verificar-sesion/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            
            const data = await response.json();
            console.log('📊 Respuesta del servidor:', data);
            
            if (!data.activa) {
                // Verificar si estamos en período de gracia para sesiones nuevas
                const timeSinceStart = Date.now() - this.startTime;
                if (timeSinceStart < this.gracePeroid) {
                    console.log('⏳ Sesión en período de gracia, no cerrar aún');
                    return;
                }
                
                console.log('❌ Sesión cerrada externamente:', data.message);
                this.handleSessionClosed(data.message);
            } else {
                console.log('✅ Sesión activa');
                // Sesión activa, resetear advertencias
                this.warningShown = false;
            }
            
        } catch (error) {
            console.error('❌ Error verificando estado de sesión:', error);
            // En caso de error, verificar más frecuentemente
            setTimeout(() => this.checkSessionStatus(), 5000);
        }
    }
    
    /**
     * Maneja cuando la sesión ha sido cerrada externamente
     */
    handleSessionClosed(message) {
        if (this.sessionClosed) {
            return; // Ya se manejó el cierre
        }
        
        this.sessionClosed = true;
        this.stopMonitoring();
        
        // Bloquear todas las interacciones inmediatamente
        this.blockAllInteractions();
        
        // Mostrar notificación modal
        this.showSessionClosedModal(message);
    }
    
    /**
     * Muestra un modal informando que la sesión fue cerrada
     */
    showSessionClosedModal(message) {
        // Crear modal dinámicamente con z-index muy alto
        const modalHTML = `
            <div class="modal fade session-monitor-modal" id="sessionClosedModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false" style="z-index: 9999;">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content border-0 shadow-lg">
                        <div class="modal-header bg-danger text-white border-0">
                            <h4 class="modal-title w-100 text-center">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                ⚠️ SESIÓN CERRADA POR ADMINISTRADOR ⚠️
                            </h4>
                        </div>
                        <div class="modal-body text-center p-4">
                            <div class="mb-4">
                                <i class="fas fa-sign-out-alt text-danger warning-icon" style="font-size: 4rem;"></i>
                            </div>
                            <h5 class="text-danger mb-3">¡Tu sesión ha sido cerrada!</h5>
                            <p class="fs-6 mb-4">${message}</p>
                            <div class="alert alert-warning" role="alert">
                                <i class="fas fa-info-circle me-2"></i>
                                <strong>IMPORTANTE:</strong> No puedes continuar navegando.<br>
                                Serás redirigido al inicio de sesión en <span id="countdown" class="countdown-text fw-bold">5</span> segundos.
                            </div>
                        </div>
                        <div class="modal-footer border-0 justify-content-center">
                            <button type="button" class="btn btn-danger btn-lg" id="btnRedirectNow">
                                <i class="fas fa-sign-in-alt me-2"></i>
                                Ir al Inicio de Sesión AHORA
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Agregar modal al DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Mostrar modal inmediatamente sin animación para que aparezca más rápido
        const modalElement = document.getElementById('sessionClosedModal');
        modalElement.style.display = 'block';
        modalElement.classList.add('show');
        
        // Agregar event listener al botón DESPUÉS de que se cree el modal
        const btnRedirectNow = document.getElementById('btnRedirectNow');
        if (btnRedirectNow) {
            btnRedirectNow.addEventListener('click', () => {
                console.log('🔘 Botón de redirección clickeado');
                this.redirectToLogin();
            });
        }
        
        // Countdown más rápido (5 segundos en lugar de 10)
        this.startCountdown(5);
    }
    
    /**
     * Inicia el countdown para redirección automática
     */
    startCountdown(seconds = 10) {
        const countdownElement = document.getElementById('countdown');
        
        const countdownInterval = setInterval(() => {
            seconds--;
            if (countdownElement) {
                countdownElement.textContent = seconds;
            }
            
            if (seconds <= 0) {
                clearInterval(countdownInterval);
                this.redirectToLogin();
            }
        }, 1000);
    }
    
    /**
     * Redirige al usuario al inicio de sesión
     */
    redirectToLogin() {
        console.log('🔄 Iniciando redirección al login...');
        
        // Detener el monitoreo
        this.stopMonitoring();
        
        // Determinar la página de inicio de sesión según el tipo de usuario
        const currentPath = window.location.pathname;
        console.log('📍 Ruta actual:', currentPath);
        
        const isAdminPath = currentPath.includes('/admin/') || 
                           currentPath.includes('/paneladmin/') || 
                           currentPath.includes('/usuarioadmin/') ||
                           currentPath.includes('/canjeadmin/') ||
                           currentPath.includes('/estadisticasadmin/');
        
        const loginUrl = isAdminPath ? '/inicioadmin/' : '/iniciosesion/';
        console.log('🎯 URL de redirección:', loginUrl);
        
        // Intentar múltiples métodos de redirección para asegurar que funcione
        try {
            // Método 1: window.location.href
            window.location.href = loginUrl;
            
            // Método 2: window.location.replace (por si el primero falla)
            setTimeout(() => {
                window.location.replace(loginUrl);
            }, 100);
            
            // Método 3: Forzar recarga completa (último recurso)
            setTimeout(() => {
                window.location = loginUrl;
            }, 200);
        } catch (error) {
            console.error('❌ Error redirigiendo:', error);
            // Último intento con top level
            window.top.location.href = loginUrl;
        }
    }
    
    /**
     * Vincula eventos de actividad del usuario para verificaciones adicionales
     */
    bindActivityEvents() {
        // Verificar sesión cuando el usuario hace clic en elementos importantes
        // pero con un throttle para evitar verificaciones excesivas
        let lastActivityCheck = 0;
        const activityThrottle = 60000; // Solo verificar por actividad cada 60 segundos
        
        document.addEventListener('click', (e) => {
            const now = Date.now();
            if (now - lastActivityCheck > activityThrottle) {
                // Solo verificar en botones y enlaces importantes
                if (e.target.matches('button, a[href], .btn')) {
                    console.log('🔍 Verificación por actividad del usuario');
                    this.checkSessionStatus();
                    lastActivityCheck = now;
                }
            }
        });
        
        // Verificar cuando la página regresa del background (pero con throttle)
        let lastVisibilityCheck = 0;
        document.addEventListener('visibilitychange', () => {
            const now = Date.now();
            if (!document.hidden && now - lastVisibilityCheck > activityThrottle) {
                console.log('🔍 Verificación por cambio de visibilidad');
                this.checkSessionStatus();
                lastVisibilityCheck = now;
            }
        });
        
        // Verificar cuando la ventana regresa al foco (pero con throttle)
        let lastFocusCheck = 0;
        window.addEventListener('focus', () => {
            const now = Date.now();
            if (now - lastFocusCheck > activityThrottle) {
                console.log('🔍 Verificación por foco de ventana');
                this.checkSessionStatus();
                lastFocusCheck = now;
            }
        });
    }
    
    /**
     * Método manual para probar el monitor desde la consola
     */
    testSessionCheck() {
        console.log('🧪 Prueba manual del monitor de sesión');
        this.checkSessionStatus();
    }
    
    /**
     * Bloquea todas las interacciones del usuario cuando la sesión es cerrada
     */
    blockAllInteractions() {
        console.log('🚫 Bloqueando todas las interacciones del usuario');
        
        // Crear overlay para bloquear clics
        const overlay = document.createElement('div');
        overlay.id = 'session-blocked-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 9998;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.2rem;
            font-weight: bold;
        `;
        overlay.innerHTML = `
            <div style="text-align: center;">
                <i class="fas fa-exclamation-triangle" style="font-size: 3rem; color: #ffc107; margin-bottom: 1rem;"></i>
                <div>Sesión cerrada por administrador</div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">Redirigiendo...</div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Bloquear navegación del navegador
        this.blockNavigation();
        
        // Interceptar todos los clics y enlaces
        this.interceptAllClicks();
    }
    
    /**
     * Bloquea la navegación del navegador
     */
    blockNavigation() {
        // Prevenir el botón "atrás" del navegador
        window.addEventListener('beforeunload', this.preventNavigation);
        window.addEventListener('popstate', this.preventNavigation);
        
        // Reemplazar la función de navegación
        window.history.pushState = function() {
            console.log('🚫 Navegación bloqueada - sesión cerrada');
        };
        window.history.replaceState = function() {
            console.log('🚫 Navegación bloqueada - sesión cerrada');
        };
    }
    
    /**
     * Intercepta todos los clics en la página
     */
    interceptAllClicks() {
        const clickBlocker = (event) => {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            console.log('🚫 Clic bloqueado - sesión cerrada');
            return false;
        };
        
        // Agregar listener a toda la página con prioridad alta
        document.addEventListener('click', clickBlocker, true);
        document.addEventListener('mousedown', clickBlocker, true);
        document.addEventListener('mouseup', clickBlocker, true);
        document.addEventListener('touchstart', clickBlocker, true);
        document.addEventListener('touchend', clickBlocker, true);
        
        // Bloquear formularios
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', clickBlocker, true);
        });
        
        // Bloquear enlaces específicamente
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            link.addEventListener('click', clickBlocker, true);
            link.style.pointerEvents = 'none';
            link.style.opacity = '0.5';
        });
        
        // Bloquear botones específicamente
        const buttons = document.querySelectorAll('button');
        buttons.forEach(button => {
            button.addEventListener('click', clickBlocker, true);
            button.disabled = true;
            button.style.opacity = '0.5';
        });
    }
    
    /**
     * Previene la navegación
     */
    preventNavigation(event) {
        event.preventDefault();
        console.log('🚫 Navegación bloqueada - sesión cerrada');
        return false;
    }
    
    /**
     * Método manual para probar el monitor desde la consola
     */
    testSessionCheck() {
        console.log('🧪 Prueba manual del monitor de sesión');
        this.checkSessionStatus();
    }
    
    /**
     * Método manual para simular sesión cerrada
     */
    testSessionClosed() {
        console.log('🧪 Simulando sesión cerrada');
        this.handleSessionClosed('Sesión cerrada para prueba');
    }
}

// Inicializar el monitor de sesión solo si el usuario está autenticado
// y no estamos en páginas de login
console.log('🚀 Cargando monitor de sesión...');
console.log('📝 Usuario autenticado:', document.body.dataset.userAuthenticated);
console.log('📍 Ruta actual:', window.location.pathname);

if (document.body.dataset.userAuthenticated === 'true' && 
    !window.location.pathname.includes('/iniciosesion/') && 
    !window.location.pathname.includes('/inicioadmin/')) {
    
    console.log('✅ Iniciando monitor de sesión...');
    window.sessionMonitor = new SessionMonitor();
    
    // Cleanup al salir de la página
    window.addEventListener('beforeunload', () => {
        if (window.sessionMonitor) {
            window.sessionMonitor.stopMonitoring();
        }
    });
} else {
    console.log('❌ Monitor no iniciado - condiciones no cumplidas');
}
