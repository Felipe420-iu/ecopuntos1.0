"""
Servicio principal de IA para el chatbot de EcoPuntos
Maneja la comunicación con OpenAI y la lógica de respuestas
"""
import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from openai import AsyncOpenAI
from channels.db import database_sync_to_async
from core.models import ConversacionChatbot, MensajeChatbot, ContextoChatbot
from ..utils.prompts import PromptManager
from ..utils.intent_detector import IntentDetector

logger = logging.getLogger(__name__)

class ChatbotAIService:
    """Servicio principal del chatbot con IA"""
    
    def __init__(self):
        """Inicializa el servicio de IA"""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = getattr(settings, 'AI_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = getattr(settings, 'AI_MAX_TOKENS', 1000)
        self.temperature = getattr(settings, 'AI_TEMPERATURE', 0.7)
        self.prompt_manager = PromptManager()
        self.intent_detector = IntentDetector()
        
        logger.info(f"ChatbotAIService inicializado con modelo: {self.model}")
    
    async def process_message(self, user_message: str, conversacion: ConversacionChatbot) -> Dict:
        """
        Procesa un mensaje del usuario y genera una respuesta de IA
        
        Args:
            user_message (str): Mensaje del usuario
            conversacion (ConversacionChatbot): Objeto de conversación
            
        Returns:
            Dict: Respuesta procesada con metadatos
        """
        start_time = time.time()
        
        try:
            # 1. Guardar mensaje del usuario
            mensaje_usuario = await self._save_user_message(user_message, conversacion)
            
            # 2. Obtener/crear contexto
            contexto = await self._get_or_create_context(conversacion)
            
            # 3. Actualizar contexto con el nuevo mensaje
            await self._update_context_with_message(contexto, user_message)
            
            # 4. Detectar intención y entidades
            intent_data = await self._detect_intent_and_entities(user_message)
            
            # 5. Verificar si necesita escalamiento inmediato
            should_escalate = await self._should_escalate_immediately(
                user_message, contexto, intent_data
            )
            
            if should_escalate:
                return await self._handle_escalation(conversacion, contexto, "Solicitud directa de usuario")
            
            # 6. Generar respuesta con IA
            ai_response = await self._generate_ai_response(user_message, conversacion, contexto)
            
            # 7. Evaluar confianza de la respuesta
            confidence_score = await self._evaluate_response_confidence(ai_response, intent_data)
            
            # 8. Verificar si necesita escalamiento por baja confianza
            if confidence_score < getattr(settings, 'CONFIDENCE_THRESHOLD', 0.7):
                return await self._handle_escalation(
                    conversacion, contexto, f"Baja confianza en respuesta ({confidence_score:.2f})"
                )
            
            # 9. Guardar respuesta de IA
            response_time_ms = int((time.time() - start_time) * 1000)
            mensaje_ia = await self._save_ai_message(
                ai_response, conversacion, confidence_score, intent_data, response_time_ms
            )
            
            # 10. Actualizar estadísticas
            await self._update_conversation_stats(conversacion)
            
            return {
                'success': True,
                'response': ai_response,
                'confidence': confidence_score,
                'intent': intent_data.get('intent', 'unknown'),
                'escalated': False,
                'response_time_ms': response_time_ms,
                'message_id': mensaje_ia.id
            }
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': "Lo siento, ha ocurrido un error técnico. ¿Te gustaría hablar con un agente humano?",
                'confidence': 0.0,
                'escalated': False
            }
    
    async def _save_user_message(self, mensaje: str, conversacion: ConversacionChatbot) -> MensajeChatbot:
        """Guarda el mensaje del usuario en la base de datos"""
        return await database_sync_to_async(MensajeChatbot.objects.create)(
            conversacion=conversacion,
            contenido=mensaje,
            es_usuario=True
        )
    
    async def _get_or_create_context(self, conversacion: ConversacionChatbot) -> ContextoChatbot:
        """Obtiene o crea el contexto de la conversación"""
        try:
            return await asyncio.to_thread(
                lambda: conversacion.contexto
            )
        except ContextoChatbot.DoesNotExist:
            return await asyncio.to_thread(
                ContextoChatbot.objects.create,
                conversacion=conversacion,
                datos_usuario=await self._get_user_profile_data(conversacion.usuario)
            )
    
    async def _get_user_profile_data(self, usuario) -> Dict:
        """Obtiene datos del perfil del usuario para contexto"""
        return await asyncio.to_thread(lambda: {
            'username': usuario.username,
            'puntos': usuario.puntos,
            'level': usuario.get_level_display(),
            'fecha_registro': usuario.fecha_registro.isoformat(),
            'canjes_realizados': usuario.canje_set.count(),
            'notificaciones_email': usuario.notificaciones_email
        })
    
    async def _update_context_with_message(self, contexto: ContextoChatbot, mensaje: str):
        """Actualiza el contexto con el nuevo mensaje del usuario"""
        await asyncio.to_thread(contexto.actualizar_sentimiento, mensaje)
    
    async def _detect_intent_and_entities(self, mensaje: str) -> Dict:
        """Detecta la intención y entidades en el mensaje"""
        return await asyncio.to_thread(self.intent_detector.analyze_message, mensaje)
    
    async def _should_escalate_immediately(self, mensaje: str, contexto: ContextoChatbot, intent_data: Dict) -> bool:
        """Determina si debe escalar inmediatamente a un humano"""
        # Palabras clave de escalamiento
        escalate_keywords = getattr(settings, 'AUTO_ESCALATE_KEYWORDS', '').split(',')
        mensaje_lower = mensaje.lower()
        
        # Verificar palabras clave directas
        if any(keyword.strip().lower() in mensaje_lower for keyword in escalate_keywords if keyword.strip()):
            return True
        
        # Verificar nivel de frustración en contexto
        if contexto.requiere_escalamiento:
            return True
        
        # Verificar número máximo de turnos
        max_turns = getattr(settings, 'MAX_CONVERSATION_TURNS', 20)
        if contexto.conversacion.total_mensajes >= max_turns:
            return True
        
        # Verificar intenciones específicas que requieren escalamiento
        escalate_intents = ['complaint_escalation', 'speak_to_human', 'complex_technical_issue']
        if intent_data.get('intent') in escalate_intents:
            return True
        
        return False
    
    async def _generate_ai_response(self, mensaje: str, conversacion: ConversacionChatbot, contexto: ContextoChatbot) -> str:
        """Genera respuesta usando OpenAI"""
        try:
            # Construir historial de conversación
            historial = await self._build_conversation_history(conversacion)
            
            # Obtener prompt del sistema
            system_prompt = self.prompt_manager.get_system_prompt(contexto.datos_usuario)
            
            # Preparar mensajes para OpenAI
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Añadir historial de conversación
            messages.extend(historial)
            
            # Añadir mensaje actual
            messages.append({"role": "user", "content": mensaje})
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,  # Evitar repetición
                frequency_penalty=0.1   # Variedad en respuestas
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Log de uso de tokens
            if hasattr(response, 'usage'):
                logger.info(f"Tokens utilizados: {response.usage.total_tokens}")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generando respuesta con OpenAI: {str(e)}")
            return "Lo siento, no puedo procesar tu consulta en este momento. ¿Te gustaría hablar con un agente humano?"
    
    async def _build_conversation_history(self, conversacion: ConversacionChatbot, limit: int = 10) -> List[Dict]:
        """Construye el historial de conversación para contexto"""
        mensajes = await asyncio.to_thread(
            lambda: list(conversacion.mensajes.order_by('-timestamp')[:limit])
        )
        
        historial = []
        for mensaje in reversed(mensajes):  # Orden cronológico
            role = "user" if mensaje.es_usuario else "assistant"
            historial.append({
                "role": role,
                "content": mensaje.contenido
            })
        
        return historial
    
    async def _evaluate_response_confidence(self, response: str, intent_data: Dict) -> float:
        """Evalúa la confianza en la respuesta generada"""
        confidence = 0.8  # Confianza base
        
        # Ajustar según la intención detectada
        if intent_data.get('confidence', 0) > 0.8:
            confidence += 0.1
        
        # Penalizar respuestas muy cortas o genéricas
        if len(response) < 20:
            confidence -= 0.2
        
        # Penalizar respuestas con frases de incertidumbre
        uncertainty_phrases = [
            "no estoy seguro", "no sé", "puede ser", "tal vez",
            "podría ser", "es posible que", "quizás"
        ]
        
        if any(phrase in response.lower() for phrase in uncertainty_phrases):
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    async def _save_ai_message(self, respuesta: str, conversacion: ConversacionChatbot, 
                             confidence: float, intent_data: Dict, response_time_ms: int) -> MensajeChatbot:
        """Guarda la respuesta de IA en la base de datos"""
        return await asyncio.to_thread(
            MensajeChatbot.objects.create,
            conversacion=conversacion,
            contenido=respuesta,
            es_usuario=False,
            confidence_score=confidence,
            intent_detected=intent_data.get('intent', ''),
            entities_extracted=intent_data.get('entities', {}),
            response_time_ms=response_time_ms,
            ai_model_used=self.model,
            tokens_used=intent_data.get('tokens_used', 0)
        )
    
    async def _update_conversation_stats(self, conversacion: ConversacionChatbot):
        """Actualiza estadísticas de la conversación"""
        total_mensajes = await asyncio.to_thread(
            lambda: conversacion.mensajes.count()
        )
        
        promedio_confianza = await asyncio.to_thread(
            lambda: conversacion.mensajes.filter(
                es_usuario=False, confidence_score__isnull=False
            ).aggregate(avg_confidence=models.Avg('confidence_score'))['avg_confidence']
        )
        
        await asyncio.to_thread(
            lambda: ConversacionChatbot.objects.filter(id=conversacion.id).update(
                total_mensajes=total_mensajes,
                promedio_confianza=promedio_confianza
            )
        )
    
    async def _handle_escalation(self, conversacion: ConversacionChatbot, 
                               contexto: ContextoChatbot, motivo: str) -> Dict:
        """Maneja el escalamiento a un agente humano"""
        try:
            # Crear ticket de soporte
            ticket = await asyncio.to_thread(conversacion.escalar_a_humano, motivo)
            
            # Respuesta de escalamiento
            escalation_response = self.prompt_manager.get_escalation_message(ticket.numero_ticket)
            
            # Guardar mensaje de escalamiento
            await self._save_ai_message(
                escalation_response, conversacion, 1.0, {'intent': 'escalation'}, 0
            )
            
            logger.info(f"Conversación {conversacion.session_id} escalada. Ticket: {ticket.numero_ticket}")
            
            return {
                'success': True,
                'response': escalation_response,
                'confidence': 1.0,
                'escalated': True,
                'ticket_number': ticket.numero_ticket,
                'intent': 'escalation'
            }
            
        except Exception as e:
            logger.error(f"Error en escalamiento: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': "Ha ocurrido un error al conectarte con un agente. Por favor, intenta más tarde.",
                'escalated': False
            }

# Instancia global del servicio
chatbot_service = ChatbotAIService()