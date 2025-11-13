from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.contrib import messages

def is_superuser_role(user):
    """Verifica si el usuario tiene rol de superusuario"""
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'superuser'

def is_admin_or_superuser(user):
    """Verifica si el usuario es admin o superusuario"""
    return user.is_authenticated and hasattr(user, 'role') and user.role in ['admin', 'superuser']

def require_superuser(view_func):
    """Decorador que requiere permisos de superusuario"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión como superusuario.')
            return redirect('inicioadmin')
        
        if not is_superuser_role(request.user):
            messages.error(request, 'Acceso denegado. Se requieren permisos de superusuario.')
            return redirect('paneladmin')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def require_superuser_ajax(view_func):
    """Decorador AJAX que requiere permisos de superusuario"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'No autenticado.'}, status=401)
            return redirect('inicioadmin')
        
        if not is_superuser_role(request.user):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Acceso denegado. Se requieren permisos de superusuario.'}, status=403)
            return redirect('paneladmin')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def require_admin_or_superuser(view_func):
    """Decorador que requiere permisos de admin o superusuario"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión como administrador.')
            return redirect('inicioadmin')
        
        if not is_admin_or_superuser(request.user):
            messages.error(request, 'Acceso denegado. Se requieren permisos de administrador.')
            return redirect('inicioadmin')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def superuser_required(view_func):
    """Decorador usando user_passes_test para superusuario"""
    return user_passes_test(is_superuser_role)(view_func)

def admin_or_superuser_required(view_func):
    """Decorador usando user_passes_test para admin o superusuario"""
    return user_passes_test(is_admin_or_superuser)(view_func)
