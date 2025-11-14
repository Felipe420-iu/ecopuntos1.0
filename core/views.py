from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login as auth_login, get_user_model, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.urls import reverse
from .security import SecurityManager
from .models import Configuracion
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.conf import settings
from django.db import models
from .models import Usuario, Canje, MaterialTasa, RedencionPuntos, Ruta, Alerta, Categoria, Recompensa, Logro, Notificacion, SesionUsuario, IntentoAcceso, FavoritoRecompensa, RutaRecoleccion, ParadaRuta, SeguimientoRecompensa, HistorialSeguimiento
# from supabase import create_client  # Temporalmente deshabilitado
from django.http import JsonResponse
from decimal import Decimal
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.db.models import Sum, Count
from datetime import date, timedelta
from urllib.parse import urlencode
import json
import json
from django.utils.http import url_has_allowed_host_and_scheme
from functools import wraps
from django.contrib.auth.forms import PasswordChangeForm
from .forms import ProfileForm
from django.views.decorators.csrf import csrf_exempt
from .security import SecurityManager, require_secure_session
from .statistics import StatisticsManager
from django.http import JsonResponse
# from .ratelimit import ratelimit_login, ratelimit_canje, ratelimit_chatbot, smart_ratelimit
from .simple_throttle import throttle_login, throttle_canjes, throttle_chatbot, throttle_general

def usuario_desactivado(request):
    """Vista para mostrar mensaje de usuario desactivado"""
    # Asegurarse de que el usuario esté desconectado
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'core/usuario_desactivado.html', {
        'redirect_url': reverse('iniciosesion')
    })

def usuario_suspendido(request):
    """Vista para mostrar mensaje de usuario suspendido"""
    if request.user.is_authenticated and not request.user.suspended:
        return redirect('index')
    return render(request, 'core/usuario_suspendido.html')

def redirect_to_chatbot(request):
    """Redireccionar antiguas URLs de soporte al chatbot"""
    return redirect('chatbot_interface')

def test_chat(request):
    """Página de prueba para WebSocket del chat"""
    return render(request, 'core/test_chat.html')

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def usuarioadmin(request):
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión como administrador para acceder a la gestión de usuarios.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea administrador
    if not is_admin(request.user):
        messages.error(request, 'No tienes permisos de administrador para acceder a esta página.')
        return redirect('inicioadmin')
    
    users = Usuario.objects.all().order_by('-fecha_registro')
    return render(request, 'core/usuarioadmin.html', {
        'users': users,
        'total_users': users.count(),
        'active_users': users.filter(is_active=True).count(),
        'admin_users': users.filter(role='admin').count()
    })

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def edit_user(request, user_id):
    if request.method == 'POST':
        try:
            user = Usuario.objects.get(id=user_id)
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            user.role = request.POST.get('role')
            user.save()
            return JsonResponse({
                'success': True,
                'message': f'Usuario {user.username} actualizado exitosamente'
            })
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def deactivate_user(request, user_id):
    if request.method == 'POST':
        try:
            user = Usuario.objects.get(id=user_id)
            if user.role == 'admin' and Usuario.objects.filter(role='admin', is_active=True).count() <= 1:
                return JsonResponse({
                    'success': False,
                    'message': 'No se puede desactivar el último administrador'
                })
            user.is_active = False
            user.save()
            return JsonResponse({
                'success': True,
                'message': f'Usuario {user.username} desactivado exitosamente'
            })
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def suspend_user(request, user_id):
    if request.method == 'POST':
        try:
            user = Usuario.objects.get(id=user_id)
            if user.role == 'admin' and Usuario.objects.filter(role='admin', suspended=False).count() <= 1:
                return JsonResponse({
                    'success': False,
                    'message': 'No se puede suspender el último administrador'
                })
            user.suspended = True
            # NO desactivar is_active para poder diferenciar entre suspendido y desactivado
            # user.is_active = False  # Comentamos esta línea
            user.save()
            return JsonResponse({
                'success': True,
                'message': f'Usuario {user.username} suspendido exitosamente'
            })
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def reactivate_user(request, user_id):
    if request.method == 'POST':
        try:
            user = Usuario.objects.get(id=user_id)
            user.is_active = True
            user.suspended = False
            user.save()
            return JsonResponse({
                'success': True,
                'message': f'Usuario {user.username} reactivado exitosamente'
            })
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def unsuspend_user(request, user_id):
    """Función específica para quitar la suspensión de un usuario"""
    if request.method == 'POST':
        try:
            user = Usuario.objects.get(id=user_id)
            user.suspended = False
            # Mantener el estado de is_active como estaba antes
            user.save()
            return JsonResponse({
                'success': True,
                'message': f'Suspensión removida de {user.username} exitosamente'
            })
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user = Usuario.objects.get(id=user_id)
            if user.role == 'admin' and Usuario.objects.filter(role='admin').count() <= 1:
                return JsonResponse({
                    'success': False,
                    'message': 'No se puede eliminar el último administrador del sistema'
                })
            username = user.username
            user.delete()
            return JsonResponse({
                'success': True,
                'message': f'Usuario {username} eliminado exitosamente'
            })
        except Usuario.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuario no encontrado'
            })
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })

# Configuración de Supabase (temporalmente deshabilitada para evitar errores de conexión)
# supabase_url = 'https://ferrazkesahlbqcitmny.supabase.co'
# supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZlcnJhemtlc2FobGJxY2l0bW55Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg0NjY5MDYsImV4cCI6MjA2NDA0MjkwNn0.vwpKQupvRvMgxRkDvB0j3MOQPVXoCDhtbJQUX_LH8YQ'
# supabase = create_client(supabase_url, supabase_key)

def index(request):
    from .models import Usuario
    testimonios = Usuario.usuarios_con_testimonio()[:12]  # Limitar a 12 testimonios
    return render(request, 'core/index.html', {'testimonios': testimonios})

def terminos_condiciones(request):
    """Vista para mostrar los términos y condiciones"""
    context = {
        'fecha_actualizacion': '31 de agosto de 2025',
        'version': '1.0'
    }
    return render(request, 'core/terminos_condiciones.html', context)

def politica_privacidad(request):
    """Vista para mostrar la política de privacidad"""
    context = {
        'fecha_actualizacion': '31 de agosto de 2025',
        'version': '1.0'
    }
    return render(request, 'core/politica_privacidad.html', context)

def contacto_legal(request):
    """Vista para mostrar la información de contacto legal"""
    context = {
        'fecha_actualizacion': '14 de noviembre de 2025',
        'version': '1.0'
    }
    return render(request, 'core/contacto_legal.html', context)

def logout_view(request):
    next_url = request.GET.get('next', 'index')
    # Invalidar sesión segura
    SecurityManager.invalidate_session(request)
    logout(request)
    return redirect(next_url)

def registrate(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'core/registrate.html')

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'core/registrate.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe una cuenta con este correo electrónico.')
            return render(request, 'core/registrate.html')

        try:
            # Registrar en Django con 2FA
            user = User.objects.create_user(username=username, email=email, password=password1)
            
            # Configurar cuenta para 2FA - INACTIVA hasta verificar email
            user.is_active = False
            user.email_verificado = False
            user.save()
            
            # Enviar código de verificación 2FA
            from .security import TwoFactorManager
            success, message = TwoFactorManager.send_verification_email(user)
            
            if success:
                # Guardar ID del usuario en sesión para la verificación
                request.session['usuario_pendiente_verificacion'] = user.id
                request.session['email_verificacion'] = user.email
                
                # Otorgar logro de registro (se activará cuando verifique)
                from .models import Logro
                try:
                    Logro.objects.create(
                        usuario=user,
                        tipo='registro',
                        descripcion='¡Bienvenido! Te has unido a la comunidad de Eco Puntos como Ecologista Junior',
                        puntos=50
                    )
                except Exception as logro_error:
                    print(f"Error creando logro: {logro_error}")
                

                
                messages.success(request, f'¡Registro exitoso! Hemos enviado un código de verificación a {user.email}. Revisa tu bandeja de entrada.')
                return redirect('verificar_email')
            else:
                # Si falla el envío del email, eliminar usuario creado
                user.delete()
                messages.error(request, f'Error enviando código de verificación: {message}')
                return render(request, 'core/registrate.html')
                
        except Exception as e:
            messages.error(request, f'Error al registrar usuario: {str(e)}')
            return render(request, 'core/registrate.html')

    return render(request, 'core/registrate.html')

def verificar_email(request):
    """Vista para verificar el código 2FA enviado por email"""
    # Verificar que hay un usuario pendiente de verificación
    user_id = request.session.get('usuario_pendiente_verificacion')
    email_verificacion = request.session.get('email_verificacion')
    
    if not user_id:
        messages.error(request, 'No hay ningún registro pendiente de verificación.')
        return redirect('registrate')
    
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id, email=email_verificacion)
        
        # Si ya está verificado, redirigir al login
        if user.email_verificado and user.is_active:
            # Limpiar sesión
            request.session.pop('usuario_pendiente_verificacion', None)
            request.session.pop('email_verificacion', None)
            messages.success(request, '¡Tu cuenta ya está verificada! Puedes iniciar sesión.')
            return redirect('iniciosesion')
            
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado o email no coincide.')
        return redirect('registrate')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'verify':
            codigo_ingresado = request.POST.get('codigo_verificacion', '').strip()
            
            if not codigo_ingresado:
                messages.error(request, 'Por favor ingresa el código de verificación.')
                return render(request, 'core/verificar_email.html', {
                    'email': email_verificacion,
                    'user': user
                })
            
            # Verificar código con TwoFactorManager
            from .security import TwoFactorManager
            success, message = TwoFactorManager.verify_code(user, codigo_ingresado)
            
            if success:
                # Limpiar datos de sesión
                request.session.pop('usuario_pendiente_verificacion', None)
                request.session.pop('email_verificacion', None)
                
                messages.success(request, '¡Email verificado correctamente! Tu cuenta está activada. ¡Bienvenido a Eco Puntos!')
                return redirect('iniciosesion')
            else:
                messages.error(request, message)
                
        elif action == 'resend':
            # Reenviar código
            from .security import TwoFactorManager
            can_resend, resend_message = TwoFactorManager.can_resend_code(user)
            
            if can_resend:
                success, send_message = TwoFactorManager.send_verification_email(user)
                if success:
                    user._ultimo_envio_codigo = timezone.now()  # Marcar tiempo de envío
                    messages.success(request, '¡Nuevo código enviado! Revisa tu email.')
                else:
                    messages.error(request, f'Error reenviando código: {send_message}')
            else:
                messages.warning(request, resend_message)
    
    # Calcular tiempo restante para la expiración
    tiempo_restante = None
    if user.codigo_verificacion_expira:
        from django.utils import timezone
        tiempo_restante = user.codigo_verificacion_expira - timezone.now()
        if tiempo_restante.total_seconds() <= 0:
            tiempo_restante = None
    
    context = {
        'email': email_verificacion,
        'user': user,
        'tiempo_restante': tiempo_restante,
        'intentos_restantes': max(0, 3 - user.intentos_verificacion) if user.intentos_verificacion < 3 else 0,
        'bloqueado': user.verificacion_bloqueada_hasta and user.verificacion_bloqueada_hasta > timezone.now(),
    }
    
    return render(request, 'core/verificar_email.html', context)

@throttle_login
def iniciosesion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next') or request.GET.get('next')
        
        try:
            # Primero verificar si el usuario existe
            User = get_user_model()
            try:
                user_obj = User.objects.get(username=username)
                # Verificar PRIMERO si el usuario está suspendido
                if hasattr(user_obj, 'suspended') and user_obj.suspended:
                    messages.error(request, 'Tu cuenta está suspendida. Contacta al administrador para más información.')
                    return redirect('usuario_suspendido')
                
                # Verificar si el usuario está desactivado
                if not user_obj.is_active:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador para más información.')
                    return redirect('usuario_desactivado')
                    
            except User.DoesNotExist:
                # Si el usuario no existe, continuar con el proceso normal para mostrar error genérico
                pass
            
            # Autenticar con Django
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Double-check del estado del usuario después de autenticar
                # Verificar PRIMERO si el usuario está suspendido
                if hasattr(user, 'suspended') and user.suspended:
                    messages.error(request, 'Tu cuenta está suspendida. Contacta al administrador para más información.')
                    return redirect('usuario_suspendido')
                
                # Verificar si el usuario está desactivado
                if not user.is_active:
                    messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador para más información.')
                    return redirect('usuario_desactivado')
                
                # Verificar si el email está verificado (2FA)
                if hasattr(user, 'email_verificado') and not user.email_verificado:
                    # Reenviar código de verificación automáticamente
                    from .security import TwoFactorManager
                    success, message = TwoFactorManager.send_verification_email(user)
                    
                    if success:
                        request.session['usuario_pendiente_verificacion'] = user.id
                        request.session['email_verificacion'] = user.email
                        messages.warning(request, f'Tu email aún no está verificado. Hemos enviado un nuevo código a {user.email}.')
                        return redirect('verificar_email')
                    else:
                        messages.error(request, 'Error enviando código de verificación. Contacta al soporte.')
                        return render(request, 'core/iniciosesion.html', {'next': next_url})
                
                # Crear sesión segura
                SecurityManager.create_secure_session(request, user)
                auth_login(request, user)
                
                # Las notificaciones se manejan ahora a través del sistema de campana
                # No usar messages.success() para notificaciones
                
                # Determinar a dónde redirigir
                if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host(),}):
                    return redirect(next_url)
                elif hasattr(user, 'role') and user.role == 'superuser':
                    return redirect('panel_superuser')
                elif hasattr(user, 'role') and user.role == 'admin':
                    return redirect('paneladmin')
                else:
                    return redirect('dashusuario')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        except Exception as e:
            messages.error(request, f'Error de autenticación: {str(e)}')
            
    next_url = request.GET.get('next')
    return render(request, 'core/iniciosesion.html', {'next': next_url})

