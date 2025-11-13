from django.shortcuts import redirect
from django.contrib.auth import logout
from django.urls import reverse
from .security import SecurityManager
import time
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponse

class SecurityMiddleware:
    """Middleware para validar sesiones seguras con timeout de 15 minutos"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que no requieren validación de sesión
        exempt_urls = [
            '/',
            '/iniciosesion/',
            '/inicioadmin/',
            '/logout/',
            '/cerrar-sesion/',
            '/registrate/',
            '/recuperar-password/',
            '/reset-password/',
            '/static/',
            '/media/',
            '/admin/',
            '/usuario-desactivado/',
            '/usuario-suspendido/',
        ]

        # Verificar si la URL actual está exenta
        is_exempt = any(request.path.startswith(url) for url in exempt_urls)

        if request.user.is_authenticated:
            # La verificación de usuarios desactivados/suspendidos se maneja en UserStatusMiddleware
            # para evitar duplicación de lógica
            
            # Solo validar sesión si la URL no está exenta y no es superuser en admin
            if not is_exempt and not (request.path.startswith('/admin/') and request.user.is_superuser):
                is_valid, message = SecurityManager.validate_session(request)
                if not is_valid:
                    # Invalidar sesión y redirigir al login
                    SecurityManager.invalidate_session(request)
                    logout(request)
                    if 'inactividad' in message.lower() or 'expirada' in message.lower():
                        messages.warning(request, 'Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.')
                        # Redirección diferenciada según tipo de usuario
                        if hasattr(request.user, 'role') and request.user.role == 'admin':
                            return redirect('inicioadmin')
                        else:
                            return redirect('iniciosesion')
                    else:
                        messages.error(request, f'Sesión inválida: {message}')
                        # Redirección diferenciada según tipo de usuario
                        if hasattr(request.user, 'role') and request.user.role == 'admin':
                            return redirect('inicioadmin')
                        else:
                            return redirect('iniciosesion')
        
        response = self.get_response(request)
        return response

class UserStatusMiddleware:
    """Middleware para verificar el estado de usuarios desactivados o suspendidos"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # URLs que no requieren verificación de estado
        exempt_urls = [
            '/',
            '/iniciosesion/',
            '/inicioadmin/',
            '/registrate/',
            '/recuperar-password/',
            '/reset-password/',
            '/static/',
            '/media/',
            '/admin/',
            '/usuario-desactivado/',
            '/usuario-suspendido/',
            '/cerrar-sesion/',
            '/logout/',
        ]
        
        # Verificar si la URL actual está exenta
        is_exempt = any(request.path.startswith(url) for url in exempt_urls)
        
        # Solo verificar si el usuario está autenticado y la URL no está exenta
        if request.user.is_authenticated and not is_exempt and not (request.path.startswith('/admin/') and request.user.is_superuser):
            # Verificar primero si el usuario está suspendido (prioridad sobre desactivado)
            if hasattr(request.user, 'suspended') and request.user.suspended:
                logout(request)
                # Redirigir a la página de usuario suspendido
                return redirect('usuario_suspendido')
            
            # Verificar si el usuario está desactivado
            if not request.user.is_active:
                logout(request)
                # Redirigir a la página de usuario desactivado
                return redirect('usuario_desactivado')
        
        response = self.get_response(request)
        return response
