"""
AI Chat Assistant - Versión Inteligente con OpenAI y Monitoreo de Tokens
Detecta automáticamente cuando los tokens se acaban y muestra alertas
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
from datetime import datetime
import openai
import asyncio

# Cargar configuración
load_dotenv("config_temp.env")

# Crear aplicación FastAPI
app = FastAPI(
    title="AI Chat Assistant - Smart OpenAI",
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

# Configurar OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Estado del sistema
class TokenMonitor:
    def __init__(self):
        self.openai_available = True
        self.last_error = None
        self.token_status = "unknown"
        self.usage_count = 0
        self.error_count = 0
        
    def check_openai_status(self):
        """Verificar estado de OpenAI"""
        if not openai.api_key or openai.api_key == "your_openai_api_key_here":
            self.openai_available = False
            self.token_status = "no_api_key"
            return False
        
        # Si hemos tenido muchos errores recientes, asumir que no hay tokens
        if self.error_count > 3:
            self.openai_available = False
            self.token_status = "quota_exceeded"
            return False
            
        return True
    
    def record_success(self):
        """Registrar uso exitoso"""
        self.usage_count += 1
        self.error_count = 0
        self.token_status = "available"
        self.openai_available = True
        
    def record_error(self, error):
        """Registrar error"""
        self.error_count += 1
        self.last_error = str(error)
        
        if "quota" in str(error).lower() or "rate limit" in str(error).lower():
            self.token_status = "quota_exceeded"
            self.openai_available = False
        elif "api key" in str(error).lower():
            self.token_status = "invalid_api_key"
            self.openai_available = False
        else:
            self.token_status = "error"

# Instancia global del monitor
token_monitor = TokenMonitor()

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
    token_monitor.check_openai_status()
    
    return {
        "status": "healthy",
        "message": "AI Chat Assistant is running",
        "version": "1.0.0",
        "openai_status": {
            "available": token_monitor.openai_available,
            "status": token_monitor.token_status,
            "usage_count": token_monitor.usage_count,
            "error_count": token_monitor.error_count,
            "last_error": token_monitor.last_error
        }
    }

@app.post("/api/chat/send")
async def send_message(request: Request):
    """Enviar mensaje al chatbot con detección inteligente de tokens"""
    try:
        data = await request.json()
        user_message = data.get("message", "")
        
        # Verificar estado de OpenAI
        if not token_monitor.check_openai_status():
            return create_fallback_response(user_message, token_monitor.token_status)
        
        try:
            # Intentar usar OpenAI (versión compatible)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente de IA inteligente, sofisticado y profesional. Responde en español de manera útil, precisa y amigable."},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Éxito con OpenAI
            token_monitor.record_success()
            ai_message = response.choices[0].message.content
            
            return {
                "response": ai_message,
                "session_id": "openai-session",
                "confidence": 0.9,
                "context": {
                    "openai": True, 
                    "model": "gpt-3.5-turbo",
                    "tokens_used": response.usage.total_tokens,
                    "status": "openai_success"
                },
                "timestamp": datetime.now().isoformat(),
                "model_info": {
                    "model": "gpt-3.5-turbo",
                    "usage": response.usage.__dict__
                }
            }
            
        except Exception as openai_error:
            # Error con OpenAI - registrar y usar fallback
            token_monitor.record_error(openai_error)
            return create_fallback_response(user_message, token_monitor.token_status, str(openai_error))
        
    except Exception as e:
        return {
            "error": f"Error: {str(e)}",
            "message": "Lo siento, hubo un error procesando tu mensaje."
        }

def create_fallback_response(user_message: str, status: str, error_detail: str = None):
    """Crear respuesta de respaldo cuando OpenAI no está disponible"""
    
    if status == "quota_exceeded":
        response_text = f"""
🚨 **TOKENS AGOTADOS** 🚨

Tu mensaje: "{user_message}"

**Estado:** Has excedido tu cuota de OpenAI
**Solución:** 
1. Ve a https://platform.openai.com/account/billing
2. Agrega créditos a tu cuenta
3. El chat volverá automáticamente a usar OpenAI

**Respuesta simulada:** ¡Hola! Recibí tu mensaje pero estoy en modo de respaldo porque se agotaron los tokens de OpenAI. Una vez que agregues créditos, podré darte respuestas más inteligentes.
        """
    elif status == "invalid_api_key":
        response_text = f"""
🔑 **API KEY INVÁLIDA** 🔑

Tu mensaje: "{user_message}"

**Estado:** La API key de OpenAI no es válida
**Solución:** 
1. Verifica tu API key en config_temp.env
2. Obtén una nueva key en https://platform.openai.com/api-keys

**Respuesta simulada:** ¡Hola! Recibí tu mensaje pero hay un problema con la configuración de OpenAI.
        """
    elif status == "no_api_key":
        response_text = f"""
⚙️ **CONFIGURACIÓN REQUERIDA** ⚙️

Tu mensaje: "{user_message}"

**Estado:** No hay API key configurada
**Solución:** 
1. Configura OPENAI_API_KEY en config_temp.env
2. Reinicia el servidor