@csrf_exempt
def login_ajax(request):
    """Vista para manejar login via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            remember_me = data.get('remember_me', False)
            
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'error': 'Usuario y contraseña son requeridos.'
                })
            
            # Primero verificar si el usuario existe y su estado
            User = get_user_model()
            try:
                user_obj = User.objects.get(username=username)
                # Verificar PRIMERO si el usuario está suspendido
                if hasattr(user_obj, 'suspended') and user_obj.suspended:
                    return JsonResponse({
                        'success': False,
                        'error': 'Tu cuenta está suspendida. Contacta al administrador para más información.',
                        'redirect_url': '/usuario-suspendido/',
                        'is_suspended': True
                    })
                
                # Verificar si el usuario está desactivado
                if not user_obj.is_active:
                    return JsonResponse({
                        'success': False,
                        'error': 'Tu cuenta está desactivada. Contacta al administrador para más información.',
                        'redirect_url': '/usuario-desactivado/',
                        'is_deactivated': True
                    })
                    
            except User.DoesNotExist:
                # Si el usuario no existe, continuar con el proceso normal
                pass
            
            # Autenticar con Django
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Double-check del estado del usuario después de autenticar
                # Verificar PRIMERO si el usuario está suspendido
                if hasattr(user, 'suspended') and user.suspended:
                    return JsonResponse({
                        'success': False,
                        'error': 'Tu cuenta está suspendida. Contacta al administrador para más información.',
                        'redirect_url': '/usuario-suspendido/',
                        'is_suspended': True
                    })
                
                # Verificar si el usuario está desactivado
                if not user.is_active:
                    return JsonResponse({
                        'success': False,
                        'error': 'Tu cuenta está desactivada. Contacta al administrador para más información.',
                        'redirect_url': '/usuario-desactivado/',
                        'is_deactivated': True
                    })
                
                # Crear sesión segura
                SecurityManager.create_secure_session(request, user)
                auth_login(request, user)
                
                # Configurar duración de sesión si remember_me está activado
                if remember_me:
                    request.session.set_expiry(1209600)  # 2 semanas
                else:
                    request.session.set_expiry(0)  # Cerrar al cerrar navegador
                
                # Determinar URL de redirección
                if hasattr(user, 'role') and user.role == 'superuser':
                    redirect_url = '/superuser/'
                elif hasattr(user, 'role') and user.role == 'admin':
                    redirect_url = '/paneladmin/'
                else:
                    redirect_url = '/dashusuario/'
                
                return JsonResponse({
                    'success': True,
                    'message': f'Bienvenido/a {user.username}!',
                    'redirect_url': redirect_url
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Usuario o contraseña incorrectos.'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos JSON inválidos.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error de autenticación: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido.'
    })


def perfil(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('iniciosesion')

    if request.method == 'POST':
        if 'photo_submit' in request.POST:
            # Manejo de actualización solo de foto
            if 'foto_perfil' in request.FILES:
                from django.utils import timezone
                user.foto_perfil = request.FILES['foto_perfil']
                user.last_login = timezone.now()  # Actualizar para forzar cache refresh
                user.save()
                
                # Crear notificación de cambio de foto
                Notificacion.objects.create(
                    usuario=user,
                    titulo='Foto de Perfil Actualizada',
                    mensaje='Has actualizado tu foto de perfil correctamente.',
                    tipo='foto_actualizada'
                )
                
                return redirect('perfil')
        elif 'profile_submit' in request.POST:
            profile_form = ProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                # Detectar qué campos cambiaron
                cambios = []
                old_data = {
                    'email': user.email,
                    'telefono': getattr(user, 'telefono', ''),
                    'direccion': getattr(user, 'direccion', ''),
                }
                
                profile_form.save()
                
                # Verificar cambios específicos
                if old_data['email'] != user.email:
                    cambios.append('correo electrónico')
                if old_data['telefono'] != getattr(user, 'telefono', ''):
                    cambios.append('teléfono')
                if old_data['direccion'] != getattr(user, 'direccion', ''):
                    cambios.append('dirección')
                
                # Crear notificación si hubo cambios
                if cambios:
                    cambios_texto = ', '.join(cambios)
                    Notificacion.objects.create(
                        usuario=user,
                        titulo='Perfil Actualizado',
                        mensaje=f'Has actualizado tu {cambios_texto} correctamente. Los cambios han sido guardados en tu perfil.',
                        tipo='perfil_actualizado'
                    )
                
                return redirect('perfil')
            else:
                # No usar messages.error(), los errores del form se muestran en la página
                password_form = PasswordChangeForm(user)
        elif 'password_submit' in request.POST:
            profile_form = ProfileForm(instance=user)
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                
                # Crear notificación de cambio de contraseña
                Notificacion.objects.create(
                    usuario=user,
                    titulo='Contraseña Actualizada',
                    mensaje='Tu contraseña ha sido cambiada exitosamente. Si no fuiste tú, contacta al soporte inmediatamente.',
                    tipo='password_cambiado'
                )
                
                return redirect('perfil')
            else:
                # No usar messages.error(), los errores del form se muestran en la página
                pass
        else:
            profile_form = ProfileForm(instance=user)
            password_form = PasswordChangeForm(user)
    else:
        profile_form = ProfileForm(instance=user)
        password_form = PasswordChangeForm(user)

    # Obtener estadísticas del usuario
    canjes = Canje.objects.filter(usuario=user).order_by('-fecha_solicitud')
    redenciones = RedencionPuntos.objects.filter(usuario=user).order_by('-fecha_solicitud')
    
    # Estadísticas básicas
    total_canjes = canjes.count()
    total_puntos_canjeados = sum(c.puntos for c in canjes if c.estado in ['aprobado', 'completado'])
    total_dinero = sum(r.valor_cop for r in redenciones if r.estado == 'completado')
    
    # Logros del usuario
    logros_usuario = user.logro_set.all()[:3]
    
    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'user': user,
        'total_canjes': total_canjes,
        'total_puntos_canjeados': total_puntos_canjeados,
        'total_dinero': total_dinero,
        'canjes_recientes': canjes[:3],
        'logros_usuario': logros_usuario,
    }
    return render(request, 'core/perfil.html', context)

def categorias(request):
    context = {}
    if request.user.is_authenticated:
        context = {
            'puntos_actuales': request.user.puntos,
            'puntos_juego_papel': getattr(request.user, 'puntos_juego_papel', 0),
            'puntos_juego_vidrios': getattr(request.user, 'puntos_juego_vidrios', 0),
            'puntos_juego_plasticos': getattr(request.user, 'puntos_juego', 0),
            'puntos_juego_metales': getattr(request.user, 'puntos_juego_metales', 0),
        }
    return render(request, 'core/categorias.html', context)

@login_required
def juego_plasticos(request):
    """Vista para el juego de clasificación de plásticos"""
    if request.method == 'POST':
        # Verificar si es una solicitud de canje
        if request.POST.get('canje') == 'true':
            puntos_canje = int(request.POST.get('puntos_canje', 0))
            puntos_juego_actuales = getattr(request.user, 'puntos_juego_plasticos', 0)
            
            # Verificar que el usuario tenga suficientes puntos
            if puntos_canje <= puntos_juego_actuales and puntos_canje >= 2:
                # Calcular EcoPuntos a ganar (2 puntos de juego = 1 EcoPunto)
                ecopuntos_ganados = puntos_canje // 2
                
                # Actualizar puntos del usuario
                request.user.puntos_juego_plasticos = puntos_juego_actuales - puntos_canje
                request.user.puntos += ecopuntos_ganados
                request.user.save()
                
                # Crear notificación
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='🎮 ¡Canje de puntos exitoso!',
                    mensaje=f'Has canjeado {puntos_canje} puntos de juego por {ecopuntos_ganados} EcoPuntos reales en el juego de plásticos.',
                    tipo='success'
                )
                
                return JsonResponse({
                    'success': True,
                    'puntos_juego_restantes': request.user.puntos_juego_plasticos,
                    'ecopuntos_totales': request.user.puntos,
                    'ecopuntos_ganados': ecopuntos_ganados
                })
            else:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'No tienes suficientes puntos para canjear o el mínimo es 2 puntos.'
                })
        
        # Procesar resultado del juego
        puntos_ganados = int(request.POST.get('puntos', 0))
        nivel_completado = request.POST.get('nivel', 1)
        
        # Validar que los puntos sean razonables (máximo 50 puntos por juego)
        if 0 <= puntos_ganados <= 50:
            # Sistema de conversión: cada 10,000 puntos del juego = 10 puntos canjeables
            # Obtener puntos de juego acumulados del usuario (usando un campo personalizado o sesión)
            puntos_juego_actuales = getattr(request.user, 'puntos_juego_plasticos', 0)
            puntos_juego_totales = puntos_juego_actuales + puntos_ganados
            
            # Calcular puntos canjeables
            puntos_canjeables_nuevos = (puntos_juego_totales // 10000) * 10
            puntos_canjeables_anteriores = (puntos_juego_actuales // 10000) * 10
            puntos_canjeables_ganados = puntos_canjeables_nuevos - puntos_canjeables_anteriores
            
            # Actualizar puntos de juego del usuario
            request.user.puntos_juego_plasticos = puntos_juego_totales
            
            # Si se ganaron puntos canjeables, agregarlos
            if puntos_canjeables_ganados > 0:
                request.user.puntos += puntos_canjeables_ganados
            
            request.user.save()
            
            # Crear notificación apropiada
            if puntos_canjeables_ganados > 0:
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='¡Puntos canjeables obtenidos!',
                    mensaje=f'¡Felicidades! Has convertido puntos del juego en {puntos_canjeables_ganados} puntos canjeables. Total de puntos de juego: {puntos_juego_totales}',
                    tipo='success'
                )
            else:
                puntos_restantes = 10000 - (puntos_juego_totales % 10000)
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='¡Puntos de juego ganados!',
                    mensaje=f'Has ganado {puntos_ganados} puntos en el juego. Total: {puntos_juego_totales}. Necesitas {puntos_restantes} puntos más para obtener puntos canjeables.',
                    tipo='info'
                )
            
            return JsonResponse({
                'success': True,
                'puntos_ganados': puntos_ganados,
                'puntos_juego_totales': puntos_juego_totales,
                'puntos_canjeables_ganados': puntos_canjeables_ganados,
                'puntos_totales': request.user.puntos,
                'mensaje': f'¡Felicidades! Has ganado {puntos_ganados} puntos en el juego.'
            })
        else:
            return JsonResponse({
                'success': False,
                'mensaje': 'Puntos inválidos.'
            })
    
    context = {
        'user': request.user,
        'puntos_actuales': request.user.puntos,
        'puntos_juego_plasticos': getattr(request.user, 'puntos_juego_plasticos', 0)
    }
    return render(request, 'core/juego_plasticos.html', context)

@login_required
def juego_vidrios(request):
    """Vista para el juego de fábrica de reciclaje de vidrios"""
    if request.method == 'POST':
        # Verificar si es una solicitud de canje
        if request.POST.get('canje') == 'true':
            puntos_canje = int(request.POST.get('puntos_canje', 0))
            puntos_juego_actuales = getattr(request.user, 'puntos_juego_vidrios', 0)
            
            # Verificar que el usuario tenga suficientes puntos
            if puntos_canje <= puntos_juego_actuales and puntos_canje >= 2:
                # Calcular EcoPuntos a ganar (2 puntos de juego = 1 EcoPunto)
                ecopuntos_ganados = puntos_canje // 2
                
                # Actualizar puntos del usuario
                request.user.puntos_juego_vidrios = puntos_juego_actuales - puntos_canje
                request.user.puntos += ecopuntos_ganados
                request.user.save()
                
                # Crear notificación
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='🔮 ¡Canje de puntos exitoso!',
                    mensaje=f'Has canjeado {puntos_canje} puntos de juego por {ecopuntos_ganados} EcoPuntos reales en el juego de vidrios.',
                    tipo='success'
                )
                
                return JsonResponse({
                    'success': True,
                    'puntos_juego_restantes': request.user.puntos_juego_vidrios,
                    'ecopuntos_totales': request.user.puntos,
                    'ecopuntos_ganados': ecopuntos_ganados
                })
            else:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'No tienes suficientes puntos para canjear o el mínimo es 2 puntos.'
                })
        
        # Procesar resultado del juego
        puntos_ganados = int(request.POST.get('puntos', 0))
        nivel_completado = request.POST.get('nivel', 1)
        combo_maximo = int(request.POST.get('combo_maximo', 0))
        
        # Validar que los puntos sean razonables (máximo 100 puntos por juego para vidrios)
        if 0 <= puntos_ganados <= 100:
            # Sistema de conversión: cada 8,000 puntos del juego = 15 puntos canjeables (mejor ratio para vidrios)
            puntos_juego_actuales = getattr(request.user, 'puntos_juego_vidrios', 0)
            puntos_juego_totales = puntos_juego_actuales + puntos_ganados
            
            # Calcular puntos canjeables
            puntos_canjeables_nuevos = (puntos_juego_totales // 8000) * 15
            puntos_canjeables_anteriores = (puntos_juego_actuales // 8000) * 15
            puntos_canjeables_ganados = puntos_canjeables_nuevos - puntos_canjeables_anteriores
            
            # Actualizar puntos de juego del usuario
            request.user.puntos_juego_vidrios = puntos_juego_totales
            
            # Si se ganaron puntos canjeables, agregarlos
            if puntos_canjeables_ganados > 0:
                request.user.puntos += puntos_canjeables_ganados
            
            request.user.save()
            
            # Crear notificación apropiada
            if puntos_canjeables_ganados > 0:
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='¡Cristales convertidos en puntos!',
                    mensaje=f'¡Increíble! Tu fábrica de vidrio ha generado {puntos_canjeables_ganados} puntos canjeables. Combo máximo: {combo_maximo}x. Total de cristales procesados: {puntos_juego_totales}',
                    tipo='success'
                )
            else:
                puntos_restantes = 8000 - (puntos_juego_totales % 8000)
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='¡Fábrica de vidrio en acción!',
                    mensaje=f'Has procesado {puntos_ganados} cristales. Total: {puntos_juego_totales}. Necesitas {puntos_restantes} cristales más para obtener puntos canjeables. ¡Combo máximo: {combo_maximo}x!',
                    tipo='info'
                )
            
            return JsonResponse({
                'success': True,
                'puntos_ganados': puntos_ganados,
                'puntos_juego_totales': puntos_juego_totales,
                'puntos_canjeables_ganados': puntos_canjeables_ganados,
                'puntos_totales': request.user.puntos,
                'combo_maximo': combo_maximo,
                'mensaje': f'¡Excelente! Has procesado {puntos_ganados} cristales en tu fábrica.'
            })
        else:
            return JsonResponse({
                'success': False,
                'mensaje': 'Puntos inválidos.'
            })
    
    context = {
        'user': request.user,
        'puntos_actuales': request.user.puntos,
        'puntos_juego_vidrios': getattr(request.user, 'puntos_juego_vidrios', 0)
    }
    return render(request, 'core/juego_vidrios.html', context)

@login_required
def juego_papel(request):
    """Vista para el juego de papel y cartón - Fábrica de Papel Ecológica"""
    if request.method == 'POST':
        # Verificar si es una solicitud de canje
        if request.POST.get('canje') == 'true':
            puntos_canje = int(request.POST.get('puntos_canje', 0))
            puntos_juego_actuales = getattr(request.user, 'puntos_juego_papel', 0)
            
            # Verificar que el usuario tenga suficientes puntos
            if puntos_canje <= puntos_juego_actuales and puntos_canje >= 2:
                # Calcular EcoPuntos a ganar (2 puntos de juego = 1 EcoPunto)
                ecopuntos_ganados = puntos_canje // 2
                
                # Actualizar puntos del usuario
                request.user.puntos_juego_papel = puntos_juego_actuales - puntos_canje
                request.user.puntos += ecopuntos_ganados
                request.user.save()
                
                # Crear notificación
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='📄 ¡Canje de puntos exitoso!',
                    mensaje=f'Has canjeado {puntos_canje} puntos de juego por {ecopuntos_ganados} EcoPuntos reales en el juego de papel.',
                    tipo='success'
                )
                
                return JsonResponse({
                    'success': True,
                    'puntos_juego_restantes': request.user.puntos_juego_papel,
                    'ecopuntos_totales': request.user.puntos,
                    'ecopuntos_ganados': ecopuntos_ganados
                })
            else:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'No tienes suficientes puntos para canjear o el mínimo es 2 puntos.'
                })
        
        puntos_ganados = int(request.POST.get('puntos', 0))
        nivel_completado = request.POST.get('nivel', 1)
        combo_maximo = int(request.POST.get('combo_maximo', 0))
        
        # Validar que los puntos sean razonables (máximo 120 puntos por juego para papel)
        if 0 <= puntos_ganados <= 120:
            # Sistema de conversión: cada 6,000 hojas procesadas = 20 puntos canjeables (excelente ratio)
            puntos_juego_actuales = getattr(request.user, 'puntos_juego_papel', 0)
            puntos_juego_totales = puntos_juego_actuales + puntos_ganados
            
            # Calcular puntos canjeables
            puntos_canjeables_nuevos = (puntos_juego_totales // 6000) * 20
            puntos_canjeables_anteriores = (puntos_juego_actuales // 6000) * 20
            puntos_canjeables_ganados = puntos_canjeables_nuevos - puntos_canjeables_anteriores
            
            # Actualizar puntos de juego del usuario
            request.user.puntos_juego_papel = puntos_juego_totales
            
            # Si se ganaron puntos canjeables, agregarlos
            if puntos_canjeables_ganados > 0:
                request.user.puntos += puntos_canjeables_ganados
            
            request.user.save()
            
            # Crear notificación apropiada
            if puntos_canjeables_ganados > 0:
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='🌳 ¡Hojas convertidas en puntos!',
                    mensaje=f'¡Fantástico! Tu fábrica de papel ha generado {puntos_canjeables_ganados} puntos canjeables. Combo máximo: {combo_maximo}x. Total de hojas procesadas: {puntos_juego_totales}. ¡Salvaste {puntos_juego_totales//100} árboles!',
                    tipo='success'
                )
            else:
                puntos_restantes = 6000 - (puntos_juego_totales % 6000)
                arboles_salvados = puntos_juego_totales // 100
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='📄 ¡Fábrica de papel activa!',
                    mensaje=f'Has procesado {puntos_ganados} hojas. Total: {puntos_juego_totales}. Necesitas {puntos_restantes} hojas más para obtener puntos canjeables. ¡Combo máximo: {combo_maximo}x! Árboles salvados: {arboles_salvados}',
                    tipo='info'
                )
            
            return JsonResponse({
                'success': True,
                'puntos_ganados': puntos_ganados,
                'puntos_juego_totales': puntos_juego_totales,
                'puntos_canjeables_ganados': puntos_canjeables_ganados,
                'puntos_totales': request.user.puntos,
                'combo_maximo': combo_maximo,
                'arboles_salvados': puntos_juego_totales // 100,
                'mensaje': f'¡Excelente! Has procesado {puntos_ganados} hojas en tu fábrica ecológica.'
            })
        else:
            return JsonResponse({
                'success': False,
                'mensaje': 'Puntos inválidos.'
            })
    
    context = {
        'user': request.user,
        'puntos_actuales': request.user.puntos,
        'puntos_juego_papel': getattr(request.user, 'puntos_juego_papel', 0)
    }
    return render(request, 'core/juego_papel.html', context)

@login_required
def juego_metales(request):
    """Vista para el juego de metales - Fundición Magnética"""
    if request.method == 'POST':
        # Verificar si es una solicitud de canje
        if request.POST.get('canje') == 'true':
            puntos_canje = int(request.POST.get('puntos_canje', 0))
            
            # Validar que el usuario tenga suficientes puntos de juego
            puntos_juego_actuales = getattr(request.user, 'puntos_juego_metales', 0)
            
            if puntos_canje <= puntos_juego_actuales and puntos_canje >= 2:
                # Calcular EcoPuntos a ganar (2 puntos de juego = 1 EcoPunto)
                ecopuntos_ganados = puntos_canje // 2
                
                # Actualizar puntos del usuario
                request.user.puntos_juego_metales = puntos_juego_actuales - puntos_canje
                request.user.puntos += ecopuntos_ganados
                request.user.save()
                
                # Crear notificación
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='💰 ¡Canje exitoso!',
                    mensaje=f'Has canjeado {puntos_canje} puntos de juego por {ecopuntos_ganados} EcoPuntos reales.',
                    tipo='success'
                )
                
                return JsonResponse({
                    'success': True,
                    'puntos_juego_restantes': request.user.puntos_juego_metales,
                    'ecopuntos_ganados': ecopuntos_ganados,
                    'ecopuntos_totales': request.user.puntos
                })
            else:
                return JsonResponse({
                    'success': False,
                    'mensaje': 'No tienes suficientes puntos para canjear o el mínimo es 2 puntos.'
                })
        
        # Lógica normal del juego
        puntos_ganados = int(request.POST.get('puntos', 0))
        nivel_completado = request.POST.get('nivel', 1)
        combo_maximo = int(request.POST.get('combo_maximo', 0))
        
        # Validar que los puntos sean razonables (máximo 150 puntos por juego para metales)
        if 0 <= puntos_ganados <= 150:
            # Sistema de conversión: cada 4,000 metales fundidos = 25 puntos canjeables (excelente ratio)
            puntos_juego_actuales = getattr(request.user, 'puntos_juego_metales', 0)
            puntos_juego_totales = puntos_juego_actuales + puntos_ganados
            
            # Calcular puntos canjeables
            puntos_canjeables_nuevos = (puntos_juego_totales // 4000) * 25
            puntos_canjeables_anteriores = (puntos_juego_actuales // 4000) * 25
            puntos_canjeables_ganados = puntos_canjeables_nuevos - puntos_canjeables_anteriores
            
            # Actualizar puntos de juego del usuario
            request.user.puntos_juego_metales = puntos_juego_totales
            
            # Si se ganaron puntos canjeables, agregarlos
            if puntos_canjeables_ganados > 0:
                request.user.puntos += puntos_canjeables_ganados
            
            request.user.save()
            
            # Crear notificación apropiada
            if puntos_canjeables_ganados > 0:
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='⚡ ¡Metales fundidos en puntos!',
                    mensaje=f'¡Increíble! Tu fundición magnética ha generado {puntos_canjeables_ganados} puntos canjeables. Combo máximo: {combo_maximo}x. Total de metales fundidos: {puntos_juego_totales}. ¡Ahorraste {puntos_juego_totales//50} toneladas de minería!',
                    tipo='success'
                )
            else:
                puntos_restantes = 4000 - (puntos_juego_totales % 4000)
                mineria_ahorrada = puntos_juego_totales // 50
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='🔥 ¡Fundición magnética activa!',
                    mensaje=f'Has fundido {puntos_ganados} metales. Total: {puntos_juego_totales}. Necesitas {puntos_restantes} metales más para obtener puntos canjeables. ¡Combo máximo: {combo_maximo}x! Minería ahorrada: {mineria_ahorrada} toneladas',
                    tipo='info'
                )
            
            return JsonResponse({
                'success': True,
                'puntos_ganados': puntos_ganados,
                'puntos_juego_totales': puntos_juego_totales,
                'puntos_canjeables_ganados': puntos_canjeables_ganados,
                'puntos_totales': request.user.puntos,
                'combo_maximo': combo_maximo,
                'mineria_ahorrada': puntos_juego_totales // 50,
                'mensaje': f'¡Excelente! Has fundido {puntos_ganados} metales en tu fundición magnética.'
            })
        else:
            return JsonResponse({
                'success': False,
                'mensaje': 'Puntos inválidos.'
            })
    
    context = {
        'user': request.user,
        'puntos_actuales': request.user.puntos,
        'puntos_juego_metales': getattr(request.user, 'puntos_juego_metales', 0)
    }
    return render(request, 'core/juego_metales.html', context)

@login_required
@throttle_canjes
def canjes(request):
    """Vista simplificada para canjes básicos (sin recolección domiciliaria)"""
    from .forms import CanjeSimpleForm
    from .notifications import NotificacionEmail
    
    if request.method == 'POST':
        form = CanjeSimpleForm(request.POST, request.FILES)
        if form.is_valid():
            canje = form.save(commit=False)
            canje.usuario = request.user
            
            # Calcular puntos basados en peso y material
            material = form.cleaned_data['material']
            peso = form.cleaned_data['peso']
            
            # Usar puntos_por_kilo si está disponible, sino precio_por_kg
            puntos_por_kilo = getattr(material, 'puntos_por_kilo', None) or material.precio_por_kg
            canje.puntos = int(peso * puntos_por_kilo)
            
            # Estado inicial siempre pendiente para canjes básicos
            canje.estado = 'pendiente'
            canje.necesita_recoleccion = False
            
            canje.save()
            
            # Enviar notificación por email
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                subject = 'Solicitud de Canje Recibida - EcoPuntos'
                message = f"""
Hola {request.user.first_name or request.user.username},

Tu solicitud de canje ha sido recibida y está en proceso de revisión por nuestro equipo.

Detalles del canje:
- Material: {material.nombre}
- Peso estimado: {peso} kg
- Puntos estimados: {canje.puntos}

Te notificaremos por email cuando tu canje sea aprobado o revisado.

Gracias por reciclar y sumar puntos ecológicos.

