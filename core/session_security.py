from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .security import SecurityManager
from .models import SesionUsuario
import logging

logger = logging.getLogger(__name__)

class SessionSecurityMiddleware:
    """
    Middleware avanzado para gestión de seguridad de sesiones:
    - Timeout automático diferenciado: 10 minutos para admins, 15 minutos para usuarios
    - Una sola sesión activa por usuario
    - Detección de acceso desde diferentes dispositivos/IPs
    - Limpieza automática de sesiones
    - Redirección específica para administradores
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_cleanup = timezone.now()
    
    def __call__(self, request):
        # Ejecutar limpieza de sesiones cada 30 minutos
        if timezone.now() - self.last_cleanup > timedelta(minutes=30):
            self.cleanup_sessions()
            self.last_cleanup = timezone.now()
        
        # URLs que no requieren validación
        exempt_paths = [
            '/iniciosesion/',
            '/inicioadmin/',
            '/registrate/',
            '/recuperar-password/',
            '/reset-password/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        # Verificar si la ruta está exenta
        is_exempt = any(request.path.startswith(path) for path in exempt_paths)
        
        if request.user.is_authenticated and not is_exempt:
            # Validar sesión de seguridad
            if not self.validate_user_session(request):
                return self.handle_invalid_session(request)
        
        response = self.get_response(request)
        return response
    
    def validate_user_session(self, request):
        """
        Valida la sesión del usuario con múltiples verificaciones de seguridad
        """
        try:
            secure_token = request.session.get('secure_token')
            if not secure_token:
                logger.warning(f'Token de sesión faltante para usuario {request.user.username}')
                return False
            
            # Buscar la sesión activa
            try:
                session = SesionUsuario.objects.get(
                    token_sesion=secure_token,
                    usuario=request.user,
                    activa=True
                )
            except SesionUsuario.DoesNotExist:
                logger.warning(f'Sesión no encontrada para usuario {request.user.username}')
                return False
            
            # Verificar expiración
            if session.is_expired():
                logger.info(f'Sesión expirada para usuario {request.user.username}')
                session.activa = False
                session.save()
                return False
            
            # Verificar inactividad diferenciada: 10 minutos para admins, 15 para usuarios
            timeout_minutes = 10 if hasattr(request.user, 'role') and request.user.role == 'admin' else 15
            if timezone.now() - session.ultima_actividad > timedelta(minutes=timeout_minutes):
                logger.info(f'Sesión inactiva para usuario {request.user.username} (timeout: {timeout_minutes} minutos)')
                session.activa = False
                session.save()
                return False
            
            # Verificar dispositivo
            current_device_id = SecurityManager.generate_device_id(request)
            if session.dispositivo_id != current_device_id:
                logger.warning(f'Dispositivo no autorizado para usuario {request.user.username}')
                session.activa = False
                session.save()
                return False
            
            # Verificar IP
            current_ip = SecurityManager.get_client_ip(request)
            if session.ip_address != current_ip:
                logger.warning(f'IP no autorizada para usuario {request.user.username}: {current_ip} vs {session.ip_address}')
                session.activa = False
                session.save()
                return False
            
            # Actualizar actividad con timeout diferenciado
            timeout_minutes = 10 if hasattr(request.user, 'role') and request.user.role == 'admin' else 15
            session.ultima_actividad = timezone.now()
            session.fecha_expiracion = timezone.now() + timedelta(minutes=timeout_minutes)
            session.save()
            
            return True
            
        except Exception as e:
            logger.error(f'Error validando sesión para usuario {request.user.username}: {str(e)}')
            return False
    
    def handle_invalid_session(self, request):
        """
        Maneja sesiones inválidas con logout y redirección específica
        """
        username = request.user.username if request.user.is_authenticated else 'Anónimo'
        logger.info(f'Cerrando sesión inválida para usuario: {username}')
        
        # Determinar redirección antes de hacer logout
        is_admin = hasattr(request.user, 'role') and request.user.role == 'admin'
        
        # Invalidar sesión
        SecurityManager.invalidate_session(request)
        logout(request)
        
        # Mensaje informativo
        messages.warning(
            request, 
            'Tu sesión ha expirado por seguridad. Por favor, inicia sesión nuevamente.'
        )
        
        # Redirección específica según tipo de usuario
        if is_admin:
            return redirect('inicioadmin')
        else:
            return redirect('iniciosesion')
    
    def cleanup_sessions(self):
        """
        Limpia sesiones expiradas e inactivas
        """
        try:
            expired_count = SecurityManager.cleanup_expired_sessions()
            inactive_count = SecurityManager.cleanup_inactive_sessions()
            
            if expired_count > 0 or inactive_count > 0:
                logger.info(f'Limpieza automática: {expired_count} expiradas, {inactive_count} inactivas')
                
        except Exception as e:
            logger.error(f'Error en limpieza automática de sesiones: {str(e)}')