"""
Servicios del chatbot IA - Solo Google Gemini 1.5 Flash

Sistema simplificado que usa exclusivamente Gemini 1.5 Flash:
- GRATIS hasta 1.5K requests/día
- 1 millón de tokens de contexto
- Multimodal (texto, imágenes, audio)
- Baja latencia

Uso:
    from core.chatbot.services import get_ai_service
    
    service = get_ai_service()
    respuesta, confidence = await service.process_message(user, mensaje, conversacion_id)
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_ai_service():
    """
    Retorna instancia del servicio de IA Gemini
    
    Returns:
        GeminiAIService: Instancia del servicio Gemini 1.5 Flash
    
    Raises:
        ImportError: Si google-generativeai no está instalado
        ValueError: Si GOOGLE_API_KEY no está configurada
    
    Configuración en settings.py:
        GOOGLE_API_KEY = 'AIzaSyABLn0ZrFeYnJk1515uzDEowc7px-xi1Zs'
        AI_MODEL = 'gemini-1.5-flash'
    """
    try:
        from .gemini_ai_service import GeminiAIService
        logger.info("✅ Servicio Gemini 1.5 Flash inicializado")
        return GeminiAIService()
    except ImportError as e:
        logger.error(f"❌ Error: google-generativeai no está instalado")
        logger.error(f"   Ejecuta: pip install google-generativeai")
        raise ImportError(
            "Instala google-generativeai: pip install google-generativeai"
        ) from e
    except Exception as e:
        logger.error(f"❌ Error inicializando Gemini: {e}")
        raise


def get_provider_info() -> dict:
    """
    Retorna información sobre Gemini 1.5 Flash
    
    Returns:
        Dict con información del proveedor
    """
    return {
        'name': 'Google Gemini 1.5 Flash',
        'cost': 'GRATIS hasta 1,500 requests/día',
        'context_window': '1,000,000 tokens',
        'multimodal': True,
        'speed': 'Rápido (baja latencia)',
        'setup_url': 'https://makersuite.google.com/app/apikey',
        'docs_url': 'https://ai.google.dev/docs',
        'features': [
            'Contexto gigante (1M tokens)',
            'Análisis de imágenes nativo',
            'Gratis para desarrollo',
            'API simple y fácil',
            'Escalable y confiable'
        ]
    }


# Exportar función principal
__all__ = [
    'get_ai_service',
    'get_provider_info'
]
