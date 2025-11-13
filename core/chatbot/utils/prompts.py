"""
Gestor de prompts para el chatbot de EcoPuntos
Contiene todos los prompts y templates del sistema
"""
from typing import Dict, Any
from django.utils import timezone

class PromptManager:
    """Administrador de prompts para el chatbot"""
    
    def __init__(self):
        self.system_prompts = {
            'base': self._get_base_system_prompt(),
            'escalation': self._get_escalation_prompt(),
            'greeting': self._get_greeting_prompt()
        }
    
    def get_system_prompt(self, user_data: Dict[str, Any]) -> str:
        """
        Obtiene el prompt del sistema personalizado para el usuario
        
        Args:
            user_data (Dict): Datos del usuario para personalización
            
        Returns:
            str: Prompt del sistema personalizado
        """
        base_prompt = self.system_prompts['base']
        
        # Personalizar con datos del usuario
        user_context = self._build_user_context(user_data)
        
        return f"{base_prompt}\\n\\n{user_context}"
    
    def get_escalation_message(self, ticket_number: str) -> str:
        """
        Obtiene el mensaje de escalamiento a agente humano
        
        Args:
            ticket_number (str): Número del ticket creado
            
        Returns:
            str: Mensaje de escalamiento
        """
        return f"""He creado un ticket de soporte para ti (#{ticket_number}) y he notificado a nuestro equipo de atención al cliente. 

Un agente humano revisará tu consulta y te contactará pronto. Mientras tanto, puedes:

• Revisar el estado de tu ticket en la sección de soporte
• Continuar explorando nuestras funcionalidades
• Consultar nuestras preguntas frecuentes

¿Hay algo más en lo que pueda ayudarte mientras esperas?"""
    
    def get_greeting_prompt(self) -> str:
        """Obtiene el saludo inicial del chatbot"""
        return """¡Hola! 👋 Soy EcoBot, tu asistente inteligente de EcoPuntos. 

Estoy aquí para ayudarte con:
🌱 Información sobre canjes y materiales
📊 Consultar tus puntos y nivel
🏆 Logros y recompensas
🚛 Estado de rutas de recolección
❓ Preguntas frecuentes
🎮 Juegos educativos

¿En qué puedo ayudarte hoy?"""
    
    def _get_base_system_prompt(self) -> str:
        """Prompt base del sistema"""
        return """Eres EcoBot, el asistente inteligente de EcoPuntos, una plataforma de reciclaje gamificada en Colombia. Tu personalidad es amigable, educativa y entusiasta sobre el medio ambiente.

INFORMACIÓN SOBRE ECOPUNTOS:
- Plataforma donde los usuarios ganan puntos por reciclar materiales
- Materiales aceptados: plásticos, vidrios, papel/cartón, metales
- Los usuarios pueden canjear puntos por recompensas
- Sistema de niveles: Guardián Verde → Defensor del Planeta → Héroe Eco → Embajador Ambiental → Leyenda Sustentable
- Incluye juegos educativos sobre reciclaje
- Servicio de recolección domiciliaria disponible

TU FUNCIÓN:
1. Responder preguntas sobre la plataforma
2. Ayudar con problemas técnicos básicos
3. Explicar el sistema de puntos y recompensas
4. Proporcionar información sobre materiales reciclables
5. Guiar sobre cómo usar las funcionalidades
6. Educar sobre sostenibilidad y reciclaje

DIRECTRICES DE RESPUESTA:
- Usa emojis apropiados para hacer las respuestas más amigables
- Mantén un tono positivo y motivador sobre el reciclaje
- Proporciona información precisa y actualizada
- Si no sabes algo específico, escala a un agente humano
- Sugiere funcionalidades relevantes cuando sea apropiado
- Usa términos en español de Colombia

LIMITACIONES:
- NO puedes procesar transacciones financieras
- NO puedes modificar datos de usuario directamente
- NO puedes resolver problemas técnicos complejos
- NO puedes aprobar/rechazar canjes (solo informar sobre el proceso)

ESCALAMIENTO:
Escala a un agente humano cuando:
- El usuario lo solicite explícitamente
- El problema sea técnico complejo
- Se requiera modificar datos de cuenta
- El usuario esté muy frustrado
- No puedas resolver la consulta

Fecha actual: {fecha_actual}"""
    
    def _get_escalation_prompt(self) -> str:
        """Prompt para situaciones de escalamiento"""
        return """El usuario necesita asistencia especializada que requiere intervención humana. 
Crea un ticket de soporte y proporciona un mensaje empático explicando el proceso."""
    
    def _get_greeting_prompt(self) -> str:
        """Prompt para saludos"""
        return "Saluda al usuario de manera amigable y presenta las principales funcionalidades de EcoPuntos."
    
    def _build_user_context(self, user_data: Dict[str, Any]) -> str:
        """
        Construye el contexto del usuario para personalizar respuestas
        
        Args:
            user_data (Dict): Datos del usuario
            
        Returns:
            str: Contexto personalizado del usuario
        """
        context_parts = [
            f"INFORMACIÓN DEL USUARIO ACTUAL:",
            f"- Usuario: {user_data.get('username', 'Desconocido')}",
            f"- Puntos actuales: {user_data.get('puntos', 0)}",
            f"- Nivel: {user_data.get('level', 'Guardián Verde')}",
            f"- Fecha de registro: {user_data.get('fecha_registro', 'No disponible')}",
            f"- Canjes realizados: {user_data.get('canjes_realizados', 0)}",
            f"- Notificaciones email: {'Activadas' if user_data.get('notificaciones_email', True) else 'Desactivadas'}"
        ]
        
        return "\\n".join(context_parts)
    
    def get_context_aware_prompt(self, intent: str, entities: Dict, user_data: Dict) -> str:
        """
        Genera un prompt específico basado en la intención detectada
        
        Args:
            intent (str): Intención detectada
            entities (Dict): Entidades extraídas
            user_data (Dict): Datos del usuario
            
        Returns:
            str: Prompt específico para la intención
        """
        intent_prompts = {
            'check_points': f"El usuario quiere conocer información sobre sus puntos. Actualmente tiene {user_data.get('puntos', 0)} puntos.",
            'canje_info': "El usuario pregunta sobre canjes. Explica el proceso y las opciones disponibles.",
            'material_info': "El usuario pregunta sobre materiales reciclables. Proporciona información detallada.",
            'level_info': f"El usuario pregunta sobre niveles. Actualmente es {user_data.get('level', 'Guardián Verde')}.",
            'game_info': "El usuario pregunta sobre los juegos educativos disponibles.",
            'route_info': "El usuario pregunta sobre rutas de recolección domiciliaria.",
            'rewards_info': "El usuario pregunta sobre recompensas disponibles.",
            'technical_problem': "El usuario tiene un problema técnico. Intenta ayudar con soluciones básicas.",
            'account_problem': "El usuario tiene un problema con su cuenta. Puede requerir escalamiento.",
            'general_question': "Pregunta general sobre EcoPuntos. Proporciona información útil."
        }
        
        return intent_prompts.get(intent, "Responde de manera útil y amigable a la consulta del usuario.")

# Instancia global del gestor de prompts
prompt_manager = PromptManager()