from django.views.decorators.csrf import csrf_exempt
from .permissions import require_superuser_ajax
from django.views.decorators.http import require_http_methods
# --- API: Obtener datos de usuario para edición ---
@require_superuser_ajax
@require_http_methods(["GET"])
def obtener_usuario_superuser(request, user_id):
    try:
        user = get_object_or_404(Usuario, id=user_id)
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'suspended': user.suspended,
                'puntos': user.puntos,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# --- API: Editar usuario (nombre, email, rol, estado, suspendido, contraseña opcional) ---
@require_superuser_ajax
@require_http_methods(["POST"])
@csrf_exempt
def editar_usuario_superuser(request, user_id):
    try:
        user = get_object_or_404(Usuario, id=user_id)
        data = json.loads(request.body)
        # No permitir cambiar username
        user.email = data.get('email', user.email)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.role = data.get('role', user.role)
        user.is_active = data.get('is_active', user.is_active)
        user.suspended = data.get('suspended', user.suspended)
        # Actualizar permisos de staff
        user.is_staff = user.role in ['admin', 'superuser']
        # Cambiar contraseña solo si se envía
        password = data.get('password', None)
        if password:
            user.set_password(password)
        user.save()
        return JsonResponse({'success': True, 'message': 'Usuario actualizado correctamente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# --- API: Ajustar puntos del usuario (añadir o quitar) ---
@require_superuser_ajax
@require_http_methods(["POST"])
@csrf_exempt
def ajustar_puntos_usuario(request, user_id):
    try:
        user = get_object_or_404(Usuario, id=user_id)
        data = json.loads(request.body)
        
        action = data.get('action')  # 'add' o 'subtract'
        cantidad = int(data.get('cantidad', 0))
        motivo = data.get('motivo', '')
        
        if cantidad <= 0:
            return JsonResponse({'success': False, 'message': 'La cantidad debe ser mayor a 0'})
        
        puntos_anteriores = user.puntos
        
        if action == 'add':
            user.puntos += cantidad
            mensaje = f'Se añadieron {cantidad} puntos'
        elif action == 'subtract':
            if user.puntos < cantidad:
                return JsonResponse({
                    'success': False, 
                    'message': f'El usuario solo tiene {user.puntos} puntos. No se pueden quitar {cantidad} puntos.'
                })
            user.puntos -= cantidad
            mensaje = f'Se quitaron {cantidad} puntos'
        else:
            return JsonResponse({'success': False, 'message': 'Acción no válida'})
        
        user.save()
        
        # Crear notificación para el usuario
        accion_texto = 'añadido' if action == 'add' else 'quitado'
        notif_mensaje = f'Un administrador ha {accion_texto} {cantidad} puntos a tu cuenta.'
        if motivo:
            notif_mensaje += f' Motivo: {motivo}'
        
        Notificacion.objects.create(
            usuario=user,
            tipo='puntos',
            mensaje=notif_mensaje
        )
        
        # Log de la operación
        print(f"AJUSTE DE PUNTOS - Usuario: {user.username}")
        print(f"  Acción: {action}")
        print(f"  Cantidad: {cantidad}")
        print(f"  Puntos anteriores: {puntos_anteriores}")
        print(f"  Puntos nuevos: {user.puntos}")
        if motivo:
            print(f"  Motivo: {motivo}")
        
        return JsonResponse({
            'success': True, 
            'message': mensaje,
            'puntos_anteriores': puntos_anteriores,
            'puntos_nuevos': user.puntos
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Usuario, Notificacion, SesionUsuario
from .permissions import require_superuser, require_superuser_ajax, is_superuser_role
from .notifications import NotificacionEmail
import json

User = get_user_model()

@require_superuser
def panel_superuser(request):
    """Panel principal del superusuario"""
    # Estadísticas generales
    total_users = Usuario.objects.count()
    total_admins = Usuario.objects.filter(role='admin').count()
    total_superusers = Usuario.objects.filter(role='superuser').count()
    active_users = Usuario.objects.filter(is_active=True).count()
    suspended_users = Usuario.objects.filter(suspended=True).count()
    
    # Usuarios recientes
    recent_users = Usuario.objects.all().order_by('-fecha_registro')[:5]
    
    # Sesiones activas
    active_sessions = SesionUsuario.objects.filter(activa=True).count()
    
    context = {
        'total_users': total_users,
        'total_admins': total_admins,
        'total_superusers': total_superusers,
        'active_users': active_users,
        'suspended_users': suspended_users,
        'recent_users': recent_users,
        'active_sessions': active_sessions,
    }
    
    return render(request, 'core/superuser/panel.html', context)

@require_superuser
def gestion_usuarios_superuser(request):
    """Gestión completa de usuarios por el superusuario"""
    # Filtros
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    users = Usuario.objects.all()
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True, suspended=False)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'suspended':
        users = users.filter(suspended=True)
    
    users = users.order_by('-fecha_registro')
    
    # Paginación
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'total_users': Usuario.objects.count(),
        'roles': Usuario.ROLES,
    }
    
    return render(request, 'core/superuser/gestion_usuarios.html', context)

@require_superuser_ajax
@require_http_methods(["POST"])
def crear_usuario_superuser(request):
    """Crear nuevo usuario desde el panel de superusuario"""
    try:
        data = json.loads(request.body)
        
        # Validar datos requeridos
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'user')
        
        if not all([username, email, password]):
            return JsonResponse({
                'success': False,
                'message': 'Username, email y contraseña son requeridos.'
            })
        
        # Validar longitud de contraseña
        if len(password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'La contraseña debe tener al menos 8 caracteres.'
            })
        
        # Validar rol válido
        valid_roles = [choice[0] for choice in Usuario.ROLES]
        if role not in valid_roles:
            return JsonResponse({
                'success': False,
                'message': f'Rol inválido. Roles válidos: {", ".join(valid_roles)}'
            })
        
        # Verificar que el username no existe
        if Usuario.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': f'El nombre de usuario "{username}" ya existe.'
            })
        
        # Verificar que el email no existe
        if Usuario.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': f'El email "{email}" ya está registrado.'
            })
        
        # Crear usuario
        user = Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            telefono=data.get('telefono', ''),
            role=role,
            is_staff=role in ['admin', 'superuser'],
            is_active=data.get('is_active', True),
            terminos_aceptados=True  # Usuario creado por admin tiene términos aceptados
        )
        
        # Definir permisos iniciales según el rol
        permisos_mensaje = {
            'user': 'Usuario regular con acceso a funciones básicas del sistema.',
            'conductor': 'Conductor con acceso al panel de rutas y recolección.',
            'admin': 'Administrador con permisos de gestión del sistema.',
            'superuser': 'Superusuario con acceso total al sistema.'
        }
        
        # Crear notificación
        Notificacion.objects.create(
            usuario=user,
            titulo='¡Bienvenido a EcoPuntos!',
            mensaje=f'Tu cuenta ha sido creada por el superusuario {request.user.username}. {permisos_mensaje.get(role, "")}',
            tipo='sistema'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {username} creado exitosamente con rol {user.get_role_display()}.',
            'user_id': user.id,
            'user_data': {
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'role_display': user.get_role_display()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al crear usuario: {str(e)}'
        })
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al crear usuario: {str(e)}'
        })

