document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('recoveryForm');
    const emailInput = document.getElementById('email');
    const codeInput = document.getElementById('code');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    let sessionToken = '';
    let resetToken = '';

    // Paso 1: Enviar código de verificación
    async function sendVerificationCode(email) {
        try {
            const response = await fetch('/api/password-recovery/send-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email })
            });
            const data = await response.json();
            
            if (response.ok) {
                sessionToken = data.token;
                showMessage('success', 'Código enviado correctamente. Revisa tu correo.');
                step1.classList.add('d-none');
                step2.classList.remove('d-none');
            } else {
                showMessage('error', data.error || 'Error al enviar el código');
            }
        } catch (error) {
            showMessage('error', 'Error de conexión');
        }
    }

    // Paso 2: Verificar código
    async function verifyCode(code) {
        try {
            const response = await fetch('/api/password-recovery/verify-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: emailInput.value,
                    code: code,
                    token: sessionToken
                })
            });
            const data = await response.json();
            
            if (response.ok) {
                resetToken = data.reset_token;
                showMessage('success', 'Código verificado correctamente');
                step2.classList.add('d-none');
                step3.classList.remove('d-none');
            } else {
                showMessage('error', data.error || 'Error al verificar el código');
            }
        } catch (error) {
            showMessage('error', 'Error de conexión');
        }
    }

    // Paso 3: Restablecer contraseña
    async function resetPassword(password) {
        try {
            const response = await fetch('/api/password-recovery/reset-password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: emailInput.value,
                    password: password,
                    token: resetToken
                })
            });
            const data = await response.json();
            
            if (response.ok) {
                showMessage('success', 'Contraseña restablecida correctamente');
                setTimeout(() => {
                    window.location.href = '/iniciosesion/';
                }, 2000);
            } else {
                showMessage('error', data.error || 'Error al restablecer la contraseña');
            }
        } catch (error) {
            showMessage('error', 'Error de conexión');
        }
    }

    // Función auxiliar para mostrar mensajes
    function showMessage(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        const messagesContainer = document.getElementById('messages');
        messagesContainer.innerHTML = '';
        messagesContainer.appendChild(alertDiv);
    }

    // Event listeners
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const currentStep = document.querySelector('.recovery-step:not(.d-none)');
            
            if (currentStep.id === 'step1') {
                await sendVerificationCode(emailInput.value);
            } else if (currentStep.id === 'step2') {
                await verifyCode(codeInput.value);
            } else if (currentStep.id === 'step3') {
                if (passwordInput.value !== confirmPasswordInput.value) {
                    showMessage('error', 'Las contraseñas no coinciden');
                    return;
                }
                await resetPassword(passwordInput.value);
            }
        });
    }
});
