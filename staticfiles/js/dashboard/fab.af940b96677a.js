/* ============================================
   🎭 FLOATING ACTION BUTTON - ECOPUNTOS
   ============================================ */

class FloatingActionButton {
    constructor() {
        this.fabContainer = null;
        this.isOpen = false;
        this.options = [];
        this.currentTheme = localStorage.getItem('ecopuntos_theme') || 'light';
        
        this.init();
    }

    init() {
        this.createFAB();
        this.attachEvents();
        this.loadTheme();
        
        console.log('🎭 FAB System initialized');
    }

    createFAB() {
        // Crear container principal del FAB
        this.fabContainer = document.createElement('div');
        this.fabContainer.className = 'fab-container';
        this.fabContainer.innerHTML = this.getFABHTML();
        
        document.body.appendChild(this.fabContainer);
        
        // Referencias a elementos
        this.fabMain = this.fabContainer.querySelector('.fab-main');
        this.fabOptions = this.fabContainer.querySelectorAll('.fab-option');
        this.fabOverlay = this.fabContainer.querySelector('.fab-overlay');
    }

    getFABHTML() {
        return `
            <!-- FAB Overlay -->
            <div class="fab-overlay"></div>
            
            <!-- Botón principal del FAB -->
            <button class="fab-main" aria-label="Acciones rápidas">
                <i class="fas fa-plus fab-icon"></i>
            </button>
            
            <!-- Opciones del FAB -->
            <div class="fab-options">
                <!-- Capturar Foto -->
                <button class="fab-option" data-action="camera" aria-label="Tomar foto">
                    <i class="fas fa-camera"></i>
                    <span class="fab-tooltip">Foto</span>
                </button>
                
                <!-- Cambiar Tema -->
                <button class="fab-option" data-action="theme" aria-label="Cambiar tema">
                    <i class="fas fa-palette"></i>
                    <span class="fab-tooltip">Tema</span>
                </button>
                
                <!-- Soporte -->
                <button class="fab-option" data-action="support" aria-label="Soporte">
                    <i class="fas fa-headset"></i>
                    <span class="fab-tooltip">Ayuda</span>
                </button>
                
                <!-- Configuración -->
                <button class="fab-option" data-action="settings" aria-label="Configuración">
                    <i class="fas fa-cog"></i>
                    <span class="fab-tooltip">Config</span>
                </button>
            </div>
        `;
    }

