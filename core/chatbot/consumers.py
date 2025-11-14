"""
WebSocket Consumer para el chatbot IA de EcoPuntos
Maneja la comunicación en tiempo real entre el usuario y el chatbot
"""
import json
import uuid
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from core.models import ConversacionChatbot, MensajeChatbot, ContextoChatbot
from .services import get_ai_service

User = get_user_model()
logger = logging.getLogger(__name__)

class ChatbotConsumer(AsyncWebsocketConsumer):
    """Consumer para el chatbot IA en tiempo real"""
    
    async def connect(self):
        """Maneja la conexión WebSocket"""
        logger.info(f"=== INTENTO DE CONEXIÓN WEBSOCKET ===")
        logger.info(f"Usuario: {self.scope.get('user', 'No disponible')}")
        logger.info(f"Path: {self.scope.get('path', 'No disponible')}")
        
        # Verificar autenticación
        if self.scope["user"].is_anonymous:
            logger.warning("❌ Usuario anónimo intentó conectar al chatbot")
            await self.close(code=4001)
            return
        
        logger.info(f"✅ Usuario autenticado: {self.scope['user'].username}")
        
        # Verificar si el chatbot está habilitado
        if not getattr(settings, 'CHATBOT_ENABLED', True):
            await self.send(text_data=json.dumps({
                'type': 'system_message',
                'message': 'El chatbot no está disponible en este momento. Por favor, intenta más tarde.'
            }))
            await self.close()
            return
        
        self.user = self.scope["user"]
        # Usar directamente el ID del usuario autenticado
        self.user_id = str(self.user.id)
        self.room_group_name = f'chatbot_{self.user_id}'
        
        # Unirse al grupo personal del usuario
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Inicializar o recuperar conversación
        self.conversacion = await self._get_or_create_conversation()
        
        # Enviar mensaje de bienvenida
        await self._send_welcome_message()
        
        logger.info(f"Usuario {self.user.username} conectado al chatbot. Conversación: {self.conversacion.session_id}")
    
    async def disconnect(self, close_code):
        """Maneja la desconexión WebSocket"""
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Actualizar última actividad de la conversación
        if hasattr(self, 'conversacion'):
            await self._update_conversation_activity()
        
        logger.info(f"Usuario {self.user.username if hasattr(self, 'user') else 'Unknown'} desconectado del chatbot")
    
    async def receive(self, text_data):
        """Procesa mensajes recibidos del cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Aceptar tanto 'chat_message' como 'user_message'
            if message_type in ['chat_message', 'user_message']:
                await self._handle_chat_message(data)
            elif message_type == 'human_support_message':
                await self._handle_human_support_message(data)
            elif message_type == 'request_human_support':
                await self._handle_human_request(data)
            elif message_type == 'typing_indicator':
                await self._handle_typing_indicator(data)
            elif message_type == 'request_human':
                await self._handle_human_request(data)
            elif message_type == 'end_conversation':
                await self._handle_end_conversation(data)
            else:
                logger.warning(f"Tipo de mensaje desconocido: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Error al decodificar JSON del mensaje")
            await self._send_error_message("Formato de mensaje inválido")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            await self._send_error_message("Error interno del servidor")
    
    async def _handle_chat_message(self, data):
        """Maneja mensajes de chat del usuario"""
        message = data.get('message', '').strip()
        
        if not message:
            return
        
        # Verificar límite de caracteres
        if len(message) > 1000:
            await self._send_error_message("El mensaje es demasiado largo. Máximo 1000 caracteres.")
            return
        
        # Verificar rate limiting básico
        if not await self._check_rate_limit():
            await self._send_error_message("Estás enviando mensajes muy rápido. Por favor, espera un momento.")
            return
        
        # Enviar indicador de que el bot está procesando
        await self._send_typing_indicator(True)
        
        try:
            logger.info(f"🎯 Procesando mensaje del usuario {self.user.username}: {message[:50]}...")
            
            # Obtener servicio de IA (Gemini)
            logger.info("📡 Obteniendo servicio de IA...")
            service = get_ai_service()
            logger.info("✅ Servicio de IA obtenido correctamente")
            
            # Procesar mensaje con IA
            logger.info(f"🤖 Enviando mensaje al modelo Gemini...")
            respuesta, confidence = await service.process_message(
                user=self.scope["user"],
                mensaje=message,
                conversacion_id=self.conversacion.id,
                include_history=True
            )
            logger.info(f"✅ Respuesta recibida del modelo. Confidence: {confidence}")
            logger.info(f"📝 Respuesta (primeros 100 chars): {respuesta[:100]}...")
            
            # Preparar datos de respuesta
            response_data = {
                'response': respuesta,  # Cambiado de 'respuesta' a 'response'
                'confidence': confidence
            }
            
            # Enviar respuesta al usuario
            logger.info("📤 Enviando respuesta al usuario...")
            await self._send_bot_response(response_data)
            logger.info("✅ Respuesta enviada al usuario correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje con IA: {str(e)}")
            import traceback
            logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
            await self._send_error_message("Lo siento, ha ocurrido un error. ¿Te gustaría hablar con un agente humano?")
        finally:
            # Quitar indicador de escritura
            await self._send_typing_indicator(False)
    
    async def _handle_typing_indicator(self, data):
        """Maneja indicadores de escritura"""
        # Por ahora no implementado - podría usarse para analytics
        pass
    
    
    async def _handle_human_support_message(self, data):
        """Maneja mensajes cuando hay soporte humano activo"""
        message = data.get('message', '').strip()
        
        if not message:
            return
        
        try:
            # Guardar mensaje del usuario
            await database_sync_to_async(MensajeChatbot.objects.create)(
                conversacion=self.conversacion,
                usuario=self.user,
                contenido=message,
                es_de_usuario=True,
                timestamp=timezone.now()
            )
            
            # Enviar confirmación de que el mensaje fue enviado al soporte
            await self.send(text_data=json.dumps({
                'type': 'human_support_confirmation',
                'message': 'Tu mensaje ha sido enviado al equipo de soporte. Te responderemos por email muy pronto. 📧',
                'timestamp': timezone.now().isoformat()
            }))
            
            logger.info(f"Mensaje de soporte humano guardado para usuario {self.user.username}")
            
        except Exception as e:
            logger.error(f"Error procesando mensaje de soporte humano: {str(e)}")
            await self._send_error_message("Error al enviar mensaje al soporte. Por favor intenta de nuevo.")
    
    async def _handle_human_request(self, data):
        """Maneja solicitudes de escalamiento a humano"""
        motivo = data.get('reason', 'Solicitud directa del usuario desde mini chat')
        
        try:
            # Escalar a humano (ahora solo envía email)
            success = await database_sync_to_async(self.conversacion.escalar_a_humano)(motivo)
            
            if success:
                # Enviar confirmación
                await self.send(text_data=json.dumps({
                    'type': 'human_support_confirmation',
                    'message': 'He enviado tu solicitud al equipo de soporte. Te contactaremos por email muy pronto. 📧\n\nAhora puedes escribir mensajes directos al equipo de soporte.',
                    'timestamp': timezone.now().isoformat()
                }))
                
                # Indicar que ahora hay soporte humano conectado
                await self.send(text_data=json.dumps({
                    'type': 'human_connected',
                    'message': 'Conectado con soporte humano',
                    'timestamp': timezone.now().isoformat()
                }))
            else:
                await self._send_error_message("Ya has solicitado soporte anteriormente. Te contactaremos pronto.")
            
        except Exception as e:
            logger.error(f"Error escalando a humano: {str(e)}")
            await self._send_error_message("Error al enviar la solicitud. Por favor, intenta más tarde.")
    
    async def _handle_end_conversation(self, data):
        """Maneja el final de la conversación"""
        try:
            await database_sync_to_async(self.conversacion.finalizar)()
            
            await self.send(text_data=json.dumps({
                'type': 'conversation_ended',
                'message': '¡Gracias por usar EcoPuntos! Que tengas un excelente día. 🌱',
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error finalizando conversación: {str(e)}")
    
    async def _get_or_create_conversation(self) -> ConversacionChatbot:
        """Obtiene o crea una conversación activa para el usuario"""
        try:
            # Buscar conversación activa
            conversacion = await database_sync_to_async(
                ConversacionChatbot.objects.filter(
                    usuario=self.user,
                    estado='activa'
                ).first
            )()
            
            if conversacion:
                return conversacion
            
            # Crear nueva conversación
            session_id = f"chat_{self.user_id}_{uuid.uuid4().hex[:8]}"
            
            conversacion = await database_sync_to_async(
                ConversacionChatbot.objects.create
            )(
                usuario=self.user,
                session_id=session_id,
                estado='activa'
            )
            
            return conversacion
            
        except Exception as e:
            logger.error(f"Error obteniendo/creando conversación: {str(e)}")
            raise
    
    async def _send_welcome_message(self):
        """Envía mensaje de bienvenida al usuario"""
        # Verificar si es la primera conexión de hoy
        is_first_today = await self._is_first_connection_today()
        
        if is_first_today:
            welcome_msg = "¡Hola! 👋 Soy EcoBot, tu asistente inteligente de EcoPuntos. ¿En qué puedo ayudarte hoy?"
        else:
            welcome_msg = "¡Hola de nuevo! ¿En qué puedo ayudarte hoy?"
        
        await self.send(text_data=json.dumps({
            'type': 'bot_message',
            'message': welcome_msg,
            'is_welcome': True,
            'timestamp': timezone.now().isoformat(),
            'confidence': 1.0
        }))
    
    async def _send_bot_response(self, response_data):
        """Envía respuesta del bot al usuario"""
        message_data = {
            'type': 'bot_message',
            'message': response_data['response'],
            'confidence': response_data.get('confidence', 0.0),
            'intent': response_data.get('intent', 'unknown'),
            'escalated': response_data.get('escalated', False),
            'timestamp': timezone.now().isoformat()
        }
        
        # Añadir información adicional si fue escalado
        if response_data.get('escalated'):
            message_data['escalated_info'] = response_data.get('escalated_info')
        
        await self.send(text_data=json.dumps(message_data))
    
    async def _send_error_message(self, error_message):
        """Envía mensaje de error al usuario"""
        await self.send(text_data=json.dumps({
            'type': 'error_message',
            'message': error_message,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def _send_typing_indicator(self, is_typing):
        """Envía indicador de escritura"""
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'is_typing': is_typing,
            'timestamp': timezone.now().isoformat()
        }))
    
    async def _check_rate_limit(self) -> bool:
        """Verifica límites de velocidad de mensajes"""
        # Implementación básica - podría mejorarse con Redis
        if not hasattr(self, '_last_message_time'):
            self._last_message_time = timezone.now()
            return True
        
        time_diff = (timezone.now() - self._last_message_time).total_seconds()
        self._last_message_time = timezone.now()
        
        # Mínimo 1 segundo entre mensajes
        return time_diff >= 1.0
    
    async def _is_first_connection_today(self) -> bool:
        """Verifica si es la primera conexión del usuario hoy"""
        today = timezone.now().date()
        
        count = await database_sync_to_async(
            ConversacionChatbot.objects.filter(
                usuario=self.user,
                fecha_inicio__date=today
            ).count
        )()
        
        return count <= 1
    
    async def _update_conversation_activity(self):
        """Actualiza la última actividad de la conversación"""
        try:
            await database_sync_to_async(
                ConversacionChatbot.objects.filter(
                    id=self.conversacion.id
                ).update
            )(fecha_actualizacion=timezone.now())
        except Exception as e:
            logger.error(f"Error actualizando actividad de conversación: {str(e)}")
    
    # Métodos para recibir mensajes del grupo (para futuras funcionalidades)
    async def chatbot_message(self, event):
        """Recibe mensajes enviados al grupo del chatbot"""
        await self.send(text_data=json.dumps(event['message']))
    
    async def system_notification(self, event):
        """Recibe notificaciones del sistema"""
        await self.send(text_data=json.dumps({
            'type': 'system_notification',
            'message': event['message'],
            'timestamp': timezone.now().isoformat()
        }))