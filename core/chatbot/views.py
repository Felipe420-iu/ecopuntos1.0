"""
Vistas para el chatbot IA de EcoPuntos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg
from django.conf import settings

from core.models import ConversacionChatbot, MensajeChatbot, ContextoChatbot, EstadisticasChatbot, Usuario, SolicitudSoporte
from core.ratelimit import smart_ratelimit
from core.views import is_admin

@login_required
@smart_ratelimit(key='user', rate='60/m', method='GET')
def chatbot_view(request):
    """Vista principal del chatbot para usuarios"""
    # Verificar si el chatbot está habilitado
    if not getattr(settings, 'CHATBOT_ENABLED', True):
        messages.warning(request, 'El chatbot no está disponible en este momento.')
        return redirect('dashusuario')  # Redirigir al dashboard
    
    # Verificar si hay una clave de API de Gemini configurada
    if not getattr(settings, 'GOOGLE_API_KEY', ''):
        messages.error(request, 'El servicio de chatbot no está configurado correctamente.')
        return redirect('dashusuario')
    
    # Obtener conversaciones recientes del usuario
    conversaciones_recientes = ConversacionChatbot.objects.filter(
        usuario=request.user
    ).order_by('-fecha_inicio')[:5]
    
    context = {
        'user': request.user,
        'conversaciones_recientes': conversaciones_recientes,
        'chatbot_enabled': True
    }
    
    return render(request, 'core/chatbot_interface.html', context)

@login_required
def historial_conversaciones(request):
    """Vista del historial de conversaciones del usuario"""
    conversaciones = ConversacionChatbot.objects.filter(
        usuario=request.user
    ).order_by('-fecha_inicio')
    
    context = {
        'conversaciones': conversaciones
    }
    
    return render(request, 'core/historial_chatbot.html', context)

@login_required
def ver_conversacion(request, conversacion_id):
    """Vista para ver una conversación específica"""
    conversacion = get_object_or_404(
        ConversacionChatbot, 
        id=conversacion_id, 
        usuario=request.user
    )
    
    mensajes = conversacion.mensajes.order_by('timestamp')
    
    context = {
        'conversacion': conversacion,
        'mensajes': mensajes
    }
    
    return render(request, 'core/ver_conversacion_chatbot.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.role == 'admin')
def admin_chatbot_stats(request):
    """Vista de estadísticas del chatbot para administradores"""
    # Estadísticas generales
    total_conversaciones = ConversacionChatbot.objects.count()
    conversaciones_activas = ConversacionChatbot.objects.filter(estado='activa').count()
    conversaciones_escaladas = ConversacionChatbot.objects.filter(escalado_a_humano=True).count()
    
    # Estadísticas de hoy
    hoy = timezone.now().date()
    conversaciones_hoy = ConversacionChatbot.objects.filter(fecha_inicio__date=hoy).count()
    mensajes_hoy = MensajeChatbot.objects.filter(timestamp__date=hoy).count()
    
    # Promedio de confianza
    promedio_confianza = MensajeChatbot.objects.filter(
        es_usuario=False,
        confidence_score__isnull=False
    ).aggregate(avg_confidence=Avg('confidence_score'))['avg_confidence'] or 0
    
    # Usuarios más activos
    usuarios_activos = Usuario.objects.annotate(
        total_conversaciones=Count('conversaciones_chatbot')
    ).filter(total_conversaciones__gt=0).order_by('-total_conversaciones')[:10]
    
    # Temas más frecuentes (simplificado)
    intents_frecuentes = MensajeChatbot.objects.filter(
        es_usuario=False,
        intent_detected__isnull=False
    ).exclude(intent_detected='').values('intent_detected').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'total_conversaciones': total_conversaciones,
        'conversaciones_activas': conversaciones_activas,
        'conversaciones_escaladas': conversaciones_escaladas,
        'conversaciones_hoy': conversaciones_hoy,
        'mensajes_hoy': mensajes_hoy,
        'promedio_confianza': round(promedio_confianza * 100, 1),
        'porcentaje_escalamiento': round((conversaciones_escaladas / max(total_conversaciones, 1)) * 100, 1),
        'usuarios_activos': usuarios_activos,
        'intents_frecuentes': intents_frecuentes,
        'chatbot_enabled': getattr(settings, 'CHATBOT_ENABLED', True),
        'api_key_configured': bool(getattr(settings, 'GOOGLE_API_KEY', ''))
    }
    
    return render(request, 'core/admin/chatbot_stats.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff or u.role == 'admin')
def admin_conversaciones(request):
    """Vista de todas las conversaciones para administradores"""
    conversaciones = ConversacionChatbot.objects.select_related('usuario').order_by('-fecha_inicio')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        conversaciones = conversaciones.filter(estado=estado_filtro)
    
    escaladas_filtro = request.GET.get('escaladas', '')
    if escaladas_filtro == 'si':
        conversaciones = conversaciones.filter(escalado_a_humano=True)
    elif escaladas_filtro == 'no':
        conversaciones = conversaciones.filter(escalado_a_humano=False)
    
    context = {
        'conversaciones': conversaciones[:50],  # Limitar a 50 para rendimiento
        'estados': ConversacionChatbot.ESTADOS,
        'filtros': {
            'estado': estado_filtro,
            'escaladas': escaladas_filtro
        }
    }
    
    return render(request, 'core/admin/conversaciones_chatbot.html', context)

@login_required
@user_passes_test(is_admin)
def listar_solicitudes_soporte(request):
    """Vista para listar las solicitudes de soporte humano"""
    solicitudes = SolicitudSoporte.objects.all().order_by('-fecha_creacion')
    
    # Calcular estadísticas
    solicitudes_pendientes = solicitudes.filter(estado='pendiente').count()
    solicitudes_aceptadas = solicitudes.filter(estado='aceptada').count()
    solicitudes_rechazadas = solicitudes.filter(estado='rechazada').count()
    
    context = {
        'solicitudes': solicitudes,
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_aceptadas': solicitudes_aceptadas,
        'solicitudes_rechazadas': solicitudes_rechazadas,
    }
    
    return render(request, 'core/chatbot/listar_solicitudes.html', context)

@login_required
@user_passes_test(is_admin)
def gestionar_solicitud(request, solicitud_id):
    """Vista para aceptar o rechazar una solicitud de soporte humano"""
    solicitud = get_object_or_404(SolicitudSoporte, id=solicitud_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        respuesta = request.POST.get('respuesta', '')
        
        if accion == 'aceptar':
            from core.models import ConversacionDirecta
            import uuid
            
            # Actualizar solicitud
            solicitud.estado = 'en_chat'
            solicitud.admin_asignado = request.user
            solicitud.save()
            
            # Crear conversación directa
            try:
                conversacion = ConversacionDirecta.objects.create(
                    solicitud_soporte=solicitud,
                    usuario=solicitud.usuario,
                    admin=request.user,
                    session_id=f"chat_direct_{uuid.uuid4().hex[:8]}"
                )
                
                messages.success(request, f'¡Chat iniciado con {solicitud.usuario.username}!')
                return redirect('chat_directo', conversation_id=conversacion.id)
                
            except Exception as e:
                messages.error(request, f'Error iniciando chat: {e}')
                return redirect('listar_solicitudes_soporte')
                
        elif accion == 'rechazar':
            solicitud.estado = 'rechazada'
            solicitud.save()
            messages.warning(request, f'Solicitud de {solicitud.usuario.username} ha sido rechazada.')
            
        return redirect('listar_solicitudes_soporte')

    return render(request, 'core/chatbot/gestionar_solicitud.html', {'solicitud': solicitud})

@login_required
@user_passes_test(lambda u: u.is_staff or u.role == 'admin')
def toggle_chatbot(request):
    """API para habilitar/deshabilitar el chatbot"""
    if request.method == 'POST':
        # En un entorno real, esto se haría modificando configuraciones de base de datos
        # Por ahora solo retornamos el estado actual
        enabled = getattr(settings, 'CHATBOT_ENABLED', True)
        
        return JsonResponse({
            'success': True,
            'enabled': enabled,
            'message': f'Chatbot {"habilitado" if enabled else "deshabilitado"}'
        })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def check_chatbot_status(request):
    """API para verificar el estado del chatbot"""
    return JsonResponse({
        'enabled': getattr(settings, 'CHATBOT_ENABLED', True),
        'api_configured': bool(getattr(settings, 'GOOGLE_API_KEY', '')),
        'user_has_conversaciones': ConversacionChatbot.objects.filter(
            usuario=request.user
        ).exists()
    })

@login_required
@smart_ratelimit(key='user', rate='60/m', method='GET')
def chatbot_soporte(request):
    """Vista del soporte del chatbot - redirige a administradores a las solicitudes"""
    # Si es administrador, redirigir a la gestión de solicitudes
    if is_admin(request.user):
        return redirect('listar_solicitudes_soporte')
    
    # Si es usuario normal, mostrar el chatbot de soporte
    return render(request, 'core/chatbot/chatbot_soporte.html')

@login_required
@smart_ratelimit(key='user', rate='60/m', method='POST')
def escalar_a_humano(request):
    """Escala la solicitud de soporte a un humano"""
    if request.method == 'POST':
        # Crear solicitud de soporte
        from core.models import SolicitudSoporte
        
        # Verificar si ya existe una solicitud pendiente o en chat
        solicitud_existente = SolicitudSoporte.objects.filter(
            usuario=request.user,
            estado__in=['pendiente', 'en_chat']
        ).first()
        
        if solicitud_existente:
            if solicitud_existente.estado == 'en_chat':
                # Ya hay un chat activo, devolver ID de conversación
                if hasattr(solicitud_existente, 'conversacion_directa'):
                    return JsonResponse({
                        'success': True,
                        'message': 'Chat directo ya activo',
                        'chat_activo': True,
                        'conversation_id': solicitud_existente.conversacion_directa.id
                    })
            return JsonResponse({
                'success': True,
                'message': 'Solicitud ya enviada, esperando respuesta del administrador',
                'pendiente': True
            })
        
        # Crear nueva solicitud
        mensaje_contexto = request.POST.get('mensaje', 'Solicitud de chat directo desde el chatbot')
        
        solicitud = SolicitudSoporte.objects.create(
            usuario=request.user,
            mensaje=mensaje_contexto,
            estado='pendiente'
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Solicitud enviada al equipo de soporte',
            'solicitud_id': solicitud.id
        })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
@require_http_methods(["GET"])
def verificar_chat_directo(request):
    """Verifica si el usuario tiene un chat directo activo"""
    from core.models import SolicitudSoporte
    
    try:
        # Buscar solicitud en chat activo
        solicitud = SolicitudSoporte.objects.filter(
            usuario=request.user,
            estado='en_chat'
        ).first()
        
        if solicitud and hasattr(solicitud, 'conversacion_directa'):
            conversacion = solicitud.conversacion_directa
            # Verificar que la conversación también esté activa
            if conversacion.estado == 'activa':
                return JsonResponse({
                    'chat_activo': True,
                    'conversation_id': conversacion.id,
                    'admin_nombre': conversacion.admin.get_full_name() or conversacion.admin.username,
                    'fecha_inicio': conversacion.fecha_inicio.strftime('%d/%m/%Y %H:%M')
                })
        
        # Buscar solicitud pendiente
        solicitud_pendiente = SolicitudSoporte.objects.filter(
            usuario=request.user,
            estado='pendiente'
        ).first()
        
        if solicitud_pendiente:
            return JsonResponse({
                'chat_activo': False,
                'pendiente': True,
                'mensaje': 'Esperando que un administrador acepte tu solicitud'
            })
        
        return JsonResponse({
            'chat_activo': False,
            'pendiente': False
        })
        
    except Exception as e:
        print(f"Error en verificar_chat_directo: {e}")
        return JsonResponse({
            'chat_activo': False,
            'pendiente': False,
            'error': str(e)
        })

@login_required
@require_http_methods(["POST"])
def enviar_mensaje_usuario_a_chat(request):
    """API para que el usuario envíe mensajes al chat directo desde el chatbot"""
    from core.models import SolicitudSoporte, MensajeDirecto
    from django.utils import timezone
    
    try:
        # Verificar si tiene chat activo
        solicitud = SolicitudSoporte.objects.filter(
            usuario=request.user,
            estado='en_chat'
        ).first()
        
        if not solicitud or not hasattr(solicitud, 'conversacion_directa'):
            return JsonResponse({'error': 'No tienes un chat directo activo'}, status=400)
        
        conversacion = solicitud.conversacion_directa
        
        # Verificar que la conversación esté activa
        if conversacion.estado != 'activa':
            return JsonResponse({'error': 'La conversación no está activa'}, status=400)
        
        mensaje_texto = request.POST.get('mensaje', '').strip()
        
        if not mensaje_texto:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
        
        # Crear mensaje
        mensaje = MensajeDirecto.objects.create(
            conversacion=conversacion,
            autor=request.user,
            contenido=mensaje_texto
        )
        
        # Actualizar última actividad
        conversacion.fecha_ultima_actividad = timezone.now()
        conversacion.save()
        
        return JsonResponse({
            'success': True,
            'mensaje_id': mensaje.id,
            'timestamp': mensaje.timestamp.strftime('%H:%M')
        })
        
    except Exception as e:
        print(f"Error en enviar_mensaje_usuario_a_chat: {e}")
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

@login_required
@require_http_methods(["GET"])
def obtener_mensajes_chat_directo(request):
    """API para obtener mensajes del chat directo del usuario"""
    from core.models import SolicitudSoporte, MensajeDirecto
    
    try:
        # Verificar si tiene chat activo
        solicitud = SolicitudSoporte.objects.filter(
            usuario=request.user,
            estado='en_chat'
        ).first()
        
        if not solicitud or not hasattr(solicitud, 'conversacion_directa'):
            return JsonResponse({'mensajes': [], 'error': 'No hay chat activo'})
        
        conversacion = solicitud.conversacion_directa
        
        # Verificar que la conversación esté activa
        if conversacion.estado != 'activa':
            return JsonResponse({'mensajes': [], 'error': 'Conversación no activa'})
        
        # Obtener mensajes
        mensajes = MensajeDirecto.objects.filter(
            conversacion=conversacion
        ).order_by('timestamp')
        
        # Marcar como leídos los mensajes del admin
        MensajeDirecto.objects.filter(
            conversacion=conversacion,
            leido=False,
            autor=conversacion.admin
        ).update(leido=True)
        
        mensajes_data = []
        for mensaje in mensajes:
            mensajes_data.append({
                'id': mensaje.id,
                'autor': 'admin' if mensaje.autor == conversacion.admin else 'usuario',
                'nombre': mensaje.autor.get_full_name() or mensaje.autor.username,
                'contenido': mensaje.contenido,
                'timestamp': mensaje.timestamp.strftime('%H:%M'),
                'fecha': mensaje.timestamp.strftime('%d/%m/%Y'),
                'es_admin': mensaje.autor == conversacion.admin
            })
        
        return JsonResponse({
            'mensajes': mensajes_data,
            'admin_nombre': conversacion.admin.get_full_name() or conversacion.admin.username
        })
        
    except Exception as e:
        print(f"Error en obtener_mensajes_chat_directo: {e}")
        return JsonResponse({'mensajes': [], 'error': str(e)})

# ====================================
# VISTAS PARA CHAT DIRECTO USUARIO-ADMIN
# ====================================

@login_required
def chat_directo(request, conversation_id):
    """Vista principal del chat directo entre usuario y administrador"""
    from core.models import ConversacionDirecta, MensajeDirecto
    
    # Obtener la conversación
    conversacion = get_object_or_404(ConversacionDirecta, id=conversation_id)
    
    # Verificar permisos: solo el usuario, el admin asignado o superuser pueden acceder
    if not (request.user == conversacion.usuario or 
            request.user == conversacion.admin or 
            request.user.is_superuser):
        messages.error(request, 'No tienes permisos para acceder a esta conversación.')
        return redirect('/')
    
    # Marcar mensajes como leídos si no son del usuario actual
    MensajeDirecto.objects.filter(
        conversacion=conversacion,
        leido=False
    ).exclude(autor=request.user).update(leido=True)
    
    # Obtener mensajes
    mensajes = MensajeDirecto.objects.filter(conversacion=conversacion).order_by('timestamp')
    
    context = {
        'conversacion': conversacion,
        'mensajes': mensajes,
        'es_admin': request.user == conversacion.admin or request.user.is_superuser,
        'es_usuario': request.user == conversacion.usuario,
    }
    
    return render(request, 'core/chatbot/chat_directo.html', context)

@login_required
@require_POST
def enviar_mensaje_directo(request, conversation_id):
    """API para enviar mensajes en chat directo"""
    from core.models import ConversacionDirecta, MensajeDirecto
    from django.utils import timezone
    
    try:
        conversacion = get_object_or_404(ConversacionDirecta, id=conversation_id)
        
        # Verificar permisos
        if not (request.user == conversacion.usuario or 
                request.user == conversacion.admin or 
                request.user.is_superuser):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        # Verificar que la conversación esté activa
        if conversacion.estado != 'activa':
            return JsonResponse({'error': 'Conversación no activa'}, status=400)
        
        contenido = request.POST.get('mensaje', '').strip()
        if not contenido:
            return JsonResponse({'error': 'Mensaje vacío'}, status=400)
        
        # Crear mensaje
        mensaje = MensajeDirecto.objects.create(
            conversacion=conversacion,
            autor=request.user,
            contenido=contenido
        )
        
        # Actualizar última actividad
        conversacion.fecha_ultima_actividad = timezone.now()
        conversacion.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': {
                'id': mensaje.id,
                'autor': mensaje.autor.get_full_name() or mensaje.autor.username,
                'contenido': mensaje.contenido,
                'timestamp': mensaje.timestamp.strftime('%H:%M'),
                'es_admin': mensaje.es_admin
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def finalizar_chat_directo(request, conversation_id):
    """API para finalizar una conversación directa"""
    from core.models import ConversacionDirecta
    
    try:
        conversacion = get_object_or_404(ConversacionDirecta, id=conversation_id)
        
        # Solo admin o superuser pueden finalizar
        if not (request.user == conversacion.admin or request.user.is_superuser):
            return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        # Finalizar conversación
        conversacion.finalizar()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def listar_conversaciones_activas(request):
    """Vista para listar conversaciones activas (solo admins)"""
    from core.models import ConversacionDirecta
    from django.db.models import Count
    
    if not is_admin(request.user):
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('/')
    
    conversaciones_activas = ConversacionDirecta.objects.filter(
        estado='activa'
    ).select_related('usuario', 'admin', 'solicitud_soporte').annotate(
        num_mensajes=Count('mensajes')
    ).order_by('-fecha_ultima_actividad')
    
    context = {
        'conversaciones': conversaciones_activas,
        'total_activas': conversaciones_activas.count(),
    }
    
    return render(request, 'core/chatbot/conversaciones_activas.html', context)