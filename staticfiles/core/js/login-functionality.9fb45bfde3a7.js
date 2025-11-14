// Funcionalidades modernas para el inicio de sesión
class LoginManager {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.usernameInput = document.getElementById('username');
        this.passwordInput = document.getElementById('password');
        this.togglePasswordBtn = document.getElementById('togglePassword');
        this.loginBtn = document.getElementById('loginBtn');
        this.rememberCheckbox = document.getElementById('rememberMe');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupValidation();
        this.setupPasswordToggle();
        this.setupFormSubmission();
        this.loadRememberedCredentials();
        this.setupAccessibility();
        this.setupProgressiveEnhancement();
    }

    setupEventListeners() {
        // Validación en tiempo real
        this.usernameInput?.addEventListener('input', (e) => this.validateField(e.target));
        this.usernameInput?.addEventListener('blur', (e) => this.validateField(e.target));
        this.passwordInput?.addEventListener('input', (e) => this.validateField(e.target));
        this.passwordInput?.addEventListener('blur', (e) => this.validateField(e.target));
        
        // Toggle de contraseña
        this.togglePasswordBtn?.addEventListener('click', () => this.togglePasswordVisibility());
        
        // Envío del formulario
        this.form?.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Recordar credenciales
        this.rememberCheckbox?.addEventListener('change', () => this.handleRememberMe());
        
        // Atajos de teclado
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Auto-dismiss de alertas
        this.setupAlertAutoDismiss();
    }

    setupValidation() {
        // Reglas de validación
        this.validationRules = {
            username: {
                required: true,
                minLength: 3,
                pattern: /^[a-zA-Z0-9._-]+$/,
                message: 'El nombre de usuario debe tener al menos 3 caracteres y solo puede contener letras, números, puntos, guiones y guiones bajos.'
            },
            password: {
                required: true,
                minLength: 6,
                message: 'La contraseña debe tener al menos 6 caracteres.'
            }
        };
    }

    validateField(field) {
        const fieldName = field.name || field.id;
        const value = field.value.trim();
        const rules = this.validationRules[fieldName];
        
        if (!rules) return true;
        
        let isValid = true;
        let errorMessage = '';
        
        // Validación requerida
        if (rules.required && !value) {
            isValid = false;
            errorMessage = `Este campo es obligatorio.`;
        }
        
        // Validación de longitud mínima
        if (isValid && rules.minLength && value.length < rules.minLength) {
            isValid = false;
            errorMessage = `Debe tener al menos ${rules.minLength} caracteres.`;
        }
        
        // Validación de patrón
        if (isValid && rules.pattern && !rules.pattern.test(value)) {
            isValid = false;
            errorMessage = rules.message;
        }
        
        this.updateFieldValidation(field, isValid, errorMessage);
        this.updateFormState();
        
        return isValid;
    }

    updateFieldValidation(field, isValid, errorMessage) {
        const fieldContainer = field.closest('.form-group');
        const feedback = fieldContainer?.querySelector('.invalid-feedback, .valid-feedback');
        
        // Remover clases anteriores
        field.classList.remove('valid', 'invalid');
        
        if (field.value.trim()) {
            if (isValid) {
                field.classList.add('valid');
                if (feedback) {
                    feedback.className = 'valid-feedback';
                    feedback.textContent = '✓ Válido';
                }
            } else {
                field.classList.add('invalid');
                if (feedback) {
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = errorMessage;
                } else {
                    // Crear elemento de feedback si no existe
                    const newFeedback = document.createElement('div');
                    newFeedback.className = 'invalid-feedback';
                    newFeedback.textContent = errorMessage;
                    fieldContainer?.appendChild(newFeedback);
                }
            }
        } else {
            // Campo vacío
            if (feedback) {
                feedback.textContent = '';
            }
        }
    }

    updateFormState() {
        const isFormValid = this.isFormValid();
        if (this.loginBtn) {
            this.loginBtn.disabled = !isFormValid;
        }
    }

    isFormValid() {
        const usernameValid = this.usernameInput ? this.validateField(this.usernameInput) : true;
        const passwordValid = this.passwordInput ? this.validateField(this.passwordInput) : true;
        
        return usernameValid && passwordValid && 
               this.usernameInput?.value.trim() && 
               this.passwordInput?.value.trim();
    }

    setupPasswordToggle() {
        if (!this.togglePasswordBtn || !this.passwordInput) return;
        
        this.togglePasswordBtn.addEventListener('click', () => {
            this.togglePasswordVisibility();
        });
        
        // Accesibilidad con teclado
        this.togglePasswordBtn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.togglePasswordVisibility();
            }
        });
    }

    togglePasswordVisibility() {
        const isPassword = this.passwordInput.type === 'password';
        const icon = this.togglePasswordBtn.querySelector('i');
        
        this.passwordInput.type = isPassword ? 'text' : 'password';
        
        if (icon) {
            icon.className = isPassword ? 'fas fa-eye-slash' : 'fas fa-eye';
        }
        
        // Actualizar aria-label para accesibilidad
        this.togglePasswordBtn.setAttribute('aria-label', 
            isPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'
        );
        
        // Mantener el foco en el input
        this.passwordInput.focus();
    }

    setupFormSubmission() {
        if (!this.form) return;
        
        this.form.addEventListener('submit', (e) => {
            this.handleFormSubmit(e);
        });
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        // Validar formulario completo
        if (!this.isFormValid()) {
            this.showAlert('Por favor, corrige los errores en el formulario.', 'danger');
            return;
        }
        
        // Mostrar estado de carga
        this.setLoadingState(true);
        
        try {
            // Preparar datos del formulario
            const formData = new FormData(this.form);
            
            // Manejar "Recordarme"
            if (this.rememberCheckbox?.checked) {
                this.saveCredentials();
            } else {
                this.clearSavedCredentials();
            }
            
            // Enviar formulario
            const response = await fetch(this.form.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json().catch(() => null);
                
                if (data && data.success) {
                    this.showAlert('¡Inicio de sesión exitoso! Redirigiendo...', 'success');
                    setTimeout(() => {
                        window.location.href = data.redirect_url || '/dashboard/';
                    }, 1500);
                } else if (data && data.error) {
                    this.showAlert(data.error, 'danger');
                } else {
                    // Fallback para respuestas HTML (redirección del servidor)
                    window.location.reload();
                }
            } else {
                throw new Error('Error en la respuesta del servidor');
            }
            
        } catch (error) {
            console.error('Error en el inicio de sesión:', error);
            this.showAlert('Error de conexión. Por favor, inténtalo de nuevo.', 'danger');
        } finally {
            this.setLoadingState(false);
        }
    }

    setLoadingState(loading) {
        if (!this.loginBtn) return;
        
        if (loading) {
            this.loginBtn.disabled = true;
            this.loginBtn.classList.add('loading');
            const spinner = this.loginBtn.querySelector('.spinner');
            const btnText = this.loginBtn.querySelector('.btn-text');
            
            if (spinner) spinner.style.display = 'inline-block';
            if (btnText) btnText.textContent = 'Iniciando sesión...';
        } else {
            this.loginBtn.disabled = false;
            this.loginBtn.classList.remove('loading');
            const spinner = this.loginBtn.querySelector('.spinner');
            const btnText = this.loginBtn.querySelector('.btn-text');
            
            if (spinner) spinner.style.display = 'none';
            if (btnText) btnText.textContent = 'Iniciar Sesión';
        }
    }

    getCSRFToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }

    showAlert(message, type = 'info') {
        // Remover alertas existentes
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        // Crear nueva alerta
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
        `;
        
        // Insertar antes del formulario
        const formContainer = this.form?.parentElement;
        if (formContainer) {
            formContainer.insertBefore(alertDiv, this.form);
        }
        
        // Auto-dismiss después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentElement) {
                alertDiv.remove();
            }
        }, 5000);
    }

    setupAlertAutoDismiss() {
        // Auto-dismiss para alertas existentes
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                if (alert.parentElement) {
                    alert.style.opacity = '0';
                    alert.style.transform = 'translateY(-20px)';
                    setTimeout(() => alert.remove(), 300);
                }
            }, 5000);
        });
    }

    // Funcionalidad "Recordarme"
    saveCredentials() {
        if (!this.usernameInput || !this.rememberCheckbox?.checked) return;
        
        try {
            localStorage.setItem('rememberedUsername', this.usernameInput.value);
            localStorage.setItem('rememberMe', 'true');
        } catch (error) {
            console.warn('No se pudo guardar las credenciales:', error);
        }
    }

    loadRememberedCredentials() {
        try {
            const rememberedUsername = localStorage.getItem('rememberedUsername');
            const rememberMe = localStorage.getItem('rememberMe') === 'true';
            
            if (rememberMe && rememberedUsername && this.usernameInput) {
                this.usernameInput.value = rememberedUsername;
                if (this.rememberCheckbox) {
                    this.rememberCheckbox.checked = true;
                }
                // Enfocar en el campo de contraseña
                if (this.passwordInput) {
                    this.passwordInput.focus();
                }
            }
        } catch (error) {
            console.warn('No se pudo cargar las credenciales guardadas:', error);
        }
    }

    clearSavedCredentials() {
        try {
            localStorage.removeItem('rememberedUsername');
            localStorage.removeItem('rememberMe');
        } catch (error) {
            console.warn('No se pudo limpiar las credenciales:', error);
        }
    }

    handleRememberMe() {
        if (!this.rememberCheckbox?.checked) {
            this.clearSavedCredentials();
        }
    }

    // Atajos de teclado
    handleKeyboardShortcuts(e) {
        // Enter en cualquier campo del formulario
        if (e.key === 'Enter' && e.target.closest('#loginForm')) {
            if (this.isFormValid()) {
                this.form?.requestSubmit();
            }
        }
        
        // Escape para limpiar formulario
        if (e.key === 'Escape' && e.target.closest('#loginForm')) {
            this.clearForm();
        }
    }

    clearForm() {
        if (this.usernameInput) this.usernameInput.value = '';
        if (this.passwordInput) this.passwordInput.value = '';
        if (this.rememberCheckbox) this.rememberCheckbox.checked = false;
        
        // Limpiar validaciones
        const inputs = this.form?.querySelectorAll('.custom-input');
        inputs?.forEach(input => {
            input.classList.remove('valid', 'invalid');
        });
        
        const feedbacks = this.form?.querySelectorAll('.invalid-feedback, .valid-feedback');
        feedbacks?.forEach(feedback => feedback.textContent = '');
        
        this.updateFormState();
        
        // Enfocar en el primer campo
        if (this.usernameInput) this.usernameInput.focus();
    }

    setupAccessibility() {
        // Mejorar la navegación con teclado
        const focusableElements = this.form?.querySelectorAll(
            'input, button, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        focusableElements?.forEach((element, index) => {
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    // Lógica personalizada de navegación si es necesaria
                }
            });
        });
        
        // Anunciar cambios importantes para lectores de pantalla
        this.setupScreenReaderAnnouncements();
    }

    setupScreenReaderAnnouncements() {
        // Crear región live para anuncios
        if (!document.getElementById('sr-announcements')) {
            const announceDiv = document.createElement('div');
            announceDiv.id = 'sr-announcements';
            announceDiv.setAttribute('aria-live', 'polite');
            announceDiv.setAttribute('aria-atomic', 'true');
            announceDiv.style.position = 'absolute';
            announceDiv.style.left = '-10000px';
            announceDiv.style.width = '1px';
            announceDiv.style.height = '1px';
            announceDiv.style.overflow = 'hidden';
            document.body.appendChild(announceDiv);
        }
    }

    announceToScreenReader(message) {
        const announceDiv = document.getElementById('sr-announcements');
        if (announceDiv) {
            announceDiv.textContent = message;
            setTimeout(() => {
                announceDiv.textContent = '';
            }, 1000);
        }
    }

    setupProgressiveEnhancement() {
        // Detectar capacidades del navegador
        this.browserCapabilities = {
            localStorage: this.testLocalStorage(),
            fetch: typeof fetch !== 'undefined',
            intersectionObserver: 'IntersectionObserver' in window
        };
        
        // Aplicar mejoras según las capacidades
        if (this.browserCapabilities.intersectionObserver) {
            this.setupAnimationOnScroll();
        }
    }

    testLocalStorage() {
        try {
            const test = 'test';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (e) {
            return false;
        }
    }

    setupAnimationOnScroll() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        });
        
        const animatedElements = document.querySelectorAll('.login-container');
        animatedElements.forEach(el => observer.observe(el));
    }
}

// Funcionalidad para recuperación de contraseña
class PasswordRecovery {
    constructor() {
        this.modal = document.getElementById('passwordRecoveryModal');
        this.form = document.getElementById('passwordRecoveryForm');
        this.emailInput = document.getElementById('recoveryEmail');
        this.submitBtn = document.getElementById('recoverySubmitBtn');
        
        this.init();
    }

    init() {
        if (!this.form) return;
        
        this.setupEventListeners();
        this.setupValidation();
    }

    setupEventListeners() {
        this.form?.addEventListener('submit', (e) => this.handleSubmit(e));
        this.emailInput?.addEventListener('input', () => this.validateEmail());
        
        // Cerrar modal con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal?.classList.contains('show')) {
                this.closeModal();
            }
        });
    }

    setupValidation() {
        this.emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    }

    validateEmail() {
        if (!this.emailInput) return false;
        
        const email = this.emailInput.value.trim();
        const isValid = this.emailPattern.test(email);
        
        this.emailInput.classList.toggle('valid', isValid && email);
        this.emailInput.classList.toggle('invalid', !isValid && email);
        
        if (this.submitBtn) {
            this.submitBtn.disabled = !isValid;
        }
        
        return isValid;
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        if (!this.validateEmail()) {
            this.showModalAlert('Por favor, ingresa un email válido.', 'danger');
            return;
        }
        
        this.setLoadingState(true);
        
        try {
            const formData = new FormData(this.form);
            
            const response = await fetch('/password-recovery/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showModalAlert('Se ha enviado un enlace de recuperación a tu email.', 'success');
                setTimeout(() => this.closeModal(), 3000);
            } else {
                this.showModalAlert(data.error || 'Error al enviar el email de recuperación.', 'danger');
            }
            
        } catch (error) {
            console.error('Error en recuperación de contraseña:', error);
            this.showModalAlert('Error de conexión. Inténtalo de nuevo.', 'danger');
        } finally {
            this.setLoadingState(false);
        }
    }

    setLoadingState(loading) {
        if (!this.submitBtn) return;
        
        this.submitBtn.disabled = loading;
        this.submitBtn.textContent = loading ? 'Enviando...' : 'Enviar';
    }

    showModalAlert(message, type) {
        const alertContainer = this.modal?.querySelector('.modal-body');
        if (!alertContainer) return;
        
        // Remover alertas existentes
        const existingAlerts = alertContainer.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        // Crear nueva alerta
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
    }

    getCSRFToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfInput ? csrfInput.value : '';
    }

    closeModal() {
        if (this.modal && window.bootstrap) {
            const modalInstance = bootstrap.Modal.getInstance(this.modal);
            modalInstance?.hide();
        }
    }
}

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar gestor de login
    try {
        const loginManager = new LoginManager();
        console.log('Login functionality initialized successfully');
    } catch (error) {
        console.error('Error initializing login manager:', error);
    }
    
    // Configurar tema oscuro/claro
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    function handleThemeChange(e) {
        document.body.classList.toggle('dark-theme', e.matches);
    }
    
    if (prefersDarkScheme.addEventListener) {
        prefersDarkScheme.addEventListener('change', handleThemeChange);
    } else {
        prefersDarkScheme.addListener(handleThemeChange);
    }
    handleThemeChange(prefersDarkScheme);
    
    // Precargar imágenes importantes
    const imagesToPreload = [
        '../img/nature-3294681_1920 (1) (1).jpg',
        '../img/eco.jpg'
    ];
    
    imagesToPreload.forEach(src => {
        const img = new Image();
        img.src = src;
    });
    
    // Configurar service worker si está disponible
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(err => {
            console.log('Service Worker registration failed:', err);
        });
    }
});

// Exportar para uso en otros módulos si es necesario
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LoginManager };
}