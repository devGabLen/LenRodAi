"""
AI Chat Assistant - Versión Optimizada para Desarrollo Rápido
"""

import os
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from datetime import datetime
import asyncio

# Crear aplicación FastAPI (sin eventos de startup/shutdown)
app = FastAPI(
    title="AI Chat Assistant",
    version="1.0.0",
    docs_url="/api/docs"
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

# Almacenar conexiones WebSocket activas
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

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
        
        # Respuesta rápida simulada
        ai_response = {
            "message": f"¡Hola! Recibí tu mensaje: '{user_message}'. Esta es una respuesta rápida de prueba.",
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
            "model": "fast-demo"
        }
        
        return {
            "response": ai_response["message"],
            "session_id": "fast-session",
            "confidence": ai_response["confidence"],
            "context": {"demo": True, "fast": True},
            "timestamp": ai_response["timestamp"],
            "model_info": {"model": ai_response["model"]}
        }
        
    except Exception as e:
        return {
            "error": f"Error: {str(e)}",
            "message": "Lo siento, hubo un error."
        }

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para chat en tiempo real"""
    await manager.connect(websocket)
    try:
        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Procesar el mensaje
            if message_data.get("type") == "message":
                user_message = message_data.get("message", "")
                session_id = message_data.get("session_id", "default")
                
                # Simular respuesta de IA
                ai_response = {
                    "type": "response",
                    "message": f"¡Hola! Recibí tu mensaje: '{user_message}'. Esta es una respuesta rápida desde WebSocket.",
                    "confidence": 0.9,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "model_info": {"model": "fast-websocket-demo"}
                }
                
                # Enviar respuesta al cliente
                await manager.send_personal_message(json.dumps(ai_response), websocket)
                
            elif message_data.get("type") == "ping":
                # Responder al ping
                pong_response = {"type": "pong", "timestamp": datetime.now().isoformat()}
                await manager.send_personal_message(json.dumps(pong_response), websocket)
                
            elif message_data.get("type") == "typing":
                # Manejar indicador de escritura
                typing_response = {
                    "type": "typing",
                    "is_typing": message_data.get("is_typing", False),
                    "timestamp": datetime.now().isoformat()
                }
                await manager.send_personal_message(json.dumps(typing_response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    # Configuración optimizada para desarrollo rápido
    uvicorn.run(
        "main_fast:app",
        host="127.0.0.1",  # Más rápido que 0.0.0.0
        port=8000,
        reload=False,      # Sin auto-reload para ser más rápido
        log_level="warning",  # Menos logs = más rápido
        access_log=False   # Sin logs de acceso = más rápido
    )