@require_superuser_ajax
@require_http_methods(["POST"])
def eliminar_usuario_superuser(request, user_id):
    """Eliminar usuario completamente (solo superusuario)"""
    try:
        user = get_object_or_404(Usuario, id=user_id)
        
        # No permitir eliminar el último superusuario
        if user.role == 'superuser':
            superuser_count = Usuario.objects.filter(role='superuser').count()
            if superuser_count <= 1:
                return JsonResponse({
                    'success': False,
                    'message': 'No se puede eliminar el último superusuario del sistema.'
                })
        
        # No permitir auto-eliminación
        if user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'No puedes eliminarte a ti mismo.'
            })
        
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {username} eliminado permanentemente.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar usuario: {str(e)}'
        })

@require_superuser_ajax
@require_http_methods(["POST"])
def cambiar_rol_usuario(request, user_id):
    """Cambiar rol de usuario (solo superusuario)"""
    try:
        user = get_object_or_404(Usuario, id=user_id)
        data = json.loads(request.body)
        nuevo_rol = data.get('role')
        
        if nuevo_rol not in [choice[0] for choice in Usuario.ROLES]:
            return JsonResponse({
                'success': False,
                'message': 'Rol inválido.'
            })
        
        # No permitir cambiar el rol del último superusuario
        if user.role == 'superuser' and nuevo_rol != 'superuser':
            superuser_count = Usuario.objects.filter(role='superuser').count()
            if superuser_count <= 1:
                return JsonResponse({
                    'success': False,
                    'message': 'No se puede cambiar el rol del último superusuario.'
                })
        
        # No permitir auto-degradación del último superusuario
        if user == request.user and user.role == 'superuser' and nuevo_rol != 'superuser':
            superuser_count = Usuario.objects.filter(role='superuser').count()
            if superuser_count <= 1:
                return JsonResponse({
                    'success': False,
                    'message': 'No puedes cambiar tu propio rol siendo el último superusuario.'
                })
        
        rol_anterior = user.get_role_display()
        user.role = nuevo_rol
        
        # Actualizar permisos de staff
        user.is_staff = nuevo_rol in ['admin', 'superuser']
        user.save()
        
        # Crear notificación
        Notificacion.objects.create(
            usuario=user,
            titulo='Rol actualizado',
            mensaje=f'Tu rol ha sido cambiado de {rol_anterior} a {user.get_role_display()} por el superusuario {request.user.username}.',
            tipo='sistema'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Rol de {user.username} cambiado exitosamente a {user.get_role_display()}.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar rol: {str(e)}'
        })

@require_superuser
def gestion_admins_superuser(request):
    """Gestión específica de administradores"""
    admins = Usuario.objects.filter(role='admin').order_by('-fecha_registro')
    superusers = Usuario.objects.filter(role='superuser').order_by('-fecha_registro')
    conductores = Usuario.objects.filter(role='conductor', is_active=True).order_by('-fecha_registro')
    
    context = {
        'admins': admins,
        'superusers': superusers,
        'conductores': conductores,
    }
    
    return render(request, 'core/superuser/gestion_admins.html', context)

@require_superuser_ajax
@require_http_methods(["POST"])
def promover_a_admin(request, user_id):
    """Promover usuario regular a administrador"""
    try:
        user = get_object_or_404(Usuario, id=user_id)
        
        if user.role != 'user':
            return JsonResponse({
                'success': False,
                'message': 'Solo se pueden promover usuarios regulares.'
            })
        
        user.role = 'admin'
        user.is_staff = True
        user.save()
        
        # Crear notificación
        Notificacion.objects.create(
            usuario=user,
            titulo='Promovido a Administrador',
            mensaje=f'Has sido promovido a administrador por el superusuario {request.user.username}.',
            tipo='sistema'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {user.username} promovido a administrador exitosamente.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al promover usuario: {str(e)}'
        })

@require_superuser_ajax
@require_http_methods(["POST"])
def degradar_admin(request, user_id):
    """Degradar administrador a usuario regular"""
    try:
        user = get_object_or_404(Usuario, id=user_id)
        
        if user.role != 'admin':
            return JsonResponse({
                'success': False,
                'message': 'Solo se pueden degradar administradores.'
            })
        
        user.role = 'user'
        user.is_staff = False
        user.save()
        
        # Crear notificación
        Notificacion.objects.create(
            usuario=user,
            titulo='Rol actualizado',
            mensaje=f'Tu rol de administrador ha sido removido por el superusuario {request.user.username}.',
            tipo='sistema'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {user.username} degradado a usuario regular exitosamente.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al degradar usuario: {str(e)}'
        })

@require_superuser
def configuracion_sistema_superuser(request):
    """Configuración avanzada del sistema"""
    from .models import Configuracion
    
    if request.method == 'POST':
        # DEBUG: Ver qué se está recibiendo
        print("=" * 50)
        print("DEBUG: Datos recibidos en POST")
        for key, value in request.POST.items():
            if key.startswith('config_'):
                print(f"  {key}: {value}")
        print("=" * 50)
        
        # Lista de checkboxes para manejar correctamente
        checkboxes = ['email_notifications', 'sms_notifications', 'push_notifications']
        
        # Procesar cambios de configuración
        for key, value in request.POST.items():
            if key.startswith('config_'):
                config_name = key.replace('config_', '')
                print(f"Guardando {config_name} = {value}")  # DEBUG
                try:
                    config_obj, created = Configuracion.objects.get_or_create(
                        nombre=config_name,
                        defaults={'valor': value, 'categoria': 'sistema'}
                    )
                    if not created:
                        config_obj.valor = value
                        config_obj.save()
                        print(f"  ✓ Actualizado {config_name} a {value}")  # DEBUG
                    else:
                        print(f"  ✓ Creado {config_name} con valor {value}")  # DEBUG
                except Exception as e:
                    print(f"  ✗ ERROR en {config_name}: {str(e)}")  # DEBUG
                    messages.error(request, f'Error al actualizar {config_name}: {str(e)}')
        
        # Manejar checkboxes no marcados (no se envían en POST)
        for checkbox in checkboxes:
            if f'config_{checkbox}' not in request.POST:
                try:
                    config_obj, created = Configuracion.objects.get_or_create(
                        nombre=checkbox,
                        defaults={'valor': 'false', 'categoria': 'sistema'}
                    )
                    if not created:
                        config_obj.valor = 'false'
                        config_obj.save()
                except Exception as e:
                    messages.error(request, f'Error al actualizar {checkbox}: {str(e)}')
            else:
                # Checkbox marcado, guardar como 'true'
                try:
                    config_obj, created = Configuracion.objects.get_or_create(
                        nombre=checkbox,
                        defaults={'valor': 'true', 'categoria': 'sistema'}
                    )
                    if not created:
                        config_obj.valor = 'true'
                        config_obj.save()
                except Exception as e:
                    messages.error(request, f'Error al actualizar {checkbox}: {str(e)}')
        
        messages.success(request, 'Configuración actualizada exitosamente.')
        return redirect('configuracion_sistema_superuser')
    
    # Obtener configuraciones existentes
    configs = Configuracion.objects.all().order_by('categoria', 'nombre')
    
    # Crear diccionario de configuraciones para fácil acceso en template
    config_dict = {config.nombre: config.valor for config in configs}
    
    # DEBUG: Imprimir valores en consola del servidor
    print("=" * 50)
    print("DEBUG: Valores cargados desde BD")
    for key, value in config_dict.items():
        print(f"  {key}: {value}")
    print("=" * 50)
    
    # Valores por defecto si no existen en BD
    defaults = {
        'admin_session_timeout': '10',
        'user_session_timeout': '15',
        'max_login_attempts': '3',
        'default_points': '100',
        'points_to_cop': '0.50',
        'sender_email': 'noreply@ecopuntos.com',
        'email_notifications': 'true',
        'sms_notifications': 'false',
        'push_notifications': 'true',
    }
    
    # Combinar con valores guardados
    for key, default_value in defaults.items():
        if key not in config_dict:
            config_dict[key] = default_value
    
    context = {
        'configs': configs,
        'config_values': config_dict,
    }
    
    return render(request, 'core/superuser/configuracion_sistema.html', context)
