"""
Middleware adicional para bloquear usuarios con sesiones cerradas por admin
"""
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from .models import SesionUsuario
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SessionValidationMiddleware:
    """
    Middleware que valida que la sesión personalizada esté activa
    antes de permitir cualquier petición
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # URLs que no requieren validación de sesión
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
            '/verificar-sesion/',  # Permitir el endpoint de verificación
        ]
        
        # Verificar si la URL actual está exenta
        is_exempt = any(request.path.startswith(url) for url in exempt_urls)
        
        # Solo verificar si el usuario está autenticado y la URL no está exenta
        if request.user.is_authenticated and not is_exempt:
            # Verificar si es una petición AJAX para verificar sesión
            if request.path == '/verificar-sesion/':
                # Permitir que pase para que pueda verificar
                pass
            else:
                # Verificar si la sesión personalizada está activa
                session_token = request.session.get('session_token')
                
                if session_token:
                    try:
                        sesion = SesionUsuario.objects.get(
                            token_sesion=session_token,
                            usuario=request.user,
                            activa=True
                        )
                        
                        # Verificar si no ha expirado
                        if sesion.fecha_expiracion < timezone.now():
                            # Sesión expirada
                            logout(request)
                            messages.warning(request, 'Tu sesión ha expirado.')
                            return self._redirect_to_login(request)
                            
                    except SesionUsuario.DoesNotExist:
                        # La sesión fue cerrada por un administrador
                        logger.warning(f"🔒 Sesión cerrada detectada para usuario {request.user.username} en {request.path}")
                        logout(request)
                        
                        # Si es una petición AJAX, devolver JSON
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            logger.info(f"📡 Respondiendo con JSON para petición AJAX de {request.user.username}")
                            return JsonResponse({
                                'success': False,
                                'session_closed': True,
                                'message': 'Tu sesión ha sido cerrada por un administrador.',
                                'redirect_url': self._get_login_url(request)
                            })
                        
                        logger.info(f"🔄 Redirigiendo usuario {request.user.username} al login")
                        messages.warning(request, 'Tu sesión ha sido cerrada por un administrador.')
                        return self._redirect_to_login(request)
        
        response = self.get_response(request)
        return response
    
    def _redirect_to_login(self, request):
        """Redirige al login apropiado según el tipo de usuario"""
        # Determinar si era un admin por la URL
        is_admin_path = any(path in request.path for path in [
            '/admin/', '/paneladmin/', '/usuarioadmin/', 
            '/canjeadmin/', '/estadisticasadmin/', '/monitor-sesiones/'
        ])
        
        if is_admin_path:
            return redirect('inicioadmin')
        else:
            return redirect('iniciosesion')
    
    def _get_login_url(self, request):
        """Obtiene la URL de login apropiada"""
        is_admin_path = any(path in request.path for path in [
            '/admin/', '/paneladmin/', '/usuarioadmin/', 
            '/canjeadmin/', '/estadisticasadmin/', '/monitor-sesiones/'
        ])
        
        if is_admin_path:
            return '/inicioadmin/'
        else:
            return '/iniciosesion/'
