"""
Servicio simplificado de IA para el chatbot - Version corregida async/sync
"""
import json
import time
import logging
from typing import Dict, Optional
from django.conf import settings
from django.utils import timezone
from openai import AsyncOpenAI
from channels.db import database_sync_to_async
from core.models import ConversacionChatbot, MensajeChatbot, ContextoChatbot

logger = logging.getLogger(__name__)

class SimpleChatbotAIService:
    """Servicio simplificado del chatbot con IA - compatible con async"""
    
    def __init__(self):
        """Inicializa el servicio de IA"""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = getattr(settings, 'AI_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = getattr(settings, 'AI_MAX_TOKENS', 500)
        self.temperature = getattr(settings, 'AI_TEMPERATURE', 0.7)
        
        logger.info(f"SimpleChatbotAIService inicializado con modelo: {self.model}")
    
    async def process_message(self, user_message: str, conversacion: ConversacionChatbot) -> Dict:
        """
        Procesa un mensaje del usuario y genera una respuesta de IA
        """
        start_time = time.time()
        
        try:
            # 1. Guardar mensaje del usuario
            await self._save_user_message(user_message, conversacion)
            
            # 2. Generar respuesta con IA
            ai_response = await self._generate_ai_response(user_message, conversacion)
            
            # 3. Guardar respuesta del bot
            await self._save_bot_message(ai_response, conversacion)
            
            # 4. Actualizar actividad de conversación
            await self._update_conversation_activity(conversacion)
            
            response_time = time.time() - start_time
            logger.info(f"Mensaje procesado en {response_time:.2f}s")
            
            return {
                'message': ai_response,
                'confidence': 0.85,  # Confianza fija por ahora
                'response_time': response_time,
                'escalated': False,
                'type': 'chatbot_message'
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                'message': 'Lo siento, ha ocurrido un error técnico. ¿Te gustaría hablar con un agente humano?',
                'confidence': 0.0,
                'response_time': time.time() - start_time,
                'escalated': True,
                'type': 'error_message'
            }
    
    async def _save_user_message(self, mensaje: str, conversacion: ConversacionChatbot):
        """Guarda el mensaje del usuario en la base de datos"""
        return await database_sync_to_async(MensajeChatbot.objects.create)(
            conversacion=conversacion,
            contenido=mensaje,
            es_usuario=True
        )
    
    async def _save_bot_message(self, mensaje: str, conversacion: ConversacionChatbot):
        """Guarda el mensaje del bot en la base de datos"""
        return await database_sync_to_async(MensajeChatbot.objects.create)(
            conversacion=conversacion,
            contenido=mensaje,
            es_usuario=False,
            confidence_score=0.85
        )
    
    async def _update_conversation_activity(self, conversacion: ConversacionChatbot):
        """Actualiza la última actividad de la conversación"""
        try:
            await database_sync_to_async(
                ConversacionChatbot.objects.filter(id=conversacion.id).update
            )(fecha_actualizacion=timezone.now())
        except Exception as e:
            logger.error(f"Error actualizando actividad de conversación: {str(e)}")
    
    async def _generate_ai_response(self, user_message: str, conversacion: ConversacionChatbot) -> str:
        """Genera respuesta usando OpenAI API"""
        try:
            # Obtener historial de mensajes recientes
            recent_messages = await self._get_recent_messages(conversacion)
            
            # Construir prompt del sistema
            system_prompt = self._get_system_prompt()
            
            # Construir conversación para OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            
            # Agregar mensajes recientes
            for msg in recent_messages[-5:]:  # Últimos 5 mensajes
                role = "user" if msg.es_usuario else "assistant"
                messages.append({"role": role, "content": msg.contenido})
            
            # Agregar mensaje actual
            messages.append({"role": "user", "content": user_message})
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=30
            )
            
            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                return content.strip() if content else self._get_fallback_response(user_message)
            else:
                logger.warning("Respuesta vacía de OpenAI")
                return self._get_fallback_response(user_message)
            
        except Exception as e:
            logger.error(f"Error generando respuesta de IA: {str(e)}")
            return self._get_fallback_response(user_message)
    
    async def _get_recent_messages(self, conversacion: ConversacionChatbot):
        """Obtiene mensajes recientes de la conversación"""
        try:
            def get_messages():
                return list(conversacion.mensajes.order_by('-fecha_creacion')[:10])
            
            return await database_sync_to_async(get_messages)()
        except Exception:
            return []
    
    def _get_system_prompt(self) -> str:
        """Obtiene el prompt del sistema para el chatbot"""
        return """¡Hola! 👋 Soy EcoBot, tu asistente inteligente de EcoPuntos. 

Estoy aquí para ayudarte con:
🎯 Información sobre canjes y materiales
📊 Consultar tus puntos y nivel  
🏆 Logros y recompensas
🚛 Estado de rutas de recolección
❓ Preguntas frecuentes
🎮 Juegos educativos

¿En qué puedo ayudarte hoy?

Responde de manera amigable, concisa y siempre enfocada en EcoPuntos. 
Si no sabes algo específico, ofrece ayuda alternativa o escala a un agente humano."""
    
    def _get_fallback_response(self, user_message: str) -> str:
        """Respuesta de fallback cuando OpenAI falla"""
        fallback_responses = {
            'canjes': '🎯 Para información sobre canjes, puedes acceder a la sección "Mis Puntos" donde encontrarás todas las recompensas disponibles. ¿Te gustaría que te ayude con algo específico sobre canjes?',
            'puntos': '📊 Puedes consultar tus puntos en la sección "Mi Cuenta". También puedes ganar más puntos participando en nuestros juegos educativos. ¿Quieres saber cómo ganar más puntos?',
            'recompensas': '🏆 Las recompensas están disponibles en la sección "Mis Puntos". Tenemos desde productos eco-friendly hasta experiencias sostenibles. ¿Buscas alguna recompensa en particular?',
            'rutas': '🚛 El estado de las rutas de recolección lo puedes ver en la sección "Reciclaje". ¿Necesitas información sobre alguna ruta específica?',
            'juegos': '🎮 Tenemos juegos educativos sobre reciclaje de plásticos, vidrios, papel y metales. ¿Te gustaría jugar alguno?'
        }
        
        user_lower = user_message.lower()
        
        for keyword, response in fallback_responses.items():
            if keyword in user_lower:
                return response
        
        return "¡Hola! Soy EcoBot, tu asistente de EcoPuntos. Estoy aquí para ayudarte con información sobre canjes, puntos, recompensas y más. ¿En qué puedo ayudarte? 😊"

# Instancia global
simple_chatbot_service = SimpleChatbotAIService()