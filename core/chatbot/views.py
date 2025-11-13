"""
Vistas para el chatbot IA de EcoPuntos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
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
            solicitud.estado = 'aceptada'
            solicitud.respuesta_admin = respuesta
            solicitud.save()
            messages.success(request, f'Solicitud de {solicitud.usuario.username} ha sido aceptada exitosamente.')
        elif accion == 'rechazar':
            solicitud.estado = 'rechazada'
            solicitud.respuesta_admin = respuesta
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
        # Aquí puedes registrar la solicitud en la base de datos o enviar una notificación
        messages.success(request, 'La solicitud de soporte humano ha sido enviada.')
        return JsonResponse({'success': True, 'message': 'Solicitud enviada'})

    return JsonResponse({'success': False, 'message': 'Método no permitido'})