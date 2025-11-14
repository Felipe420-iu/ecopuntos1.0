document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('recoveryForm');
    const emailInput = document.getElementById('emailInput');
    const codeInput = document.getElementById('codeInput');
    const step1 = document.getElementById('step1');
    const step2 = document.getElementById('step2');
    const step3 = document.getElementById('step3');
    let token = '';

    async function enviarCodigo(email) {
        try {
            const response = await fetch('/api/password-recovery/send-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ email: email })
            });

            const data = await response.json();
            
            if (response.ok) {
                token = data.token;
                Swal.fire({
                    icon: 'success',
                    title: '¡Código enviado!',
                    text: 'Hemos enviado un código a tu correo electrónico'
                });
                step1.classList.add('d-none');
                step2.classList.remove('d-none');
            } else {
                throw new Error(data.error || 'Error al enviar el código');
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message
            });
        }
    }

    async function verificarCodigo(code) {
        try {
            const response = await fetch('/api/password-recovery/verify-code/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    email: emailInput.value,
                    code: code,
                    token: token
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                token = data.reset_token;
                Swal.fire({
                    icon: 'success',
                    title: '¡Código verificado!',
                    text: 'Ahora puedes establecer tu nueva contraseña'
                });
                step2.classList.add('d-none');
                step3.classList.remove('d-none');
            } else {
                throw new Error(data.error || 'Código inválido');
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message
            });
        }
    }

    async function cambiarPassword(password) {
        try {
            const response = await fetch('/api/password-recovery/reset-password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    email: emailInput.value,
                    password: password,
                    token: token
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                Swal.fire({
                    icon: 'success',
                    title: '¡Contraseña actualizada!',
                    text: 'Tu contraseña ha sido cambiada correctamente',
                    confirmButtonText: 'Ir al login'
                }).then(() => {
                    window.location.href = '/iniciosesion/';
                });
            } else {
                throw new Error(data.error || 'Error al cambiar la contraseña');
            }
        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: error.message
            });
        }
    }

    // Función para obtener el token CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Manejador del formulario
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const currentStep = document.querySelector('.recovery-step:not(.d-none)');
            
            if (currentStep.id === 'step1') {
                if (!emailInput.value) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Por favor ingresa tu correo electrónico'
                    });
                    return;
                }
                await enviarCodigo(emailInput.value);
            }
            else if (currentStep.id === 'step2') {
                if (!codeInput.value) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Por favor ingresa el código de verificación'
                    });
                    return;
                }
                await verificarCodigo(codeInput.value);
            }
            else if (currentStep.id === 'step3') {
                const password = document.getElementById('passwordInput').value;
                const confirmPassword = document.getElementById('confirmPasswordInput').value;
                
                if (password !== confirmPassword) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Las contraseñas no coinciden'
                    });
                    return;
                }
                
                if (password.length < 8) {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'La contraseña debe tener al menos 8 caracteres'
                    });
                    return;
                }
                
                await cambiarPassword(password);
            }
        });
    }
});
