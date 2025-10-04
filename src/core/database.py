"""
Configuración de base de datos
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.core.config import settings

class DatabaseManager:
    """Gestor de base de datos para el chatbot"""
    
    def __init__(self):
        self.db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        self.init_db()
    
    def init_db(self):
        """Inicializar base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de conversaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                context TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de sesiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        """)
        
        # Tabla de contexto de usuario
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_context (
                session_id TEXT PRIMARY KEY,
                preferences TEXT,
                topics TEXT,
                personality_profile TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, session_id: str, user_message: str, 
                         ai_response: str, context: Dict = None, 
                         confidence: float = 0.0) -> int:
        """Guardar conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations 
            (session_id, user_message, ai_response, context, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user_message, ai_response, 
              json.dumps(context) if context else None, confidence))
        
        conversation_id = cursor.lastrowid
        
        # Actualizar sesión
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (id, last_activity, message_count)
            VALUES (?, CURRENT_TIMESTAMP, 
                   COALESCE((SELECT message_count FROM sessions WHERE id = ?), 0) + 1)
        """, (session_id, session_id))
        
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Obtener historial de conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_message, ai_response, context, confidence, timestamp
            FROM conversations 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (session_id, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "user_message": row[0],
                "ai_response": row[1],
                "context": json.loads(row[2]) if row[2] else None,
                "confidence": row[3],
                "timestamp": row[4]
            })
        
        conn.close()
        return results
    
    def update_user_context(self, session_id: str, preferences: Dict = None,
                           topics: List[str] = None, personality: Dict = None):
        """Actualizar contexto del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_context 
            (session_id, preferences, topics, personality_profile)
            VALUES (?, ?, ?, ?)
        """, (session_id, 
              json.dumps(preferences) if preferences else None,
              json.dumps(topics) if topics else None,
              json.dumps(personality) if personality else None))
        
        conn.commit()
        conn.close()
    
    def get_user_context(self, session_id: str) -> Dict:
        """Obtener contexto del usuario"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT preferences, topics, personality_profile
            FROM user_context 
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "preferences": json.loads(row[0]) if row[0] else {},
                "topics": json.loads(row[1]) if row[1] else [],
                "personality": json.loads(row[2]) if row[2] else {}
            }
        
        return {"preferences": {}, "topics": [], "personality": {}}

# Instancia global del gestor de base de datos
db_manager = DatabaseManager()

async def init_database():
    """Inicializar base de datos"""
    db_manager.init_db()
    print("✅ Base de datos inicializada")
