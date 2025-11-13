"""
Servicio de IA usando Google Gemini 1.5 Flash

Características principales:
- GRATIS hasta 1,500 requests/día
- 1 millón de tokens de contexto
- Multimodal nativo (texto, imágenes, audio)
- Latencia más baja
- API más simple
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai no está instalado. Ejecuta: pip install google-generativeai")

from django.conf import settings
from core.models import MensajeChatbot, ContextoChatbot

logger = logging.getLogger(__name__)


class GeminiAIService:
    """Servicio de IA usando Gemini Flash 2.0 - Gratis y Potente"""
    
    def __init__(self):
        """Inicializa el servicio de Gemini"""
        if not GEMINI_AVAILABLE:
            raise ImportError("Instala google-generativeai: pip install google-generativeai")
        
        # Configurar API key
        api_key = getattr(settings, 'GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY'))
        if not api_key:
            raise ValueError("GOOGLE_API_KEY no configurada en settings o .env")
        
        genai.configure(api_key=api_key)
        
        # Modelo: gemini-2.5-flash (versión más reciente y gratuita)
        self.model_name = getattr(settings, 'AI_MODEL', 'gemini-2.5-flash')
        
        # Configuración de generación
        self.generation_config = {
            'temperature': 0.7,  # Equilibrio entre creatividad y precisión
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 1024,  # Suficiente para respuestas del chatbot
        }
        
        # Configuraciones de seguridad (ajustables según necesidad)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        # Crear modelo
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        logger.info(f"✅ Gemini AI Service inicializado con {self.model_name}")
    
    def _build_system_prompt(self, user) -> str:
        """
        Construye el prompt del sistema con información contextual
        
        VENTAJA GEMINI: Con 1M de tokens, podemos incluir MUCHA información
        sin preocuparnos por el límite
        """
        return f"""Eres EcoBot, el asistente inteligente oficial de EcoPuntos, una plataforma de reciclaje gamificada en Colombia.

INFORMACIÓN DEL USUARIO ACTUAL:
- Nombre: {user.get_full_name() or user.username}
- Puntos Actuales: {getattr(user, 'puntos', 0)} EcoPuntos
- Nivel: {getattr(user, 'level', 'Guardián Verde')}

INFORMACIÓN CORRECTA SOBRE ECOPUNTOS:
=======================================

¿QUÉ ES ECOPUNTOS?
EcoPuntos es una plataforma donde los usuarios entregan materiales reciclables y obtienen puntos que pueden canjear por recompensas específicas (NO por dinero).

SISTEMA DE FUNCIONAMIENTO REAL:
1. **ENTREGA DE MATERIALES**: Los usuarios solicitan canjes entregando materiales reciclables
2. **VERIFICACIÓN**: El equipo de EcoPuntos verifica y pesa los materiales
3. **PUNTOS**: Se otorgan puntos según el peso real y tipo de material
4. **RECOMPENSAS**: Los puntos se canjean únicamente por recompensas del catálogo

MATERIALES ACEPTADOS Y PUNTOS:
- **Plásticos**: Puntos variables por kilogramo según tipo
- **Vidrio**: Puntos específicos por kilogramo 
- **Papel y Cartón**: Puntos específicos por kilogramo
- **Metales**: Puntos específicos por kilogramo
(Los puntos exactos por kilo se definen por material específico)

PROCESO DE CANJE:
1. Usuario solicita canje especificando material y peso estimado
2. Equipo programa recolección o usuario entrega en punto de acopio
3. Material se verifica y pesa (peso real puede diferir del estimado)
4. Se aprueban puntos según peso real × puntos por kilo del material
5. Puntos se agregan automáticamente a la cuenta del usuario

RECOMPENSAS DISPONIBLES:
Los puntos SOLO se pueden canjear por:
- Productos del catálogo de recompensas
- Experiencias específicas disponibles
- Beneficios y descuentos con aliados
- NUNCA por dinero en efectivo

NIVELES DE USUARIO:
- Guardián Verde (inicial)
- Defensor del Planeta  
- Héroe Eco
- Embajador Ambiental
- Leyenda Sustentable

FUNCIONALIDADES ADICIONALES:
- Juegos educativos de reciclaje (se pueden ganar puntos jugando)
- Sistema de notificaciones
- Rutas de recolección programadas
- Seguimiento de estadísticas personales

ESTADOS DE CANJES:
- Pendiente: Solicitud enviada
- Confirmado: Solicitud aceptada
- En Recolección: Material siendo recolectado
- Verificando: Material siendo verificado
- Aprobado: Puntos otorgados
- Rechazado: Material no aceptado
- Completado: Proceso finalizado

