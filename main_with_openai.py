import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
from datetime import datetime
import openai

load_dotenv("config_temp.env")

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

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "AI Chat Assistant is running",
        "version": "1.0.0",
        "openai_configured": bool(openai.api_key and openai.api_key != "your_openai_api_key_here")
    }

@app.post("/api/chat/send")
async def send_message(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "")
        
        if not openai.api_key or openai.api_key == "your_openai_api_key_here":
            return {
                "response": "OpenAI no está configurado. Por favor, configura tu API key en config_temp.env",
                "session_id": "demo-session",
                "confidence": 0.0,
                "context": {"demo": True, "openai_configured": False},
                "timestamp": datetime.now().isoformat(),
                "model_info": {"model": "demo"}
            }
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente de IA inteligente, sofisticado y profesional. Responde en español de manera útil, precisa y amigable."},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_message = response.choices[0].message.content
            
            return {
                "response": ai_message,
                "session_id": "openai-session",
                "confidence": 0.9,
                "context": {"openai": True, "model": "gpt-3.5-turbo"},
                "timestamp": datetime.now().isoformat(),
                "model_info": {
                    "model": "gpt-3.5-turbo",
                    "usage": response.usage.__dict__
                }
            }
            
        except Exception as openai_error:
            return {
                "response": f"Error con OpenAI: {str(openai_error)}. Verifica tu API key.",
                "session_id": "error-session",
                "confidence": 0.0,
                "context": {"error": True},
                "timestamp": datetime.now().isoformat(),
                "model_info": {"model": "error"}
            }
        
    except Exception as e:
        return {
            "error": f"Error: {str(e)}",
            "message": "Lo siento, hubo un error procesando tu mensaje."
        }

if __name__ == "__main__":
    print("Iniciando AI Chat Assistant con OpenAI...")
    print("Abriendo en: http://localhost:8001")
    print("OpenAI configurado:", bool(openai.api_key and openai.api_key != "your_openai_api_key_here"))
    
    uvicorn.run(
        "main_with_openai:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        log_level="warning",
        access_log=False
    )