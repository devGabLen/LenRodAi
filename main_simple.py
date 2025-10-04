"""
AI Chat Assistant - Versión Simplificada
Asistente de chat inteligente básico
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
from datetime import datetime

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

# Conexiones WebSocket activas
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Inicializar la aplicación"""
    print("Iniciando AI Chat Assistant...")
    print("Aplicacion iniciada correctamente")

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar la aplicación"""
    print("Cerrando AI Chat Assistant...")
    print("Aplicacion cerrada correctamente")

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

@app.post("/api/chat/send")
async def send_message(request: Request):
    """Enviar mensaje al chatbot"""
    try:
        data = await request.json()
        user_message = data.get("message", "")
        session_id = data.get("session_id", "default")
        
        # Respuesta simulada (sin OpenAI por ahora)
        ai_response = {
            "message": f"¡Hola! Recibí tu mensaje: '{user_message}'. Esta es una respuesta de prueba. Para usar OpenAI, configura tu API key.",
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
            "model": "demo",
            "usage": {"total_tokens": 50}
        }
        
        return {
            "response": ai_response["message"],
            "session_id": session_id,
            "confidence": ai_response["confidence"],
            "context": {"demo": True},
            "timestamp": ai_response["timestamp"],
            "model_info": {
                "model": ai_response["model"],
                "usage": ai_response["usage"]
            }
        }
        
    except Exception as e:
        return {
            "error": f"Error procesando mensaje: {str(e)}",
            "message": "Lo siento, hubo un error procesando tu mensaje."
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
            
            # Procesar mensaje
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
    """Procesar mensaje de chat"""
    try:
        user_message = message_data.get("message", "")
        session_id = message_data.get("session_id", "default")
        
        # Respuesta simulada
        ai_response = {
            "message": f"¡Hola! Recibí tu mensaje: '{user_message}'. Esta es una respuesta de prueba via WebSocket.",
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "type": "response",
            "message": ai_response["message"],
            "confidence": ai_response["confidence"],
            "context": {"demo": True},
            "timestamp": ai_response["timestamp"]
        }
        
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error procesando mensaje: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