    attachEvents() {
        if (this.fabMain) {
            this.fabMain.addEventListener('click', () => this.toggleFAB());
        }
        
        if (this.fabOverlay) {
            this.fabOverlay.addEventListener('click', () => this.closeFAB());
        }
        
        this.fabOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleAction(action);
            });
        });
        
        // Cerrar FAB con tecla Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeFAB();
            }
        });
        
        // Cerrar FAB al hacer scroll
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            if (this.isOpen) {
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    this.closeFAB();
                }, 150);
            }
        });
    }

    toggleFAB() {
        if (this.isOpen) {
            this.closeFAB();
        } else {
            this.openFAB();
        }
    }

    openFAB() {
        this.isOpen = true;
        this.fabContainer.classList.add('fab-open');
        
        // Cambiar icono principal
        const icon = this.fabMain.querySelector('.fab-icon');
        if (icon) {
            icon.className = 'fas fa-times fab-icon';
        }
        
        // Animar opciones con delay
        this.fabOptions.forEach((option, index) => {
            setTimeout(() => {
                option.classList.add('fab-option-visible');
            }, index * 50);
        });
        
        // Mostrar overlay
        this.fabOverlay.style.opacity = '1';
        this.fabOverlay.style.visibility = 'visible';
        
        // Analytics
        this.trackEvent('fab_opened');
        
        console.log('🎭 FAB opened');
    }

    closeFAB() {
        this.isOpen = false;
        this.fabContainer.classList.remove('fab-open');
        
        // Cambiar icono principal
        const icon = this.fabMain.querySelector('.fab-icon');
        if (icon) {
            icon.className = 'fas fa-plus fab-icon';
        }
        
        // Ocultar opciones
        this.fabOptions.forEach(option => {
            option.classList.remove('fab-option-visible');
        });
        
        // Ocultar overlay
        this.fabOverlay.style.opacity = '0';
        this.fabOverlay.style.visibility = 'hidden';
        
        // Analytics
        this.trackEvent('fab_closed');
        
        console.log('🎭 FAB closed');
    }

    handleAction(action) {
        this.closeFAB();
        
        switch (action) {
            case 'camera':
                this.openCamera();
                break;
            case 'theme':
                this.toggleTheme();
                break;
            case 'support':
                this.openSupport();
                break;
            case 'settings':
                this.openSettings();
                break;
            default:
                console.log('Unknown FAB action:', action);
        }
        
        // Analytics
        this.trackEvent('fab_action', { action });
    }

    openCamera() {
        // Verificar si el dispositivo tiene cámara
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            this.showCameraModal();
        } else {
            this.showMessage('Cámara no disponible en este dispositivo', 'warning');
        }
    }

    showCameraModal() {
        const modal = document.createElement('div');
        modal.className = 'camera-modal';
        modal.innerHTML = `
            <div class="camera-modal-content">
                <div class="camera-modal-header">
                    <h5>📸 Capturar Imagen</h5>
                    <button class="camera-modal-close">&times;</button>
                </div>
                <div class="camera-modal-body">
                    <video id="cameraVideo" autoplay playsinline></video>
                    <canvas id="cameraCanvas" style="display: none;"></canvas>
                    <div class="camera-controls">
                        <button id="captureBtn" class="btn btn-primary">
                            <i class="fas fa-camera me-2"></i>Capturar
                        </button>
                        <button id="cancelCameraBtn" class="btn btn-secondary">
                            <i class="fas fa-times me-2"></i>Cancelar
                        </button>
                    </div>
                    <div id="capturedImagePreview" style="display: none;">
                        <img id="previewImg" alt="Vista previa">
                        <div class="preview-controls">
                            <button id="retakeBtn" class="btn btn-outline-secondary">
                                <i class="fas fa-redo me-2"></i>Repetir
                            </button>
                            <button id="savePhotoBtn" class="btn btn-success">
                                <i class="fas fa-save me-2"></i>Guardar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        this.initCameraModal(modal);
    }

    initCameraModal(modal) {
        const video = modal.querySelector('#cameraVideo');
        const canvas = modal.querySelector('#cameraCanvas');
        const captureBtn = modal.querySelector('#captureBtn');
        const closeBtn = modal.querySelector('.camera-modal-close');
        const cancelBtn = modal.querySelector('#cancelCameraBtn');
        
        let stream = null;
        
        // Iniciar cámara
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(mediaStream => {
                stream = mediaStream;
                video.srcObject = stream;
            })
            .catch(err => {
                console.error('Error accessing camera:', err);
                this.showMessage('No se pudo acceder a la cámara', 'danger');
                modal.remove();
            });
        
        // Capturar imagen
        captureBtn.addEventListener('click', () => {
            this.captureImage(video, canvas, modal);
        });
        
        // Cerrar modal
        const closeModal = () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            modal.remove();
        };
        
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // Cerrar con Escape
        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', handleKeydown);
            }
        };
        document.addEventListener('keydown', handleKeydown);
    }

    captureImage(video, canvas, modal) {
        const context = canvas.getContext('2d');
        
        // Configurar canvas con el tamaño del video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Dibujar frame actual del video en el canvas
        context.drawImage(video, 0, 0);
        
        // Convertir a imagen
        const imageDataUrl = canvas.toDataURL('image/jpeg', 0.8);
        
        // Mostrar preview
        const preview = modal.querySelector('#capturedImagePreview');
        const previewImg = modal.querySelector('#previewImg');
        const videoContainer = video.parentElement;
        
        previewImg.src = imageDataUrl;
        video.style.display = 'none';
        modal.querySelector('.camera-controls').style.display = 'none';
        preview.style.display = 'block';
        
        // Manejar botones del preview
        modal.querySelector('#retakeBtn').addEventListener('click', () => {
            video.style.display = 'block';
            modal.querySelector('.camera-controls').style.display = 'flex';
            preview.style.display = 'none';
        });
        
        modal.querySelector('#savePhotoBtn').addEventListener('click', () => {
            this.savePhoto(imageDataUrl);
            modal.remove();
        });
        
        // Analytics
        this.trackEvent('photo_captured');
    }

    savePhoto(imageDataUrl) {
        // Crear enlace de descarga
        const link = document.createElement('a');
        link.download = `ecopuntos-${Date.now()}.jpg`;
        link.href = imageDataUrl;
        link.click();
        
        this.showMessage('Foto guardada exitosamente', 'success');
        
        // Analytics
        this.trackEvent('photo_saved');
    }

    toggleTheme() {
        const themes = ['light', 'dark', 'auto'];
        const currentIndex = themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.currentTheme = themes[nextIndex];
        
        this.applyTheme(this.currentTheme);
        localStorage.setItem('ecopuntos_theme', this.currentTheme);
        
        this.showMessage(`Tema cambiado a: ${this.getThemeName(this.currentTheme)}`, 'info');
        
        // Analytics
        this.trackEvent('theme_changed', { theme: this.currentTheme });
    }

    applyTheme(theme) {
        const body = document.body;
        
        // Remover clases de tema anteriores
        body.classList.remove('theme-light', 'theme-dark', 'theme-auto');
        
        if (theme === 'auto') {
            // Usar preferencia del sistema
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            body.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
            body.classList.add('theme-auto');
        } else {
            body.setAttribute('data-theme', theme);
            body.classList.add(`theme-${theme}`);
        }
        
        // Actualizar favicon según el tema
        this.updateFavicon(theme);
    }

    updateFavicon(theme) {
        const favicon = document.querySelector('link[rel="icon"]');
        if (favicon) {
            const isDark = theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
            favicon.href = `/static/img/favicon-${isDark ? 'dark' : 'light'}.png`;
        }
    }

    getThemeName(theme) {
        const names = {
            'light': 'Claro',
            'dark': 'Oscuro',
            'auto': 'Automático'
        };
        return names[theme] || theme;
    }

    loadTheme() {
        this.applyTheme(this.currentTheme);
        
        // Escuchar cambios en la preferencia del sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (this.currentTheme === 'auto') {
                this.applyTheme('auto');
            }
        });
    }

    openSupport() {
        window.open('/soporte/', '_blank');
        this.trackEvent('support_opened');
    }

    openSettings() {
        window.location.href = '/mi-cuenta/';
        this.trackEvent('settings_opened');
    }

    showMessage(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fab-toast fab-toast-${type}`;
        toast.innerHTML = `
            <div class="fab-toast-content">
                <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animar entrada
        setTimeout(() => toast.classList.add('fab-toast-show'), 10);
        
        // Remover después de 3 segundos
        setTimeout(() => {
            toast.classList.remove('fab-toast-show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'danger': 'times-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    trackEvent(eventName, data = {}) {
        if (window.ecoAnalytics) {
            window.ecoAnalytics.trackEvent(`fab_${eventName}`, data);
        }
    }

    // Métodos públicos
    addOption(option) {
        this.options.push(option);
        // Recrear FAB con nueva opción
        this.createFAB();
    }

    removeOption(actionName) {
        this.options = this.options.filter(opt => opt.action !== actionName);
        this.createFAB();
    }

    isOpened() {
        return this.isOpen;
    }

    forceClose() {
        this.closeFAB();
    }

    getCurrentTheme() {
        return this.currentTheme;
    }

    setTheme(theme) {
        if (['light', 'dark', 'auto'].includes(theme)) {
            this.currentTheme = theme;
            this.applyTheme(theme);
            localStorage.setItem('ecopuntos_theme', theme);
        }
    }
}

// CSS dinámico para el FAB
const fabStyles = `
.fab-container {
    position: fixed;
    bottom: var(--fab-bottom, 30px);
    right: var(--fab-right, 30px);
    z-index: var(--z-fixed);
    font-family: var(--font-family-primary);
}

.fab-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.3);
    opacity: 0;
    visibility: hidden;
    transition: var(--transition-normal);
    z-index: -1;
    backdrop-filter: blur(2px);
}

