import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Notificacion, Canje, Usuario
from django.core.serializers import serialize
from django.forms.models import model_to_dict
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer para chat global en tiempo real"""
    
    async def connect(self):
        # Verificar que el usuario esté autenticado
        if self.scope["user"].is_anonymous:
            await self.close()
            return
        
        self.room_group_name = "global_chat"
        
        # Unirse al grupo de chat global
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar mensaje de bienvenida
        await self.send(text_data=json.dumps({
            'type': 'system',
            'message': f'¡Bienvenido al chat, {self.scope["user"].username}!'
        }))

    async def disconnect(self, close_code):
        # Salir del grupo de chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get('message', '').strip()
            
            if not message:
                return
            
            # Enviar mensaje al grupo
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.scope["user"].username
                }
            )
        except json.JSONDecodeError:
            logger.error("Error parsing JSON in ChatConsumer")

    async def chat_message(self, event):
        # Enviar mensaje al WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username']
        }))


class NotificacionConsumer(AsyncWebsocketConsumer):
    """Consumer para notificaciones en tiempo real"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'notificaciones_{self.user_id}'
        
        # Unirse al grupo de notificaciones del usuario
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar notificaciones no leídas al conectarse
        await self.send_unread_notifications()
    
    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Manejar mensajes recibidos del cliente"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'mark_read':
                notification_id = text_data_json.get('notification_id')
                await self.mark_notification_read(notification_id)
            elif message_type == 'mark_all_read':
                await self.mark_all_notifications_read()
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
    
    async def notification_message(self, event):
        """Enviar notificación al WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    @database_sync_to_async
    def get_unread_notifications(self):
        """Obtener notificaciones no leídas del usuario"""
        try:
            user = User.objects.get(id=self.user_id)
            notifications = Notificacion.objects.filter(
                usuario=user, leida=False
            ).order_by('-fecha_creacion')[:10]
            
            return [{
                'id': notif.id,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'tipo': notif.tipo,
                'fecha_creacion': notif.fecha_creacion.isoformat(),
                'leida': notif.leida
            } for notif in notifications]
        except User.DoesNotExist:
            return []
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Marcar notificación como leída"""
        try:
            notification = Notificacion.objects.get(
                id=notification_id, usuario_id=self.user_id
            )
            notification.leida = True
            notification.save()
            return True
        except Notificacion.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        """Marcar todas las notificaciones como leídas"""
        try:
            Notificacion.objects.filter(
                usuario_id=self.user_id, leida=False
            ).update(leida=True)
            return True
        except:
            return False
    
    async def send_unread_notifications(self):
        """Enviar notificaciones no leídas al conectarse"""
        notifications = await self.get_unread_notifications()
        await self.send(text_data=json.dumps({
            'type': 'unread_notifications',
            'notifications': notifications,
            'count': len(notifications)
        }))


class DashboardConsumer(AsyncWebsocketConsumer):
    """Consumer para actualizaciones del dashboard en tiempo real"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'dashboard_{self.user_id}'
        
        # Unirse al grupo del dashboard del usuario
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar datos iniciales del dashboard
        await self.send_dashboard_data()
    
    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Manejar mensajes recibidos del cliente"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'refresh_dashboard':
                await self.send_dashboard_data()
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
    
    async def dashboard_update(self, event):
        """Enviar actualización del dashboard"""
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'data': event['data']
        }))
    
    @database_sync_to_async
    def get_dashboard_data(self):
        """Obtener datos del dashboard del usuario"""
        try:
            user = User.objects.get(id=self.user_id)
            
            # Datos básicos del usuario
            data = {
                'puntos_totales': user.puntos,
                'canjes_totales': Canje.objects.filter(usuario=user).count(),
                'notificaciones_no_leidas': Notificacion.objects.filter(
                    usuario=user, leida=False
                ).count(),
                'ranking_posicion': Usuario.objects.filter(
                    puntos__gt=user.puntos
                ).count() + 1
            }
            
            return data
        except User.DoesNotExist:
            return {}
    
    async def send_dashboard_data(self):
        """Enviar datos del dashboard"""
        data = await self.get_dashboard_data()
        await self.send(text_data=json.dumps({
            'type': 'dashboard_data',
            'data': data
        }))


class CanjeConsumer(AsyncWebsocketConsumer):
    """Consumer para actualizaciones de canjes en tiempo real"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'canjes_{self.user_id}'
        
        # Unirse al grupo de canjes del usuario
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Manejar mensajes recibidos del cliente"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'get_canjes':
                await self.send_user_canjes()
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
    
    async def canje_update(self, event):
        """Enviar actualización de canje"""
        await self.send(text_data=json.dumps({
            'type': 'canje_update',
            'canje': event['canje']
        }))
    
    @database_sync_to_async
    def get_user_canjes(self):
        """Obtener canjes del usuario"""
        try:
            user = User.objects.get(id=self.user_id)
            canjes = Canje.objects.filter(usuario=user).order_by('-fecha')[:10]
            
            return [{
                'id': canje.id,
                'material': canje.material.nombre,
                'cantidad': float(canje.cantidad),
                'puntos_ganados': canje.puntos_ganados,
                'estado': canje.estado,
                'fecha': canje.fecha.isoformat()
            } for canje in canjes]
        except User.DoesNotExist:
            return []
    
    async def send_user_canjes(self):
        """Enviar canjes del usuario"""
        canjes = await self.get_user_canjes()
        await self.send(text_data=json.dumps({
            'type': 'user_canjes',
            'canjes': canjes
        }))


# Funciones auxiliares para enviar mensajes a los grupos
async def send_notification_to_user(user_id, notification_data):
    """Enviar notificación a un usuario específico"""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f'notificaciones_{user_id}',
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )


async def send_dashboard_update_to_user(user_id, dashboard_data):
    """Enviar actualización del dashboard a un usuario específico"""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f'dashboard_{user_id}',
        {
            'type': 'dashboard_update',
            'data': dashboard_data
        }
    )


class CanjeConsumer(AsyncWebsocketConsumer):
    """Consumer para actualizaciones de canjes en tiempo real"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'canjes_{self.user_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        pass  # No necesitamos recibir mensajes por ahora
    
    async def canje_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'canje_update',
            'canje': event['canje']
        }))

async def send_canje_update_to_user(user_id, canje_data):
    """Enviar actualización de canje a un usuario específico"""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f'canjes_{user_id}',
        {
            'type': 'canje_update',
            'canje': canje_data
        }
    )