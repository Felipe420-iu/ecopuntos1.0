"""
Detector de intenciones para el chatbot de EcoPuntos
Analiza mensajes de usuario para identificar intenciones y entidades
"""
import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class IntentDetector:
    """Detector de intenciones basado en reglas y patrones"""
    
    def __init__(self):
        """Inicializa el detector con patrones de intenciones"""
        self.intent_patterns = self._load_intent_patterns()
        self.entities_patterns = self._load_entity_patterns()
        
    def analyze_message(self, mensaje: str) -> Dict:
        """
        Analiza un mensaje para detectar intención y entidades
        
        Args:
            mensaje (str): Mensaje del usuario
            
        Returns:
            Dict: Resultado del análisis con intención, entidades y confianza
        """
        mensaje_clean = self._clean_message(mensaje)
        
        # Detectar intención
        intent, intent_confidence = self._detect_intent(mensaje_clean)
        
        # Extraer entidades
        entities = self._extract_entities(mensaje_clean)
        
        # Detectar sentimiento básico
        sentiment = self._detect_sentiment(mensaje_clean)
        
        return {
            'intent': intent,
            'confidence': intent_confidence,
            'entities': entities,
            'sentiment': sentiment,
            'original_message': mensaje,
            'cleaned_message': mensaje_clean
        }
    
    def _clean_message(self, mensaje: str) -> str:
        """Limpia y normaliza el mensaje"""
        # Convertir a minúsculas
        mensaje = mensaje.lower().strip()
        
        # Eliminar caracteres especiales pero mantener acentos
        mensaje = re.sub(r'[^\w\sáéíóúñü]', ' ', mensaje)
        
        # Normalizar espacios
        mensaje = re.sub(r'\s+', ' ', mensaje)
        
        return mensaje
    
    def _detect_intent(self, mensaje: str) -> Tuple[str, float]:
        """
        Detecta la intención principal del mensaje
        
        Args:
            mensaje (str): Mensaje limpio
            
        Returns:
            Tuple[str, float]: Intención detectada y nivel de confianza
        """
        best_intent = 'general_question'
        best_confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            confidence = self._calculate_pattern_match(mensaje, patterns)
            
            if confidence > best_confidence:
                best_intent = intent
                best_confidence = confidence
        
        return best_intent, best_confidence
    
    def _extract_entities(self, mensaje: str) -> Dict:
        """
        Extrae entidades del mensaje
        
        Args:
            mensaje (str): Mensaje limpio
            
        Returns:
            Dict: Entidades encontradas
        """
        entities = {}
        
        for entity_type, patterns in self.entities_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, mensaje)
                matches.extend(found)
            
            if matches:
                entities[entity_type] = list(set(matches))  # Remover duplicados
        
        return entities
    
    def _detect_sentiment(self, mensaje: str) -> str:
        """
        Detecta el sentimiento básico del mensaje
        
        Args:
            mensaje (str): Mensaje limpio
            
        Returns:
            str: Sentimiento detectado (positive, negative, neutral)
        """
        positive_words = [
            'gracias', 'excelente', 'genial', 'perfecto', 'bien', 'bueno',
            'fantástico', 'increíble', 'maravilloso', 'feliz', 'contento',
            'satisfecho', 'me gusta', 'amor', 'amo'
        ]
        
        negative_words = [
            'malo', 'terrible', 'horrible', 'pésimo', 'molesto', 'frustrado',
            'enojado', 'furioso', 'problema', 'error', 'falla', 'no funciona',
            'odio', 'detesto', 'disgusto', 'mal', 'triste', 'decepcionado'
        ]
        
        positive_count = sum(1 for word in positive_words if word in mensaje)
        negative_count = sum(1 for word in negative_words if word in mensaje)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_pattern_match(self, mensaje: str, patterns: List[str]) -> float:
        """
        Calcula qué tan bien coincide un mensaje con los patrones de una intención
        
        Args:
            mensaje (str): Mensaje a analizar
            patterns (List[str]): Lista de patrones de la intención
            
        Returns:
            float: Nivel de confianza (0.0 - 1.0)
        """
        matches = 0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if re.search(pattern, mensaje):
                matches += 1
        
        if matches == 0:
            return 0.0
        
        # Calcular confianza basada en coincidencias
        base_confidence = matches / total_patterns
        
        # Bonus por múltiples coincidencias
        if matches > 1:
            base_confidence = min(1.0, base_confidence * 1.2)
        
        return base_confidence
    
    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Carga los patrones de intenciones"""
        return {
            'check_points': [
                r'cuantos puntos.*tengo',
                r'ver.*mis puntos',
                r'consultar.*puntos',
                r'puntos.*actuales',
                r'mi.*saldo',
                r'balance.*puntos'
            ],
            
            'canje_info': [
                r'como.*canjear',
                r'canje.*materiales',
                r'intercambiar.*materiales',
                r'vender.*materiales',
                r'entregar.*materiales',
                r'solicitar.*canje'
            ],
            
            'material_info': [
                r'que.*materiales.*acepta',
                r'tipos.*materiales',
                r'materiales.*reciclables',
                r'plastico.*vidrio.*papel',
                r'que.*puedo.*reciclar',
                r'lista.*materiales'
            ],
            
            'level_info': [
                r'mi.*nivel',
                r'que.*nivel.*soy',
                r'nivel.*actual',
                r'como.*subir.*nivel',
                r'niveles.*disponibles',
                r'guardian.*verde'
            ],
            
            'game_info': [
                r'juegos.*disponibles',
                r'jugar.*juegos',
                r'juegos.*educativos',
                r'entretenimiento',
                r'minijuegos'
            ],
            
            'route_info': [
                r'ruta.*recoleccion',
                r'recoger.*materiales',
                r'domicilio',
                r'agendar.*recogida',
                r'cuando.*recogen',
                r'horarios.*recoleccion'
            ],
            
            'rewards_info': [
                r'recompensas.*disponibles',
                r'que.*puedo.*obtener',
                r'premios',
                r'beneficios',
                r'catalogo.*recompensas'
            ],
            
            'technical_problem': [
                r'no.*funciona',
                r'error.*en',
                r'problema.*con',
                r'falla.*la',
                r'bug',
                r'no.*puedo.*acceder',
                r'no.*carga'
            ],
            
            'account_problem': [
                r'mi.*cuenta',
                r'no.*puedo.*iniciar.*sesion',
                r'olvide.*mi.*contraseña',
                r'cambiar.*email',
                r'actualizar.*perfil',
                r'borrar.*cuenta'
            ],
            
            'speak_to_human': [
                r'hablar.*con.*persona',
                r'agente.*humano',
                r'operador',
                r'representante',
                r'alguien.*real',
                r'persona.*real',
                r'ayuda.*humana'
            ],
            
            'complaint_escalation': [
                r'queja',
                r'reclamo',
                r'no.*estoy.*satisfecho',
                r'mal.*servicio',
                r'frustrante',
                r'supervisor',
                r'gerente'
            ],
            
            'greeting': [
                r'^(hola|hi|hey|buenas)',
                r'buenos.*dias',
                r'buenas.*tardes',
                r'buenas.*noches',
                r'que.*tal',
                r'como.*estas'
            ],
            
            'goodbye': [
                r'adios',
                r'hasta.*luego',
                r'nos.*vemos',
                r'chao',
                r'bye',
                r'gracias.*por.*todo'
            ]
        }
    
    def _load_entity_patterns(self) -> Dict[str, List[str]]:
        """Carga los patrones para extracción de entidades"""
        return {
            'materials': [
                r'(plastico|plasticos)',
                r'(vidrio|vidrios)',
                r'(papel|carton)',
                r'(metal|metales|aluminio)',
                r'(latas|botellas|envases)'
            ],
            
            'quantities': [
                r'(\d+)\s*(kilos?|kg)',
                r'(\d+)\s*(gramos?|gr?)',
                r'(\d+)\s*(libras?)',
                r'(\d+)\s*(toneladas?)'
            ],
            
            'time_references': [
                r'(hoy|mañana|pasado mañana)',
                r'(lunes|martes|miercoles|jueves|viernes|sabado|domingo)',
                r'(mañana|tarde|noche)',
                r'(\d{1,2})\s*(am|pm)'
            ],
            
            'locations': [
                r'(bogota|medellin|cali|barranquilla|cartagena)',
                r'(norte|sur|este|oeste|centro)',
                r'(barrio|localidad|sector)'
            ],
            
            'money_amounts': [
                r'\$?\s*(\d+(?:\\.\d{3})*(?:,\d{2})?)',
                r'(\d+)\s*pesos',
                r'(\d+)\s*cop'
            ]
        }

# Instancia global del detector
intent_detector = IntentDetector()