TU PERSONALIDAD Y TONO:
- Amigable, motivador y entusiasta sobre el reciclaje
- Educativo pero no condescendiente  
- Usa emojis ocasionalmente ♻️ 🌱 🎯
- Celebra los logros del usuario
- Motiva a seguir reciclando

RESTRICCIONES IMPORTANTES:
❌ NUNCA digas que los puntos se pueden canjear por dinero
❌ NUNCA inventes información sobre recompensas que no existen
❌ NUNCA prometas funciones que no están implementadas
❌ NUNCA des información incorrecta sobre el proceso de canjes

✅ SIEMPRE explica que los puntos son para recompensas específicas
✅ SIEMPRE menciona que los materiales deben ser verificados
✅ SIEMPRE deriva a soporte si no sabes algo específico
✅ SIEMPRE celebra cuando el usuario recicla

FRASES CLAVE A USAR:
- "Los puntos se canjean por recompensas del catálogo, no por dinero"
- "El equipo verificará tus materiales y asignará puntos según el peso real"
- "¡Excelente contribución al medio ambiente!"
- "Cada material reciclado cuenta para un planeta más limpio"

EJEMPLO DE RESPUESTA CORRECTA:
Usuario: "¿Puedo sacar dinero de mis puntos?"
Respuesta: "Los EcoPuntos no se pueden convertir en dinero 💰. En lugar de eso, puedes canjearlos por increíbles recompensas de nuestro catálogo: productos ecológicos, experiencias, descuentos con aliados y mucho más. ¡Es una forma genial de obtener beneficios mientras cuidas el planeta! 🌱 ¿Te gustaría que te muestre qué recompensas están disponibles?"

Recuerda: Tu objetivo es hacer que reciclar sea fácil, divertido y gratificante, siempre con información precisa."""
    
    async def _build_conversation_history(
        self, 
        conversacion_id: int, 
        include_context: bool = True,
        max_messages: int = 20  # Puedes aumentar esto gracias al contexto de 1M
    ) -> List[Dict[str, str]]:
        """
        Construye el historial de conversación (versión async)
        
        VENTAJA GEMINI: Podemos incluir muchos más mensajes sin problema
        """
        from channels.db import database_sync_to_async
        
        messages = []
        
        try:
            # Obtener mensajes recientes (async)
            @database_sync_to_async
            def get_mensajes():
                mensajes = MensajeChatbot.objects.filter(
                    conversacion_id=conversacion_id
                ).order_by('-timestamp')[:max_messages]
                return list(reversed(mensajes))
            
            mensajes = await get_mensajes()
            
            # Construir historial
            for mensaje in mensajes:
                role = 'user' if mensaje.es_usuario else 'model'
                messages.append({
                    'role': role,
                    'parts': [mensaje.contenido]
                })
            
            logger.info(f"📚 Historial construido: {len(messages)} mensajes")
            
        except Exception as e:
            logger.error(f"Error al construir historial: {e}")
        
        return messages
    
    async def process_message(
        self,
        user,
        mensaje: str,
        conversacion_id: int,
        include_history: bool = True
    ) -> Tuple[str, float]:
        """
        Procesa un mensaje del usuario y genera respuesta con Gemini
        
        Args:
            user: Usuario de Django
            mensaje: Texto del mensaje
            conversacion_id: ID de la conversación
            include_history: Si incluir historial de chat
        
        Returns:
            Tupla (respuesta, confidence)
        """
        try:
            # Construir sistema de prompts
            system_prompt = self._build_system_prompt(user)
            
            # Iniciar chat session
            if include_history:
                history = await self._build_conversation_history(conversacion_id)
            else:
                history = []
            
            # Gemini usa sessions para mantener contexto
            chat = self.model.start_chat(history=history)
            
            # Construir mensaje completo
            if not history:  # Primera interacción
                full_message = f"{system_prompt}\n\nUsuario: {mensaje}"
            else:
                full_message = mensaje
            
            # Generar respuesta (síncrono - Gemini no tiene async nativo)
            # Ejecutar en thread pool para no bloquear
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: chat.send_message(full_message)
            )
            
            # Extraer texto de respuesta
            respuesta = response.text
            
            # Calcular confidence (Gemini no proporciona directamente, usamos heurística)
            confidence = self._calculate_confidence(response)
            
            logger.info(f"✅ Respuesta generada - Confidence: {confidence:.2f}")
            logger.debug(f"Respuesta: {respuesta[:100]}...")
            
            return respuesta, confidence
            
        except Exception as e:
            logger.error(f"❌ Error en process_message: {e}")
            return self._get_fallback_response(), 0.5
    
    def _calculate_confidence(self, response) -> float:
        """
        Calcula nivel de confianza de la respuesta
        
        Gemini no proporciona confidence score directamente,
        así que usamos heurísticas
        """
        try:
            # Si la respuesta fue bloqueada por seguridad
            if hasattr(response, 'prompt_feedback'):
                if response.prompt_feedback.block_reason:
                    return 0.0
            
            # Longitud de respuesta como indicador
            text_length = len(response.text)
            if text_length < 20:
                return 0.3  # Respuesta muy corta, baja confianza
            elif text_length < 50:
                return 0.5
            elif text_length < 100:
                return 0.7
            else:
                return 0.9  # Respuesta completa
            
        except Exception as e:
            logger.warning(f"No se pudo calcular confidence: {e}")
            return 0.7  # Default medio
    
    def _get_fallback_response(self) -> str:
        """Respuesta de respaldo si algo falla"""
        return (
            "Disculpa, estoy teniendo problemas técnicos en este momento. 🔧\n\n"
            "Por favor:\n"
            "- Intenta reformular tu pregunta\n"
            "- O contacta a soporte: soporte@ecopuntos.com\n\n"
            "¡Gracias por tu paciencia! ♻️"
        )
    
    async def detect_intent(self, mensaje: str) -> Dict[str, any]:
        """
        Detecta la intención del mensaje usando Gemini
        
        VENTAJA: Detección más precisa sin necesidad de fine-tuning
        """
        try:
            prompt = f"""Analiza este mensaje de un usuario y clasifica su intención:

