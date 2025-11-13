#!/usr/bin/env python
"""
Script para limpiar estados inconsistentes del chat directo
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto2023.settings')
django.setup()

from core.models import *
from django.utils import timezone

def limpiar_chats_inconsistentes():
    """Limpia estados inconsistentes en el sistema de chat directo"""
    print("🧹 Limpiando estados inconsistentes del chat directo...")
    
    # 1. Buscar solicitudes 'en_chat' sin conversación directa
    solicitudes_huerfanas = SolicitudSoporte.objects.filter(
        estado='en_chat'
    ).exclude(
        conversacion_directa__isnull=False
    )
    
    if solicitudes_huerfanas.exists():
        print(f"   - Encontradas {solicitudes_huerfanas.count()} solicitudes 'en_chat' sin conversación")
        for solicitud in solicitudes_huerfanas:
            print(f"     * Corrigiendo solicitud {solicitud.id} de {solicitud.usuario.username}")
            solicitud.estado = 'pendiente'
            solicitud.save()
    
    # 2. Buscar conversaciones 'activa' pero con solicitud no 'en_chat'
    conversaciones_inconsistentes = ConversacionDirecta.objects.filter(
        estado='activa'
    ).exclude(
        solicitud_soporte__estado='en_chat'
    )
    
    if conversaciones_inconsistentes.exists():
        print(f"   - Encontradas {conversaciones_inconsistentes.count()} conversaciones activas inconsistentes")
        for conversacion in conversaciones_inconsistentes:
            print(f"     * Finalizando conversación {conversacion.id}")
            conversacion.estado = 'finalizada'
            conversacion.fecha_fin = timezone.now()
            conversacion.save()
    
    # 3. Buscar conversaciones finalizadas pero con solicitud aún 'en_chat'
    solicitudes_finalizadas_mal = SolicitudSoporte.objects.filter(
        estado='en_chat',
        conversacion_directa__estado='finalizada'
    )
    
    if solicitudes_finalizadas_mal.exists():
        print(f"   - Encontradas {solicitudes_finalizadas_mal.count()} solicitudes mal finalizadas")
        for solicitud in solicitudes_finalizadas_mal:
            print(f"     * Finalizando solicitud {solicitud.id}")
            solicitud.estado = 'finalizada'
            solicitud.save()
    
    # 4. Mostrar resumen del estado actual
    print("\n📊 Estado actual del sistema:")
    print(f"   - Solicitudes pendientes: {SolicitudSoporte.objects.filter(estado='pendiente').count()}")
    print(f"   - Solicitudes en chat: {SolicitudSoporte.objects.filter(estado='en_chat').count()}")
    print(f"   - Solicitudes finalizadas: {SolicitudSoporte.objects.filter(estado='finalizada').count()}")
    print(f"   - Conversaciones activas: {ConversacionDirecta.objects.filter(estado='activa').count()}")
    print(f"   - Conversaciones finalizadas: {ConversacionDirecta.objects.filter(estado='finalizada').count()}")
    
    # 5. Verificar consistencia
    chats_activos = SolicitudSoporte.objects.filter(estado='en_chat').count()
    conversaciones_activas = ConversacionDirecta.objects.filter(estado='activa').count()
    
    if chats_activos == conversaciones_activas:
        print(f"✅ Sistema consistente: {chats_activos} chats activos")
    else:
        print(f"⚠️  Inconsistencia detectada: {chats_activos} solicitudes en chat vs {conversaciones_activas} conversaciones activas")
    
    print("\n🎉 Limpieza completada!")

if __name__ == "__main__":
    limpiar_chats_inconsistentes()