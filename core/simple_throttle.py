"""
Sistema de throttling personalizado para EcoPuntos
Funciona sin Redis y es compatible con el desarrollo local
"""
import time
from collections import defaultdict
from django.http import HttpResponse
from django.shortcuts import render
from functools import wraps
from django.conf import settings

# Cache en memoria para desarrollo
_throttle_cache = defaultdict(list)

def clean_old_entries(key, window_seconds):
    """Limpia entradas antiguas del cache"""
    current_time = time.time()
    _throttle_cache[key] = [
        timestamp for timestamp in _throttle_cache[key]
        if current_time - timestamp < window_seconds
    ]

def simple_throttle(rate='5/m', key_func=None):
    """
    Decorador de throttling simple
    rate: '5/m' = 5 por minuto, '10/h' = 10 por hora
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Parsear rate
            try:
                limit, period = rate.split('/')
                limit = int(limit)
                
                if period == 'm':
                    window_seconds = 60
                elif period == 'h':
                    window_seconds = 3600
                elif period == 'd':
                    window_seconds = 86400
                else:
                    window_seconds = 60
                    
            except ValueError:
                return view_func(request, *args, **kwargs)
            
            # Determinar key para throttling
            if key_func:
                cache_key = key_func(request)
            else:
                # Usar IP por defecto
                ip = get_client_ip(request)
                cache_key = f"{view_func.__name__}:{ip}"
            
            current_time = time.time()
            
            # Limpiar entradas antiguas
            clean_old_entries(cache_key, window_seconds)
            
            # Verificar límite
            if len(_throttle_cache[cache_key]) >= limit:
                # Rate limit exceeded
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # AJAX request
                    return HttpResponse(
                        '{"error": "Rate limit exceeded", "retry_after": 60}',
                        status=429,
                        content_type='application/json'
                    )
                else:
                    # Página normal
                    return render(request, 'core/ratelimit_error.html', {
                        'retry_after': 60,
                        'limit': limit,
                        'period': period
                    }, status=429)
            
            # Agregar timestamp actual
            _throttle_cache[cache_key].append(current_time)
            
            # Ejecutar vista normal
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def user_key(request):
    """Genera key basada en usuario autenticado"""
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    else:
        return f"ip:{get_client_ip(request)}"

def ip_key(request):
    """Genera key basada en IP"""
    return f"ip:{get_client_ip(request)}"

# Decoradores predefinidos para diferentes casos
throttle_login = simple_throttle('5/m', ip_key)
throttle_register = simple_throttle('3/h', ip_key)
throttle_canjes = simple_throttle('10/h', user_key)
throttle_chatbot = simple_throttle('30/m', user_key)
throttle_general = simple_throttle('100/h', user_key)