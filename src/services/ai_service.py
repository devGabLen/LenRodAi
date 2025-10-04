"""
Servicio de IA con OpenAI
"""

import openai
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.core.config import settings
from src.core.database import db_manager

class AIService:
    """Servicio para interactuar con OpenAI"""
    
    def __init__(self):
        self.client = None
        self.model = settings.MODEL_NAME
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
    
    async def initialize(self):
        """Inicializar cliente OpenAI"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no está configurada")
        
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        print("✅ Servicio OpenAI inicializado")
    
    async def generate_response(self, user_message: str, 
                              conversation_history: List[Dict] = None,
                              context: Dict = None) -> Dict[str, Any]:
        """Generar respuesta usando OpenAI"""
        try:
            # Construir mensajes del sistema
            system_prompt = self._build_system_prompt(context)
            messages = [{"role": "system", "content": system_prompt}]
            
            # Agregar historial de conversación
            if conversation_history:
                for msg in conversation_history[-10:]:  # Últimos 10 mensajes
                    messages.append({
                        "role": "user", 
                        "content": msg.get("user_message", "")
                    })
                    messages.append({
                        "role": "assistant", 
                        "content": msg.get("ai_response", "")
                    })
            
            # Agregar mensaje actual
            messages.append({"role": "user", "content": user_message})
            
            # Llamar a OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content
            confidence = self._calculate_confidence(response)
            
            return {
                "message": ai_response,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "message": f"Lo siento, hubo un error procesando tu mensaje: {str(e)}",
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _build_system_prompt(self, context: Dict = None) -> str:
        """Construir prompt del sistema"""
        base_prompt = """Eres un asistente de IA inteligente, sofisticado y profesional. 
        Tu objetivo es ayudar a los usuarios de manera útil, precisa y amigable.
        
        Características de tu personalidad:
        - Eres elegante y sofisticado en tus respuestas
        - Mantienes un tono profesional pero amigable
        - Eres preciso y detallado cuando es necesario
        - Adaptas tu estilo según el contexto de la conversación
        - Eres creativo y original en tus respuestas
        
        Instrucciones:
        - Responde siempre en español (a menos que se solicite otro idioma)
        - Sé conciso pero completo
        - Si no estás seguro de algo, admítelo honestamente
        - Proporciona información útil y práctica
        - Mantén la conversación fluida y natural"""
        
        if context:
            if context.get("topics"):
                base_prompt += f"\n\nContexto de temas de interés: {', '.join(context['topics'])}"
            
            if context.get("personality"):
                personality = context["personality"]
                if personality.get("communication_style"):
                    base_prompt += f"\n\nEstilo de comunicación preferido: {personality['communication_style']}"
        
        return base_prompt
    
    def _calculate_confidence(self, response) -> float:
        """Calcular confianza basada en la respuesta"""
        # Análisis básico de confianza
        confidence = 0.8  # Base
        
        # Ajustar según tokens utilizados
        if response.usage.total_tokens < 50:
            confidence -= 0.1
        elif response.usage.total_tokens > 500:
            confidence += 0.1
        
        # Ajustar según presencia de indicadores de incertidumbre
        response_text = response.choices[0].message.content.lower()
        uncertainty_words = ["no estoy seguro", "no sé", "tal vez", "posiblemente", "quizás"]
        
        for word in uncertainty_words:
            if word in response_text:
                confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analizar sentimiento del texto"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Analiza el sentimiento del siguiente texto y responde solo con un JSON que contenga: sentiment (positive/negative/neutral), confidence (0-1), emotions (lista de emociones detectadas)."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "emotions": [],
                "error": str(e)
            }
    
    async def extract_keywords(self, text: str) -> List[str]:
        """Extraer palabras clave del texto"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extrae las palabras clave más importantes del siguiente texto. Responde solo con una lista de palabras separadas por comas."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            keywords = response.choices[0].message.content.split(",")
            return [kw.strip() for kw in keywords if kw.strip()]
            
        except Exception as e:
            return []
    
    async def cleanup(self):
        """Limpiar recursos"""
        if self.client:
            # Cerrar conexiones si es necesario
            pass
