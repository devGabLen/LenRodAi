"""
WebSocket endpoints para chat en tiempo real
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

from src.services.ai_service import AIService
from src.services.ml_service import MLService
from src.core.database import db_manager

# Crear router
websocket_router = APIRouter()

# Instancias de servicios
ai_service = AIService()
ml_service = MLService()

# Conexiones WebSocket activas
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_sessions: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if session_id:
            self.connection_sessions[websocket] = session_id
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_sessions:
            del self.connection_sessions[websocket]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remover conexiones que fallan
                self.disconnect(connection)

# Instancia del gestor de conexiones
manager = ConnectionManager()

@websocket_router.websocket("/chat")
async def websocket_chat(websocket: WebSocket, session_id: str = None):
    """WebSocket para chat en tiempo real"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Procesar mensaje
            response = await process_websocket_message(message_data, websocket)
            
            # Enviar respuesta
            await manager.send_personal_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        manager.disconnect(websocket)

async def process_websocket_message(message_data: Dict[str, Any], websocket: WebSocket) -> Dict[str, Any]:
    """Procesar mensaje del WebSocket"""
    try:
        message_type = message_data.get("type", "message")
        user_message = message_data.get("message", "")
        session_id = message_data.get("session_id") or manager.connection_sessions.get(websocket)
        
        if message_type == "message":
            return await handle_chat_message(user_message, session_id, message_data)
        elif message_type == "typing":
            return await handle_typing_indicator(message_data)
        elif message_type == "context_update":
            return await handle_context_update(message_data, session_id)
        else:
            return {
                "type": "error",
                "message": f"Tipo de mensaje no reconocido: {message_type}",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error procesando mensaje: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def handle_chat_message(user_message: str, session_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manejar mensaje de chat"""
    try:
        # Obtener historial de conversación
        conversation_history = db_manager.get_conversation_history(session_id, limit=10) if session_id else []
        
        # Analizar contexto con ML
        context = await ml_service.analyze_context(user_message, conversation_history)
        
        # Generar respuesta con IA
        ai_response = await ai_service.generate_response(
            user_message,
            conversation_history,
            context
        )
        
        # Guardar conversación si hay session_id
        if session_id:
            db_manager.save_conversation(
                session_id=session_id,
                user_message=user_message,
                ai_response=ai_response["message"],
                context=context,
                confidence=ai_response.get("confidence", 0.8)
            )
        
        return {
            "type": "response",
            "message": ai_response["message"],
            "session_id": session_id,
            "confidence": ai_response.get("confidence", 0.8),
            "context": context,
            "timestamp": ai_response.get("timestamp", datetime.now().isoformat()),
            "model_info": {
                "model": ai_response.get("model", "unknown"),
                "usage": ai_response.get("usage", {})
            }
        }
        
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error procesando mensaje: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def handle_typing_indicator(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manejar indicador de escritura"""
    is_typing = message_data.get("is_typing", False)
    user_id = message_data.get("user_id", "unknown")
    
    return {
        "type": "typing",
        "is_typing": is_typing,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat()
    }

async def handle_context_update(message_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
    """Manejar actualización de contexto"""
    try:
        if not session_id:
            return {
                "type": "error",
                "message": "Session ID requerido para actualizar contexto",
                "timestamp": datetime.now().isoformat()
            }
        
        # Actualizar contexto del usuario
        db_manager.update_user_context(
            session_id=session_id,
            preferences=message_data.get("preferences"),
            topics=message_data.get("topics"),
            personality=message_data.get("personality")
        )
        
        return {
            "type": "context_updated",
            "message": "Contexto actualizado correctamente",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error actualizando contexto: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@websocket_router.websocket("/admin")
async def websocket_admin(websocket: WebSocket):
    """WebSocket para administración en tiempo real"""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Procesar comandos de administración
            response = await handle_admin_command(message_data)
            await manager.send_personal_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error en WebSocket admin: {e}")
        manager.disconnect(websocket)

async def handle_admin_command(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Manejar comandos de administración"""
    try:
        command = message_data.get("command")
        
        if command == "get_stats":
            return await get_admin_stats()
        elif command == "get_connections":
            return await get_connection_stats()
        elif command == "broadcast":
            message = message_data.get("message", "")
            await manager.broadcast(json.dumps({
                "type": "admin_broadcast",
                "message": message,
                "timestamp": datetime.now().isoformat()
            }))
            return {
                "type": "broadcast_sent",
                "message": "Mensaje enviado a todas las conexiones",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "type": "error",
                "message": f"Comando no reconocido: {command}",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error procesando comando: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

async def get_admin_stats() -> Dict[str, Any]:
    """Obtener estadísticas de administración"""
    return {
        "type": "admin_stats",
        "stats": {
            "active_connections": len(manager.active_connections),
            "total_sessions": len(manager.connection_sessions),
            "timestamp": datetime.now().isoformat()
        }
    }

async def get_connection_stats() -> Dict[str, Any]:
    """Obtener estadísticas de conexiones"""
    return {
        "type": "connection_stats",
        "connections": [
            {
                "session_id": session_id,
                "connected_at": datetime.now().isoformat()
            }
            for session_id in manager.connection_sessions.values()
        ],
        "timestamp": datetime.now().isoformat()
    }
