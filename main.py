"""
AI Chat Assistant - Main Application
Asistente de chat inteligente con procesamiento de lenguaje natural
"""

import os
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
import asyncio
from typing import List, Dict, Any

from src.api.chat import chat_router
from src.api.websocket import websocket_router
from src.core.config import settings
from src.core.database import init_database
from src.services.ai_service import AIService
from src.services.ml_service import MLService

# Cargar variables de entorno
load_dotenv()

# Crear aplicación FastAPI
app = FastAPI(
    title="AI Chat Assistant",
    description="Asistente de chat inteligente con procesamiento de lenguaje natural",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="templates")

# Incluir routers
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(websocket_router, prefix="/ws", tags=["websocket"])

# Inicializar servicios
ai_service = AIService()
ml_service = MLService()

# Conexiones WebSocket activas
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Inicializar la aplicación"""
    print("🚀 Iniciando AI Chat Assistant...")
    await init_database()
    await ai_service.initialize()
    await ml_service.initialize()
    print("✅ Aplicación iniciada correctamente")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar la aplicación"""
    print("🛑 Cerrando AI Chat Assistant...")
    await ai_service.cleanup()
    await ml_service.cleanup()
    print("✅ Aplicación cerrada correctamente")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Página principal"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Verificar estado de la aplicación"""
    return {
        "status": "healthy",
        "message": "AI Chat Assistant is running",
        "version": "1.0.0"
    }

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para chat en tiempo real"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Procesar mensaje con IA
            response = await process_chat_message(message_data)
            
            # Enviar respuesta
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

async def process_chat_message(message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Procesar mensaje de chat con IA"""
    try:
        user_message = message_data.get("message", "")
        conversation_history = message_data.get("history", [])
        
        # Procesar con modelo de ML para contexto
        context = await ml_service.analyze_context(user_message, conversation_history)
        
        # Generar respuesta con OpenAI
        ai_response = await ai_service.generate_response(
            user_message, 
            conversation_history, 
            context
        )
        
        return {
            "type": "response",
            "message": ai_response["message"],
            "confidence": ai_response.get("confidence", 0.8),
            "context": context,
            "timestamp": ai_response.get("timestamp")
        }
        
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error procesando mensaje: {str(e)}",
            "timestamp": None
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
