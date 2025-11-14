// Test simple para verificar que el monitor funciona
console.log('🔍 Iniciando test simple del monitor...');

// Función para probar manualmente la verificación de sesión
window.testSessionMonitor = function() {
    console.log('🧪 Ejecutando test manual...');
    
    fetch('/verificar-sesion/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        console.log('📊 Respuesta del test:', data);
        
        if (!data.activa) {
            console.log('❌ Sesión inactiva detectada');
            // Mostrar modal inmediatamente
            showSessionClosedModal(data.message);
        } else {
            console.log('✅ Sesión activa');
        }
    })
    .catch(error => {
        console.error('❌ Error en test:', error);
    });
};

// Función para mostrar el modal de sesión cerrada
function showSessionClosedModal(message) {
    console.log('🚨 Mostrando modal de sesión cerrada');
    
    // Crear modal dinámicamente
    const modalHTML = `
        <div class="modal fade session-monitor-modal" id="testSessionModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg">
                    <div class="modal-header bg-warning text-dark border-0">
                        <h4 class="modal-title w-100 text-center">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Sesión Cerrada por Administrador
                        </h4>
                    </div>
                    <div class="modal-body text-center p-4">
                        <div class="mb-4">
                            <i class="fas fa-sign-out-alt text-warning" style="font-size: 4rem; animation: pulse 2s infinite;"></i>
                        </div>
                        <h5 class="text-warning mb-3">¡Tu sesión ha sido cerrada!</h5>
                        <p class="fs-6 mb-4">${message}</p>
                        <div class="alert alert-info" role="alert">
                            <i class="fas fa-info-circle me-2"></i>
                            Serás redirigido al inicio de sesión en <span id="testCountdown" class="fw-bold text-warning">10</span> segundos.
                        </div>
                    </div>
                    <div class="modal-footer border-0 justify-content-center">
                        <button type="button" class="btn btn-warning btn-lg" onclick="redirectToLogin()">
                            <i class="fas fa-sign-in-alt me-2"></i>
                            Ir al Inicio de Sesión Ahora
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Agregar modal al DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('testSessionModal'));
    modal.show();
    
    // Countdown para redirección automática
    startTestCountdown();
}

// Función para el countdown
function startTestCountdown() {
    let seconds = 10;
    const countdownElement = document.getElementById('testCountdown');
    
    const countdownInterval = setInterval(() => {
        seconds--;
        if (countdownElement) {
            countdownElement.textContent = seconds;
        }
        
        if (seconds <= 0) {
            clearInterval(countdownInterval);
            redirectToLogin();
        }
    }, 1000);
}

// Función para redirigir
function redirectToLogin() {
    console.log('🔄 Redirigiendo al login...');
    const currentPath = window.location.pathname;
    const isAdminPath = currentPath.includes('/admin/') || 
                       currentPath.includes('/paneladmin/') || 
                       currentPath.includes('/usuarioadmin/') ||
                       currentPath.includes('/canjeadmin/') ||
                       currentPath.includes('/estadisticasadmin/');
    
    if (isAdminPath) {
        window.location.href = '/inicioadmin/';
    } else {
        window.location.href = '/iniciosesion/';
    }
}

console.log('✅ Test funciones cargadas. Ejecuta testSessionMonitor() en la consola para probar.');
