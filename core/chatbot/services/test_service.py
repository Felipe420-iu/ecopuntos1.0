"""
Servicio de prueba para el chatbot - Respuestas locales sin usar IA
Este servicio es útil para desarrollo y testing sin gastar API calls
"""
import json
import time
import logging
from typing import Dict
from django.utils import timezone
from channels.db import database_sync_to_async
from core.models import ConversacionChatbot, MensajeChatbot

logger = logging.getLogger(__name__)

class TestChatbotService:
    """Servicio de prueba del chatbot - solo respuestas locales"""
    
    def __init__(self):
        logger.info("TestChatbotService inicializado - Solo respuestas locales")
    
    async def process_message(self, user_message: str, conversacion: ConversacionChatbot) -> Dict:
        """Procesa un mensaje y devuelve una respuesta local"""
        start_time = time.time()
        
        try:
            # 1. Guardar mensaje del usuario
            await self._save_user_message(user_message, conversacion)
            
            # 2. Generar respuesta local
            response_message = self._generate_local_response(user_message)
            
            # 3. Guardar respuesta del bot
            await self._save_bot_message(response_message, conversacion)
            
            # 4. Actualizar actividad de conversación
            await self._update_conversation_activity(conversacion)
            
            response_time = time.time() - start_time
            logger.info(f"Mensaje procesado en {response_time:.2f}s")
            
            return {
                'message': response_message,
                'confidence': 0.95,
                'response_time': response_time,
                'escalated': False,
                'type': 'chatbot_message'
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                'message': 'Error procesando tu mensaje. Por favor, inténtalo de nuevo.',
                'confidence': 0.0,
                'response_time': time.time() - start_time,
                'escalated': False,
                'type': 'error_message'
            }
    
    async def _save_user_message(self, mensaje: str, conversacion: ConversacionChatbot):
        """Guarda el mensaje del usuario"""
        return await database_sync_to_async(MensajeChatbot.objects.create)(
            conversacion=conversacion,
            contenido=mensaje,
            es_usuario=True
        )
    
    async def _save_bot_message(self, mensaje: str, conversacion: ConversacionChatbot):
        """Guarda el mensaje del bot"""
        return await database_sync_to_async(MensajeChatbot.objects.create)(
            conversacion=conversacion,
            contenido=mensaje,
            es_usuario=False,
            confidence_score=0.95
        )
    
    async def _update_conversation_activity(self, conversacion: ConversacionChatbot):
        """Actualiza la actividad de la conversación"""
        try:
            await database_sync_to_async(
                ConversacionChatbot.objects.filter(id=conversacion.id).update
            )(fecha_actualizacion=timezone.now())
        except Exception as e:
            logger.error(f"Error actualizando conversación: {str(e)}")
    
    def _generate_local_response(self, user_message: str) -> str:
        """Genera respuesta local basada en palabras clave"""
        message_lower = user_message.lower()
        
        # Respuestas específicas por tema
        if any(word in message_lower for word in ['canjes', 'canje', 'intercambio']):
            return """🎯 **Información sobre Canjes:**

Para canjear tus puntos:
1. Ve a la sección "Mis Puntos"
2. Explora las recompensas disponibles
3. Selecciona la que más te guste
4. Confirma tu canje

Tienes recompensas eco-friendly, experiencias sostenibles y productos verdes. ¿Hay alguna recompensa específica que te interese?"""

        elif any(word in message_lower for word in ['puntos', 'punto', 'puntaje']):
            return """📊 **Información sobre Puntos:**

Puedes ganar puntos de estas formas:
• Reciclando materiales 🗂️
• Jugando nuestros juegos educativos 🎮
• Completando rutas de recolección 🚛
• Participando en actividades eco-friendly 🌱

Tu nivel actual y puntos los puedes ver en "Mi Cuenta". ¿Quieres saber cómo ganar más puntos?"""

        elif any(word in message_lower for word in ['recompensas', 'recompensa', 'premio']):
            return """🏆 **Recompensas Disponibles:**

Nuestras categorías de recompensas:
• Productos eco-friendly 🌿
• Experiencias sostenibles 🌍
• Herramientas de jardín 🌱
• Productos reciclados ♻️
• Vouchers de descuento 🎫

Todas las recompensas están en "Mis Puntos". ¿Buscas algo en particular?"""

        elif any(word in message_lower for word in ['rutas', 'ruta', 'recolección', 'recoleccion']):
            return """🚛 **Estado de Rutas de Recolección:**

En la sección "Reciclaje" puedes:
• Ver rutas disponibles en tu zona
• Consultar horarios de recolección
• Seguir el estado de tus entregas
• Programar recolecciones especiales

¿Necesitas información sobre alguna ruta específica?"""

        elif any(word in message_lower for word in ['juegos', 'juego', 'educativo']):
            return """🎮 **Juegos Educativos:**

Tenemos juegos sobre:
• Reciclaje de plásticos 🧴
• Clasificación de vidrios 🍾
• Separación de papel 📄
• Identificación de metales 🔧

Cada juego te da puntos y conocimiento. ¿Cuál te gustaría jugar?"""

        elif any(word in message_lower for word in ['hola', 'buenos', 'buenas', 'saludos']):
            return """¡Hola! 👋 

Soy EcoBot, tu asistente inteligente de EcoPuntos. Estoy aquí para ayudarte con:

🎯 Información sobre canjes y materiales
📊 Consultar tus puntos y nivel  
🏆 Logros y recompensas
🚛 Estado de rutas de recolección
❓ Preguntas frecuentes
🎮 Juegos educativos

¿En qué puedo ayudarte hoy?"""

        elif any(word in message_lower for word in ['ayuda', 'help', 'que puedes hacer', 'opciones']):
            return """🤖 **¿Cómo puedo ayudarte?**

Puedo asistirte con:

**📊 Consultas:**
• Estado de tus puntos
• Nivel actual y progreso
• Historial de transacciones

**🎯 Canjes:**
• Recompensas disponibles
• Proceso de canje
• Seguimiento de entregas

**🎮 Actividades:**
• Juegos educativos
• Desafíos de reciclaje
• Logros disponibles

**🚛 Recolección:**
• Rutas cercanas
• Horarios de recolección
• Materiales aceptados

¡Pregúntame lo que necesites!"""

        elif any(word in message_lower for word in ['gracias', 'thank', 'perfecto', 'excelente']):
            return """¡De nada! 😊 

Me alegra poder ayudarte. Si tienes más preguntas sobre EcoPuntos, canjes, puntos o cualquier cosa relacionada con el reciclaje, estaré aquí.

¡Sigamos construyendo un mundo más verde juntos! 🌱♻️"""

        else:
            # Respuesta genérica
            return f"""¡Hola! Recibí tu mensaje: "{user_message}"

Soy EcoBot y puedo ayudarte con:
• **Canjes** - Intercambia tus puntos por recompensas
• **Puntos** - Consulta tu puntaje y nivel
• **Recompensas** - Ve qué premios están disponibles  
• **Rutas** - Estado de recolección en tu zona
• **Juegos** - Actividades educativas de reciclaje

¿Sobre cuál de estos temas te gustaría saber más? 🌱"""

# Instancia global del servicio de prueba
test_chatbot_service = TestChatbotService()