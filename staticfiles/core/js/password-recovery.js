class PasswordRecoveryManager {
    constructor() {
        this.currentStep = 1;
        this.userEmail = '';
        this.verificationToken = '';
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateProgressBar();
    }

    bindEvents() {
        // Paso 1: Enviar código por email
        const emailForm = document.getElementById('emailVerificationForm');
        if (emailForm) {
            emailForm.addEventListener('submit', (e) => this.handleEmailSubmit(e));
        }

        // Paso 2: Verificar código
        const codeForm = document.getElementById('codeVerificationForm');
        if (codeForm) {
            codeForm.addEventListener('submit', (e) => this.handleCodeSubmit(e));
        }

        // Paso 3: Cambiar contraseña
        const passwordForm = document.getElementById('newPasswordForm');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => this.handlePasswordSubmit(e));
        }

        // Reenviar código
        const resendBtn = document.getElementById('resendCodeBtn');
        if (resendBtn) {
            resendBtn.addEventListener('click', () => this.resendCode());
        }

        // Toggle password visibility
        const toggleBtn = document.getElementById('toggleNewPassword');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.togglePasswordVisibility());
        }

        // Validación en tiempo real para el código
        const codeInput = document.getElementById('verificationCode');
        if (codeInput) {
            codeInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/\D/g, '').substring(0, 6);
            });
        }

        // Validación de confirmación de contraseña
        const confirmInput = document.getElementById('confirmPassword');
        if (confirmInput) {
            confirmInput.addEventListener('input', () => this.validatePasswordMatch());
        }
    }

    async handleEmailSubmit(e) {
        e.preventDefault();
        
        const emailInput = document.getElementById('recoveryEmail');
        const submitBtn = document.getElementById('sendCodeBtn');
        const email = emailInput.value.trim();

        if (!this.validateEmail(email)) {
            this.showError('email-error', 'Por favor ingresa un correo electrónico válido');
            return;
        }

        this.setLoadingState(submitBtn, true);
        this.clearError('email-error');

        try {
            const response = await fetch('/api/password-recovery/send-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ email: email })
            });

            const data = await response.json();

            if (response.ok) {
                this.userEmail = email;
                this.verificationToken = data.token;
                this.goToStep(2);
                document.getElementById('emailDisplay').textContent = email;
                this.showSuccess('Código enviado exitosamente');
            } else {
                this.showError('email-error', data.error || 'Error al enviar el código');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('email-error', 'Error de conexión. Inténtalo de nuevo.');
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }

    async handleCodeSubmit(e) {
        e.preventDefault();
        
        const codeInput = document.getElementById('verificationCode');
        const submitBtn = document.getElementById('verifyCodeBtn');
        const code = codeInput.value.trim();

        if (code.length !== 6 || !/^\d{6}$/.test(code)) {
            this.showError('code-error', 'El código debe tener 6 dígitos');
            return;
        }

        this.setLoadingState(submitBtn, true);
        this.clearError('code-error');

        try {
            const response = await fetch('/api/password-recovery/verify-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ 
                    email: this.userEmail,
                    code: code,
                    token: this.verificationToken
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.verificationToken = data.reset_token;
                this.goToStep(3);
                this.showSuccess('Código verificado correctamente');
            } else {
                this.showError('code-error', data.error || 'Código inválido');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('code-error', 'Error de conexión. Inténtalo de nuevo.');
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }

    async handlePasswordSubmit(e) {
        e.preventDefault();
        
        const passwordInput = document.getElementById('newPassword');
        const confirmInput = document.getElementById('confirmPassword');
        const submitBtn = document.getElementById('changePasswordBtn');
        
        const password = passwordInput.value;
        const confirmPassword = confirmInput.value;

        if (!this.validatePassword(password)) {
            this.showError('password-error', 'La contraseña debe tener al menos 8 caracteres');
            return;
        }

        if (password !== confirmPassword) {
            this.showError('confirm-password-error', 'Las contraseñas no coinciden');
            return;
        }

        this.setLoadingState(submitBtn, true);
        this.clearError('password-error');
        this.clearError('confirm-password-error');

        try {
            const response = await fetch('/api/password-recovery/reset-password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ 
                    email: this.userEmail,
                    password: password,
                    token: this.verificationToken
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.goToStep('success');
            } else {
                this.showError('password-error', data.error || 'Error al cambiar la contraseña');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('password-error', 'Error de conexión. Inténtalo de nuevo.');
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }

    async resendCode() {
        const resendBtn = document.getElementById('resendCodeBtn');
        resendBtn.disabled = true;
        resendBtn.textContent = 'Enviando...';

        try {
            const response = await fetch('/api/password-recovery/send-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ email: this.userEmail })
            });

            const data = await response.json();

            if (response.ok) {
                this.verificationToken = data.token;
                this.showSuccess('Código reenviado exitosamente');
                
                // Countdown para reenvío
                let countdown = 60;
                const interval = setInterval(() => {
                    resendBtn.textContent = `Reenviar en ${countdown}s`;
                    countdown--;
                    
                    if (countdown < 0) {
                        clearInterval(interval);
                        resendBtn.textContent = '¿No recibiste el código? Reenviar';
                        resendBtn.disabled = false;
                    }
                }, 1000);
            } else {
                this.showError('code-error', data.error || 'Error al reenviar el código');
                resendBtn.disabled = false;
                resendBtn.textContent = '¿No recibiste el código? Reenviar';
            }
        } catch (error) {
            console.error('Error:', error);
            this.showError('code-error', 'Error de conexión');
            resendBtn.disabled = false;
            resendBtn.textContent = '¿No recibiste el código? Reenviar';
        }
    }

    goToStep(step) {
        // Ocultar todos los pasos
        document.querySelectorAll('.recovery-step').forEach(el => {
            el.classList.add('d-none');
        });

        // Mostrar el paso actual
        if (step === 'success') {
            document.getElementById('successStep').classList.remove('d-none');
            this.updateProgressBar(100);
            this.updateStepLabels(4);
        } else {
            document.getElementById(`step${step}`).classList.remove('d-none');
            this.currentStep = step;
            this.updateProgressBar();
            this.updateStepLabels(step);
        }
    }

    updateProgressBar(customWidth = null) {
        const progressBar = document.getElementById('recoveryProgress');
        const width = customWidth || (this.currentStep * 33.33);
        progressBar.style.width = `${Math.min(width, 100)}%`;
        progressBar.setAttribute('aria-valuenow', Math.min(width, 100));
    }

    updateStepLabels(activeStep) {
        for (let i = 1; i <= 3; i++) {
            const label = document.getElementById(`step${i}Label`);
            if (i <= activeStep) {
                label.className = 'text-primary fw-bold';
            } else {
                label.className = 'text-muted';
            }
        }
    }

    togglePasswordVisibility() {
        const passwordInput = document.getElementById('newPassword');
        const toggleBtn = document.getElementById('toggleNewPassword');
        const icon = toggleBtn.querySelector('i');

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            passwordInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    validatePasswordMatch() {
        const password = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (confirmPassword && password !== confirmPassword) {
            this.showError('confirm-password-error', 'Las contraseñas no coinciden');
        } else {
            this.clearError('confirm-password-error');
        }
    }

    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    validatePassword(password) {
        return password && password.length >= 8;
    }

    setLoadingState(button, loading) {
        const spinner = button.querySelector('.spinner-border');
        const text = button.querySelector('.btn-text');
        
        if (loading) {
            button.disabled = true;
            spinner.classList.remove('d-none');
            text.textContent = 'Procesando...';
        } else {
            button.disabled = false;
            spinner.classList.add('d-none');
            // Restaurar texto original basado en el ID del botón
            if (button.id === 'sendCodeBtn') text.textContent = 'Enviar Código';
            else if (button.id === 'verifyCodeBtn') text.textContent = 'Verificar Código';
            else if (button.id === 'changePasswordBtn') text.textContent = 'Cambiar Contraseña';
        }
    }

    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
            
            // Agregar clase de error al input
            const input = errorElement.previousElementSibling?.querySelector('input');
            if (input) {
                input.classList.add('is-invalid');
            }
        }
    }

    clearError(elementId) {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.style.display = 'none';
            
            // Remover clase de error del input
            const input = errorElement.previousElementSibling?.querySelector('input');
            if (input) {
                input.classList.remove('is-invalid');
            }
        }
    }

    showSuccess(message) {
        // Crear y mostrar alerta de éxito temporal
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remover después de 3 segundos
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 3000);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Inicializar cuando el modal se abra
document.addEventListener('DOMContentLoaded', function() {
    const passwordRecoveryModal = document.getElementById('passwordRecoveryModal');
    let recoveryManager = null;
    
    if (passwordRecoveryModal) {
        passwordRecoveryModal.addEventListener('shown.bs.modal', function() {
            if (!recoveryManager) {
                recoveryManager = new PasswordRecoveryManager();
            }
        });
        
        // Resetear el modal cuando se cierre
        passwordRecoveryModal.addEventListener('hidden.bs.modal', function() {
            if (recoveryManager) {
                recoveryManager.goToStep(1);
                recoveryManager.userEmail = '';
                recoveryManager.verificationToken = '';
                
                // Limpiar formularios
                document.querySelectorAll('#passwordRecoveryModal form').forEach(form => {
                    form.reset();
                });
                
                // Limpiar errores
                document.querySelectorAll('#passwordRecoveryModal .invalid-feedback').forEach(error => {
                    error.textContent = '';
                    error.style.display = 'none';
                });
                
                // Remover clases de error
                document.querySelectorAll('#passwordRecoveryModal .is-invalid').forEach(input => {
                    input.classList.remove('is-invalid');
                });
            }
        });
    }
});