Equipo EcoPuntos
"""
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [request.user.email],
                    fail_silently=False,
                )
                print("✅ Email de canje enviado exitosamente")
            except Exception as e:
                print(f"❌ Error enviando email de canje: {e}")
            
            # Crear notificación en el sistema
            try:
                from .views import crear_notificacion
                crear_notificacion(
                    request.user,
                    'Canje Solicitado',
                    f'Tu solicitud de canje de {peso}kg de {material.nombre} ha sido recibida y está siendo revisada.'
                )
            except:
                pass  # Si no funciona la notificación, continuar
            
            return JsonResponse({
                'success': True,
                'message': 'Canje solicitado exitosamente. Será revisado por nuestro equipo. Te notificaremos por email.',
                'puntos_estimados': canje.puntos
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    # GET request - mostrar formulario
    form = CanjeSimpleForm()
    materials = MaterialTasa.objects.filter(activo=True).order_by('nombre')
    
    # Obtener canjes del usuario
    user_canjes = []
    if request.user.is_authenticated:
        canjes_query = Canje.objects.filter(usuario=request.user).order_by('-fecha_solicitud')
        for canje in canjes_query:
            canje_data = {
                'canje': canje,
                'ruta_info': None  # Los canjes básicos no tienen ruta asociada
            }
            user_canjes.append(canje_data)
    
    context = {
        'form': form,
        'materials': materials,
        'user_canjes': user_canjes,
        'show_simple_view': True
    }
    return render(request, 'core/canjes.html', context)

def historial(request):
    if not request.user.is_authenticated:
        return redirect('iniciosesion')
    from .models import Canje, RedencionPuntos
    import json
    
    # Todos los canjes para mostrar en el historial
    canjes = Canje.objects.filter(usuario=request.user).order_by('-fecha_solicitud')
    redenciones = RedencionPuntos.objects.filter(usuario=request.user).order_by('-fecha_solicitud')
    
    # Solo canjes aprobados para estadísticas
    canjes_aprobados = canjes.filter(estado='aprobado')
    
    # Estadísticas basadas únicamente en canjes aprobados
    total_canjes = canjes_aprobados.count()
    total_puntos = sum(c.puntos_finales or c.puntos for c in canjes_aprobados)
    total_dinero = sum(r.valor_cop for r in redenciones if r.estado == 'completado')
    
    # Calcular peso total reciclado (solo aprobados)
    total_peso_reciclado = sum(c.peso_real or c.peso for c in canjes_aprobados)
    
    # Datos para gráficas (solo canjes aprobados)
    from collections import defaultdict
    import datetime
    puntos_por_mes = defaultdict(int)
    dinero_por_mes = defaultdict(int)
    canjes_por_mes = defaultdict(int)
    materiales_stats = defaultdict(lambda: {'count': 0, 'puntos': 0, 'peso': 0})
    
    for c in canjes_aprobados:
        mes = c.fecha_solicitud.strftime('%Y-%m')
        mes_nombre = c.fecha_solicitud.strftime('%b')
        puntos = c.puntos_finales or c.puntos
        peso = c.peso_real or c.peso
        
        puntos_por_mes[mes_nombre] += puntos
        canjes_por_mes[mes_nombre] += 1
        
        # Estadísticas por material
        material_nombre = c.material.nombre
        materiales_stats[material_nombre]['count'] += 1
        materiales_stats[material_nombre]['puntos'] += puntos
        materiales_stats[material_nombre]['peso'] += float(peso)
    
    for r in redenciones:
        if r.estado == 'completado':
            mes = r.fecha_solicitud.strftime('%b')
            dinero_por_mes[mes] += float(r.valor_cop)
    
    meses = list({*puntos_por_mes.keys(), *dinero_por_mes.keys(), *canjes_por_mes.keys()})
    meses.sort(key=lambda m: datetime.datetime.strptime(m, '%b').month)
    
    # Preparar datos para gráficas avanzadas
    materiales_nombres = list(materiales_stats.keys())
    materiales_counts = [materiales_stats[m]['count'] for m in materiales_nombres]
    materiales_puntos = [materiales_stats[m]['puntos'] for m in materiales_nombres]
    materiales_pesos = [round(materiales_stats[m]['peso'], 2) for m in materiales_nombres]
    
    # Estadísticas adicionales
    promedio_puntos_por_canje = round(total_puntos / max(total_canjes, 1), 2)
    promedio_peso_por_canje = round(float(total_peso_reciclado) / max(total_canjes, 1), 2)
    
    context = {
        'canjes': canjes,
        'redenciones': redenciones,
        'canjes_aprobados': canjes_aprobados,
        'total_canjes': total_canjes,
        'total_puntos': total_puntos,
        'total_dinero': total_dinero,
        'total_peso_reciclado': total_peso_reciclado,
        'promedio_puntos_por_canje': promedio_puntos_por_canje,
        'promedio_peso_por_canje': promedio_peso_por_canje,
        
        # Datos para gráficas básicas
        'puntos_por_mes_json': json.dumps([puntos_por_mes[m] for m in meses]),
        'dinero_por_mes_json': json.dumps([dinero_por_mes[m] for m in meses]),
        'canjes_por_mes_json': json.dumps([canjes_por_mes[m] for m in meses]),
        'meses_json': json.dumps(meses),
        'meses': meses,
        
        # Datos para gráficas avanzadas
        'materiales_nombres_json': json.dumps(materiales_nombres),
        'materiales_counts_json': json.dumps(materiales_counts),
        'materiales_puntos_json': json.dumps(materiales_puntos),
        'materiales_pesos_json': json.dumps(materiales_pesos),
    }
    return render(request, 'core/historial.html', context)

def logros(request):
    if not request.user.is_authenticated:
        return redirect('iniciosesion')
    from .models import Logro
    logros_usuario = Logro.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'core/logros.html', {'logros': logros_usuario})

def recompensas(request):
    if not request.user.is_authenticated:
        return redirect('iniciosesion')
    from .models import Recompensa, RedencionPuntos, Categoria, FavoritoRecompensa
    from django.db.models import Q
    import json
    
    # Obtener parámetros de filtro
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('busqueda', '')
    orden = request.GET.get('orden', 'puntos_asc')
    rango_puntos = request.GET.get('rango_puntos')
    solo_disponibles = request.GET.get('solo_disponibles') == 'true'
    solo_favoritos = request.GET.get('solo_favoritos') == 'true'
    
    # Filtrar recompensas
    recompensas = Recompensa.objects.filter(activa=True)
    
    if categoria_id:
        recompensas = recompensas.filter(categoria_id=categoria_id)
    
    if busqueda:
        recompensas = recompensas.filter(
            Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )
    
    if rango_puntos:
        if rango_puntos == '0-100':
            recompensas = recompensas.filter(puntos_requeridos__lte=100)
        elif rango_puntos == '100-500':
            recompensas = recompensas.filter(puntos_requeridos__gte=100, puntos_requeridos__lte=500)
        elif rango_puntos == '500+':
            recompensas = recompensas.filter(puntos_requeridos__gte=500)
    
    if solo_disponibles:
        recompensas = recompensas.filter(stock__gt=0)
    
    if solo_favoritos:
        favoritos_ids = FavoritoRecompensa.objects.filter(usuario=request.user).values_list('recompensa_id', flat=True)
        recompensas = recompensas.filter(id__in=favoritos_ids)
    
    # Ordenar
    if orden == 'puntos_asc':
        recompensas = recompensas.order_by('puntos_requeridos')
    elif orden == 'puntos_desc':
        recompensas = recompensas.order_by('-puntos_requeridos')
    elif orden == 'nombre':
        recompensas = recompensas.order_by('nombre')
    elif orden == 'popular':
        recompensas = recompensas.order_by('-veces_canjeada')
    elif orden == 'nuevo':
        recompensas = recompensas.order_by('-fecha_creacion')
    
    recompensas_reclamables = recompensas.filter(puntos_requeridos__lte=request.user.puntos)
    
    # Obtener favoritos del usuario
    favoritos_ids = list(FavoritoRecompensa.objects.filter(usuario=request.user).values_list('recompensa_id', flat=True))
    
    # Manejar POST requests
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'canjear':
            recompensa_id = request.POST.get('recompensa_id')
            recompensa = Recompensa.objects.filter(id=recompensa_id, activa=True).first()
            
            if recompensa and recompensa.puntos_requeridos <= request.user.puntos and recompensa.stock > 0:
                from django.db import transaction
                from .models import MovimientoStock
                
                with transaction.atomic():
                    # Registrar la redención
                    redencion = RedencionPuntos.objects.create(
                        usuario=request.user,
                        puntos=recompensa.puntos_requeridos,
                        valor_cop=0,
                        metodo_pago='nequi',
                        numero_cuenta='-',
                        estado='pendiente',
                    )
                    
                    # Descontar puntos del usuario
                    request.user.puntos -= recompensa.puntos_requeridos
                    request.user.save()
                    
                    # Registrar movimiento de stock ANTES de actualizar
                    stock_anterior = recompensa.stock
                    MovimientoStock.objects.create(
                        recompensa=recompensa,
                        tipo_movimiento='canje',
                        cantidad_anterior=stock_anterior,
                        cantidad_nueva=stock_anterior - 1,
                        cantidad_cambiada=-1,
                        motivo=f'Canje de recompensa por usuario {request.user.username}',
                        usuario_responsable=request.user,
                        canje_relacionado=None  # Podríamos crear un campo para RedencionPuntos si es necesario
                    )
                    
                    # Descontar stock
                    recompensa.stock -= 1
                recompensa.veces_canjeada += 1
                recompensa.save()
                
                # Crear notificación principal
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='Recompensa Canjeada',
                    mensaje=f'¡Felicidades! Has canjeado exitosamente la recompensa "{recompensa.nombre}" por {recompensa.puntos_requeridos} puntos.',
                    tipo='recompensa_canjeada'
                )
                
                # Crear seguimiento de recompensa
                from datetime import datetime, timedelta
                
                # Obtener dirección de entrega (priorizar la del formulario)
                direccion_formulario = request.POST.get('direccion_entrega', '').strip()
                if direccion_formulario:
                    direccion_usuario = direccion_formulario
                    direccion_incompleta = False
                else:
                    # Usar dirección del perfil como fallback
                    direccion_usuario = getattr(request.user, 'direccion', '') or ''
                    direccion_incompleta = False
                    if not direccion_usuario.strip():
                        direccion_usuario = 'Dirección no especificada - Por favor actualiza tu perfil'
                        direccion_incompleta = True
                
                # Obtener teléfono del usuario con validación
                telefono_usuario = getattr(request.user, 'telefono', '') or ''
                if not telefono_usuario.strip():
                    telefono_usuario = 'No especificado'
                
                # Notificación adicional si el perfil está incompleto
                if direccion_incompleta:
                    Notificacion.objects.create(
                        usuario=request.user,
                        titulo='Actualiza tu Perfil',
                        mensaje=f'Para recibir tu recompensa "{recompensa.nombre}", por favor actualiza tu dirección de entrega en tu perfil.',
                        tipo='perfil_incompleto'
                    )
                
                try:
                    seguimiento = SeguimientoRecompensa.objects.create(
                        usuario=request.user,
                        recompensa=recompensa,
                        redencion=redencion,
                        direccion_entrega=direccion_usuario,
                        telefono_contacto=telefono_usuario,
                        fecha_estimada_entrega=timezone.now() + timedelta(days=3),  # Estimación de 3 días
                        estado='solicitado'
                    )
                except Exception as e:
                    print(f"Error creando seguimiento: {e}")
                    # Si falla la creación del seguimiento, continuar sin interrumpir el canje
                    seguimiento = None
                
                # Crear primer registro en historial solo si el seguimiento se creó exitosamente
                if seguimiento:
                    try:
                        HistorialSeguimiento.objects.create(
                            seguimiento=seguimiento,
                            estado_anterior=None,
                            estado_nuevo='solicitado',
                            comentario=f'Recompensa "{recompensa.nombre}" solicitada exitosamente',
                            usuario_responsable=request.user
                        )
                    except Exception as e:
                        print(f"Error creando historial: {e}")
                
                # Enviar correo de confirmación de recompensa canjeada
                try:
                    enviar_correo_recompensa_canjeada(request.user, recompensa, redencion)
                except Exception as e:
                    # Si falla el correo, continuar sin interrumpir el proceso
                    pass
                
                # No usar messages.success(), confiar en el sistema de notificaciones
                return redirect('recompensas')
            else:
                # No usar messages.error(), el usuario verá el estado actual en la página
                return redirect('recompensas')
        
        elif action == 'toggle_favorito':
            recompensa_id = request.POST.get('recompensa_id')
            recompensa = Recompensa.objects.filter(id=recompensa_id).first()
            
            if recompensa:
                favorito, created = FavoritoRecompensa.objects.get_or_create(
                    usuario=request.user,
                    recompensa=recompensa
                )
                
                if not created:
                    favorito.delete()
                    return JsonResponse({'favorito': False})
                else:
                    return JsonResponse({'favorito': True})
    
    # Obtener categorías para filtros
    categorias = Categoria.objects.filter(activa=True)
    
    # Obtener seguimientos del usuario
    mis_seguimientos = []
    if request.user.is_authenticated:
        mis_seguimientos = SeguimientoRecompensa.objects.filter(
            usuario=request.user
        ).select_related('recompensa', 'redencion').prefetch_related('historial').order_by('-fecha_solicitud')
    
    context = {
        'recompensas': recompensas,
        'recompensas_reclamables': recompensas_reclamables,
        'categorias': categorias,
        'favoritos_ids': favoritos_ids,
        'mis_seguimientos': mis_seguimientos,
        'filtros': {
            'categoria_id': categoria_id,
            'busqueda': busqueda,
            'orden': orden,
            'rango_puntos': rango_puntos,
            'solo_disponibles': solo_disponibles,
            'solo_favoritos': solo_favoritos,
        }
    }
    
    return render(request, 'core/recompensas.html', context)

def configuracion(request):
    return render(request, 'core/configuracion.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def retiroadmin(request):
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión como administrador para acceder a la gestión de retiros.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea administrador
    if not is_admin(request.user):
        messages.error(request, 'No tienes permisos de administrador para acceder a esta página.')
        return redirect('inicioadmin')
    
    return render(request, 'core/retiroadmin.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def stock_recompensas(request):
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión como administrador para acceder al stock de recompensas.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea administrador
    if not is_admin(request.user):
        messages.error(request, 'No tienes permisos de administrador para acceder a esta página.')
        return redirect('inicioadmin')
    
    # Obtener todas las recompensas disponibles
    from .models import Recompensa
    recompensas = Recompensa.objects.all().order_by('categoria', 'nombre')
    
    # Calcular estadísticas avanzadas
    total_recompensas = recompensas.count()
    stock_bajo = recompensas.filter(stock__lte=5, stock__gt=0).count()
    agotadas = recompensas.filter(stock=0).count()
    activas = recompensas.filter(activa=True).count()
    
    # Calcular valor total del inventario
    valor_total_inventario = sum(r.stock * r.puntos_requeridos for r in recompensas)
    
    # Recompensas que necesitan atención
    recompensas_criticas = recompensas.filter(stock__lte=3, activa=True)
    
    # Obtener las 5 más canjeadas (basado en veces_canjeada si existe)
    from django.db.models import F
    recompensas_populares = recompensas.filter(activa=True).order_by('-veces_canjeada')[:5]
    
    # OBTENER DATOS DE SEGUIMIENTOS
    seguimientos = SeguimientoRecompensa.objects.select_related(
        'usuario', 'recompensa', 'redencion'
    ).prefetch_related('historial').order_by('-fecha_solicitud')
    
    # Estadísticas de seguimientos
    from django.db.models import Count, Q
    total_seguimientos = seguimientos.count()
    seguimientos_pendientes = seguimientos.filter(Q(estado='SOLICITADO') | Q(estado='PREPARANDO')).count()
    seguimientos_proceso = seguimientos.filter(estado='EN_CAMINO').count()
    seguimientos_completados = seguimientos.filter(estado='ENTREGADO').count()
    
    # Convertir seguimientos a formato JSON-like para el template
    seguimientos_data = []
    for s in seguimientos:
        seguimientos_data.append({
            'id': s.id,
            'codigo': s.codigo_seguimiento,
            'usuario': s.usuario.username,
            'telefono': s.telefono_contacto or '',
            'recompensa': s.recompensa.nombre,
            'puntos': s.recompensa.puntos_requeridos,
            'estado': s.estado,
            'estado_display': s.get_estado_display(),
            'progreso': s.porcentaje_progreso,
            'fecha_solicitud': s.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
            'fecha_estimada': s.fecha_estimada_entrega.strftime('%d/%m/%Y') if s.fecha_estimada_entrega else None,
            'direccion': s.direccion_entrega[:50] + '...' if len(s.direccion_entrega) > 50 else s.direccion_entrega,
        })
    
    context = {
        'recompensas': recompensas,
        'total_recompensas': total_recompensas,
        'stock_bajo': stock_bajo,
        'agotadas': agotadas,
        'activas': activas,
        'valor_total_inventario': valor_total_inventario,
        'recompensas_criticas': recompensas_criticas,
        'recompensas_populares': recompensas_populares,
        # DATOS DE SEGUIMIENTOS
        'seguimientos_data': seguimientos_data,
        'total_seguimientos': total_seguimientos,
        'seguimientos_pendientes': seguimientos_pendientes,
        'seguimientos_proceso': seguimientos_proceso,
        'seguimientos_completados': seguimientos_completados,
    }
    
    return render(request, 'core/stock_recompensas.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def editar_stock_recompensa(request, recompensa_id):
    """Vista para editar el stock de una recompensa"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'No tienes permisos de administrador.'})
    
    try:
        from .models import Recompensa, MovimientoStock
        from django.db import transaction
        
        recompensa = get_object_or_404(Recompensa, id=recompensa_id)
        nuevo_stock = int(request.POST.get('nuevo_stock', 0))
        motivo = request.POST.get('motivo', 'Ajuste manual desde panel de administración')
        
        if nuevo_stock < 0:
            return JsonResponse({'success': False, 'message': 'El stock no puede ser negativo.'})
        
        with transaction.atomic():
            stock_anterior = recompensa.stock
            cambio = nuevo_stock - stock_anterior
            
            # Crear registro de movimiento
            MovimientoStock.objects.create(
                recompensa=recompensa,
                tipo_movimiento='ajuste_manual',
                cantidad_anterior=stock_anterior,
                cantidad_nueva=nuevo_stock,
                cantidad_cambiada=cambio,
                motivo=motivo,
                usuario_responsable=request.user
            )
            
            # Actualizar stock
            recompensa.stock = nuevo_stock
            recompensa.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Stock actualizado correctamente. Cambio: {cambio:+d}',
                'nuevo_stock': nuevo_stock,
                'stock_anterior': stock_anterior
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al actualizar stock: {str(e)}'})

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def toggle_recompensa(request, recompensa_id):
    """Vista para activar/desactivar una recompensa"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'No tienes permisos de administrador.'})
    
    try:
        from .models import Recompensa
        recompensa = get_object_or_404(Recompensa, id=recompensa_id)
        
        recompensa.activa = not recompensa.activa
        recompensa.save()
        
        estado = "activada" if recompensa.activa else "desactivada"
        return JsonResponse({
            'success': True, 
            'message': f'Recompensa {estado} correctamente.',
            'nueva_estado': recompensa.activa
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al cambiar estado: {str(e)}'})

@login_required
@user_passes_test(lambda u: u.is_staff)
def agregar_recompensa(request):
    """Vista para agregar una nueva recompensa"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'No tienes permisos de administrador.'})
    
    if request.method == 'POST':
        try:
            from .models import Recompensa, Categoria
            
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion', '')
            puntos_requeridos = int(request.POST.get('puntos_requeridos'))
            stock = int(request.POST.get('stock', 0))
            categoria_id = request.POST.get('categoria_id')
            imagen = request.POST.get('imagen', 'core/img/recom.jpg')
            
            if not nombre or puntos_requeridos <= 0:
                return JsonResponse({'success': False, 'message': 'Datos inválidos. Verifica nombre y puntos.'})
            
            categoria = None
            if categoria_id:
                categoria = get_object_or_404(Categoria, id=categoria_id)
            
            recompensa = Recompensa.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                puntos_requeridos=puntos_requeridos,
                stock=stock,
                categoria=categoria,
                imagen=imagen,
                activa=True
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Recompensa creada correctamente.',
                'recompensa_id': recompensa.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al crear recompensa: {str(e)}'})
    
    # GET request - mostrar formulario
    from .models import Categoria
    categorias = Categoria.objects.filter(activa=True)
    context = {'categorias': categorias}
    return render(request, 'core/agregar_recompensa.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def historial_stock(request, recompensa_id):
    """Vista para ver el historial de movimientos de una recompensa"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'No tienes permisos de administrador.'})
    
    try:
        from .models import Recompensa, MovimientoStock
        recompensa = get_object_or_404(Recompensa, id=recompensa_id)
        movimientos = MovimientoStock.objects.filter(recompensa=recompensa).order_by('-fecha_movimiento')[:20]
        
        context = {
            'recompensa': recompensa,
            'movimientos': movimientos
        }
        return render(request, 'core/historial_stock.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al cargar historial: {str(e)}')
        return redirect('stock_recompensas')

@login_required
@user_passes_test(lambda u: u.is_staff)
def reabastecer_stock(request, recompensa_id):
    """Vista para reabastecer stock de una recompensa"""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'No tienes permisos de administrador.'})
    
    if request.method == 'POST':
        try:
            from .models import Recompensa, MovimientoStock
            from django.db import transaction
            
            recompensa = get_object_or_404(Recompensa, id=recompensa_id)
            cantidad_agregar = int(request.POST.get('cantidad_agregar', 0))
            motivo = request.POST.get('motivo', 'Reabastecimiento')
            proveedor = request.POST.get('proveedor', '')
            
            if cantidad_agregar <= 0:
                return JsonResponse({'success': False, 'message': 'La cantidad debe ser mayor a 0.'})
            
            with transaction.atomic():
                stock_anterior = recompensa.stock
                nuevo_stock = stock_anterior + cantidad_agregar
                
                # Crear registro de movimiento
                MovimientoStock.objects.create(
                    recompensa=recompensa,
                    tipo_movimiento='reabastecimiento',
                    cantidad_anterior=stock_anterior,
                    cantidad_nueva=nuevo_stock,
                    cantidad_cambiada=cantidad_agregar,
                    motivo=f"{motivo} - Proveedor: {proveedor}" if proveedor else motivo,
                    usuario_responsable=request.user
                )
                
                # Actualizar stock
                recompensa.stock = nuevo_stock
                recompensa.save()
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Stock reabastecido correctamente. +{cantidad_agregar} unidades',
                    'nuevo_stock': nuevo_stock,
                    'stock_anterior': stock_anterior
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al reabastecer: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

def pagos(request):
    # Obtener historial de redenciones del usuario (últimas 10)
    transactions = RedencionPuntos.objects.filter(usuario=request.user).order_by('-fecha_solicitud')[:10]
    
    # Calcular estadísticas
    total_redenciones = RedencionPuntos.objects.filter(usuario=request.user).count()
    total_puntos_canjeados = RedencionPuntos.objects.filter(usuario=request.user).aggregate(
        total=models.Sum('puntos')
    )['total'] or 0
    
    context = {
        'transactions': transactions,
        'user': request.user,
        'total_redenciones': total_redenciones,
        'total_puntos_canjeados': total_puntos_canjeados,
    }
    
    return render(request, 'core/pagos.html', context)

def usuarioadmin(request):
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión como administrador para acceder a la gestión de usuarios.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea administrador
    if not is_admin(request.user):
        messages.error(request, 'No tienes permisos de administrador para acceder a esta página.')
        return redirect('inicioadmin')
    
    User = get_user_model()
    users = User.objects.all().order_by('-fecha_registro')
    
    # Estadísticas
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    new_users = users.filter(fecha_registro__month=timezone.now().month).count()
    total_points = sum(user.puntos for user in users)
    
    # Paginación
    paginator = Paginator(users, 10)  # 10 usuarios por página
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    context = {
        'users': users,
        'total_users': total_users,
        'active_users': active_users,
        'new_users': new_users,
        'total_points': total_points,
    }
    
    return render(request, 'core/usuarioadmin.html', context)

def canjeadmin(request):
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión como administrador o conductor para acceder a la gestión de canjes.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea administrador o conductor
    if request.user.role not in ['admin', 'superuser', 'conductor']:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('inicioadmin')
        
    # Canjes recientes (filtrados por estado pendiente para administración)
    pending_exchanges = Canje.objects.select_related('usuario', 'material').filter(
        estado='pendiente'
    ).order_by('-fecha_solicitud')
    
    # Canjes procesados (aprobados y rechazados) para el historial
    processed_exchanges = Canje.objects.select_related('usuario', 'material').filter(
        estado__in=['aprobado', 'rechazado']
    ).order_by('-fecha_procesamiento', '-fecha_solicitud')[:100]  # Últimos 100 canjes procesados

    context = {
        'pending_exchanges': pending_exchanges,
        'processed_exchanges': processed_exchanges,
        'is_conductor': request.user.role == 'conductor',  # Para mostrar/ocultar opciones en el template
    }
    return render(request, 'core/canjeadmin.html', context)

from django.db import connection
from django.views.decorators.cache import cache_page
from django.core.cache import cache

@cache_page(60)  # Cache la página por 60 segundos
def dashusuario(request):
    if not request.user.is_authenticated:
        return redirect('iniciosesion')
    
    user = request.user
    # Verificar si el usuario está inactivo o suspendido
    if not user.is_active:
        return redirect('usuario_desactivado')
    elif hasattr(user, 'suspended') and user.suspended:
        return redirect('usuario_suspendido')
        
    # Usar el debugger de Django para ver las consultas SQL
    connection.queries
    
    # Definir los niveles y puntos requeridos
    levels = {
        'guardian_verde': 0,
        'defensor_planeta': 100,
        'heroe_eco': 500,
        'embajador_ambiental': 1000,
        'leyenda_sustentable': 2000,
    }
    
    current_level = 'guardian_verde'
    next_level_points = 0
    next_level_name = 'N/A'

    sorted_levels = sorted(levels.items(), key=lambda item: item[1])

    for i, (name, points_needed) in enumerate(sorted_levels):
        if user.puntos >= points_needed:
            current_level = name
            if i + 1 < len(sorted_levels):
                next_level_name = sorted_levels[i+1][0]
                next_level_points = sorted_levels[i+1][1]
            else:
                next_level_name = 'Máximo Nivel'
                next_level_points = user.puntos # Already at max, show current points
        else:
            if i > 0:
                # This is the first level where user.puntos is less than points_needed
                # So, the previous level is the current level, and this is the next.
                next_level_name = name
                next_level_points = points_needed
            break # Found the level, no need to check further
    
    # Calcular progreso para el siguiente nivel
    progress_from = 0
    if current_level != 'Máximo Nivel':
        for name, points_needed in sorted_levels:
            if name == current_level:
                progress_from = points_needed
                break

    # Evitar división por cero si el siguiente nivel es 0 puntos
    if next_level_points - progress_from > 0:
        progress_percentage = ((user.puntos - progress_from) / (next_level_points - progress_from)) * 100
    else:
        progress_percentage = 100 # Si ya alcanzó o superó el siguiente nivel (o es el nivel inicial sin un siguiente)
    # Calcular puntos restantes para el siguiente nivel
    points_needed = max(0, next_level_points - user.puntos) if next_level_name != 'Máximo Nivel' else 0
    
    # Obtener estadísticas del usuario
    recent_exchanges = []
    logros_usuario = []
    notificaciones = []
    recompensas_favoritas = []
    
    try:
        # Obtener canjes recientes
        recent_exchanges = Canje.objects.filter(usuario=user).order_by('-fecha_solicitud')[:5]
        print("✓ Canjes recientes obtenidos correctamente")
    except Exception as e:
        print(f"✗ Error obteniendo canjes recientes: {e}")
        
    try:
        # Obtener logros del usuario
        logros_usuario = Logro.objects.filter(usuario=user)[:5]
        print("✓ Logros obtenidos correctamente")
    except Exception as e:
        print(f"✗ Error obteniendo logros: {e}")
        
    try:
        # Obtener notificaciones recientes
        notificaciones = Notificacion.objects.filter(usuario=user, leida=False)[:5]
        print("✓ Notificaciones obtenidas correctamente")
    except Exception as e:
        print(f"✗ Error obteniendo notificaciones: {e}")
        
    try:
        # Obtener recompensas favoritas
        favoritos_ids = FavoritoRecompensa.objects.filter(usuario=user).values_list('recompensa_id', flat=True)
        recompensas_favoritas = Recompensa.objects.filter(id__in=favoritos_ids)[:3]
        print("✓ Recompensas favoritas obtenidas correctamente")
    except Exception as e:
        print(f"✗ Error obteniendo recompensas favoritas: {e}")
    
    # Obtener categorías activas
    try:
        categorias = Categoria.objects.filter(activa=True).exclude(nombre__in=[
            'Electrónicos',
            'Hogar Y Jardín',
            'Deportes Y Fitness',
            'Alimentación',
            'Belleza Y Cuidado Personal',
            'Libros Y Educación',
        ])
    except Exception as e:
        print(f"✗ Error obteniendo categorías: {e}")
        categorias = []

    # Calcular el número total de canjes
    canjes_count = recent_exchanges.count() if recent_exchanges else 0
    
    # Datos para Centro de Actividad Reciente
    try:
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Actividades recientes (últimos 10 días)
        recent_activities = []
        
        # Agregar canjes recientes
        recent_canjes = Canje.objects.filter(
            usuario=user, 
            fecha_solicitud__gte=timezone.now() - timedelta(days=10)
        ).order_by('-fecha_solicitud')[:3]
        
        for canje in recent_canjes:
            recent_activities.append({
                'tipo': 'canje',
                'descripcion': f'Canjeaste {canje.peso}kg de {canje.material.nombre}',
                'fecha': canje.fecha_solicitud,
                'puntos': canje.puntos,
            })
        
        # Agregar logros recientes
        recent_logros = Logro.objects.filter(
            usuario=user,
            fecha_creacion__gte=timezone.now() - timedelta(days=30)
        ).order_by('-fecha_creacion')[:2]
        
        for logro in recent_logros:
            recent_activities.append({
                'tipo': 'logro',
                'descripcion': f'Desbloqueaste el logro "{logro.descripcion}"',
                'fecha': logro.fecha_creacion,
                'puntos': getattr(logro, 'puntos', 0),
            })
        
        # Ordenar actividades por fecha
        recent_activities = sorted(recent_activities, key=lambda x: x['fecha'], reverse=True)[:5]
        
        # Estadísticas de la semana
        week_start = timezone.now() - timedelta(days=7)
        weekly_canjes = Canje.objects.filter(
            usuario=user,
            fecha_solicitud__gte=week_start,
            estado__in=['aprobado', 'completado']
        )
        weekly_points = sum(canje.puntos for canje in weekly_canjes) or 0
        
        # Calcular racha actual (días consecutivos con actividad)
        current_streak = 1
        for i in range(1, 30):  # Revisar últimos 30 días
            date_check = timezone.now().date() - timedelta(days=i)
            day_activity = Canje.objects.filter(
                usuario=user,
                fecha_solicitud__date=date_check
            ).exists()
            if day_activity:
                current_streak += 1
            else:
                break
        
        # Próxima recompensa alcanzable
        next_reward = Recompensa.objects.filter(
            puntos_requeridos__gt=user.puntos,
            activa=True
        ).order_by('puntos_requeridos').first()
        
        # Calcular puntos restantes
        next_reward_points_remaining = 0
        if next_reward:
            next_reward_points_remaining = next_reward.puntos_requeridos - user.puntos
        else:
            # Si no hay próxima recompensa, usar el siguiente nivel
            next_reward_points_remaining = max(0, 1000 - user.puntos)
        
    except Exception as e:
        print(f"✗ Error calculando datos de actividad reciente: {e}")
        recent_activities = []
        weekly_points = 0
        current_streak = 1
        next_reward = None
        next_reward_points_remaining = 0
    
    context = {
        'user': user,
        'current_level': current_level,
        'next_level_name': next_level_name,
        'next_level_points': next_level_points,
        'progress_from': progress_from,
        'progress_percentage': min(100, progress_percentage),
        'points_needed': points_needed,
        'levels': levels,
        'recent_exchanges': recent_exchanges,
        'logros_usuario': logros_usuario,
        'notificaciones': notificaciones,
        'recompensas_favoritas': recompensas_favoritas,
        'categorias': categorias,
        'canjes_count': canjes_count,
        # Nuevos datos para Centro de Actividad Reciente
        'recent_activities': recent_activities,
        'weekly_points': weekly_points,
        'current_streak': current_streak,
        'next_reward': next_reward,
        'next_reward_points_remaining': next_reward_points_remaining,
    }
    return render(request, 'core/dashusuario.html', context)

def is_admin(user):
    return user.is_authenticated and (hasattr(user, 'is_admin_user') and user.is_admin_user()) or (hasattr(user, 'is_elevated_user') and user.is_elevated_user())

def ajax_required_admin(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        print(f"DEBUG: Ejecutando ajax_required_admin para {request.path}")
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                print("DEBUG: No autenticado (AJAX)")
                return JsonResponse({'success': False, 'message': 'No autenticado.'}, status=401)
            print("DEBUG: No autenticado (HTML)")
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
        
        # Permitir acceso a admin, superuser y conductor
        if not (is_admin(request.user) or request.user.role == 'conductor'):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                print("DEBUG: No tiene permisos (AJAX)")
                return JsonResponse({'success': False, 'message': 'Acceso denegado. Se requieren permisos de administrador o conductor.'}, status=403)
            print("DEBUG: No tiene permisos (HTML)")
            return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
            
        print("DEBUG: Acceso permitido.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def paneladmin(request):
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión como administrador para acceder al panel.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea administrador
    if not is_admin(request.user):
        messages.error(request, 'No tienes permisos de administrador para acceder a esta página.')
        return redirect('inicioadmin')
    
    return render(request, 'core/paneladmin.html')


def panel_conductor(request):
    """Vista del panel del conductor con acceso limitado a rutas y canjes"""
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión como conductor para acceder al panel.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea conductor
    if request.user.role != 'conductor':
        messages.error(request, 'No tienes permisos de conductor para acceder a esta página.')
        return redirect('inicioadmin')
    
    return render(request, 'core/panel_conductor.html')

@login_required
def conductor_estadisticas(request):
    """API para obtener estadísticas del conductor"""
    if request.user.role != 'conductor':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    from django.db.models import Count, Q
    
    # Estadísticas de rutas
    total_rutas = Ruta.objects.count()
    rutas_pendientes = Ruta.objects.filter(estado='pendiente').count()
    rutas_completadas = Ruta.objects.filter(estado='reagendada').count()
    
    # Estadísticas de canjes
    total_canjes = Canje.objects.filter(
        Q(estado='aprobado') | Q(estado='rechazado')
    ).count()
    
    return JsonResponse({
        'total_rutas': total_rutas,
        'rutas_pendientes': rutas_pendientes,
        'rutas_completadas': rutas_completadas,
        'total_canjes': total_canjes
    })

@login_required
def conductor_graficas(request):
    """API para obtener datos de gráficas del conductor"""
    if request.user.role != 'conductor':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Canjes por estado
    canjes_pendientes = Canje.objects.filter(estado='pendiente').count()
    canjes_aprobados = Canje.objects.filter(estado='aprobado').count()
    canjes_rechazados = Canje.objects.filter(estado='rechazado').count()
    
    # Rutas por mes (últimos 6 meses)
    hoy = timezone.now()
    rutas_por_mes = []
    for i in range(5, -1, -1):
        mes_inicio = (hoy - timedelta(days=30*i)).replace(day=1)
        mes_fin = (mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        count = Ruta.objects.filter(
            fecha__gte=mes_inicio,
            fecha__lte=mes_fin,
            estado='reagendada'
        ).count()
        rutas_por_mes.append(count)
    
    return JsonResponse({
        'canjes_por_estado': {
            'pendiente': canjes_pendientes,
            'aprobado': canjes_aprobados,
            'rechazado': canjes_rechazados
        },
        'rutas_por_mes': rutas_por_mes
    })

def panel_superuser(request):
    if request.user.username != 'superadmin' or not request.user.is_superuser:
        from django.contrib import messages
        messages.error(request, 'Acceso solo para el superusuario principal.')
        return redirect('inicioadmin')
    return render(request, 'core/superuser/panel.html')

def estadisticasadmin(request):
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión como administrador para acceder a las estadísticas.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea administrador
    if not is_admin(request.user):
        messages.error(request, 'No tienes permisos de administrador para acceder a esta página.')
        return redirect('inicioadmin')
    
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import datetime, timedelta
    import json
    import calendar
    
    # Obtener estadísticas generales
    total_points_assigned = Usuario.objects.aggregate(total=Sum('puntos'))['total'] or 0
    total_points_redeemed = RedencionPuntos.objects.filter(estado='completado').aggregate(total=Sum('puntos'))['total'] or 0
    total_users = Usuario.objects.count()
    total_canjes = Canje.objects.filter(estado='aprobado').count()
    total_redenciones = RedencionPuntos.objects.filter(estado='completado').count()
    
    # Estadísticas adicionales de administrador
    # Definir fecha límite para cálculos de tiempo
    from datetime import datetime, timedelta
    now = timezone.now()
    fecha_limite = now - timedelta(days=30)  # Usuarios activos en los últimos 30 días
    
    # Usuarios con más puntos
    top_users_points = Usuario.objects.filter(puntos__gt=0).order_by('-puntos')[:10]
    
    # Usuarios más activos (más canjes)
    from django.db.models import Q
    top_users_canjes = Usuario.objects.annotate(
        total_canjes=Count('canje', filter=Q(canje__estado='aprobado'))
    ).filter(total_canjes__gt=0).order_by('-total_canjes')[:10]
    
    # Estadísticas de puntos
    avg_points_per_user = Usuario.objects.aggregate(avg=Sum('puntos'))['avg'] or 0
    if total_users > 0:
        avg_points_per_user = avg_points_per_user / total_users
    
    # Usuarios nuevos (últimos 30 días)
    usuarios_nuevos = Usuario.objects.filter(date_joined__gte=fecha_limite).count()
    
    # Distribución por género - Campo no disponible en el modelo
    usuarios_masculino = 0
    usuarios_femenino = 0
    usuarios_otro = 0
    usuarios_sin_genero = total_users
    
    # Canjes pendientes y rechazados
    canjes_pendientes = Canje.objects.filter(estado='pendiente').count()
    canjes_rechazados = Canje.objects.filter(estado='rechazado').count()
    
    # Redenciones pendientes
    redenciones_pendientes = RedencionPuntos.objects.filter(estado='pendiente').count()
    
    # Total de peso reciclado
    total_peso_reciclado = Canje.objects.filter(estado='aprobado').aggregate(total=Sum('peso'))['total'] or 0
    
    # Top 5 materiales más canjeados
    top_materials_raw = Canje.objects.filter(estado='aprobado').values('material__nombre').annotate(
        total_peso=Sum('peso')
    ).order_by('-total_peso')[:5]
    
    # Calcular porcentajes para los materiales
    total_peso_all = sum([m['total_peso'] for m in top_materials_raw]) if top_materials_raw else 1
    top_materials = []
    for material in top_materials_raw:
        material['porcentaje'] = (material['total_peso'] / total_peso_all) * 100
        top_materials.append(material)
    
    # Datos para gráfico de materiales
    materiales_labels = [m['material__nombre'] for m in top_materials]
    materiales_data = [float(m['total_peso']) for m in top_materials]
    
    # Datos para gráfico de usuarios activos vs inactivos
    usuarios_activos = Usuario.objects.filter(last_login__gte=fecha_limite).count()
    usuarios_inactivos = total_users - usuarios_activos
    
    # Datos para gráfico de canjes por mes (últimos 12 meses)
    canjes_labels = []
    canjes_data = []
    
    for i in range(11, -1, -1):
        month_date = now - timedelta(days=30*i)
        month_name = calendar.month_name[month_date.month]
        year = month_date.year
        
        # Contar canjes del mes
        canjes_count = Canje.objects.filter(
            estado='aprobado',
            fecha_solicitud__year=year,
            fecha_solicitud__month=month_date.month
        ).aggregate(total_puntos=Sum('puntos'))['total_puntos'] or 0
        
        canjes_labels.append(f"{month_name[:3]} {year}")
        canjes_data.append(canjes_count)
    
    # Datos para gráfico de redenciones por mes (últimos 12 meses)
    redenciones_labels = []
    redenciones_data = []
    
    for i in range(11, -1, -1):
        month_date = now - timedelta(days=30*i)
        month_name = calendar.month_name[month_date.month]
        year = month_date.year
        
        # Contar redenciones del mes
        redenciones_count = RedencionPuntos.objects.filter(
            estado='completado',
            fecha_solicitud__year=year,
            fecha_solicitud__month=month_date.month
        ).aggregate(total_puntos=Sum('puntos'))['total_puntos'] or 0
        
        redenciones_labels.append(f"{month_name[:3]} {year}")
        redenciones_data.append(redenciones_count)
    
    context = {
        'total_points_assigned': total_points_assigned,
        'total_points_redeemed': total_points_redeemed,
        'total_users': total_users,
        'total_canjes': total_canjes,
        'total_redenciones': total_redenciones,
        'top_materials': top_materials,
        'usuarios_activos': usuarios_activos,
        'usuarios_inactivos': usuarios_inactivos,
        'canjes_labels_json': json.dumps(canjes_labels),
        'canjes_data_json': json.dumps(canjes_data),
        'redenciones_labels_json': json.dumps(redenciones_labels),
        'redenciones_data_json': json.dumps(redenciones_data),
        'materiales_labels_json': json.dumps(materiales_labels),
        'materiales_data_json': json.dumps(materiales_data),
        # Nuevas estadísticas de administrador
        'top_users_points': top_users_points,
        'top_users_canjes': top_users_canjes,
        'avg_points_per_user': avg_points_per_user,
        'usuarios_nuevos': usuarios_nuevos,
        'usuarios_masculino': usuarios_masculino,
        'usuarios_femenino': usuarios_femenino,
        'usuarios_otro': usuarios_otro,
        'usuarios_sin_genero': usuarios_sin_genero,
        'canjes_pendientes': canjes_pendientes,
        'canjes_rechazados': canjes_rechazados,
        'redenciones_pendientes': redenciones_pendientes,
        'total_peso_reciclado': total_peso_reciclado,
    }
    
    return render(request, 'core/estadisticasadmin.html', context)

def rutas(request):
    # Verificar que el usuario esté autenticado
    if not request.user.is_authenticated:
        messages.error(request, 'Debes iniciar sesión para acceder a las rutas.')
        return redirect('inicioadmin')
    
    # Verificar que el usuario sea administrador o conductor
    if request.user.role not in ['admin', 'superuser', 'conductor']:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('inicioadmin')
    
    routes = Ruta.objects.all().order_by('-fecha_creacion')
    context = {
        'show_integrated_view': True,
        'routes': routes,
        'is_conductor': request.user.role == 'conductor',  # Para mostrar/ocultar opciones en el template
    }

    return render(request, 'core/rutas.html', context)

@ajax_required_admin
def add_ruta(request):
    if request.method == 'POST':
        try:
            fecha = request.POST.get('fecha')
            hora = request.POST.get('hora')
            barrio = request.POST.get('barrio')
            referencia = request.POST.get('referencia', '') # Puede ser opcional
            direccion = request.POST.get('direccion')

            Ruta.objects.create(
                fecha=fecha,
                hora=hora,
                barrio=barrio,
                referencia=referencia,
                direccion=direccion
            )
            return JsonResponse({'success': True, 'message': 'Ruta agregada exitosamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al agregar la ruta: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@ajax_required_admin
def edit_ruta(request, ruta_id):
    if request.method == 'POST':
        try:
            ruta = get_object_or_404(Ruta, id=ruta_id)
            
            # Guardar valores originales
            fecha_original = ruta.fecha
            hora_original = ruta.hora
            
            # Actualizar con nuevos valores
            nueva_fecha = request.POST.get('fecha')
            nueva_hora = request.POST.get('hora')
            
            ruta.fecha = nueva_fecha
            ruta.hora = nueva_hora
            ruta.barrio = request.POST.get('barrio')
            ruta.referencia = request.POST.get('referencia', '')
            ruta.direccion = request.POST.get('direccion')
            ruta.save()
            
            # Verificar si hubo cambios en fecha u hora para enviar correo de reagendamiento
            if str(fecha_original) != nueva_fecha or str(hora_original) != nueva_hora:
                try:
                    usuario = ruta.usuario
                    subject = '📅 Tu Recolección ha sido Reagendada - EcoPuntos'
                    
                    # Formatear fechas y horas
                    from datetime import datetime
                    try:
                        fecha_obj = datetime.strptime(nueva_fecha, '%Y-%m-%d')
                        fecha_formateada = fecha_obj.strftime('%d de %B de %Y')
                        # Traducir mes al español
                        meses = {
                            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
                            'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
                            'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
                            'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
                        }
                        for en, es in meses.items():
                            fecha_formateada = fecha_formateada.replace(en, es)
                    except:
                        fecha_formateada = nueva_fecha
                    
                    # Formatear hora original y nueva
                    try:
                        fecha_orig_obj = datetime.strptime(str(fecha_original), '%Y-%m-%d')
                        fecha_orig_formateada = fecha_orig_obj.strftime('%d de %B de %Y')
                        for en, es in meses.items():
                            fecha_orig_formateada = fecha_orig_formateada.replace(en, es)
                    except:
                        fecha_orig_formateada = str(fecha_original)
                    
                    hora_formateada = nueva_hora if nueva_hora else 'Por confirmar'
                    hora_orig_formateada = str(hora_original) if hora_original else 'Por confirmar'
                    
                    # Generar enlace para que vea sus rutas con el modal
                    enlace_rutas = f"{request.build_absolute_uri('/rutasusuario/reagendada/' + str(ruta.id) + '/')}"
                    
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                            .header {{ background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                            .info-card {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                            .info-row {{ display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #eee; }}
                            .info-label {{ font-weight: bold; color: #3498db; }}
                            .info-value {{ color: #555; }}
                            .highlight {{ background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db; }}
                            .comparison {{ display: flex; gap: 20px; margin: 20px 0; }}
                            .before, .after {{ flex: 1; padding: 15px; border-radius: 8px; text-align: center; }}
                            .before {{ background: #ffebee; border: 2px solid #f44336; }}
                            .after {{ background: #e8f5e8; border: 2px solid #4caf50; }}
                            .footer {{ text-align: center; margin-top: 20px; color: #777; font-size: 12px; }}
                            .btn-primary {{ background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; display: inline-block; margin: 20px 0; font-weight: bold; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>📅 Reagendamiento de Recolección</h1>
                            </div>
                            <div class="content">
                                <p>Hola <strong>{usuario.first_name if usuario.first_name else usuario.username}</strong>,</p>
                                
                                <div class="highlight">
                                    <h3 style="margin-top: 0; color: #3498db;">ℹ️ Tu recolección ha sido reagendada</h3>
                                    <p>Hemos actualizado la fecha y/o hora de tu recolección. A continuación encontrarás los nuevos detalles.</p>
                                </div>
                                
                                <h3 style="color: #333;">📋 Cambios Realizados:</h3>
                                <div class="comparison">
                                    <div class="before">
                                        <h4 style="color: #f44336; margin-top: 0;">❌ Fecha/Hora Anterior</h4>
                                        <p><strong>Fecha:</strong> {fecha_orig_formateada}</p>
                                        <p><strong>Hora:</strong> {hora_orig_formateada}</p>
                                    </div>
                                    <div class="after">
                                        <h4 style="color: #4caf50; margin-top: 0;">✅ Nueva Fecha/Hora</h4>
                                        <p><strong>Fecha:</strong> {fecha_formateada}</p>
                                        <p><strong>Hora:</strong> {hora_formateada}</p>
                                    </div>
                                </div>
                                
                                <div class="info-card">
                                    <h3 style="color: #3498db; margin-top: 0;">📍 Detalles de la Recolección</h3>
                                    <div class="info-row">
                                        <span class="info-label">📅 Nueva Fecha:</span>
                                        <span class="info-value">{fecha_formateada}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">🕐 Nueva Hora:</span>
                                        <span class="info-value">{hora_formateada}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">🏘️ Barrio:</span>
                                        <span class="info-value">{ruta.barrio}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-label">📍 Dirección:</span>
                                        <span class="info-value">{ruta.direccion}</span>
                                    </div>
                                    {f'<div class="info-row"><span class="info-label">📌 Referencia:</span><span class="info-value">{ruta.referencia}</span></div>' if ruta.referencia else ''}
                                </div>
                                
                                <div style="text-align: center; margin: 30px 0;">
                                    <a href="{enlace_rutas}" class="btn-primary">
                                        🔍 Ver mis Rutas de Recolección
                                    </a>
                                </div>
                                
                                <div class="highlight">
                                    <p style="margin: 0;"><strong>🔔 Importante:</strong> Por favor, asegúrate de estar disponible en la nueva fecha y hora programada. Haz clic en el botón de arriba para ver todos los detalles en tu panel de usuario.</p>
                                </div>
                                
                                <div class="footer">
                                    <p>Gracias por contribuir con el medio ambiente 🌱</p>
                                    <p><strong>EcoPuntos</strong> - Transformando el mundo a través del reciclaje responsable</p>
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Enviar correo
                    msg = EmailMultiAlternatives(
                        subject,
                        f"Tu recolección ha sido reagendada para el {fecha_formateada} a las {hora_formateada}.",
                        settings.DEFAULT_FROM_EMAIL,
                        [usuario.email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                    
                    # Crear notificación en el sistema
                    Notificacion.objects.create(
                        usuario=usuario,
                        titulo="Recolección Reagendada",
                        mensaje=f"Tu recolección ha sido reagendada para el {fecha_formateada} a las {hora_formateada}.",
                        tipo='sistema'
                    )
                    
                except Exception as e:
                    print(f"Error enviando correo de reagendamiento: {str(e)}")
                
                # Agregar parámetros de reagendamiento a la respuesta
                return JsonResponse({
                    'success': True, 
                    'message': 'Ruta actualizada exitosamente. Se ha notificado al usuario.',
                    'reagendada': True,
                    'nueva_fecha': nueva_fecha,
                    'nueva_hora': nueva_hora
                })
            else:
                return JsonResponse({'success': True, 'message': 'Ruta actualizada exitosamente.'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al actualizar la ruta: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@ajax_required_admin
def delete_ruta(request, ruta_id):
    if request.method == 'POST':
        try:
            ruta = get_object_or_404(Ruta, id=ruta_id)
            ruta.delete()
            return JsonResponse({'success': True, 'message': 'Ruta eliminada exitosamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al eliminar la ruta: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@ajax_required_admin
@throttle_general
def confirmar_ruta(request, ruta_id):
    if request.method == 'POST':
        try:
            ruta = get_object_or_404(Ruta, id=ruta_id)
            ruta.estado = 'confirmada'
            ruta.fecha_procesamiento = timezone.now()
            ruta.save()
            
            # Enviar correo de confirmación al usuario
            try:
                usuario = ruta.usuario
                subject = '✅ Tu Recolección ha sido Confirmada - EcoPuntos'
                
                # Formatear fecha y hora
                from datetime import datetime
                try:
                    fecha_obj = datetime.strptime(str(ruta.fecha), '%Y-%m-%d')
                    fecha_formateada = fecha_obj.strftime('%d de %B de %Y')
                    # Traducir mes al español
                    meses = {
                        'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo',
                        'April': 'Abril', 'May': 'Mayo', 'June': 'Junio',
                        'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
                        'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
                    }
                    for en, es in meses.items():
                        fecha_formateada = fecha_formateada.replace(en, es)
                except:
                    fecha_formateada = str(ruta.fecha)
                
                hora_formateada = ruta.hora if ruta.hora else 'Por confirmar'
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: linear-gradient(135deg, #27ae60 0%, #229954 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                        .info-card {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                        .info-row {{ display: flex; padding: 10px 0; border-bottom: 1px solid #eee; }}
                        .info-label {{ font-weight: bold; color: #27ae60; min-width: 120px; }}
                        .info-value {{ color: #555; }}
                        .highlight {{ background: #d5f4e6; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #27ae60; }}
                        .footer {{ text-align: center; margin-top: 20px; color: #777; font-size: 12px; }}
                        .button {{ display: inline-block; padding: 12px 30px; background: #27ae60; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                        .conductor-card {{ background: white; padding: 25px; border-radius: 12px; margin: 25px 0; box-shadow: 0 3px 10px rgba(0,0,0,0.15); text-align: center; border: 2px solid #27ae60; }}
                        .conductor-photo {{ width: 150px; height: 150px; border-radius: 50%; object-fit: cover; border: 5px solid #27ae60; margin: 0 auto 15px; display: block; }}
                        .conductor-name {{ font-size: 22px; font-weight: bold; color: #27ae60; margin: 10px 0; }}
                        .conductor-title {{ color: #666; font-size: 14px; margin: 5px 0; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🎉 ¡Recolección Confirmada!</h1>
                        </div>
                        <div class="content">
                            <p>Hola <strong>{usuario.first_name if usuario.first_name else usuario.username}</strong>,</p>
                            
                            <div class="highlight">
                                <h3 style="margin-top: 0; color: #27ae60;">✅ Tu solicitud de recolección ha sido confirmada</h3>
                                <p>Nuestro conductor pasará por tu domicilio en la fecha y hora indicadas.</p>
                            </div>
                            
                            <div class="conductor-card">
                                <h3 style="color: #27ae60; margin-top: 0;">👨‍💼 Tu Conductor Asignado</h3>
                                <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=400&fit=crop&crop=faces" alt="Conductor David Rodríguez" class="conductor-photo">
                                <div class="conductor-name">David Rodríguez</div>
                                <div class="conductor-title">Conductor Certificado EcoPuntos</div>
                                <p style="margin-top: 15px; color: #555; font-size: 14px;">
                                    <strong>David</strong> será tu conductor asignado. Cuenta con amplia experiencia en manejo de materiales reciclables.
                                </p>
                            </div>
                            
                            <div class="info-card">
                                <h3 style="color: #27ae60; margin-top: 0;">📋 Detalles de la Recolección</h3>
                                <div class="info-row">
                                    <span class="info-label">📅 Fecha:</span>
                                    <span class="info-value">{fecha_formateada}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">🕒 Hora:</span>
                                    <span class="info-value">{hora_formateada}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">📍 Dirección:</span>
                                    <span class="info-value">{ruta.direccion}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">🚛 Conductor:</span>
                                    <span class="info-value">David Rodríguez</span>
                                </div>
                            </div>
                            
                            <div class="highlight">
                                <h4 style="margin-top: 0;">🚛 ¿Qué sigue?</h4>
                                <ul style="margin: 10px 0; padding-left: 20px;">
                                    <li>Prepara tus materiales reciclables</li>
                                    <li>Espera a David en la fecha y hora indicadas</li>
                                    <li>El conductor pesará y verificará los materiales</li>
                                    <li>Recibirás tus puntos EcoPuntos al completar la recolección</li>
                                </ul>
                            </div>
                            
                            <p style="text-align: center; margin-top: 20px;">
                                <strong>¡Gracias por contribuir al cuidado del medio ambiente!</strong> 🌱
                            </p>
                            
                            <div class="footer">
                                <p>Este es un correo automático de EcoPuntos</p>
                                <p>Si tienes alguna pregunta, contáctanos a través de nuestra plataforma</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                text_content = f"""
                ¡Recolección Confirmada!
                
                Hola {usuario.first_name if usuario.first_name else usuario.username},
                
                Tu solicitud de recolección ha sido confirmada.
                
                Tu Conductor Asignado: David Rodríguez
                David será tu conductor asignado y cuenta con amplia experiencia en manejo de materiales reciclables.
                
                Detalles de la Recolección:
                - Fecha: {fecha_formateada}
                - Hora: {hora_formateada}
                - Dirección: {ruta.direccion}
                - Conductor: David Rodríguez
                
                ¿Qué sigue?
                - Prepara tus materiales reciclables
                - Espera a David en la fecha y hora indicadas
                - El conductor pesará y verificará los materiales
                - Recibirás tus puntos EcoPuntos al completar la recolección
                
                ¡Gracias por contribuir al cuidado del medio ambiente!
                
                EcoPuntos
                """
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[usuario.email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                
                print(f"✅ Email de confirmación enviado a {usuario.email}")
            except Exception as e:
                print(f"⚠️ Error al enviar email de confirmación: {str(e)}")
            
            return JsonResponse({'success': True, 'message': 'Ruta confirmada exitosamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al confirmar la ruta: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@ajax_required_admin
def rechazar_ruta(request, ruta_id):
    if request.method == 'POST':
        try:
            ruta = get_object_or_404(Ruta, id=ruta_id)
            motivo = request.POST.get('motivo', '')
            ruta.estado = 'rechazada'
            ruta.fecha_procesamiento = timezone.now()
            ruta.notas_admin = motivo
            ruta.save()
            return JsonResponse({'success': True, 'message': 'Ruta rechazada exitosamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al rechazar la ruta: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@ajax_required_admin
def reagendar_ruta(request, ruta_id):
    if request.method == 'POST':
        try:
            ruta = get_object_or_404(Ruta, id=ruta_id)
            nueva_fecha = request.POST.get('fecha')
            nueva_hora = request.POST.get('hora')
            ruta.fecha = nueva_fecha
            ruta.hora = nueva_hora
            ruta.estado = 'reagendada'
            ruta.fecha_procesamiento = timezone.now()
            notas = request.POST.get('notas_admin', '')
            if notas:
                ruta.notas_admin = notas
            ruta.save()
            
            # Enviar correo de reagendamiento
            try:
                usuario = ruta.usuario
                subject = '📅 Tu Ruta de Recolección ha sido Reagendada - EcoPuntos'
                
                # Formatear fecha y hora para mostrar
                from datetime import datetime
                try:
                    fecha_obj = datetime.strptime(nueva_fecha, '%Y-%m-%d')
                    fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
                except:
                    fecha_formateada = nueva_fecha
                
                try:
                    hora_obj = datetime.strptime(nueva_hora, '%H:%M')
                    hora_formateada = hora_obj.strftime('%I:%M %p')
                except:
                    hora_formateada = nueva_hora
                
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                        .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                        .info {{ color: #3498db; font-weight: bold; }}
                        .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
                        .label {{ font-weight: bold; color: #555; }}
                        .value {{ color: #3498db; font-weight: bold; }}
                        .alert {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }}
                        .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>📅 Ruta Reagendada</h1>
                        </div>
                        <div class="content">
                            <p>Hola <strong>{usuario.first_name if usuario.first_name else usuario.username}</strong>,</p>
                            <p>Te informamos que tu ruta de recolección ha sido <span class="info">REAGENDADA</span> para una nueva fecha y hora.</p>
                            
                            <div class="card">
                                <h3>📍 Nueva Información de la Ruta:</h3>
                                <div class="info-row">
                                    <span class="label">📅 Nueva Fecha:</span>
                                    <span class="value">{fecha_formateada}</span>
                                </div>
                                <div class="info-row">
                                    <span class="label">🕐 Nueva Hora:</span>
                                    <span class="value">{hora_formateada}</span>
                                </div>
                                <div class="info-row">
                                    <span class="label">📍 Dirección:</span>
                                    <span>{ruta.direccion}</span>
                                </div>
                                <div class="info-row">
                                    <span class="label">🏘️ Barrio:</span>
                                    <span>{ruta.barrio}</span>
                                </div>
                            </div>
                            
                            {f'<div class="alert"><strong>📝 Motivo del Reagendamiento:</strong><br>{notas}</div>' if notas else ''}
                            
                            <p><strong>Por favor, ten en cuenta la nueva fecha y hora.</strong></p>
                            <p>Recuerda tener listos tus materiales reciclables para la recolección.</p>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="http://127.0.0.1:8000/misrutas/" style="background: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                    Ver Mis Rutas
                                </a>
                            </div>
                        </div>
                        <div class="footer">
                            <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                            <p>&copy; 2025 EcoPuntos - Cuidando el planeta juntos 🌍</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                text_content = f"""
                Ruta Reagendada - EcoPuntos
                
                Hola {usuario.first_name if usuario.first_name else usuario.username},
                
                Te informamos que tu ruta de recolección ha sido REAGENDADA para una nueva fecha y hora.
                
                Nueva Información de la Ruta:
                - Nueva Fecha: {fecha_formateada}
                - Nueva Hora: {hora_formateada}
                - Dirección: {ruta.direccion}
                - Barrio: {ruta.barrio}
                
                {f'Motivo del Reagendamiento: {notas}' if notas else ''}
                
                Por favor, ten en cuenta la nueva fecha y hora.
                Recuerda tener listos tus materiales reciclables para la recolección.
                
                ---
                EcoPuntos - Cuidando el planeta juntos 🌍
                """
                
                msg = EmailMultiAlternatives(
                    subject,
                    text_content,
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                print(f"✅ Correo de reagendamiento enviado a {usuario.email}")
                
                # Crear notificación en el sistema para el modal
                from .models import Notificacion
                Notificacion.objects.create(
                    usuario=usuario,
                    titulo="Recolección Reagendada",
                    mensaje=f"Tu recolección ha sido reagendada para el {fecha_formateada} a las {hora_formateada}. {f'Motivo: {notas}' if notas else ''}",
                    tipo='sistema',
                    leida=False  # Importante: debe estar como no leída para que aparezca el modal
                )
                print(f"✅ Notificación de reagendamiento creada para {usuario.username}")
                
            except Exception as e:
                print(f"❌ Error enviando correo de reagendamiento: {e}")
            
            return JsonResponse({'success': True, 'message': 'Ruta reagendada exitosamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error al reagendar la ruta: {str(e)}'})
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@ajax_required_admin
def procesar_canje(request, canje_id):
    print(f"🔍 DEBUG: procesar_canje llamado con canje_id={canje_id}")
    if request.method == 'POST':
        print(f"🔍 DEBUG: Método POST recibido")
        canje = get_object_or_404(Canje, id=canje_id)
        accion = request.POST.get('accion')
        print(f"🔍 DEBUG: Acción solicitada: {accion}")
        print(f"🔍 DEBUG: Usuario del canje: {canje.usuario.username} ({canje.usuario.email})")
        
        if accion == 'aprobar':
            # Verificar si se envió un peso real
            peso_real = request.POST.get('peso_real')
            print(f"🔍 DEBUG: Peso real recibido: {peso_real}")
            
            if peso_real:
                # Actualizar peso y recalcular puntos
                peso_real = float(peso_real)
                canje.peso = peso_real
                canje.puntos = int(peso_real * canje.material.puntos_por_kilo)
                canje.estado = 'aprobado'
                canje.fecha_procesamiento = timezone.now()
                canje.save()
                
                # Sumar puntos al usuario
                canje.usuario.puntos += canje.puntos
                canje.usuario.save()
                
                # Crear notificación para el usuario
                Notificacion.objects.create(
                    usuario=canje.usuario,
                    titulo='Canje Aprobado',
                    mensaje=f'¡Tu canje de {canje.material.nombre} ({canje.peso} kg) ha sido aprobado! Se han agregado {canje.puntos} puntos a tu cuenta.',
                    tipo='canje_aprobado'
                )
                
                # Enviar correo de confirmación de canje aprobado
                print(f"🔍 DEBUG: Iniciando envío de correo a {canje.usuario.email}")
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    subject = f'¡Canje Aprobado! +{canje.puntos} puntos - EcoPuntos'
                    message = f"""
Hola {canje.usuario.first_name or canje.usuario.username},

¡Excelentes noticias! Tu canje ha sido aprobado por nuestro equipo.

Detalles del canje aprobado:
- Material: {canje.material.nombre}
- Peso procesado: {canje.peso} kg
- Puntos otorgados: {canje.puntos}

Los puntos han sido agregados automáticamente a tu cuenta.

¡Gracias por reciclar y sumar puntos ecológicos!

Equipo EcoPuntos
"""
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [canje.usuario.email],
                        fail_silently=False,
                    )
                    print(f"✅ Email de canje aprobado enviado exitosamente a {canje.usuario.email}")
                except Exception as e:
                    # Si falla el correo, continuar sin interrumpir el proceso
                    print(f"❌ Error enviando correo de canje aprobado: {e}")
                    import traceback
                    traceback.print_exc()
                
                mensaje_admin = f'✅ Canje #{canje.id} APROBADO exitosamente\n👤 Usuario: {canje.usuario.username}\n📦 Material: {canje.material.nombre}\n⚖️ Peso: {canje.peso} kg\n🎯 Puntos otorgados: {canje.puntos}'
                
                return JsonResponse({
                    'status': 'success',
                    'action': 'aprobar',
                    'message': mensaje_admin,
                    'canje_id': canje.id,
                    'usuario': canje.usuario.username,
                    'puntos': canje.puntos
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Peso real es requerido para aprobar'}, status=400)
                
        elif accion == 'rechazar':
            canje.estado = 'rechazado'
            canje.fecha_procesamiento = timezone.now()
            canje.save()
            
            # Crear notificación para el usuario
            Notificacion.objects.create(
                usuario=canje.usuario,
                titulo='Canje Rechazado',
                mensaje=f'Tu canje de {canje.material.nombre} ({canje.peso} kg) ha sido rechazado. Si tienes dudas sobre el motivo, contacta con soporte.',
                tipo='canje_rechazado'
            )
            
            mensaje_admin = f'❌ Canje #{canje.id} RECHAZADO\n👤 Usuario: {canje.usuario.username}\n📦 Material: {canje.material.nombre}\n⚖️ Peso: {canje.peso} kg'
            
            return JsonResponse({
                'status': 'success',
                'action': 'rechazar',
                'message': mensaje_admin,
                'canje_id': canje.id,
                'usuario': canje.usuario.username
            })
        
        return JsonResponse({'status': 'error', 'message': 'Acción no válida'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def inicioadmin(request):
    # Verificar si se solicita cerrar sesión
    if request.GET.get('logout') == '1':
        from django.contrib.auth import logout
        logout(request)
        messages.info(request, 'Sesión cerrada exitosamente.')
        return redirect('inicioadmin')  # Redirigir sin parámetros
    
    # Si el usuario ya está autenticado y es admin o conductor, mostrar mensaje informativo
    if request.user.is_authenticated and request.user.role in ['admin', 'conductor']:
        panel_url = '/panel_conductor/' if request.user.role == 'conductor' else '/paneladmin/'
        messages.info(request, f'Ya tienes una sesión activa como {request.user.username}. <a href="?logout=1" class="alert-link">Cerrar sesión</a> o <a href="{panel_url}" class="alert-link">continuar al panel</a>.')
        return render(request, 'core/inicioadmin.html')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            # Verificar si hay sesiones activas para este usuario y invalidarlas
            try:
                existing_user = Usuario.objects.get(username=username)
                active_sessions = SesionUsuario.objects.filter(usuario=existing_user, activa=True)
                if active_sessions.exists():
                    from .security import SecurityManager
                    SecurityManager.invalidate_all_user_sessions(existing_user)
                    messages.info(request, 'Se han cerrado las sesiones anteriores de este usuario.')
            except Usuario.DoesNotExist:
                pass
            
            # Primero autenticar con Django
            user = authenticate(request, username=username, password=password)
            if user is not None and user.role in ['admin', 'superuser', 'conductor']:
                # Crear sesión segura
                from .security import SecurityManager
                session_token = SecurityManager.create_secure_session(request, user)
                
                # Hacer login
                auth_login(request, user)
                
                # Guardar token en la sesión
                request.session['session_token'] = session_token
                
                # Redirigir según el rol
                if user.role == 'superuser':
                    messages.success(request, f'Bienvenido/a Superusuario {user.username}!')
                    return redirect('panel_superuser')
                elif user.role == 'conductor':
                    messages.success(request, f'Bienvenido/a Conductor {user.username}!')
                    return redirect('panel_conductor')
                else:
                    messages.success(request, f'Bienvenido/a Administrador {user.username}!')
                    return redirect('paneladmin')
            else:
                if user is None:
                    messages.error(request, 'Usuario o contraseña incorrectos.')
                else:
                    messages.error(request, 'No tienes permisos de administrador, conductor o superusuario.')
                return render(request, 'core/inicioadmin.html')
                
        except Exception as e:
            messages.error(request, f'Error de autenticación: {str(e)}')
            
    return render(request, 'core/inicioadmin.html')

# --- CANJE DE PUNTOS ---

@login_required
def solicitar_canje(request):
    if request.method == 'POST':
        try:
            material_id = request.POST.get('material')
            peso = float(request.POST.get('peso'))
        
            material = MaterialTasa.objects.get(id=material_id, activo=True)
            puntos = int(peso * material.puntos_por_kilo)
            
            canje = Canje.objects.create(
                usuario=request.user,
                material=material,
                peso=peso,
                puntos=puntos,
                estado='pendiente',
            )
            
            # Otorgar logro de primer canje si es la primera vez
            if otorgar_logro_automatico(request.user, 'reciclador_novato'):
                # Crear notificación especial para el logro
                Notificacion.objects.create(
                    usuario=request.user,
                    titulo='¡Nuevo Logro Desbloqueado!',
                    mensaje='¡Felicidades! Has ganado el logro "Reciclador Novato" por realizar tu primer canje.',
                    tipo='sistema'
                )
            
            # Crear notificación para el usuario
            Notificacion.objects.create(
                usuario=request.user,
                titulo='Canje en Revisión',
                mensaje=f'Tu solicitud de canje de {peso}kg de {material.nombre} ha sido recibida y está siendo revisada.'
            )
            
            # Verificar si es una petición AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Solicitud de canje enviada exitosamente. Te notificaremos cuando sea procesada.',
                    'canje': {
                        'id': canje.id,
                        'material': material.nombre,
                        'peso': peso,
                        'puntos': puntos,
                        'estado': 'Pendiente'
                    }
                })
            else:
                # No usar messages.success(), confiar en el sistema de notificaciones
                return redirect('canjes')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Ocurrió un error al procesar tu solicitud.'
                }, status=400)
            else:
                messages.error(request, 'Ocurrió un error al procesar tu solicitud.')
                return redirect('canjes')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido.'
        }, status=405)
    return redirect('canjes')

@login_required
def get_pending_canjes(request):
    canjes = Canje.objects.filter(
        usuario=request.user,
        estado__in=['pendiente', 'aprobado']
    ).order_by('-fecha_solicitud')
    
    canjes_data = [{
        'id': canje.id,
        'fecha_solicitud': canje.fecha_solicitud.isoformat(),
        'material_nombre': canje.material.nombre,
        'peso': str(canje.peso),
        'puntos': canje.puntos,
        'estado': canje.estado.title()
    } for canje in canjes]
    
    return JsonResponse({
        'success': True,
        'canjes': canjes_data
    })

@ajax_required_admin
def get_pending_canjes_for_admin(request):
    canjes = Canje.objects.filter(
        estado__in=['pendiente', 'aprobado']
    ).select_related('usuario', 'material').order_by('-fecha_solicitud')
    
    canjes_data = [{
        'id': canje.id,
        'fecha_solicitud': canje.fecha_solicitud.isoformat(),
        'material_nombre': canje.material.nombre,
        'peso': str(canje.peso),
        'puntos': canje.puntos,
        'estado': canje.estado.title(),
        'usuario_username': canje.usuario.username
    } for canje in canjes]
    
    return JsonResponse({
        'success': True,
        'canjes': canjes_data
    })

@login_required
def aprobar_canje(request, canje_id):
    # Verificar permisos: staff o conductor
    if not (request.user.is_staff or request.user.role == 'conductor'):
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para realizar esta acción'
        })
    
    try:
        canje = Canje.objects.get(id=canje_id)
        canje.estado = 'aprobado'
        canje.fecha_procesamiento = timezone.now()
        canje.save()
        
        # Actualizar puntos del usuario
        usuario = canje.usuario
        usuario.puntos += canje.puntos
        usuario.save()
        
        # Crear notificación para el usuario
        Notificacion.objects.create(
            usuario=usuario,
            titulo='Canje Aprobado',
            mensaje=f'¡Excelente! Tu canje de {canje.material.nombre} ({canje.cantidad} kg) ha sido aprobado. Has ganado {canje.puntos} puntos.',
            tipo='canje_aprobado'
        )
        
        return JsonResponse({'success': True, 'message': 'Canje aprobado exitosamente.'})
        
    except Canje.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Canje no encontrado.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al aprobar el canje: {str(e)}.'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@require_POST
@throttle_general
def aprobar_canje_peso_real(request, canje_id):
    """Aprobar canje con peso real ingresado por conductor/admin"""
    # Verificar permisos: staff o conductor
    if not (request.user.is_staff or request.user.role == 'conductor'):
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para realizar esta acción'
        }, status=403)
    
    try:
        canje = Canje.objects.get(id=canje_id)
        
        # Obtener peso real y puntos del request
        peso_real = request.POST.get('peso_real')
        puntos = request.POST.get('puntos')
        
        if not peso_real or not puntos:
            return JsonResponse({
                'success': False,
                'error': 'Faltan datos requeridos (peso_real y puntos)'
            }, status=400)
        
        try:
            peso_real = float(peso_real)
            puntos = int(puntos)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Datos inválidos para peso o puntos'
            }, status=400)
        
        # Validar peso mínimo
        if peso_real < 0.1:
            return JsonResponse({
                'success': False,
                'error': 'El peso mínimo debe ser 0.1 kg'
            }, status=400)
        
        # Actualizar el canje
        canje.cantidad = peso_real  # Actualizar con el peso real
        canje.puntos = puntos  # Actualizar con los puntos calculados
        canje.estado = 'aprobado'
        canje.fecha_procesamiento = timezone.now()
        canje.save()
        
        # Actualizar puntos del usuario
        usuario = canje.usuario
        usuario.puntos += puntos
        usuario.save()
        
        # Crear notificación para el usuario
        Notificacion.objects.create(
            usuario=usuario,
            titulo='Canje Aprobado',
            mensaje=f'¡Excelente! Tu canje de {canje.material.nombre} ({peso_real} kg) ha sido aprobado. Has ganado {puntos} puntos.',
            tipo='canje_aprobado'
        )
        
        # Enviar correo de confirmación
        try:
            subject = '✅ ¡Tu Canje ha sido Aprobado! - EcoPuntos'
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .success {{ color: #2ecc71; font-weight: bold; font-size: 24px; }}
                    .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
                    .label {{ font-weight: bold; color: #555; }}
                    .value {{ color: #2ecc71; font-weight: bold; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 ¡Canje Aprobado!</h1>
                    </div>
                    <div class="content">
                        <p>Hola <strong>{usuario.first_name if usuario.first_name else usuario.username}</strong>,</p>
                        <p>¡Excelentes noticias! Tu canje de materiales reciclables ha sido procesado y <span class="success">APROBADO</span>.</p>
                        
                        <div class="card">
                            <h3>📋 Detalles del Canje:</h3>
                            <div class="info-row">
                                <span class="label">Material:</span>
                                <span>{canje.material.nombre}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">Peso Real:</span>
                                <span class="value">{peso_real} kg</span>
                            </div>
                            <div class="info-row">
                                <span class="label">Puntos Ganados:</span>
                                <span class="value">+{puntos} puntos</span>
                            </div>
                            <div class="info-row">
                                <span class="label">Fecha de Aprobación:</span>
                                <span>{timezone.now().strftime('%d/%m/%Y %H:%M')}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">Puntos Totales:</span>
                                <span class="value">{usuario.puntos} puntos</span>
                            </div>
                        </div>
                        
                        <p><strong>¡Gracias por contribuir al medio ambiente!</strong> 🌱</p>
                        <p>Ahora puedes usar tus puntos para canjear increíbles recompensas en nuestra plataforma.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://127.0.0.1:8000/dashboard/" style="background: #2ecc71; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Ver Mis Puntos
                            </a>
                        </div>
                    </div>
                    <div class="footer">
                        <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                        <p>&copy; 2025 EcoPuntos - Cuidando el planeta juntos 🌍</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            ¡Canje Aprobado! - EcoPuntos
            
            Hola {usuario.first_name if usuario.first_name else usuario.username},
            
            ¡Excelentes noticias! Tu canje de materiales reciclables ha sido procesado y APROBADO.
            
            Detalles del Canje:
            - Material: {canje.material.nombre}
            - Peso Real: {peso_real} kg
            - Puntos Ganados: +{puntos} puntos
            - Fecha de Aprobación: {timezone.now().strftime('%d/%m/%Y %H:%M')}
            - Puntos Totales: {usuario.puntos} puntos
            
            ¡Gracias por contribuir al medio ambiente! 🌱
            
            Ahora puedes usar tus puntos para canjear increíbles recompensas en nuestra plataforma.
            
            ---
            EcoPuntos - Cuidando el planeta juntos 🌍
            """
            
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            print(f"✅ Correo de aprobación enviado a {usuario.email}")
        except Exception as e:
            print(f"❌ Error enviando correo de aprobación: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Canje aprobado exitosamente.',
            'peso_real': peso_real,
            'puntos': puntos
        })
        
    except Canje.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Canje no encontrado.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al aprobar el canje: {str(e)}'
        }, status=500)

