import os
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
from datetime import datetime
import openai
import asyncio

load_dotenv("config_temp.env")

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI(
    title="AI Chat Assistant - Smart Version",
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

class TokenMonitor:
    def __init__(self):
        self.openai_available = True
        self.last_error = None
        self.error_count = 0
        self.last_check = None
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
        
    def check_openai_availability(self):
        self.last_check = datetime.now()
        return self.openai_available
    
    def handle_openai_error(self, error):
        self.last_error = str(error)
        self.error_count += 1
        self.consecutive_errors += 1
        
        if "quota" in str(error).lower() or "rate limit" in str(error).lower():
            self.openai_available = False
            print(f"OpenAI no disponible - Error de cuota: {error}")
            return False
        
        if self.consecutive_errors >= self.max_consecutive_errors:
            self.openai_available = False
            print(f"OpenAI no disponible - Demasiados errores consecutivos: {self.consecutive_errors}")
            return False
        
        return True
    
    def reset_errors(self):
        self.consecutive_errors = 0
        if self.error_count > 0:
            self.openai_available = True
            print("Errores de OpenAI reseteados - Disponible nuevamente")
    
    def get_status(self):
        return {
            "openai_available": self.openai_available,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "consecutive_errors": self.consecutive_errors,
            "last_check": self.last_check.isoformat() if self.last_check else None
        }

token_monitor = TokenMonitor()

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

def create_fallback_response(user_message: str, session_id: str = "default"):
    fallback_responses = [
        f"Entiendo tu mensaje: '{user_message}'. Actualmente estoy usando respuestas simuladas porque mi API de OpenAI no está disponible. ¡Pero sigo aquí para ayudarte!",
        f"¡Hola! Recibí: '{user_message}'. Estoy funcionando en modo respaldo mientras se resuelve la conexión con OpenAI.",
        f"Perfecto, capté tu mensaje: '{user_message}'. Aunque no tengo acceso a OpenAI en este momento, puedo simular respuestas inteligentes para ti.",
        f"Gracias por tu mensaje: '{user_message}'. Estoy operando con respuestas de respaldo hasta que se restaure el servicio de IA.",
        f"¡Muy bien! Tu mensaje '{user_message}' fue recibido. Funcionando en modo de respaldo con respuestas simuladas."
    ]
    
    import random
    response_text = random.choice(fallback_responses)
    
    return {
        "response": response_text,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.7,
        "context": {
            "fallback_mode": True,
            "openai_available": False,
            "message_count": 1,
            "session_duration": 0,
            "user_preferences": {"language": "es"}
        },
        "model_info": {
            "model": "fallback-simulator",
            "version": "1.0.0",
            "note": "Respuesta simulada - OpenAI no disponible"
        },
        "session_id": session_id,
        "warning": "Los tokens de OpenAI se han agotado o hay un problema de conexión. Usando respuestas simuladas."
    }

async def call_openai_api(message: str, session_id: str = "default"):
    try:
        if not token_monitor.check_openai_availability():
            return None
        
        response = openai.ChatCompletion.create(
            model=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": "Eres un asistente de IA útil y amigable. Responde en español de manera clara y concisa."},
                {"role": "user", "content": message}
            ],
            max_tokens=int(os.getenv("MAX_TOKENS", 1000)),
            temperature=float(os.getenv("TEMPERATURE", 0.7))
        )
        
        token_monitor.reset_errors()
        
        ai_response = response.choices[0].message.content
        
        return {
            "response": ai_response,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.9,
            "context": {
                "openai_available": True,
                "message_count": 1,
                "session_duration": 0,
                "user_preferences": {"language": "es"}
            },
            "model_info": {
                "model": os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
                "version": "1.0.0",
                "usage": response.usage
            },
            "session_id": session_id
        }
        
    except Exception as error:
        print(f"Error llamando a OpenAI: {error}")
        
        if not token_monitor.handle_openai_error(error):
            return None
        
        raise error

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections),
        "openai_status": token_monitor.get_status()
    }

@app.get("/api/token-status")
async def get_token_status():
    return {
        "status": token_monitor.get_status(),
        "message": "OpenAI no disponible - Tokens agotados" if not token_monitor.openai_available else "OpenAI disponible",
        "timestamp": datetime.now().isoformat()
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
        
        try:
            response_data = await call_openai_api(message, session_id)
            
            if response_data:
                return response_data
            else:
                print("OpenAI no disponible, usando respuesta de respaldo")
                return create_fallback_response(message, session_id)
                
        except Exception as error:
            print(f"Error en API de OpenAI: {error}")
            return create_fallback_response(message, session_id)
        
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
                
                try:
                    response_data = await call_openai_api(user_message, session_id)
                    
                    if response_data:
                        ai_response = {
                            "type": "response",
                            "message": response_data["response"],
                            "confidence": response_data["confidence"],
                            "timestamp": response_data["timestamp"],
                            "session_id": session_id,
                            "model_info": response_data["model_info"],
                            "context": response_data["context"]
                        }
                    else:
                        fallback_data = create_fallback_response(user_message, session_id)
                        ai_response = {
                            "type": "response",
                            "message": fallback_data["response"],
                            "confidence": fallback_data["confidence"],
                            "timestamp": fallback_data["timestamp"],
                            "session_id": session_id,
                            "model_info": fallback_data["model_info"],
                            "context": fallback_data["context"],
                            "warning": fallback_data["warning"]
                        }
                    
                    await manager.send_personal_message(json.dumps(ai_response), websocket)
                    
                except Exception as error:
                    print(f"Error en WebSocket OpenAI: {error}")
                    fallback_data = create_fallback_response(user_message, session_id)
                    ai_response = {
                        "type": "response",
                        "message": fallback_data["response"],
                        "confidence": fallback_data["confidence"],
                        "timestamp": fallback_data["timestamp"],
                        "session_id": session_id,
                        "model_info": fallback_data["model_info"],
                        "context": fallback_data["context"],
                        "warning": fallback_data["warning"]
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
        "main_openai_smart:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )