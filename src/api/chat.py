"""
API endpoints para chat
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from src.services.ai_service import AIService
from src.services.ml_service import MLService
from src.core.database import db_manager

# Crear router
chat_router = APIRouter()

# Instancias de servicios
ai_service = AIService()
ml_service = MLService()

# Modelos Pydantic
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    confidence: float
    context: Dict[str, Any]
    timestamp: str
    model_info: Dict[str, Any]

class ConversationHistory(BaseModel):
    session_id: str
    limit: Optional[int] = 10

class UserContext(BaseModel):
    session_id: str
    preferences: Optional[Dict[str, Any]] = None
    topics: Optional[List[str]] = None
    personality: Optional[Dict[str, Any]] = None

@chat_router.post("/send", response_model=ChatResponse)
async def send_message(message_data: ChatMessage):
    """Enviar mensaje al chatbot"""
    try:
        # Generar session_id si no se proporciona
        session_id = message_data.session_id or str(uuid.uuid4())
        
        # Obtener historial de conversación
        conversation_history = db_manager.get_conversation_history(session_id, limit=10)
        
        # Analizar contexto con ML
        context = await ml_service.analyze_context(
            message_data.message, 
            conversation_history
        )
        
        # Generar respuesta con IA
        ai_response = await ai_service.generate_response(
            message_data.message,
            conversation_history,
            context
        )
        
        # Guardar conversación
        db_manager.save_conversation(
            session_id=session_id,
            user_message=message_data.message,
            ai_response=ai_response["message"],
            context=context,
            confidence=ai_response.get("confidence", 0.8)
        )
        
        return ChatResponse(
            response=ai_response["message"],
            session_id=session_id,
            confidence=ai_response.get("confidence", 0.8),
            context=context,
            timestamp=ai_response.get("timestamp", datetime.now().isoformat()),
            model_info={
                "model": ai_response.get("model", "unknown"),
                "usage": ai_response.get("usage", {})
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando mensaje: {str(e)}")

@chat_router.get("/history/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 10):
    """Obtener historial de conversación"""
    try:
        history = db_manager.get_conversation_history(session_id, limit)
        return {
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@chat_router.post("/context")
async def update_user_context(context_data: UserContext):
    """Actualizar contexto del usuario"""
    try:
        db_manager.update_user_context(
            session_id=context_data.session_id,
            preferences=context_data.preferences,
            topics=context_data.topics,
            personality=context_data.personality
        )
        
        return {
            "message": "Contexto actualizado correctamente",
            "session_id": context_data.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando contexto: {str(e)}")

@chat_router.get("/context/{session_id}")
async def get_user_context(session_id: str):
    """Obtener contexto del usuario"""
    try:
        context = db_manager.get_user_context(session_id)
        return {
            "session_id": session_id,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo contexto: {str(e)}")

@chat_router.post("/analyze")
async def analyze_message(message_data: ChatMessage):
    """Analizar mensaje sin generar respuesta"""
    try:
        # Analizar contexto con ML
        context = await ml_service.analyze_context(message_data.message)
        
        # Analizar sentimiento
        sentiment = await ai_service.analyze_sentiment(message_data.message)
        
        # Extraer palabras clave
        keywords = await ai_service.extract_keywords(message_data.message)
        
        return {
            "message": message_data.message,
            "analysis": {
                "context": context,
                "sentiment": sentiment,
                "keywords": keywords
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analizando mensaje: {str(e)}")

@chat_router.post("/feedback")
async def submit_feedback(feedback_data: Dict[str, Any]):
    """Enviar feedback sobre la respuesta"""
    try:
        session_id = feedback_data.get("session_id")
        conversation_id = feedback_data.get("conversation_id")
        rating = feedback_data.get("rating")  # 1-5
        comment = feedback_data.get("comment", "")
        
        # Aquí podrías guardar el feedback en la base de datos
        # para mejorar el modelo en el futuro
        
        return {
            "message": "Feedback recibido correctamente",
            "session_id": session_id,
            "rating": rating
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando feedback: {str(e)}")

@chat_router.get("/stats/{session_id}")
async def get_session_stats(session_id: str):
    """Obtener estadísticas de la sesión"""
    try:
        history = db_manager.get_conversation_history(session_id, limit=100)
        
        if not history:
            return {
                "session_id": session_id,
                "message_count": 0,
                "avg_confidence": 0,
                "topics": [],
                "emotions": []
            }
        
        # Calcular estadísticas
        message_count = len(history)
        avg_confidence = sum(msg.get("confidence", 0) for msg in history) / message_count
        
        # Extraer temas y emociones
        all_topics = []
        all_emotions = []
        
        for msg in history:
            if msg.get("context"):
                context = msg["context"]
                if context.get("keywords"):
                    all_topics.extend(context["keywords"])
                if context.get("emotions", {}).get("emotions"):
                    all_emotions.extend(context["emotions"]["emotions"])
        
        # Contar frecuencia
        from collections import Counter
        topic_counts = Counter(all_topics)
        emotion_counts = Counter(all_emotions)
        
        return {
            "session_id": session_id,
            "message_count": message_count,
            "avg_confidence": round(avg_confidence, 2),
            "topics": [{"topic": topic, "count": count} for topic, count in topic_counts.most_common(5)],
            "emotions": [{"emotion": emotion, "count": count} for emotion, count in emotion_counts.most_common(5)]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")