**Respuesta simulada:** ¡Hola! Recibí tu mensaje pero necesito configurar OpenAI para darte respuestas inteligentes.
        """
    else:
        response_text = f"""
⚠️ **MODO DE RESPALDO** ⚠️

Tu mensaje: "{user_message}"

**Estado:** OpenAI temporalmente no disponible
**Error:** {error_detail or "Error desconocido"}

**Respuesta simulada:** ¡Hola! Recibí tu mensaje pero estoy en modo de respaldo. Una vez que se resuelva el problema con OpenAI, podré darte respuestas más inteligentes.
        """
    
    return {
        "response": response_text,
        "session_id": "fallback-session",
        "confidence": 0.3,
        "context": {
            "fallback": True,
            "openai_status": status,
            "error_detail": error_detail,
            "status": "fallback_mode"
        },
        "timestamp": datetime.now().isoformat(),
        "model_info": {
            "model": "fallback-simulator",
            "openai_available": False
        }
    }

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para chat en tiempo real con detección de tokens"""
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
                
                # Verificar estado de OpenAI
                if not token_monitor.check_openai_status():
                    # Usar respuesta de respaldo
                    fallback_response = create_fallback_response(user_message, token_monitor.token_status)
                    ai_response = {
                        "type": "response",
                        "message": fallback_response["response"],
                        "confidence": fallback_response["confidence"],
                        "timestamp": fallback_response["timestamp"],
                        "session_id": session_id,
                        "context": fallback_response["context"],
                        "model_info": fallback_response["model_info"]
                    }
                else:
                    try:
                        # Intentar usar OpenAI (versión compatible)
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "Eres un asistente de IA inteligente. Responde en español de manera útil y amigable."},
                                {"role": "user", "content": user_message}
                            ],
                            max_tokens=500,
                            temperature=0.7
                        )
                        
                        # Éxito con OpenAI
                        token_monitor.record_success()
                        ai_response = {
                            "type": "response",
                            "message": response.choices[0].message.content,
                            "confidence": 0.9,
                            "timestamp": datetime.now().isoformat(),
                            "session_id": session_id,
                            "context": {
                                "openai": True,
                                "model": "gpt-3.5-turbo",
                                "tokens_used": response.usage.total_tokens
                            },
                            "model_info": {
                                "model": "gpt-3.5-turbo",
                                "usage": response.usage.__dict__
                            }
                        }
                        
                    except Exception as openai_error:
                        # Error con OpenAI
                        token_monitor.record_error(openai_error)
                        fallback_response = create_fallback_response(user_message, token_monitor.token_status, str(openai_error))
                        ai_response = {
                            "type": "response",
                            "message": fallback_response["response"],
                            "confidence": fallback_response["confidence"],
                            "timestamp": fallback_response["timestamp"],
                            "session_id": session_id,
                            "context": fallback_response["context"],
                            "model_info": fallback_response["model_info"]
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

@app.get("/api/token-status")
async def get_token_status():
    """Endpoint para verificar estado de tokens"""
    token_monitor.check_openai_status()
    
    return {
        "openai_available": token_monitor.openai_available,
        "status": token_monitor.token_status,
        "usage_count": token_monitor.usage_count,
        "error_count": token_monitor.error_count,
        "last_error": token_monitor.last_error,
        "message": get_status_message(token_monitor.token_status)
    }

def get_status_message(status: str) -> str:
    """Obtener mensaje descriptivo del estado"""
    messages = {
        "available": "✅ OpenAI disponible - Tokens disponibles",
        "quota_exceeded": "🚨 Tokens agotados - Agrega créditos en OpenAI",
        "invalid_api_key": "🔑 API key inválida - Verifica tu configuración",
        "no_api_key": "⚙️ API key no configurada - Configura OPENAI_API_KEY",
        "error": "⚠️ Error temporal - Reintentando...",
        "unknown": "❓ Estado desconocido - Verificando..."
    }
    return messages.get(status, "❓ Estado desconocido")

if __name__ == "__main__":
    print("=" * 60)
    print("AI Chat Assistant - Smart OpenAI Version")
    print("=" * 60)
    print("Caracteristicas:")
    print("   • Deteccion automatica de tokens agotados")
    print("   • Alertas cuando se acaban los creditos")
    print("   • Modo de respaldo automatico")
    print("   • Monitoreo de uso de OpenAI")
    print("=" * 60)
    
    # Verificar configuración inicial
    token_monitor.check_openai_status()
    
    if token_monitor.openai_available:
        print("OpenAI configurado y disponible")
    else:
        print(f"OpenAI no disponible: {token_monitor.token_status}")
        print("   El chat funcionara en modo de respaldo")
    
    print("=" * 60)
    print("Abriendo en: http://localhost:8002")
    print("Estado de tokens: http://localhost:8002/api/token-status")
    print("=" * 60)
    
    uvicorn.run(
        "main_openai_smart:app",
        host="127.0.0.1",
        port=8002,
        reload=False,
        log_level="warning",
        access_log=False
    )
