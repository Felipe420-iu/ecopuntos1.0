import json
import random
import string
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Configuración de Supabase
SUPABASE_URL = getattr(settings, 'SUPABASE_URL', '')
SUPABASE_KEY = getattr(settings, 'SUPABASE_ANON_KEY', '')

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    logger.warning("Supabase no está configurado correctamente")

def generate_verification_code():
    """Genera un código de verificación de 6 dígitos"""
    return ''.join(random.choices(string.digits, k=6))

def generate_token():
    """Genera un token único para la sesión de recuperación"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

@csrf_exempt
@require_http_methods(["POST"])
def send_verification_code(request):
    """Envía código de verificación por email"""
    print("=== INICIANDO SEND_VERIFICATION_CODE ===")
    
    try:
        # Decodificar datos del request
        try:
            body_unicode = request.body.decode('utf-8')
            data = json.loads(body_unicode)
            print(f"Datos recibidos: {data}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"Error decodificando JSON: {str(e)}")
            return JsonResponse({
                'error': 'Datos JSON inválidos',
                'detail': str(e)
            }, status=400)
        
        email = data.get('email', '').strip().lower()
        print(f"Email procesado: {email}")
        
        if not email:
            print("Email vacío")
            return JsonResponse({'error': 'Email es requerido'}, status=400)
        
        # Verificar si el usuario existe
        try:
            user = User.objects.get(email=email)
            print(f"Usuario encontrado: {user.username}")
        except User.DoesNotExist:
            print(f"Usuario no encontrado para email: {email}")
            return JsonResponse({'error': 'No existe una cuenta con este correo electrónico'}, status=404)
        except Exception as e:
            print(f"Error buscando usuario: {str(e)}")
            return JsonResponse({'error': 'Error al buscar usuario'}, status=500)
        
        # Generar código y token
        verification_code = generate_verification_code()
        session_token = generate_token()
        
        print(f"Código generado: {verification_code}")
        print(f"Token generado: {session_token}")
        
        # Guardar en cache
        cache_key = f"password_recovery_{session_token}"
        cache_data = {
            'email': email,
            'code': verification_code,
            'created_at': datetime.now().isoformat(),
            'attempts': 0
        }
        
        try:
            cache.set(cache_key, cache_data, 600)  # 10 minutos
            print(f"Datos guardados en cache con clave: {cache_key}")
        except Exception as e:
            print(f"Error guardando en cache: {str(e)}")
            return JsonResponse({'error': 'Error interno del sistema'}, status=500)
        
        # Enviar email
        try:
            print("=== ENVIANDO EMAIL ===")
            subject = 'Código de Recuperación de Contraseña - EcoPuntos'
            message = f"""
Hola {user.first_name or 'Usuario'},

Has solicitado restablecer tu contraseña en EcoPuntos.

Tu código de verificación es: {verification_code}

Este código expirará en 10 minutos.

Si no solicitaste este cambio, puedes ignorar este mensaje.

Saludos,
Equipo EcoPuntos
            """
            
            print(f"Enviando correo a: {email}")
            print(f"Código: {verification_code}")
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            print("✅ Email enviado exitosamente")
            
            return JsonResponse({
                'success': True,
                'message': 'Código enviado exitosamente',
                'token': session_token
            })
            
        except Exception as e:
            print(f"❌ Error enviando email: {str(e)}")
            return JsonResponse({'error': 'Error al enviar el correo electrónico'}, status=500)
            
    except Exception as e:
        print(f"❌ Error general en send_verification_code: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def verify_code(request):
    """Verifica el código de verificación"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        token = data.get('token', '').strip()
        
        if not all([email, code, token]):
            return JsonResponse({'error': 'Email, código y token son requeridos'}, status=400)
        
        # Verificar datos en cache
        cache_key = f"password_recovery_{token}"
        cache_data = cache.get(cache_key)
        
        if not cache_data:
            return JsonResponse({'error': 'Sesión expirada. Solicita un nuevo código'}, status=400)
        
        # Verificar email
        if cache_data['email'] != email:
            return JsonResponse({'error': 'Datos inválidos'}, status=400)
        
        # Verificar intentos
        if cache_data['attempts'] >= 3:
            cache.delete(cache_key)
            return JsonResponse({'error': 'Demasiados intentos. Solicita un nuevo código'}, status=400)
        
        # Verificar código
        if cache_data['code'] != code:
            cache_data['attempts'] += 1
            cache.set(cache_key, cache_data, 600)
            return JsonResponse({'error': f'Código incorrecto. Intentos restantes: {3 - cache_data["attempts"]}'}, status=400)
        
        # Código correcto - generar token de reset
        reset_token = generate_token()
        reset_cache_key = f"password_reset_{reset_token}"
        reset_data = {
            'email': email,
            'verified': True,
            'created_at': datetime.now().isoformat()
        }
        cache.set(reset_cache_key, reset_data, 900)  # 15 minutos
        
        # Limpiar cache de verificación
        cache.delete(cache_key)
        
        logger.info(f"Código verificado correctamente para {email}")
        
        return JsonResponse({
            'success': True,
            'message': 'Código verificado correctamente',
            'reset_token': reset_token
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error en verify_code: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def reset_password(request):
    """Cambia la contraseña del usuario"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        token = data.get('token', '').strip()
        
        if not all([email, password, token]):
            return JsonResponse({'error': 'Email, contraseña y token son requeridos'}, status=400)
        
        if len(password) < 8:
            return JsonResponse({'error': 'La contraseña debe tener al menos 8 caracteres'}, status=400)
        
        # Verificar token de reset
        cache_key = f"password_reset_{token}"
        cache_data = cache.get(cache_key)
        
        if not cache_data:
            return JsonResponse({'error': 'Token expirado o inválido'}, status=400)
        
        if cache_data['email'] != email or not cache_data.get('verified'):
            return JsonResponse({'error': 'Datos inválidos'}, status=400)
        
        # Actualizar contraseña en Django
        try:
            user = User.objects.get(email=email)
            user.password = make_password(password)
            user.save()
            
            logger.info(f"Contraseña actualizada en Django para {email}")
            
        except User.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        # Actualizar contraseña en Supabase si está configurado
        if supabase:
            try:
                # Buscar usuario en Supabase
                supabase_response = supabase.table('auth.users').select('*').eq('email', email).execute()
                
                if supabase_response.data:
                    # Actualizar contraseña en Supabase
                    supabase.auth.admin.update_user_by_id(
                        supabase_response.data[0]['id'],
                        {'password': password}
                    )
                    logger.info(f"Contraseña actualizada en Supabase para {email}")
                    
            except Exception as e:
                logger.warning(f"Error actualizando contraseña en Supabase: {str(e)}")
                # No fallar si Supabase falla, Django ya se actualizó
        
        # Limpiar cache
        cache.delete(cache_key)
        
        logger.info(f"Contraseña restablecida exitosamente para {email}")
        
        return JsonResponse({
            'success': True,
            'message': 'Contraseña cambiada exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Datos JSON inválidos'}, status=400)
    except Exception as e:
        logger.error(f"Error en reset_password: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_email_exists(request):
    """Verifica si un email existe en el sistema"""
    try:
        email = request.GET.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({'error': 'Email es requerido'}, status=400)
        
        exists = User.objects.filter(email=email).exists()
        
        return JsonResponse({
            'exists': exists
        })
        
    except Exception as e:
        logger.error(f"Error en check_email_exists: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)