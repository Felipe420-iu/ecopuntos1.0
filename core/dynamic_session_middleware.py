"""
Middleware para manejar timeouts de sesión dinámicos basados en rol de usuario
"""
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth import logout
from datetime import datetime, timedelta


class DynamicSessionTimeoutMiddleware:
    """
    Middleware que aplica timeouts de sesión diferentes según el rol del usuario
    Los valores se obtienen de la configuración en base de datos
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Excluir endpoints de verificación automática del timeout
        excluded_paths = ['/verificar-sesion/', '/api/notifications/']
        
        if request.user.is_authenticated and request.path not in excluded_paths:
            # Obtener configuración de timeout según el rol
            timeout_minutes = self.get_session_timeout(request.user)
            
            print(f"=== DEBUG SESSION TIMEOUT ===")
            print(f"Usuario: {request.user.username}")
            print(f"Rol: {request.user.role}")
            print(f"Timeout configurado: {timeout_minutes} minutos")
            print(f"Path: {request.path}")
            
            # Verificar si la sesión ha expirado
            last_activity_str = request.session.get('last_activity')
            if last_activity_str:
                last_activity = datetime.fromisoformat(last_activity_str)
                now = timezone.now()
                
                # Calcular diferencia en minutos
                time_diff = (now - last_activity).total_seconds() / 60
                
                print(f"Última actividad: {last_activity}")
                print(f"Ahora: {now}")
                print(f"Diferencia: {time_diff:.2f} minutos")
                
                if time_diff > timeout_minutes:
                    # Sesión expirada, cerrar sesión
                    print(f"SESIÓN EXPIRADA - Cerrando sesión")
                    logout(request)
                    return redirect('login')  # Redirigir al login
                else:
                    print(f"Sesión activa - Faltan {timeout_minutes - time_diff:.2f} minutos")
            else:
                print("Primera petición - inicializando last_activity")
            
            print("=============================")
            
            # Actualizar el último acceso SOLO si NO es un endpoint excluido
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Configurar el timeout de la sesión (en segundos)
            request.session.set_expiry(timeout_minutes * 60)
        
        response = self.get_response(request)
        return response
    
    def get_session_timeout(self, user):
        """
        Obtiene el timeout de sesión según el rol del usuario
        """
        from core.models import Configuracion
        
        # Valores por defecto
        default_admin_timeout = 10
        default_user_timeout = 15
        
        try:
            # Si es superusuario o admin, usar timeout de admin
            if user.role in ['superuser', 'admin']:
                config = Configuracion.objects.filter(nombre='admin_session_timeout').first()
                if config:
                    return int(config.valor)
                return default_admin_timeout
            else:
                # Para usuarios regulares y conductores
                config = Configuracion.objects.filter(nombre='user_session_timeout').first()
                if config:
                    return int(config.valor)
                return default_user_timeout
        except Exception as e:
            # En caso de error, usar valores por defecto
            print(f"Error obteniendo timeout de sesión: {e}")
            return default_user_timeout if user.role in ['user', 'conductor'] else default_admin_timeout