.fab-main {
    width: var(--fab-size, 60px);
    height: var(--fab-size, 60px);
    border-radius: var(--border-radius-full);
    background: var(--fab-bg, var(--bg-gradient-main));
    border: none;
    color: var(--text-white);
    font-size: var(--font-size-xl);
    cursor: pointer;
    box-shadow: var(--fab-shadow);
    transition: var(--transition-normal);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    z-index: 2;
}

.fab-main:hover {
    transform: scale(1.1);
    box-shadow: var(--shadow-xl);
}

.fab-main:active {
    transform: scale(0.95);
}

.fab-icon {
    transition: var(--transition-normal);
}

.fab-open .fab-main {
    background: var(--danger);
}

.fab-options {
    position: absolute;
    bottom: calc(100% + 15px);
    right: 0;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

.fab-option {
    width: 48px;
    height: 48px;
    border-radius: var(--border-radius-full);
    background: var(--bg-card);
    border: 2px solid var(--border-color);
    color: var(--text-primary);
    font-size: var(--font-size-lg);
    cursor: pointer;
    box-shadow: var(--shadow-md);
    transition: var(--transition-normal);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transform: scale(0.8) translateX(20px);
    visibility: hidden;
    position: relative;
}

.fab-option-visible {
    opacity: 1;
    transform: scale(1) translateX(0);
    visibility: visible;
}

.fab-option:hover {
    background: var(--primary);
    color: var(--text-white);
    border-color: var(--primary);
    transform: scale(1.05);
}

.fab-tooltip {
    position: absolute;
    right: calc(100% + 10px);
    top: 50%;
    transform: translateY(-50%);
    background: var(--text-primary);
    color: var(--bg-primary);
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--border-radius-sm);
    font-size: var(--font-size-xs);
    white-space: nowrap;
    opacity: 0;
    visibility: hidden;
    transition: var(--transition-fast);
    font-weight: var(--font-weight-medium);
}

