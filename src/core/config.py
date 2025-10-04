"""
Configuración de la aplicación
"""

import os
from typing import Optional

class Settings:
    """Configuración de la aplicación"""
    
    def __init__(self):
        # OpenAI
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        self.MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1000"))
        self.TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
        
        # FastAPI
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
        
        # Base de datos
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")
        
        # Seguridad
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
        
        # Modelo ML
        self.ML_MODEL_PATH: str = os.getenv("ML_MODEL_PATH", "./models/")
        self.SENTENCE_TRANSFORMER_MODEL: str = os.getenv("SENTENCE_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")

# Instancia global de configuración
settings = Settings()
