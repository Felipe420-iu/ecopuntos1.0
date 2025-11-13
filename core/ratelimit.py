"""
Decoradores y utilidades para Rate Limiting / Throttling
"""
from functools import wraps
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited


def smart_ratelimit(key='ip', rate=None, method='ALL', block=True):
    """
    Decorador inteligente para rate limiting que se adapta al contexto
    
    Args:
        key: Clave para identificar al usuario ('ip', 'user', 'user_or_ip')
        rate: Tasa de límite (ej: '5/m', '100/h'). Si None, usa configuración por defecto
        method: Métodos HTTP a limitar ('GET', 'POST', 'ALL')
        block: Si True, bloquea cuando se excede el límite
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Si rate limiting está deshabilitado, ejecutar función normalmente
            if not getattr(settings, 'RATELIMIT_ENABLE', True):
                return func(request, *args, **kwargs)
            
            # Determinar la tasa basada en el rol del usuario
            if rate is None:
                if request.user.is_authenticated:
                    if request.user.is_staff:
                        default_rate = settings.RATELIMIT_RATES.get('admin_general', '500/h')
                    elif getattr(request.user, 'role', None) == 'conductor':
                        default_rate = settings.RATELIMIT_RATES.get('conductor_general', '200/h')
                    else:
                        default_rate = settings.RATELIMIT_RATES.get('user_general', '100/h')
                else:
                    default_rate = settings.RATELIMIT_RATES.get('anonymous', '20/h')
            else:
                default_rate = rate
            
            # Aplicar rate limiting
            @ratelimit(key=key, rate=default_rate, method=method, block=block)
            def limited_func(req, *a, **kw):
                return func(req, *a, **kw)
            
            try:
                return limited_func(request, *args, **kwargs)
            except Ratelimited:
                # Manejar cuando se excede el límite
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                   request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'Límite de solicitudes excedido',
                        'message': 'Has realizado demasiadas solicitudes. Por favor, intenta más tarde.',
                        'retry_after': '60'  # segundos
                    }, status=429)
                else:
                    return HttpResponse(
                        '<h1>Límite de solicitudes excedido</h1>'
                        '<p>Has realizado demasiadas solicitudes. Por favor, intenta más tarde.</p>',
                        status=429
                    )
        
        return wrapper
    return decorator


def ratelimit_login(func):
    """Decorador específico para login - muy restrictivo"""
    rate = settings.RATELIMIT_RATES.get('login', '5/m')
    return smart_ratelimit(key='ip', rate=rate, method='POST', block=True)(func)


def ratelimit_register(func):
    """Decorador específico para registro"""
    rate = settings.RATELIMIT_RATES.get('register', '3/h')
    return smart_ratelimit(key='ip', rate=rate, method='POST', block=True)(func)


def ratelimit_canje(func):
    """Decorador para operaciones de canje"""
    rate = settings.RATELIMIT_RATES.get('canjes', '10/h')
    return smart_ratelimit(key='user_or_ip', rate=rate, method='POST', block=True)(func)


def ratelimit_chatbot(func):
    """Decorador para mensajes del chatbot"""
    rate = settings.RATELIMIT_RATES.get('chatbot_message', '30/m')
    return smart_ratelimit(key='user_or_ip', rate=rate, method='POST', block=True)(func)


def ratelimit_email(func):
    """Decorador para envío de emails"""
    rate = settings.RATELIMIT_RATES.get('send_email', '5/h')
    return smart_ratelimit(key='user_or_ip', rate=rate, method='POST', block=True)(func)


def ratelimit_api(func):
    """Decorador general para APIs"""
    rate = settings.RATELIMIT_RATES.get('api_general', '100/h')
    return smart_ratelimit(key='user_or_ip', rate=rate, method='ALL', block=True)(func)


def get_client_ip(request):
    """
    Obtiene la IP real del cliente, considerando proxies
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
