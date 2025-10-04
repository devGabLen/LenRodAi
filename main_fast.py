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

app = FastAPI(
    title="AI Chat Assistant",
    version="1.0.0",
    docs_url="/api/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Conexión WebSocket establecida. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"Conexión WebSocket cerrada. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error enviando mensaje personal: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error en broadcast: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections)
    }

@app.post("/api/chat/send")
async def send_message(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "")
        session_id = body.get("session_id", "default")
        
        if not message.strip():
            return {"error": "El mensaje no puede estar vacío"}
        
        if len(message) > 2000:
            return {"error": "El mensaje es demasiado largo"}
        
        ai_response = f"¡Hola! Recibí tu mensaje: '{message}'. Esta es una respuesta rápida desde FastAPI."
        
        response_data = {
            "response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.9,
            "context": {
                "message_count": 1,
                "session_duration": 0,
                "user_preferences": {"language": "es"}
            },
            "model_info": {
                "model": "fast-demo",
                "version": "1.0.0"
            },
            "session_id": session_id
        }
        
        return response_data
        
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        return {"error": "Error interno del servidor"}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                user_message = message_data.get("message", "")
                session_id = message_data.get("session_id", "default")
                
                ai_response = {
                    "type": "response",
                    "message": f"¡Hola! Recibí tu mensaje: '{user_message}'. Esta es una respuesta rápida desde WebSocket.",
                    "confidence": 0.9,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "model_info": {"model": "fast-websocket-demo"}
                }
                
                await manager.send_personal_message(json.dumps(ai_response), websocket)
                
            elif message_data.get("type") == "ping":
                pong_response = {"type": "pong", "timestamp": datetime.now().isoformat()}
                await manager.send_personal_message(json.dumps(pong_response), websocket)
                
            elif message_data.get("type") == "typing":
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
    uvicorn.run(
        "main_fast:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )