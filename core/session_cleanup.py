from django.utils import timezone
from .models import SesionUsuario

def cleanup_expired_sessions():
    """Elimina las sesiones expiradas"""
    expired_sessions = SesionUsuario.objects.filter(
        fecha_expiracion__lt=timezone.now()
    )
    count = expired_sessions.count()
    expired_sessions.delete()
    return count