.fab-option:hover .fab-tooltip {
    opacity: 1;
    visibility: visible;
}

/* Camera Modal */
.camera-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.9);
    z-index: var(--z-modal);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-md);
}

.camera-modal-content {
    background: var(--bg-card);
    border-radius: var(--border-radius-lg);
    max-width: 500px;
    width: 100%;
    max-height: 90vh;
    overflow: hidden;
    box-shadow: var(--shadow-xl);
}

.camera-modal-header {
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.camera-modal-header h5 {
    margin: 0;
    color: var(--text-primary);
    font-weight: var(--font-weight-semibold);
}

.camera-modal-close {
    background: none;
    border: none;
    font-size: var(--font-size-xl);
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--border-radius-sm);
    transition: var(--transition-fast);
}

.camera-modal-close:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
}

.camera-modal-body {
    padding: var(--spacing-lg);
}

#cameraVideo {
    width: 100%;
    height: 300px;
    object-fit: cover;
    border-radius: var(--border-radius-sm);
    background: #000;
}

.camera-controls {
    display: flex;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
    justify-content: center;
}

#capturedImagePreview img {
    width: 100%;
    height: 300px;
    object-fit: cover;
    border-radius: var(--border-radius-sm);
}

.preview-controls {
    display: flex;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
    justify-content: center;
}

/* Toast Messages */
.fab-toast {
    position: fixed;
    bottom: 100px;
    right: var(--spacing-lg);
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-md);
    box-shadow: var(--shadow-lg);
    padding: var(--spacing-md);
    z-index: var(--z-max);
    transform: translateY(100%);
    opacity: 0;
    transition: var(--transition-normal);
    max-width: 300px;
}

.fab-toast-show {
    transform: translateY(0);
    opacity: 1;
}

.fab-toast-content {
    display: flex;
    align-items: center;
    color: var(--text-primary);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
}

.fab-toast-success {
    border-left: 4px solid var(--success);
}

.fab-toast-warning {
    border-left: 4px solid var(--warning);
}

.fab-toast-danger {
    border-left: 4px solid var(--danger);
}

.fab-toast-info {
    border-left: 4px solid var(--info);
}

/* Responsive */
@media (max-width: 767.98px) {
    .fab-container {
        bottom: 20px;
        right: 20px;
    }
    
    .fab-main {
        width: 50px;
        height: 50px;
        font-size: var(--font-size-lg);
    }
    
    .fab-option {
        width: 42px;
        height: 42px;
        font-size: var(--font-size-base);
    }
    
    .camera-modal-content {
        margin: var(--spacing-sm);
        max-height: calc(100vh - 2rem);
    }
    
    #cameraVideo,
    #capturedImagePreview img {
        height: 250px;
    }
    
    .fab-toast {
        right: var(--spacing-sm);
        left: var(--spacing-sm);
        max-width: none;
    }
}
`;

// Inyectar estilos
const fabStyleSheet = document.createElement('style');
fabStyleSheet.textContent = fabStyles;
document.head.appendChild(fabStyleSheet);

// Inicialización automática
document.addEventListener('DOMContentLoaded', function() {
    window.fab = new FloatingActionButton();
});

// Exportar para uso global
window.FloatingActionButton = FloatingActionButton;