@require_POST
def rechazar_canje_ajax(request, canje_id):
    """Rechazar un canje vía AJAX"""
    # Verificar permisos: staff o conductor
    if not (request.user.is_staff or request.user.role == 'conductor'):
        return JsonResponse({
            'success': False,
            'error': 'No tienes permisos para realizar esta acción'
        }, status=403)
    
    try:
        canje = Canje.objects.get(id=canje_id)
        canje.estado = 'rechazado'
        canje.fecha_procesamiento = timezone.now()
        canje.save()
        
        # Crear notificación para el usuario
        usuario = canje.usuario
        Notificacion.objects.create(
            usuario=usuario,
            titulo='Canje Rechazado',
            mensaje=f'Tu canje de {canje.material.nombre} ({canje.cantidad} kg) ha sido rechazado. Por favor, contacta con el administrador para más información.',
            tipo='canje_rechazado'
        )
        
        # Enviar correo de rechazo
        try:
            subject = '❌ Canje Rechazado - EcoPuntos'
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .card {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .warning {{ color: #e74c3c; font-weight: bold; }}
                    .info-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }}
                    .label {{ font-weight: bold; color: #555; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #777; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⚠️ Canje Rechazado</h1>
                    </div>
                    <div class="content">
                        <p>Hola <strong>{usuario.nombre}</strong>,</p>
                        <p>Lamentamos informarte que tu canje de materiales reciclables ha sido <span class="warning">RECHAZADO</span>.</p>
                        
                        <div class="card">
                            <h3>📋 Detalles del Canje:</h3>
                            <div class="info-row">
                                <span class="label">Material:</span>
                                <span>{canje.material.nombre}</span>
                            </div>
                            <div class="info-row">
                                <span class="label">Peso Estimado:</span>
                                <span>{canje.cantidad} kg</span>
                            </div>
                            <div class="info-row">
                                <span class="label">Fecha de Rechazo:</span>
                                <span>{timezone.now().strftime('%d/%m/%Y %H:%M')}</span>
                            </div>
                        </div>
                        
                        <p><strong>Posibles razones del rechazo:</strong></p>
                        <ul>
                            <li>Material no cumple con los requisitos de calidad</li>
                            <li>Material contaminado o mezclado</li>
                            <li>Peso insuficiente</li>
                            <li>Material no corresponde a la categoría especificada</li>
                        </ul>
                        
                        <p>Si tienes dudas o deseas más información, por favor contacta con nuestro equipo de soporte.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="http://127.0.0.1:8000/dashboard/" style="background: #e74c3c; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Ir al Dashboard
                            </a>
                        </div>
                    </div>
                    <div class="footer">
                        <p>Este es un correo automático, por favor no respondas a este mensaje.</p>
                        <p>&copy; 2025 EcoPuntos - Cuidando el planeta juntos 🌍</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Canje Rechazado - EcoPuntos
            
            Hola {usuario.nombre},
            
            Lamentamos informarte que tu canje de materiales reciclables ha sido RECHAZADO.
            
            Detalles del Canje:
            - Material: {canje.material.nombre}
            - Peso Estimado: {canje.cantidad} kg
            - Fecha de Rechazo: {timezone.now().strftime('%d/%m/%Y %H:%M')}
            
            Posibles razones del rechazo:
            - Material no cumple con los requisitos de calidad
            - Material contaminado o mezclado
            - Peso insuficiente
            - Material no corresponde a la categoría especificada
            
            Si tienes dudas o deseas más información, por favor contacta con nuestro equipo de soporte.
            
            ---
            EcoPuntos - Cuidando el planeta juntos 🌍
            """
            
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            print(f"✅ Correo de rechazo enviado a {usuario.email}")
        except Exception as e:
            print(f"❌ Error enviando correo de rechazo: {e}")
        
        return JsonResponse({
            'success': True,
            'message': 'Canje rechazado exitosamente.'
        })
        
    except Canje.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Canje no encontrado.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al rechazar el canje: {str(e)}'
        }, status=500)

def recuperar_password(request):
    """Vista para mostrar el formulario de recuperación de contraseña."""
    if request.user.is_authenticated:
        return redirect('index')
    
    # Agregar el contexto necesario para el formulario
    context = {
        'api_urls': {
            'send_code': reverse('send_verification_code'),
            'verify_code': reverse('verify_code'),
            'reset_password': reverse('reset_password', kwargs={'token': 'TOKEN_PLACEHOLDER'})
        }
    }
    return render(request, 'core/recuperar_password.html', context)

# Helper function to get monthly data for charts
def get_monthly_data(model, date_field, value_field, start_date, end_date):
    data = {}
    current_date = start_date
    while current_date <= end_date:
        month_key = current_date.strftime('%Y-%m')
        data[month_key] = 0
        current_date += timedelta(days=32) # Move to next month
        current_date = current_date.replace(day=1)

    # Fetch actual data
    monthly_sums = model.objects.filter(
        **{f'{date_field}__date__range': (start_date, end_date)}
    ).extra({'month': "TO_CHAR({}, 'YYYY-MM')".format(date_field)}).values('month').annotate(total=Sum(value_field))

    for item in monthly_sums:
        data[item['month']] = item['total'] or 0

    labels = []
    values = []
    current_date = start_date
    while current_date <= end_date:
        month_key = current_date.strftime('%Y-%m')
        labels.append(current_date.strftime('%b %Y'))
        values.append(data[month_key])
        current_date += timedelta(days=32) # Move to next month
        current_date = current_date.replace(day=1)

    return labels, values


@ajax_required_admin
def get_dashboard_stats(request):
    """Obtiene estadísticas completas del dashboard usando el nuevo sistema"""
    try:
        stats = StatisticsManager.get_comprehensive_dashboard_stats()
        return JsonResponse({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@ajax_required_admin
def get_chart_data(request):
    today = date.today()
    # Monthly Canjes
    monthly_canjes_data = []
    monthly_canjes_labels = []
    for i in range(6, -1, -1): # Last 7 months including current
        month_date = today - timedelta(days=30*i) # Approximate month
        start_of_month = month_date.replace(day=1)
        if month_date.month == 12:
            end_of_month = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)

        canjes_count = Canje.objects.filter(
            fecha_solicitud__range=(start_of_month, end_of_month),
            estado='aprobado'
        ).count()
        monthly_canjes_data.append(canjes_count)
        monthly_canjes_labels.append(month_date.strftime('%b'))

    # Popular Rutas (assuming each Ruta has a 'count' or 'usage' field, or we count canjes related to routes)
    # For now, let's assume we count unique Canjes associated with a Ruta, or simply count Ruta objects if they represent usage.
    # This might require a new model or field to track route usage.
    # Simulating popular_rutas for now, as direct counting from Canje->Ruta might not fit "ruta popular" logic without more schema info
    # For a real scenario, you'd aggregate data from activities related to routes.
    popular_rutas_labels = ['Ruta A', 'Ruta B', 'Ruta C', 'Ruta D', 'Ruta E']
    popular_rutas_data = [50, 40, 30, 20, 10]

    return JsonResponse({
        'success': True,
        'monthly_canjes_labels': monthly_canjes_labels,
        'monthly_canjes_data': monthly_canjes_data,
        'popular_rutas_labels': popular_rutas_labels,
        'popular_rutas_data': popular_rutas_data,
    })



def add_alerta(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        Alerta.objects.create(nombre=nombre, descripcion=descripcion)
        return JsonResponse({'status': 'success', 'message': 'Alerta agregada correctamente.'})
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def edit_alerta(request):
    if request.method == 'POST':
        alerta_id = request.POST.get('id')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        activa = request.POST.get('activa') == 'on'
        
        try:
            alerta = Alerta.objects.get(id=alerta_id)
            alerta.nombre = nombre
            alerta.descripcion = descripcion
            alerta.activa = activa
            alerta.save()
            return JsonResponse({'status': 'success', 'message': 'Alerta actualizada correctamente.'})
        except Alerta.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Alerta no encontrada.'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def delete_alerta(request):
    if request.method == 'POST':
        alerta_id = request.POST.get('id')
        try:
            alerta = Alerta.objects.get(id=alerta_id)
            alerta.delete()
            return JsonResponse({'status': 'success', 'message': 'Alerta eliminada correctamente.'})
        except Alerta.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Alerta no encontrada.'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def configuraciones(request):
    categoria = request.GET.get('categoria', 'general')
    configs = Configuracion.get_configs_by_category(categoria)
    categorias = dict(Configuracion.CATEGORIAS)
    return render(request, 'core/configuraciones.html', {
        'configs': configs,
        'categoria_actual': categoria,
        'categorias': categorias
    })

def add_configuracion(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            valor = request.POST.get('valor')
            descripcion = request.POST.get('descripcion')
            tipo = request.POST.get('tipo')
            categoria = request.POST.get('categoria')
            
            # Validar el valor según el tipo
            if tipo == 'numero':
                float(valor)  # Verificar que sea un número válido
            elif tipo == 'booleano':
                valor = str(valor.lower() == 'true')
            elif tipo == 'json':
                json.loads(valor)  # Verificar que sea JSON válido
            elif tipo == 'lista':
                # Convertir lista separada por comas en JSON
                lista = [item.strip() for item in valor.split(',')]
                valor = json.dumps(lista)
            
            Configuracion.objects.create(
                nombre=nombre,
                valor=valor,
                descripcion=descripcion,
                tipo=tipo,
                categoria=categoria
            )
            return JsonResponse({'status': 'success', 'message': 'Configuración agregada correctamente.'})
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Error en el valor: {str(e)}'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def edit_configuracion(request):
    if request.method == 'POST':
        try:
            config_id = request.POST.get('id')
            nombre = request.POST.get('nombre')
            valor = request.POST.get('valor')
            descripcion = request.POST.get('descripcion')
            tipo = request.POST.get('tipo')
            categoria = request.POST.get('categoria')
            
            config = Configuracion.objects.get(id=config_id)
            
            # Validar el valor según el tipo
            if tipo == 'numero':
                float(valor)  # Verificar que sea un número válido
            elif tipo == 'booleano':
                valor = str(valor.lower() == 'true')
            elif tipo == 'json':
                json.loads(valor)  # Verificar que sea JSON válido
            elif tipo == 'lista':
                # Convertir lista separada por comas en JSON
                lista = [item.strip() for item in valor.split(',')]
                valor = json.dumps(lista)
            
            config.nombre = nombre
            config.valor = valor
            config.descripcion = descripcion
            config.tipo = tipo
            config.categoria = categoria
            config.save()
            
            return JsonResponse({'status': 'success', 'message': 'Configuración actualizada correctamente.'})
        except Configuracion.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Configuración no encontrada.'}, status=404)
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': f'Error en el valor: {str(e)}'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def delete_configuracion(request):
    if request.method == 'POST':
        try:
            config_id = request.POST.get('id')
            config = Configuracion.objects.get(id=config_id)
            config.delete()
            return JsonResponse({'status': 'success', 'message': 'Configuración eliminada correctamente.'})
        except Configuracion.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Configuración no encontrada.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def get_config(nombre, default=None):
    """
    Obtiene el valor de una configuración por su nombre.
    Si no existe, retorna el valor por defecto.
    """
    try:
        config = Configuracion.objects.get(nombre=nombre)
        if config.tipo == 'numero':
            return float(config.valor)
        elif config.tipo == 'booleano':
            return config.valor.lower() == 'true'
        elif config.tipo == 'json':
            return json.loads(config.valor)
        return config.valor
    except Configuracion.DoesNotExist:
        return default
    except (ValueError, json.JSONDecodeError):
        return default

# Funciones helper para configuraciones específicas
def get_config_puntos(nombre, default=None):
    """Obtiene una configuración específica de puntos"""
    return get_config(nombre, default)

def get_config_rutas(nombre, default=None):
    """Obtiene una configuración específica de rutas"""
    return get_config(nombre, default)

def get_config_materiales(nombre, default=None):
    """Obtiene una configuración específica de materiales"""
    return get_config(nombre, default)

def get_config_notificaciones(nombre, default=None):
    """Obtiene una configuración específica de notificaciones"""
    return get_config(nombre, default)

# Configuraciones predefinidas
CONFIGURACIONES_PREDEFINIDAS = {
    'puntos': [
        {
            'nombre': 'puntos_por_kg',
            'valor': '10',
            'tipo': 'numero',
            'descripcion': 'Puntos otorgados por kilogramo de material reciclable',
            'categoria': 'puntos'
        },
        {
            'nombre': 'minimo_canje',
            'valor': '100',
            'tipo': 'numero',
            'descripcion': 'Puntos mínimos necesarios para realizar un canje',
            'categoria': 'puntos'
        },
        {
            'nombre': 'limite_diario',
            'valor': '1000',
            'tipo': 'numero',
            'descripcion': 'Límite diario de puntos por usuario',
            'categoria': 'puntos'
        }
    ],
    'rutas': [
        {
            'nombre': 'horarios_recoleccion',
            'valor': '["08:00-12:00", "14:00-18:00"]',
            'tipo': 'json',
            'descripcion': 'Horarios disponibles para recolección',
            'categoria': 'rutas'
        },
        {
            'nombre': 'dias_recoleccion',
            'valor': '["Lunes", "Miércoles", "Viernes"]',
            'tipo': 'json',
            'descripcion': 'Días disponibles para recolección',
            'categoria': 'rutas'
        }
    ],
    'materiales': [
        {
            'nombre': 'materiales_aceptados',
            'valor': '["Papel", "Plástico", "Vidrio", "Metal"]',
            'tipo': 'json',
            'descripcion': 'Lista de materiales aceptados para reciclaje',
            'categoria': 'materiales'
        }
    ],
    'notificaciones': [
        {
            'nombre': 'recordatorio_rutas',
            'valor': 'true',
            'tipo': 'booleano',
            'descripcion': 'Activar recordatorios de rutas de recolección',
            'categoria': 'notificaciones'
        },
        {
            'nombre': 'alertas_puntos',
            'valor': 'true',
            'tipo': 'booleano',
            'descripcion': 'Activar alertas de puntos',
            'categoria': 'notificaciones'
        }
    ],
    'general': [
        {
            'nombre': 'nombre_sistema',
            'valor': 'Eco Puntos',
            'tipo': 'texto',
            'descripcion': 'Nombre del sistema',
            'categoria': 'general'
        },
        {
            'nombre': 'moneda',
            'valor': 'Puntos',
            'tipo': 'texto',
            'descripcion': 'Nombre de la moneda virtual',
            'categoria': 'general'
        }
    ]
}

def inicializar_configuraciones():
    """Inicializa las configuraciones predefinidas si no existen"""
    for categoria, configs in CONFIGURACIONES_PREDEFINIDAS.items():
        for config in configs:
            Configuracion.objects.get_or_create(
                nombre=config['nombre'],
                defaults={
                    'valor': config['valor'],
                    'tipo': config['tipo'],
                    'descripcion': config['descripcion'],
                    'categoria': config['categoria']
                }
            )

@login_required
def rutasusuario(request):
    user_canjes_recoleccion = []
    canjes_aprobados = []
    historial_rutas = []
    user_data = {}
    
    if request.user.is_authenticated:
        # Obtener datos del usuario para auto-completar formulario
        user = request.user
        
        user_data = {
            'email': user.email or '',
            'telefono': user.telefono if hasattr(user, 'telefono') and user.telefono else '',
            'direccion': user.direccion if hasattr(user, 'direccion') and user.direccion else '',
        }
        
        # Obtener canjes del usuario que requieren recolección
        canjes_con_recoleccion = Canje.objects.filter(
            usuario=request.user, 
            necesita_recoleccion=True
        ).select_related('material').order_by('-fecha_solicitud')
        
        # Obtener canjes pendientes disponibles para recolección domiciliaria
        canjes_pendientes = Canje.objects.filter(
            usuario=request.user,
            estado='pendiente',
            necesita_recoleccion=False  # Que no estén ya programados para recolección
        ).select_related('material').order_by('-fecha_solicitud')
        
        # Preparar datos de canjes con información de ruta (basado en modelo Ruta)
        for canje in canjes_con_recoleccion:
            # Buscar ruta asociada al usuario (modelo Ruta, no RutaRecoleccion)
            ruta_info = None
            try:
                # Buscar la ruta más reciente del usuario que contenga el material del canje
                ruta_info = Ruta.objects.filter(
                    usuario=request.user,
                    materiales__icontains=canje.material.nombre
                ).order_by('-fecha_creacion').first()
                
                # Si no encuentra por material, buscar la ruta más reciente
                if not ruta_info:
                    ruta_info = Ruta.objects.filter(
                        usuario=request.user
                    ).order_by('-fecha_creacion').first()
                    
            except Exception as e:
                print(f"Error buscando ruta para canje {canje.id}: {e}")
            
            # Crear objeto compatible con RutaRecoleccion para la plantilla
            if ruta_info:
                # Convertir Ruta a formato compatible con RutaRecoleccion
                ruta_info.nombre = f"Ruta {ruta_info.id} - {canje.material.nombre}"
                ruta_info.fecha_programada = f"{ruta_info.fecha} {ruta_info.hora}"
            
            user_canjes_recoleccion.append({
                'canje': canje,
                'ruta_info': ruta_info
            })
        
        # Obtener historial de rutas completadas del usuario
        try:
            rutas_completadas = Ruta.objects.filter(
                usuario=request.user
            ).order_by('-fecha')[:10]  # Últimas 10 rutas
            
            for ruta in rutas_completadas:
                # Simular datos de historial (puedes ajustar según tu modelo)
                historial_rutas.append({
                    'nombre': f"Ruta {ruta.id}",
                    'fecha_completada': ruta.fecha if hasattr(ruta, 'fecha') else ruta.created_at if hasattr(ruta, 'created_at') else None,
                    'materiales_recolectados': ruta.materiales or "Material mixto",
                    'peso_total': "Estimado según materiales",
                    'puntos_otorgados': "Calculados automáticamente"
                })
        except Exception as e:
            print(f"Error obteniendo historial: {e}")
    
    context = {
        'user_canjes_recoleccion': user_canjes_recoleccion,
        'canjes_aprobados': canjes_pendientes,
        'historial_rutas': historial_rutas,
        'user_data': user_data,  # Datos del usuario para auto-completar
    }
    
    return render(request, 'core/rutasusuario.html', context)

@login_required
def rutasusuario_reagendada(request, ruta_id):
    """Vista especial que muestra rutasusuario con modal de reagendamiento"""
    try:
        # Buscar la ruta sin restricción de usuario para permitir acceso desde enlace de correo
        ruta = get_object_or_404(Ruta, id=ruta_id)
        
        # Si la ruta no pertenece al usuario actual, redirigir sin modal
        if ruta.usuario != request.user:
            print(f"Acceso denegado: Ruta {ruta_id} no pertenece al usuario {request.user.username}")
            return redirect('rutasusuario')
        
        # Agregar parámetros en la URL para mostrar el modal
        params = {
            'reagendada': 'true',
            'nueva_fecha': ruta.fecha.strftime('%Y-%m-%d') if ruta.fecha else '',
            'nueva_hora': ruta.hora.strftime('%H:%M') if ruta.hora else ''
        }
        
        return redirect(f"/rutasusuario/?{urlencode(params)}")
        
    except Ruta.DoesNotExist:
        print(f"Ruta {ruta_id} no encontrada")
        return redirect('rutasusuario')
    except Exception as e:
        print(f"Error en rutasusuario_reagendada: {str(e)}")
        return redirect('rutasusuario')

@login_required
@csrf_exempt
def agendar_ruta_usuario(request):
    if request.method == 'POST':
        try:
            # Obtener datos del formulario moderno
            nombre_completo = request.POST.get('nombre_completo')
            telefono = request.POST.get('telefono')
            email = request.POST.get('email', '')
            documento = request.POST.get('documento', '')
            direccion = request.POST.get('direccion')
            fecha_preferida = request.POST.get('fecha_preferida')
            hora_preferida = request.POST.get('hora_preferida')
            notas_adicionales = request.POST.get('notas_adicionales', '')
            
            # Obtener materiales/canjes seleccionados
            import json
            materiales_seleccionados = request.POST.get('materiales_seleccionados', '[]')
            try:
                materiales_data = json.loads(materiales_seleccionados)
            except:
                materiales_data = []
            
            # Preparar string de materiales para el campo y actualizar canjes
            materiales_str = ""
            canjes_ids = []
            
            for mat in materiales_data:
                if mat.get('tipo') == 'canje' and mat.get('id'):
                    # Es un canje seleccionado
                    canjes_ids.append(mat['id'])
                    materiales_str += f"{mat['material']}: {mat['peso']}kg ({mat['puntos']} puntos), "
                elif mat.get('peso', 0) > 0:
                    # Es material manual (si aún existe esta opción)
                    materiales_str += f"{mat['tipo'].capitalize()}: {mat['peso']}kg, "
            
            # Limpiar la coma final
            materiales_str = materiales_str.rstrip(', ')
            
            # Marcar los canjes seleccionados como que necesitan recolección
            if canjes_ids:
                Canje.objects.filter(
                    id__in=canjes_ids,
                    usuario=request.user
                ).update(necesita_recoleccion=True)
            
            # Crear la ruta con los nuevos datos
            nueva_ruta = Ruta.objects.create(
                usuario=request.user,
                fecha=fecha_preferida,
                hora=hora_preferida,
                direccion=direccion,
                materiales=materiales_str,
                referencia=notas_adicionales,
                # Campos adicionales para el nuevo formulario
                barrio=nombre_completo,  # Reutilizamos este campo para nombre completo
            )
            
            # Crear entrada en RutaRecoleccion si existe el modelo
            try:
                ruta_recoleccion = RutaRecoleccion.objects.create(
                    nombre=f"Recolección Usuario {request.user.id} - {nueva_ruta.id}",
                    descripcion=f"Recolección domiciliaria para {nombre_completo}",
                    fecha_programada=f"{fecha_preferida} {hora_preferida}:00",
                    direccion_inicio=direccion,
                    estado='planificada'
                )
                
                # Crear parada en la ruta
                ParadaRuta.objects.create(
                    ruta=ruta_recoleccion,
                    direccion=direccion,
                    orden=1,
                    descripcion=f"Recolección de: {materiales_str}",
                    contacto=telefono,
                    notas=notas_adicionales
                )
            except Exception as e:
                print(f"Error creando RutaRecoleccion: {e}")
            
            return JsonResponse({
                'success': True, 
                'message': '¡Tu solicitud de recolección ha sido enviada exitosamente! Te contactaremos pronto.'
            })
        except Exception as e:
            print(f"Error en agendar_ruta_usuario: {e}")
            return JsonResponse({
                'success': False, 
                'message': 'Error al procesar la solicitud. Por favor inténtalo de nuevo.'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@login_required
def ranking(request):
    # Obtener el top 10 usuarios ordenados por puntos
    top_usuarios = Usuario.objects.all().order_by('-puntos')[:10]

    # Calcular el máximo reciclado para la barra de progreso
    max_kg = 0
    ranking_data = []
    for user in top_usuarios:
        kg_reciclado = Canje.objects.filter(usuario=user, estado='aprobado').aggregate(total_kg=Sum('peso'))['total_kg'] or 0
        if kg_reciclado > max_kg:
            max_kg = kg_reciclado
        ranking_data.append({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'level': user.level,
            'role': user.role,
            'puntos': user.puntos,
            'kg_reciclado': kg_reciclado,
            'foto_perfil': user.foto_perfil.url if user.foto_perfil else None
        })

    # Calcular el porcentaje para la barra de progreso
    for user in ranking_data:
        if max_kg > 0:
            user['porcentaje'] = round((user['kg_reciclado'] / max_kg) * 100, 2)
        else:
            user['porcentaje'] = 0

    # Estadísticas generales
    total_usuarios = Usuario.objects.count()
    total_reciclado = Canje.objects.filter(estado='aprobado').aggregate(total_kg=Sum('peso'))['total_kg'] or 0
    reciclado_mes = Canje.objects.filter(estado='aprobado', fecha_solicitud__month=timezone.now().month).aggregate(total_kg=Sum('peso'))['total_kg'] or 0

    lider_actual = ranking_data[0] if ranking_data else None

    # Datos para gráfica mensual (últimos 8 meses)
    from django.db.models.functions import TruncMonth
    hoy = timezone.now()
    meses = [(hoy - timedelta(days=30*i)).replace(day=1) for i in reversed(range(8))]
    mensual_labels = [m.strftime('%b %Y') for m in meses]
    mensual_data = []
    for m in meses:
        total_mes = Canje.objects.filter(estado='aprobado', fecha_solicitud__year=m.year, fecha_solicitud__month=m.month).aggregate(total_kg=Sum('peso'))['total_kg'] or 0
        mensual_data.append(float(total_mes))

    # Datos para gráfica semanal (últimas 8 semanas)
    from django.db.models.functions import TruncWeek
    semanas = [(hoy - timedelta(days=7*i)).date() for i in reversed(range(8))]
    semanal_labels = [s.strftime('Semana %W') for s in semanas]
    semanal_data = []
    for s in semanas:
        inicio_semana = s - timedelta(days=s.weekday())
        fin_semana = inicio_semana + timedelta(days=6)
        total_semana = Canje.objects.filter(estado='aprobado', fecha_solicitud__date__gte=inicio_semana, fecha_solicitud__date__lte=fin_semana).aggregate(total_kg=Sum('peso'))['total_kg'] or 0
        semanal_data.append(float(total_semana))

    # Datos anuales por categoría
    year = hoy.year
    categorias = MaterialTasa.objects.filter(activo=True)
    categorias_data = []
    total_kg_anual = 0
    for cat in categorias:
        kg_cat = Canje.objects.filter(estado='aprobado', material=cat, fecha_solicitud__year=year).aggregate(total_kg=Sum('peso'))['total_kg'] or 0
        categorias_data.append({
            'nombre': cat.nombre,
            'kg': float(kg_cat),
            'porcentaje': 0,  # se calcula después
        })
        total_kg_anual += float(kg_cat)

    # Calcular porcentaje para cada categoría
    for cat in categorias_data:
        if total_kg_anual > 0:
            cat['porcentaje'] = round((cat['kg'] / total_kg_anual) * 100, 2)
        else:
            cat['porcentaje'] = 0

    principales = ['Plástico', 'Papel', 'Vidrio']
    otros_kg = sum(cat['kg'] for cat in categorias_data if cat['nombre'] not in principales)
    otros_porcentaje = round((otros_kg / total_kg_anual) * 100, 2) if total_kg_anual > 0 else 0

    context = {
        'ranking': ranking_data,
        'total_usuarios': total_usuarios,
        'total_reciclado': total_reciclado,
        'reciclado_mes': reciclado_mes,
        'lider_actual': lider_actual,
        'mensual_labels': mensual_labels,
        'mensual_data': mensual_data,
        'semanal_labels': semanal_labels,
        'semanal_data': semanal_data,
        'categorias_data': categorias_data,
        'otros_kg': otros_kg,
        'otros_porcentaje': otros_porcentaje,
        'total_kg_anual': total_kg_anual,
    }
    return render(request, 'core/ranking.html', context)

@login_required
def soportusu(request):
    """Vista simplificada que redirige al chatbot"""
    return redirect('chatbot_interface')
    
    return render(request, 'core/soportusu.html', context)

@login_required
@user_passes_test(is_admin)
def get_pending_redemptions(request):
    redemptions = RedencionPuntos.objects.filter(
        estado='pendiente'
    ).select_related('usuario').order_by('-fecha_solicitud')
    
    redemptions_data = [{
        'id': redemption.id,
        'fecha_solicitud': redemption.fecha_solicitud.isoformat(),
        'usuario_username': redemption.usuario.username,
        'puntos': redemption.puntos,
        'valor_cop': redemption.valor_cop,
        'metodo_pago': redemption.metodo_pago,
        'numero_cuenta': redemption.numero_cuenta
    } for redemption in redemptions]
    
    return JsonResponse({
        'success': True,
        'redemptions': redemptions_data
    })

@login_required
@user_passes_test(is_admin)
def aprobar_redencion(request, redencion_id):
    if request.method == 'POST':
        try:
            redencion = RedencionPuntos.objects.get(id=redencion_id)
            
            # Verificar que la redención esté pendiente
            if redencion.estado != 'pendiente':
                return JsonResponse({
                    'success': False,
                    'message': 'Esta redención ya ha sido procesada.'
                })
            
            # Actualizar estado de la redención
            redencion.estado = 'completado'
            redencion.fecha_procesamiento = timezone.now()
            redencion.save()
            
            # Crear notificación para el usuario
            Notificacion.objects.create(
                usuario=redencion.usuario,
                mensaje=f'¡Excelente! Tu redención de {redencion.puntos} puntos por ${redencion.valor_cop} COP ha sido aprobada. El dinero será transferido a tu cuenta {redencion.metodo_pago} ({redencion.numero_cuenta}) en las próximas 24-48 horas hábiles.'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Redención aprobada exitosamente.'
            })
            
        except RedencionPuntos.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Redención no encontrada.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al aprobar la redención: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

@login_required
@user_passes_test(is_admin)
def rechazar_redencion(request, redencion_id):
    if request.method == 'POST':
        try:
            redencion = RedencionPuntos.objects.get(id=redencion_id)
            
            # Verificar que la redención esté pendiente
            if redencion.estado != 'pendiente':
                return JsonResponse({
                    'success': False,
                    'message': 'Esta redención ya ha sido procesada.'
                })
            
            # Devolver los puntos al usuario
            usuario = redencion.usuario
            usuario.puntos += redencion.puntos
            usuario.save()
            
            # Actualizar estado de la redención
            redencion.estado = 'rechazado'
            redencion.fecha_procesamiento = timezone.now()
            redencion.save()
            
            # Crear notificación para el usuario
            Notificacion.objects.create(
                usuario=redencion.usuario,
                titulo='Redención Rechazada',
                mensaje=f'Tu solicitud de redención de {redencion.puntos} puntos ha sido rechazada. Los puntos han sido devueltos a tu cuenta. Si tienes dudas, contacta con soporte.',
                tipo='redencion_rechazada'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Redención rechazada exitosamente.'
            })
            
        except RedencionPuntos.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Redención no encontrada.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al rechazar la redención: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

@ajax_required_admin


@ajax_required_admin
def get_security_analytics(request):
    """Obtiene análisis de seguridad detallado"""
    try:
        days = int(request.GET.get('days', 30))
        stats = StatisticsManager.get_security_stats(days)
        
        # Análisis adicional de seguridad
        today = timezone.now()
        start_date = today - timedelta(days=days)
        
        # Sesiones por dispositivo
        sessions_by_device = SesionUsuario.objects.filter(
            fecha_creacion__gte=start_date
        ).values('dispositivo_id').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Usuarios con múltiples sesiones
        users_multiple_sessions = Usuario.objects.annotate(
            session_count=Count('sesiones')
        ).filter(session_count__gt=1).order_by('-session_count')[:10]
        
        security_analytics = {
            'basic_stats': stats,
            'sessions_by_device': list(sessions_by_device),
            'users_multiple_sessions': [
                {
                    'username': user.username,
                    'session_count': user.session_count,
                    'last_login': user.last_login
                }
                for user in users_multiple_sessions
            ]
        }
        
        return JsonResponse({
            'success': True,
            'analytics': security_analytics
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



@ajax_required_admin
def cleanup_expired_sessions(request):
    """Limpia sesiones expiradas"""
    try:
        cleaned_count = SecurityManager.cleanup_expired_sessions()
        return JsonResponse({
            'success': True,
            'message': f'Se limpiaron {cleaned_count} sesiones expiradas',
            'cleaned_count': cleaned_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def security_monitor(request):
    """Vista para el monitor de seguridad"""
    # Verificar si el usuario está autenticado y es admin
    if not request.user.is_authenticated:
        return redirect('iniciosesion')
    
    if not is_admin(request.user):
        return redirect('iniciosesion')
    
    return render(request, 'core/security_monitor.html')

@staff_member_required
def monitor_sesiones(request):
    """Vista para monitorear sesiones activas"""
    
    # Obtener todas las sesiones
    sesiones = SesionUsuario.objects.select_related('usuario').order_by('-fecha_creacion')
    
    # Calcular estadísticas
    total_sesiones = sesiones.count()
    sesiones_activas = sesiones.filter(activa=True).count()
    usuarios_conectados = sesiones.filter(activa=True).values('usuario').distinct().count()
    sesiones_expiradas = sesiones.filter(activa=False).count()
    
    context = {
        'title': 'Monitor de Sesiones',
        'sesiones': sesiones,
        'total_sesiones': total_sesiones,
        'sesiones_activas': sesiones_activas,
        'usuarios_conectados': usuarios_conectados, 
        'sesiones_expiradas': sesiones_expiradas
    }
    
    return render(request, 'core/monitor_sesiones.html', context)

@staff_member_required
def monitor_sesiones_refresh(request):
    """Vista AJAX para refrescar los datos del monitor de sesiones"""
    sesiones = SesionUsuario.objects.select_related('usuario').order_by('-fecha_creacion')
    
    # Calcular estadísticas
    stats = {
        'total_sesiones': sesiones.count(),
        'sesiones_activas': sesiones.filter(activa=True).count(),
        'usuarios_conectados': sesiones.filter(activa=True).values('usuario').distinct().count(),
        'sesiones_expiradas': sesiones.filter(activa=False).count()
    }
    
    sesiones_data = []
    for sesion in sesiones:
        sesiones_data.append({
            'id': sesion.id,
            'usuario': sesion.usuario.username,
            'ip': sesion.ip_address,
            'dispositivo': sesion.user_agent,
            'fecha_creacion': sesion.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S'),
            'ultima_actividad': sesion.ultima_actividad.strftime('%Y-%m-%d %H:%M:%S'),
            'activa': sesion.activa,
        })
    
    return JsonResponse({
        'stats': stats,
        'sesiones': sesiones_data
    })

@staff_member_required
def terminar_sesion(request, session_id):
    """Vista para terminar una sesión específica"""
    try:
        sesion = SesionUsuario.objects.get(id=session_id)
        sesion.activa = False
        sesion.save()
        return JsonResponse({'success': True, 'message': 'Sesión terminada correctamente'})
    except SesionUsuario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Sesión no encontrada'}, status=404)

@staff_member_required 
def limpiar_sesiones(request):
    """Vista para limpiar sesiones expiradas"""
    if request.method == 'POST':
        from .session_cleanup import cleanup_expired_sessions
        cleaned = cleanup_expired_sessions()
        return JsonResponse({
            'success': True,
            'cleaned': cleaned,
            'message': f'Se eliminaron {cleaned} sesiones expiradas'
        })
    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    context = {
        'sesiones': sesiones,
        'total_sesiones': total_sesiones,
        'sesiones_activas': sesiones_activas,
        'usuarios_conectados': usuarios_conectados,
        'sesiones_expiradas': sesiones_expiradas
    }
    
    return render(request, 'core/monitor_sesiones.html', context)

@login_required
@user_passes_test(is_admin)
@login_required
@user_passes_test(is_admin)
@login_required
@user_passes_test(is_admin)
@login_required
@user_passes_test(is_admin)
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST"])
def cerrar_sesion_admin(request, session_id):
    """Vista para cerrar una sesión específica"""
    try:
        sesion = get_object_or_404(SesionUsuario, id=session_id)
        username = sesion.usuario.username
        
        # Marcar la sesión como inactiva en la base de datos
        sesion.activa = False
        sesion.save()
        
        # Intentar invalidar la sesión usando SecurityManager
        try:
            from .security import SecurityManager
            SecurityManager.invalidate_session(sesion.token_sesion)
        except Exception as security_error:
            # Si falla la invalidación por SecurityManager, continuar
            # ya que la sesión ya fue marcada como inactiva en la BD
            pass
        
        # También intentar invalidar la sesión de Django si es posible
        try:
            from django.contrib.sessions.models import Session
            from django.utils import timezone
            
            # Buscar sesiones de Django activas para este usuario
            # y marcarlas como expiradas
            user_sessions = Session.objects.filter(
                expire_date__gte=timezone.now()
            )
            
            for session in user_sessions:
                try:
                    session_data = session.get_decoded()
                    if session_data.get('_auth_user_id') == str(sesion.usuario.id):
                        # Marcar como expirada inmediatamente
                        session.expire_date = timezone.now()
                        session.save()
                except Exception:
                    # Si no se puede decodificar, continuar
                    continue
                    
        except Exception as django_session_error:
            # Error al invalidar sesión de Django, pero continuar
            pass
        
        return JsonResponse({
            'success': True,
            'message': f'Sesión de {username} cerrada exitosamente'
        })
        
    except SesionUsuario.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'La sesión no existe o ya fue cerrada'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cerrar la sesión: {str(e)}'
        }, status=500)


def otorgar_logro_automatico(usuario, tipo_logro):
    """Función auxiliar para otorgar logros automáticamente"""
    from .models import Logro
    
    # Definir los diferentes tipos de logros
    logros_disponibles = {
        'primera_sesion': {
            'tipo': 'primera_sesion',
            'descripcion': '¡Primera aventura! Has iniciado sesión por primera vez en Eco Puntos',
            'puntos': 25
        },
        'explorador_verde': {
            'tipo': 'explorador',
            'descripcion': '¡Explorador Verde! Has visitado diferentes secciones de la plataforma',
            'puntos': 30
        },
        'reciclador_novato': {
            'tipo': 'reciclaje',
            'descripcion': '¡Reciclador Novato! Has realizado tu primer canje de materiales',
            'puntos': 75
        },
        'eco_guerrero': {
            'tipo': 'nivel',
            'descripcion': '¡Eco Guerrero! Has alcanzado un nuevo nivel ecológico',
            'puntos': 100
        },
        'guardian_ambiental': {
            'tipo': 'actividad',
            'descripcion': '¡Guardián Ambiental! Has mantenido actividad constante por una semana',
            'puntos': 150
        }
    }
    
    if tipo_logro in logros_disponibles:
        logro_info = logros_disponibles[tipo_logro]
        
        # Verificar si el usuario ya tiene este tipo de logro
        if not Logro.objects.filter(usuario=usuario, tipo=logro_info['tipo']).exists():
            Logro.objects.create(
                usuario=usuario,
                tipo=logro_info['tipo'],
                descripcion=logro_info['descripcion'],
                puntos=logro_info['puntos']
            )
            return True
    return False

@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST"])
def limpiar_sesiones_admin(request):
    """Vista para limpiar sesiones expiradas"""
    try:
        from .security import SecurityManager
        
        # Limpiar sesiones expiradas e inactivas
        expired_count = SecurityManager.cleanup_expired_sessions()
        inactive_count = SecurityManager.cleanup_inactive_sessions()
        
        total_cleaned = expired_count + inactive_count
        
        return JsonResponse({
            'success': True,
            'cleaned': total_cleaned,
            'message': f'Se limpiaron {total_cleaned} sesiones'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@user_passes_test(is_admin)
def enviar_correo_confirmacion_canje(usuario, redencion):
    """
    Envía un correo de confirmación cuando se realiza un canje de puntos.
    """
    try:
        print(f"🔧 DEBUG: Intentando enviar correo a {usuario.email}")
        print(f"🔧 DEBUG: EMAIL_BACKEND = {settings.EMAIL_BACKEND}")
        print(f"🔧 DEBUG: EMAIL_HOST_USER = {settings.EMAIL_HOST_USER}")
        
        # Verificar si el usuario tiene email
        if not usuario.email:
            print(f"❌ Error: Usuario {usuario.username} no tiene email configurado")
            return False
        
        # Renderizar templates
        subject = f'Confirmación de Canje #{redencion.id} - EcoPuntos'
        
        # Template HTML
        html_content = render_to_string('core/emails/canje_confirmacion.html', {
            'usuario': usuario,
            'redencion': redencion,
        })
        
        # Template de texto plano
        text_content = render_to_string('core/emails/canje_confirmacion.txt', {
            'usuario': usuario,
            'redencion': redencion,
        })
        
        # Crear mensaje con ambos formatos
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Enviar correo
        result = msg.send()
        print(f"✅ Correo enviado exitosamente a {usuario.email}. Result: {result}")
        
        return True
        
    except Exception as e:
        # Log del error si es necesario
        print(f"❌ Error enviando correo de confirmación: {e}")
        return False


def enviar_correo_recompensa_canjeada(usuario, recompensa, redencion):
    """
    Envía un correo de confirmación cuando se canjea una recompensa.
    """
    try:
        print(f"🔧 DEBUG: Intentando enviar correo de recompensa a {usuario.email}")
        
        # Verificar si el usuario tiene email
        if not usuario.email:
            print(f"❌ Error: Usuario {usuario.username} no tiene email configurado")
            return False
        
        # Renderizar templates
        subject = f'¡Recompensa Canjeada! {recompensa.nombre} - EcoPuntos'
        
        # Template HTML
        html_content = render_to_string('core/emails/recompensa_canjeada.html', {
            'usuario': usuario,
            'recompensa': recompensa,
            'redencion': redencion,
        })
        
        # Template de texto plano
        text_content = render_to_string('core/emails/recompensa_canjeada.txt', {
            'usuario': usuario,
            'recompensa': recompensa,
            'redencion': redencion,
        })
        
        # Crear mensaje con ambos formatos
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Enviar correo
        result = msg.send()
        print(f"✅ Correo de recompensa enviado exitosamente a {usuario.email}. Result: {result}")
        
        return True
        
    except Exception as e:
        # Log del error si es necesario
        print(f"❌ Error enviando correo de recompensa canjeada: {e}")
        return False


def enviar_correo_canje_aprobado(usuario, canje):
    """
    Envía un correo de confirmación cuando se aprueba un canje por el admin.
    """
    try:
        print(f"🔧 DEBUG: Intentando enviar correo de canje aprobado a {usuario.email}")
        
        # Verificar si el usuario tiene email
        if not usuario.email:
            print(f"❌ Error: Usuario {usuario.username} no tiene email configurado")
            return False
        
        # Renderizar templates
        subject = f'¡Canje Aprobado! +{canje.puntos} puntos - EcoPuntos'
        
        # Template HTML
        html_content = render_to_string('core/emails/canje_aprobado.html', {
            'usuario': usuario,
            'canje': canje,
        })
        
        # Template de texto plano
        text_content = render_to_string('core/emails/canje_aprobado.txt', {
            'usuario': usuario,
            'canje': canje,
        })
        
        # Crear mensaje con ambos formatos
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Enviar correo
        result = msg.send()
        print(f"✅ Correo de canje aprobado enviado exitosamente a {usuario.email}. Result: {result}")
        
        return True
        
    except Exception as e:
        # Log del error si es necesario
        print(f"❌ Error enviando correo de canje aprobado: {e}")
        return False


def test_email_config(request):
    """
    Vista temporal para probar la configuración de correo.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Usuario no autenticado'})
    
    try:
        from django.core.mail import send_mail
        
        print(f"🔧 DEBUG: Configuración de correo:")
        print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        print(f"   Usuario email: {request.user.email}")
        
        if not request.user.email:
            return JsonResponse({'error': 'Usuario no tiene email configurado'})
        
        # Enviar email de prueba
        result = send_mail(
            'Prueba de Correo - EcoPuntos',
            'Este es un correo de prueba para verificar la configuración de correo.',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        
        print(f"✅ Resultado del envío: {result}")
        
        return JsonResponse({
            'success': True, 
            'message': f'Correo de prueba enviado a {request.user.email}',
            'result': result
        })
        
    except Exception as e:
        print(f"❌ Error en prueba de correo: {e}")
        return JsonResponse({'error': str(e)})


def redimir_puntos(request):
    """
    Vista para procesar la redención de puntos.
    """
    if not request.user.is_authenticated:
        return redirect('iniciosesion')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            points = int(request.POST.get('points', 0))
            phone = request.POST.get('phone', '')
            payment_method = request.POST.get('payment_method', '')
            
            # Validaciones básicas
            if points < 100:
                # No usar messages.error(), redirect silencioso
                return redirect('pagos')
            
            if not phone:
                # No usar messages.error(), redirect silencioso
                return redirect('pagos')
            
            if not payment_method:
                # No usar messages.error(), redirect silencioso
                return redirect('pagos')
            
            # Verificar si el usuario tiene suficientes puntos
            user_points = getattr(request.user, 'puntos', 0)
            if points > user_points:
                # No usar messages.error(), redirect silencioso
                return redirect('pagos')
            
            # Calcular valor en COP
            valor_cop = points * 0.5  # 1 punto = $0.50 COP
            
            # Crear el registro de redención
            redencion = RedencionPuntos.objects.create(
                usuario=request.user,
                puntos=points,
                valor_cop=valor_cop,
                metodo_pago=payment_method,
                numero_cuenta=phone,
                estado='pendiente'
            )
            
            # Descontar los puntos del usuario
            request.user.puntos -= points
            request.user.save()
            
            # Crear notificación en lugar de messages.success()
            Notificacion.objects.create(
                usuario=request.user,
                titulo='Solicitud de Retiro Enviada',
                mensaje=f'¡Solicitud de canje enviada exitosamente! Canjeaste {points} puntos por ${valor_cop} COP. Te notificaremos cuando sea procesada.',
                tipo='retiro_enviado'
            )
            
            # Enviar correo de confirmación
            try:
                enviar_correo_confirmacion_canje(request.user, redencion)
            except Exception as e:
                # Si falla el correo, continuar sin interrumpir el proceso
                pass
            
        except ValueError:
            # No usar messages.error(), redirect silencioso
            pass
        except Exception as e:
            # No usar messages.error(), redirect silencioso
            pass
    
    return redirect('pagos')

def verificar_sesion_activa(request):
    """
    Endpoint AJAX para verificar si la sesión del usuario sigue activa
    NO usa @login_required para evitar bucles de redirección
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Primero verificar si el usuario está autenticado en Django
            if not request.user.is_authenticated:
                logger.info("Usuario no autenticado en Django")
                return JsonResponse({
                    'activa': False,
                    'message': 'Tu sesión ha expirado.'
                })
            
            # Verificar si el usuario tiene una sesión activa en nuestro sistema personalizado
            session_token = request.session.get('session_token')
            logger.info(f"Session token encontrado: {'Sí' if session_token else 'No'}")
            
            from .models import SesionUsuario
            from django.utils import timezone
            
            # Buscar TODAS las sesiones activas para este usuario
            sesiones_activas = SesionUsuario.objects.filter(
                usuario=request.user,
                activa=True
            )
            
            logger.info(f"Sesiones activas encontradas para {request.user.username}: {sesiones_activas.count()}")
            
            # Si no hay sesiones activas, la sesión fue cerrada
            if not sesiones_activas.exists():
                logger.warning(f"No hay sesiones activas para {request.user.username} - sesión cerrada por admin")
                return JsonResponse({
                    'activa': False,
                    'message': 'Tu sesión ha sido cerrada por un administrador.'
                })
            
            # Si hay sesiones activas, verificar expiración
            for sesion in sesiones_activas:
                if sesion.fecha_expiracion > timezone.now():
                    logger.info(f"Sesión válida encontrada para {request.user.username}")
                    # Si no hay token en la sesión de Django, actualizarlo
                    if not session_token:
                        request.session['session_token'] = sesion.token_sesion
                        logger.info("Token actualizado en sesión de Django")
                    
                    return JsonResponse({
                        'activa': True,
                        'message': 'Sesión activa'
                    })
            
            # Todas las sesiones están expiradas
            logger.info(f"Todas las sesiones de {request.user.username} están expiradas")
            return JsonResponse({
                'activa': False,
                'message': 'Tu sesión ha expirado.'
            })
                
        except Exception as e:
            logger.error(f"Error verificando sesión para {request.user.username}: {str(e)}")
            # En caso de error, asumir que la sesión está activa para evitar desconexiones falsas
            return JsonResponse({
                'activa': True,
                'message': f'Sesión activa (error en verificación: {str(e)})'
            })
    
    return JsonResponse({
        'activa': False,
        'message': 'Petición no válida'
    })

@login_required
@require_http_methods(["POST"])
def aceptar_terminos(request):
    """Vista para que el usuario acepte los términos y condiciones"""
    try:
        usuario = request.user
        usuario.terminos_aceptados = True
        usuario.fecha_aceptacion_terminos = timezone.now()
        usuario.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Términos aceptados correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al aceptar términos: {str(e)}'
        })

@login_required
def verificar_terminos(request):
    """Vista para verificar si el usuario ha aceptado los términos"""
    return JsonResponse({
        'terminos_aceptados': request.user.terminos_aceptados
    })

@login_required
def verificar_reagendamientos_pendientes(request):
    """Vista para verificar si el usuario tiene reagendamientos pendientes sin ver"""
    try:
        # Buscar rutas reagendadas que no han sido vistas por el usuario
        # Usamos las notificaciones de reagendamiento no leídas como indicador
        notificacion_reagendamiento = Notificacion.objects.filter(
            usuario=request.user,
            titulo="Recolección Reagendada",
            leida=False
        ).first()
        
        if notificacion_reagendamiento:
            # Extraer información de la ruta más reciente
            # Buscar la ruta más reciente del usuario
            ruta_reciente = Ruta.objects.filter(usuario=request.user).order_by('-id').first()
            
            if ruta_reciente:
                return JsonResponse({
                    'success': True,
                    'reagendamiento_pendiente': True,
                    'nueva_fecha': ruta_reciente.fecha.strftime('%Y-%m-%d') if ruta_reciente.fecha else '',
                    'nueva_hora': ruta_reciente.hora.strftime('%H:%M') if ruta_reciente.hora else '',
                    'ruta_id': ruta_reciente.id
                })
        
        return JsonResponse({
            'success': True,
            'reagendamiento_pendiente': False
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def marcar_reagendamiento_visto(request):
    """Vista para marcar un reagendamiento como visto por el usuario"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            ruta_id = data.get('ruta_id')
            
            if ruta_id:
                # Marcar las notificaciones de reagendamiento como leídas
                notificaciones_actualizadas = Notificacion.objects.filter(
                    usuario=request.user,
                    titulo="Recolección Reagendada",
                    leida=False
                ).update(leida=True)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Reagendamiento marcado como visto. {notificaciones_actualizadas} notificaciones actualizadas.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'ID de ruta requerido'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def get_notifications(request):
    """Vista para obtener notificaciones del usuario desde el modelo Notificacion"""
    try:
        from .models import Notificacion
        from django.utils import timezone
        
        # Obtener solo las notificaciones del modelo Notificacion
        notificaciones = Notificacion.objects.filter(
            usuario=request.user
        ).order_by('-fecha_creacion')[:20]  # Últimas 20 notificaciones
        
        notifications = []
        unread_count = 0
        
        for notif in notificaciones:
            # Determinar el tipo basado en el tipo de notificación
            notif_tipo = 'general'  # default
            if notif.tipo in ['recompensa_canjeada', 'retiro_enviado', 'redencion_aprobada', 'redencion_pendiente', 'redencion_rechazada']:
                notif_tipo = 'redencion'
            elif notif.tipo in ['perfil_actualizado', 'foto_actualizada']:
                notif_tipo = 'perfil'
            elif notif.tipo in ['canje_aprobado', 'canje_pendiente', 'canje_rechazado']:
                notif_tipo = 'canje'
            elif notif.tipo in ['password_cambiado', 'sistema']:
                notif_tipo = 'general'
            
            notifications.append({
                'id': notif.id,
                'tipo': notif_tipo,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'fecha_creacion': notif.fecha_creacion.isoformat(),
                'leida': notif.leida,
                'unread': not notif.leida,
                'data': {
                    'notificacion_id': notif.id,
                    'tipo': notif.tipo
                }
            })
            
            if not notif.leida:
                unread_count += 1
        
        return JsonResponse({
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'notifications': [],
            'unread_count': 0
        })

@login_required
def clear_notifications(request):
    """Vista para limpiar todas las notificaciones del usuario"""
    if request.method == 'POST':
        try:
            # Marcar todas las notificaciones como leídas
            notificaciones_actualizadas = Notificacion.objects.filter(
                usuario=request.user,
                leida=False
            ).update(leida=True)
            
            return JsonResponse({
                'success': True,
                'message': f'Se marcaron {notificaciones_actualizadas} notificaciones como leídas',
                'cleared_count': notificaciones_actualizadas
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def delete_all_notifications(request):
    """Vista para eliminar TODAS las notificaciones del usuario"""
    if request.method == 'POST':
        try:
            # Eliminar todas las notificaciones del usuario
            notificaciones_eliminadas = Notificacion.objects.filter(
                usuario=request.user
            ).count()
            
            Notificacion.objects.filter(usuario=request.user).delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Se eliminaron {notificaciones_eliminadas} notificaciones',
                'deleted_count': notificaciones_eliminadas
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def mark_notification_read(request):
    """Vista para marcar una notificación específica como leída"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')
            
            if not notification_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID de notificación requerido'
                })
            
            # Marcar la notificación específica como leída
            notificacion = Notificacion.objects.filter(
                id=notification_id,
                usuario=request.user
            ).first()
            
            if notificacion:
                notificacion.leida = True
                notificacion.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Notificación marcada como leída'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Notificación no encontrada'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def mark_all_notifications_read(request):
    """Vista para marcar todas las notificaciones como leídas"""
    if request.method == 'POST':
        try:
            # Marcar todas las notificaciones como leídas
            notificaciones_actualizadas = Notificacion.objects.filter(
                usuario=request.user,
                leida=False
            ).update(leida=True)
            
            return JsonResponse({
                'success': True,
                'message': f'Se marcaron {notificaciones_actualizadas} notificaciones como leídas',
                'updated_count': notificaciones_actualizadas
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# ========================================
# NUEVAS VISTAS DE INTEGRACIÓN CANJES-RUTAS
# ========================================

@login_required
def solicitar_canje_con_recoleccion(request):
    """Vista integrada para solicitar canje con opción de recolección domiciliaria"""
    from .forms import CanjeConRecoleccionForm
    from .models import RutaRecoleccion, ParadaRuta
    # from .services import RutaOptimizador  # Comentado para evitar error de importación
    
    if request.method == 'POST':
        form = CanjeConRecoleccionForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                # Crear el canje
                canje = form.save(commit=False)
                canje.usuario = request.user
                canje.save()
                
                # Si necesita recolección, gestionar ruta automáticamente
                if canje.necesita_recoleccion:
                    resultado_ruta = gestionar_ruta_automatica(canje)
                    
                    # Crear notificación específica según el resultado
                    if resultado_ruta['asignado_a_ruta_existente']:
                        mensaje_notif = f'Tu canje fue agregado a una ruta existente. Recolección programada para {resultado_ruta["fecha_recoleccion"]}.'
                        canje.estado = 'confirmado'
                    else:
                        mensaje_notif = f'Tu canje está programado para recolección. Te notificaremos cuando se asigne una ruta.'
                        canje.estado = 'pendiente'
                    
                    canje.save()
                    
                    # Crear notificación
                    Notificacion.objects.create(
                        usuario=request.user,
                        titulo='¡Canje con Recolección Solicitado!',
                        mensaje=mensaje_notif,
                        tipo='canje_recoleccion'
                    )
                else:
                    # Canje sin recolección (entrega directa)
                    Notificacion.objects.create(
                        usuario=request.user,
                        titulo='Canje en Revisión',
                        mensaje=f'Tu canje de {canje.material.nombre} ({canje.peso} kg) está en revisión.',
                        tipo='canje_pendiente'
                    )
                
                # Verificar logros automáticos
                if otorgar_logro_automatico(request.user, 'reciclador_novato'):
                    Notificacion.objects.create(
                        usuario=request.user,
                        titulo='¡Nuevo Logro Desbloqueado!',
                        mensaje='¡Felicidades! Has ganado el logro "Reciclador Novato" por realizar tu primer canje.',
                        tipo='logro'
                    )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Solicitud procesada exitosamente.',
                        'canje': {
                            'id': canje.id,
                            'material': canje.material.nombre,
                            'peso': float(canje.peso),
                            'puntos': canje.puntos,
                            'estado': canje.get_estado_display(),
                            'necesita_recoleccion': canje.necesita_recoleccion,
                            'ruta_asignada': bool(canje.ruta_asignada)
                        }
                    })
                else:
                    return redirect('canjes_integrados')
                    
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'Error al procesar la solicitud: {str(e)}'
                    })
                else:
                    messages.error(request, f'Error al procesar la solicitud: {str(e)}')
                    return redirect('canjes_integrados')
        else:
            # Form no válido
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Por favor corrige los errores en el formulario.',
                    'errors': form.errors
                })
    else:
        form = CanjeConRecoleccionForm(user=request.user)
    
    # Obtener materiales activos
    materiales = MaterialTasa.objects.filter(activo=True)
    
    context = {
        'form': form,
        'materiales': materiales,
        'canjes_recientes': Canje.objects.filter(usuario=request.user).order_by('-fecha_solicitud')[:5],
        'puntos_usuario': request.user.puntos
    }
    
    return render(request, 'core/canje_integrado.html', context)

def gestionar_ruta_automatica(canje):
    """Función para gestionar automáticamente la asignación de rutas"""
    from .models import RutaRecoleccion, ParadaRuta
    from django.utils import timezone
    from datetime import timedelta
    
    # Determinar zona basada en la dirección (simplificado)
    zona = determinar_zona_por_direccion(canje.direccion_recoleccion)
    
    # Buscar rutas existentes en la misma zona para los próximos 3 días
    fecha_limite = timezone.now().date() + timedelta(days=3)
    
    rutas_disponibles = RutaRecoleccion.objects.filter(
        zona=zona,
        fecha_programada__gte=timezone.now().date(),
        fecha_programada__lte=fecha_limite,
        estado__in=['planificada', 'programada']
    ).annotate(
        peso_actual=models.Sum('canje__peso')
    ).filter(
        peso_actual__lt=models.F('capacidad_maxima') - canje.peso
    )
    
    if rutas_disponibles.exists():
        # Asignar a la ruta más cercana con capacidad
        ruta = rutas_disponibles.first()
        canje.ruta_asignada = ruta
        
        # Crear parada en la ruta
        orden_siguiente = ruta.paradas.count() + 1
        ParadaRuta.objects.create(
            ruta=ruta,
            canje=canje,
            orden=orden_siguiente,
            direccion=canje.direccion_recoleccion,
            referencia=canje.referencia_direccion,
            telefono_contacto=canje.telefono_contacto,
            horario_preferido=canje.horario_disponible
        )
        
        return {
            'asignado_a_ruta_existente': True,
            'ruta_id': ruta.id,
            'fecha_recoleccion': ruta.fecha_programada.strftime('%d/%m/%Y')
        }
    else:
        # Crear nueva ruta si hay suficientes canjes en la zona
        canjes_zona_pendientes = Canje.objects.filter(
            necesita_recoleccion=True,
            ruta_asignada__isnull=True,
            direccion_recoleccion__icontains=zona,  # Búsqueda simplificada
            estado='pendiente'
        ).count()
        
        if canjes_zona_pendientes >= 3:  # Mínimo 3 canjes para crear ruta
            crear_nueva_ruta_automatica(zona, canje)
            return {
                'asignado_a_ruta_existente': False,
                'ruta_creada': True,
                'mensaje': 'Nueva ruta creada'
            }
        
        return {
            'asignado_a_ruta_existente': False,
            'ruta_creada': False,
            'mensaje': 'En espera de más solicitudes en la zona'
        }

def determinar_zona_por_direccion(direccion):
    """Función para determinar la zona basada en la dirección"""
    direccion_lower = direccion.lower()
    
    # Palabras clave para cada zona (puedes expandir esto)
    zonas = {
        'norte': ['norte', 'usaquén', 'suba', 'engativá'],
        'sur': ['sur', 'bosa', 'kennedy', 'usme', 'tunjuelito', 'rafael uribe'],
        'este': ['este', 'san cristóbal', 'ciudad bolívar'],
        'oeste': ['oeste', 'fontibón', 'puente aranda'],
        'centro': ['centro', 'candelaria', 'santa fe', 'teusaquillo', 'chapinero']
    }
    
    for zona, palabras_clave in zonas.items():
        if any(palabra in direccion_lower for palabra in palabras_clave):
            return zona
    
    return 'centro'  # Zona por defecto

def crear_nueva_ruta_automatica(zona, canje_inicial):
    """Crear una nueva ruta automáticamente cuando hay suficientes canjes"""
    from .models import RutaRecoleccion, ParadaRuta
    from django.utils import timezone
    from datetime import timedelta
    
    # Programar para el día siguiente
    fecha_programada = timezone.now().date() + timedelta(days=1)
    
    # Crear la ruta
    ruta = RutaRecoleccion.objects.create(
        nombre=f'Ruta {zona.title()} - {fecha_programada.strftime("%d/%m/%Y")}',
        fecha_programada=fecha_programada,
        hora_inicio=timezone.time(8, 0),
        hora_fin_estimada=timezone.time(12, 0),
        zona=zona,
        estado='planificada'
    )
    
    # Asignar el canje inicial
    canje_inicial.ruta_asignada = ruta
    canje_inicial.save()
    
    # Crear la primera parada
    ParadaRuta.objects.create(
        ruta=ruta,
        canje=canje_inicial,
        orden=1,
        direccion=canje_inicial.direccion_recoleccion,
        referencia=canje_inicial.referencia_direccion,
        telefono_contacto=canje_inicial.telefono_contacto,
        horario_preferido=canje_inicial.horario_disponible
    )
    
    return ruta

@login_required 
def canjes_integrados(request):
    """Vista para mostrar canjes con integración de rutas"""
    canjes = Canje.objects.filter(usuario=request.user).order_by('-fecha_solicitud')
    
    # Separar canjes por estado
    canjes_pendientes = canjes.filter(estado='pendiente')
    canjes_confirmados = canjes.filter(estado='confirmado')
    canjes_recolectados = canjes.filter(estado='recolectado')
    canjes_completados = canjes.filter(estado__in=['aprobado', 'completado'])
    
    context = {
        'canjes_pendientes': canjes_pendientes,
        'canjes_confirmados': canjes_confirmados,
        'canjes_recolectados': canjes_recolectados,
        'canjes_completados': canjes_completados,
        'total_puntos': sum(c.puntos_a_otorgar for c in canjes_completados),
        'materiales': MaterialTasa.objects.filter(activo=True)
    }
    
    return render(request, 'core/canjes_integrados.html', context)

@login_required
def dashboard_rutas(request):
    """Dashboard para visualizar rutas y su estado"""
    # Solo para conductores/admin
    if not request.user.role == 'admin':
        return redirect('dashusuario')
    
    from .models import RutaRecoleccion
    
    # Rutas de hoy
    rutas_hoy = RutaRecoleccion.objects.filter(
        fecha_programada=timezone.now().date()
    ).prefetch_related('paradas__canje__usuario')
    
    # Rutas próximas
    rutas_proximas = RutaRecoleccion.objects.filter(
        fecha_programada__gt=timezone.now().date(),
        fecha_programada__lte=timezone.now().date() + timedelta(days=7)
    ).order_by('fecha_programada')
    
    context = {
        'rutas_hoy': rutas_hoy,
        'rutas_proximas': rutas_proximas,
        'total_rutas_activas': RutaRecoleccion.objects.filter(estado__in=['planificada', 'programada', 'en_curso']).count()
    }
    
    return render(request, 'core/dashboard_rutas.html', context)

# API Endpoints para Gestión de Seguimiento de Recompensas

@login_required
@ajax_required_admin
def actualizar_estado_seguimiento(request, seguimiento_id):
    """Actualizar el estado de un seguimiento de recompensa (solo admin)"""
    if request.method == 'POST':
        try:
            seguimiento = get_object_or_404(SeguimientoRecompensa, id=seguimiento_id)
            nuevo_estado = request.POST.get('nuevo_estado')
            comentario = request.POST.get('comentario', '')
            ubicacion = request.POST.get('ubicacion', '')
            
            # Validar que el nuevo estado sea válido
            estados_validos = [estado[0] for estado in SeguimientoRecompensa.ESTADOS_SEGUIMIENTO]
            if nuevo_estado not in estados_validos:
                return JsonResponse({
                    'success': False, 
                    'message': 'Estado no válido.'
                })
            
            from django.db import transaction
            with transaction.atomic():
                # Guardar estado anterior
                estado_anterior = seguimiento.estado
                
                # Actualizar seguimiento
                seguimiento.estado = nuevo_estado
                
                # Si es entregado, marcar fecha de entrega
                if nuevo_estado == 'entregado':
                    seguimiento.fecha_entrega_real = timezone.now()
                
                seguimiento.save()
                
                # Crear registro en historial
                HistorialSeguimiento.objects.create(
                    seguimiento=seguimiento,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado,
                    comentario=comentario,
                    ubicacion=ubicacion,
                    usuario_responsable=request.user
                )
                
                # Crear notificación para el usuario
                mensaje_estado = {
                    'confirmado': 'Tu pedido ha sido confirmado y está siendo preparado.',
                    'preparando': 'Tu pedido está siendo preparado para el envío.',
                    'empacado': 'Tu pedido ha sido empacado y está listo para el envío.',
                    'en_transito': 'Tu pedido está en camino hacia tu dirección.',
                    'en_reparto': 'Tu pedido está siendo entregado por nuestro repartidor.',
                    'entregado': '¡Tu pedido ha sido entregado exitosamente!',
                    'problema': 'Hubo un problema con tu pedido. Te contactaremos pronto.',
                    'cancelado': 'Tu pedido ha sido cancelado.'
                }
                
                Notificacion.objects.create(
                    usuario=seguimiento.usuario,
                    titulo=f'Actualización de Pedido - {seguimiento.codigo_seguimiento}',
                    mensaje=mensaje_estado.get(nuevo_estado, f'Tu pedido cambió al estado: {seguimiento.get_estado_display()}'),
                    tipo='seguimiento_actualizado'
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Estado actualizado a {seguimiento.get_estado_display()}',
                'nuevo_estado': seguimiento.get_estado_display(),
                'porcentaje_progreso': seguimiento.porcentaje_progreso,
                'estado_color': seguimiento.estado_color
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al actualizar estado: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@login_required
def listar_seguimientos_admin(request):
    """Listar todos los seguimientos para administración"""
    print(f"=== LISTAR_SEGUIMIENTOS_ADMIN LLAMADO ===")
    print(f"Usuario: {request.user}")
    print(f"Es admin: {is_admin(request.user)}")
    print(f"Es AJAX: {request.headers.get('x-requested-with') == 'XMLHttpRequest'}")
    print(f"Método: {request.method}")
    
    # Verificar permisos manualmente
    if not is_admin(request.user):
        print("ERROR: Usuario no es admin")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Sin permisos de administrador.'}, status=403)
        return redirect('inicioadmin')
    
    seguimientos = SeguimientoRecompensa.objects.select_related(
        'usuario', 'recompensa', 'redencion'
    ).prefetch_related('historial').order_by('-fecha_solicitud')
    
    print(f"Total seguimientos encontrados: {seguimientos.count()}")
    
    # Filtros opcionales
    estado_filter = request.GET.get('estado')
    if estado_filter:
        seguimientos = seguimientos.filter(estado=estado_filter)
    
    usuario_filter = request.GET.get('usuario')
    if usuario_filter:
        seguimientos = seguimientos.filter(usuario__username__icontains=usuario_filter)
    
    # Si es AJAX, devolver datos JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        print("Procesando como AJAX request...")
        seguimientos_data = []
        for s in seguimientos:
            seguimientos_data.append({
                'id': s.id,
                'codigo': s.codigo_seguimiento,
                'usuario': s.usuario.username,
                'telefono': s.telefono_contacto,
                'recompensa': s.recompensa.nombre,
                'puntos': s.recompensa.puntos_requeridos,
                'estado': s.estado,
                'estado_display': s.get_estado_display(),
                'progreso': s.porcentaje_progreso,
                'fecha_solicitud': s.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
                'fecha_estimada': s.fecha_estimada_entrega.strftime('%d/%m/%Y') if s.fecha_estimada_entrega else None,
                'direccion': s.direccion_entrega[:50] + '...' if len(s.direccion_entrega) > 50 else s.direccion_entrega,
            })
        
        print(f"Seguimientos procesados: {len(seguimientos_data)}")
        
        # Calcular estadísticas
        from django.db.models import Count, Q
        estadisticas = {
            'total': seguimientos.count(),
            'pendientes': seguimientos.filter(Q(estado='SOLICITADO') | Q(estado='PREPARANDO')).count(),
            'proceso': seguimientos.filter(estado='EN_CAMINO').count(),
            'completados': seguimientos.filter(estado='ENTREGADO').count(),
        }
        
        print(f"Estadísticas calculadas: {estadisticas}")
        
        response_data = {
            'success': True,
            'seguimientos': seguimientos_data,
            'estadisticas': estadisticas
        }
        
        print(f"Enviando respuesta JSON con {len(seguimientos_data)} seguimientos")
        return JsonResponse(response_data)
    
    print("Procesando como request normal (no AJAX)")
    # Para requests normales (no AJAX)
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(seguimientos, 20)
    page = request.GET.get('page')
    seguimientos_page = paginator.get_page(page)
    
    context = {
        'seguimientos': seguimientos_page,
        'estados': SeguimientoRecompensa.ESTADOS_SEGUIMIENTO,
        'filtros': {
            'estado': estado_filter,
            'usuario': usuario_filter
        }
    }
    
    return render(request, 'core/admin/seguimientos_admin.html', context)

@login_required
def detalle_seguimiento(request, codigo_seguimiento):
    """Ver detalles completos de un seguimiento (usuario o admin)"""
    seguimiento = get_object_or_404(SeguimientoRecompensa, codigo_seguimiento=codigo_seguimiento)
    
    # Verificar permisos: el usuario o admin
    if not (seguimiento.usuario == request.user or is_admin(request.user)):
        return JsonResponse({'success': False, 'message': 'Sin permisos.'}, status=403)
    
    historial = seguimiento.historial.all().order_by('-fecha_cambio')
    
    context = {
        'seguimiento': seguimiento,
        'historial': historial,
        'es_admin': is_admin(request.user)
    }
    
    # Si es AJAX, devolver datos JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        historial_data = []
        for h in historial:
            historial_data.append({
                'estado': h.get_estado_nuevo_display(),
                'fecha': h.fecha_cambio.strftime('%d/%m/%Y %H:%M'),
                'comentario': h.comentario,
                'ubicacion': h.ubicacion,
                'responsable': h.usuario_responsable.username if h.usuario_responsable else 'Sistema'
            })
        
        return JsonResponse({
            'success': True,
            'seguimiento': {
                'codigo': seguimiento.codigo_seguimiento,
                'recompensa': seguimiento.recompensa.nombre,
                'estado': seguimiento.get_estado_display(),
                'estado_color': seguimiento.estado_color,
                'porcentaje': seguimiento.porcentaje_progreso,
                'fecha_solicitud': seguimiento.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
                'fecha_estimada': seguimiento.fecha_estimada_entrega.strftime('%d/%m/%Y') if seguimiento.fecha_estimada_entrega else None,
                'direccion': seguimiento.direccion_entrega,
                'telefono': seguimiento.telefono_contacto
            },
            'historial': historial_data
        })
    
    return render(request, 'core/detalle_seguimiento.html', context)

@login_required
@ajax_required_admin
def subir_foto_entrega(request, seguimiento_id):
    """Subir foto de entrega (solo admin/repartidor)"""
    if request.method == 'POST' and request.FILES.get('foto_entrega'):
        try:
            seguimiento = get_object_or_404(SeguimientoRecompensa, id=seguimiento_id)
            seguimiento.foto_entrega = request.FILES['foto_entrega']
            seguimiento.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Foto de entrega subida exitosamente.',
                'foto_url': seguimiento.foto_entrega.url
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al subir foto: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'No se recibió ninguna foto.'})

@login_required
def calificar_servicio(request, seguimiento_id):
    """Calificar el servicio de entrega (solo usuario)"""
    if request.method == 'POST':
        try:
            seguimiento = get_object_or_404(SeguimientoRecompensa, id=seguimiento_id, usuario=request.user)
            
            if seguimiento.estado != 'entregado':
                return JsonResponse({
                    'success': False,
                    'message': 'Solo puedes calificar pedidos entregados.'
                })
            
            calificacion = int(request.POST.get('calificacion', 0))
            if calificacion < 1 or calificacion > 5:
                return JsonResponse({
                    'success': False,
                    'message': 'La calificación debe ser entre 1 y 5 estrellas.'
                })
            
            seguimiento.calificacion_servicio = calificacion
            seguimiento.save()
            
            return JsonResponse({
                'success': True,
                'message': '¡Gracias por tu calificación!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al calificar: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido.'})

@login_required
def notificaciones(request):
    """Vista para mostrar todas las notificaciones del usuario"""
    return render(request, 'core/notificaciones.html')

@login_required
def crear_notificacion_prueba(request):
    """Endpoint para crear una notificación de prueba - solo para debugging"""
    if request.method == 'POST':
        try:
            # Crear una notificación de prueba con timestamp actual
            from django.utils import timezone
            import json
            
            # Leer los datos si es JSON, sino usar valores por defecto
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                titulo = data.get('titulo', 'Notificación de Prueba')
                mensaje = data.get('mensaje', 'Esta es una notificación de prueba generada manualmente.')
                tipo = data.get('tipo', 'sistema')
            else:
                titulo = request.POST.get('titulo', 'Notificación de Prueba')
                mensaje = request.POST.get('mensaje', 'Esta es una notificación de prueba generada manualmente.')
                tipo = request.POST.get('tipo', 'sistema')
            
            notificacion = Notificacion.objects.create(
                usuario=request.user,
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                fecha_creacion=timezone.now(),
                leida=False
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Notificación de prueba creada exitosamente',
                'notification': {
                    'id': notificacion.id,
                    'titulo': notificacion.titulo,
                    'mensaje': notificacion.mensaje,
                    'tipo': notificacion.tipo,
                    'fecha': notificacion.fecha_creacion.isoformat(),
                    'leida': notificacion.leida
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error creando notificación: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido. Use POST.'
    })


def ratelimit_error(request, exception=None):
    """
    Vista personalizada para mostrar error cuando se excede el rate limit
    """
    # Determinar si es una petición AJAX
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
              request.content_type == 'application/json'
    
    if is_ajax:
        return JsonResponse({
            'success': False,
            'error': 'Límite de solicitudes excedido',
            'message': 'Has realizado demasiadas solicitudes en poco tiempo. Por favor, espera un momento e intenta nuevamente.',
            'retry_after': 60,  # segundos
            'type': 'rate_limit'
        }, status=429)
    else:
        context = {
            'error_title': 'Demasiadas Solicitudes',
            'error_message': 'Has excedido el límite de solicitudes permitidas.',
            'retry_message': 'Por favor, espera un momento antes de intentar nuevamente.',
            'retry_seconds': 60
        }
        return render(request, 'core/ratelimit_error.html', context, status=429)