Mensaje: "{mensaje}"

Clasifica en UNA de estas categorías:
1. consulta_reciclaje - Pregunta sobre qué/cómo reciclar
2. consulta_puntos - Pregunta sobre puntos ganados o disponibles
3. consulta_recompensas - Pregunta sobre canjeo o recompensas
4. solicitud_recogida - Quiere agendar recogida de materiales
5. problema_tecnico - Reporta un error o problema
6. saludo - Saludo o despedida
7. otro - No encaja en las anteriores

Responde SOLO con el formato JSON:
{{"intent": "categoria", "confidence": 0.0-1.0, "entities": []}}"""

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Parsear respuesta JSON
            import json
            result = json.loads(response.text.strip())
            
            logger.info(f"🎯 Intención detectada: {result['intent']} ({result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error en detect_intent: {e}")
            return {
                'intent': 'otro',
                'confidence': 0.5,
                'entities': []
            }
    
    async def analyze_image(self, image_path: str, question: str = None) -> str:
        """
        Analiza una imagen usando Gemini (MULTIMODAL)
        
        VENTAJA EXCLUSIVA: Gemini Flash es multimodal nativo
        Casos de uso:
        - Usuario envía foto de material: "¿Es reciclable?"
        - Verificación de estado de materiales
        - Clasificación automática
        """
        try:
            # Cargar imagen
            import PIL.Image
            img = PIL.Image.open(image_path)
            
            # Prompt para análisis
            if question:
                prompt = question
            else:
                prompt = """Analiza esta imagen de material/producto:

1. ¿Qué material es?
2. ¿Es reciclable en EcoPuntos?
3. ¿A qué categoría pertenece? (papel, plástico, vidrio, metal, electrónico)
4. ¿Cuántos puntos podría ganar?
5. ¿Alguna recomendación para prepararlo para reciclaje?

Responde de forma clara y amigable."""
            
            # Generar respuesta con imagen
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content([prompt, img])
            )
            
            logger.info("📸 Imagen analizada exitosamente")
            return response.text
            
        except Exception as e:
            logger.error(f"Error en analyze_image: {e}")
            return "No pude analizar la imagen. Por favor intenta de nuevo."
    
    def get_model_info(self) -> Dict[str, any]:
        """Información del modelo actual"""
        return {
            'provider': 'Google Gemini',
            'model': self.model_name,
            'version': '1.5 Flash',
            'context_window': '1,000,000 tokens',
            'cost': 'GRATIS hasta 1,500 requests/día',
            'multimodal': True,
            'features': [
                'Contexto de 1M tokens',
                'Análisis de imágenes',
                'Baja latencia',
                'API simple'
            ]
        }


# Función helper para fácil integración
async def get_gemini_response(user, mensaje: str, conversacion_id: int) -> Tuple[str, float]:
    """
    Función helper para obtener respuesta de Gemini
    
    Uso:
        respuesta, confidence = await get_gemini_response(user, "Hola", 1)
    """
    service = GeminiAIService()
    return await service.process_message(user, mensaje, conversacion_id)


# Testing rápido
if __name__ == "__main__":
    async def test():
        """Test rápido del servicio"""
        print("🧪 Testing Gemini AI Service...")
        
        # Crear servicio
        service = GeminiAIService()
        print(f"✅ Servicio creado: {service.model_name}")
        
        # Info del modelo
        info = service.get_model_info()
        print(f"\n📊 Información del modelo:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        print("\n✅ Test completado!")
    
    # Ejecutar test
    asyncio.run(test())
