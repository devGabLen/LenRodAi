# AI Chat Assistant

Un asistente de chat inteligente con procesamiento de lenguaje natural, integración de APIs y aprendizaje automático para respuestas contextuales.

## Características

- **Inteligencia Artificial Avanzada**: Integración con OpenAI GPT para respuestas inteligentes y contextuales
- **Procesamiento de Lenguaje Natural**: Análisis de sentimientos, extracción de entidades y clasificación de intenciones
- **Interfaz Elegante**: Diseño moderno, profesional y sofisticado con tema claro/oscuro
- **Tiempo Real**: Comunicación WebSocket para respuestas instantáneas
- **Responsive**: Optimizado para dispositivos móviles y escritorio
- **Seguro**: Manejo seguro de datos y configuraciones
- **Análisis Avanzado**: Estadísticas de conversación y métricas de confianza

## Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido para APIs
- **OpenAI**: Integración con modelos de lenguaje avanzados
- **TensorFlow**: Machine Learning para procesamiento de lenguaje natural
- **SQLite**: Base de datos ligera para almacenamiento
- **WebSockets**: Comunicación en tiempo real

### Frontend
- **HTML5/CSS3**: Estructura y estilos modernos
- **JavaScript ES6+**: Lógica de cliente avanzada
- **Font Awesome**: Iconografía profesional
- **Google Fonts**: Tipografía elegante (Inter)

### Machine Learning
- **Sentence Transformers**: Embeddings semánticos
- **spaCy**: Procesamiento de lenguaje natural
- **NLTK**: Herramientas de análisis de texto
- **scikit-learn**: Algoritmos de clasificación

## Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Clave API de OpenAI

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/ai-chat-bot.git
cd ai-chat-bot
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copiar archivo de configuración
cp config.env .env

# Editar .env con tus configuraciones
# Especialmente importante: OPENAI_API_KEY
```

### 5. Descargar modelos de spaCy (opcional)
```bash
python -m spacy download es_core_news_sm
```

## Configuración

### Variables de Entorno

Edita el archivo `.env` con tus configuraciones:

```env
# OpenAI Configuration
OPENAI_API_KEY=tu_clave_api_aqui

# FastAPI Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Model Configuration
MODEL_NAME=gpt-3.5-turbo
MAX_TOKENS=1000
TEMPERATURE=0.7

# Database Configuration
DATABASE_URL=sqlite:///./chatbot.db

# Security
SECRET_KEY=tu_clave_secreta_aqui

# ML Model Configuration
ML_MODEL_PATH=./models/
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

### Obtener Clave API de OpenAI

1. Visita [OpenAI Platform](https://platform.openai.com/)
2. Crea una cuenta o inicia sesión
3. Ve a "API Keys" en tu dashboard
4. Crea una nueva clave API
5. Copia la clave y pégala en tu archivo `.env`

## Uso

### Iniciar el servidor
```bash
python main.py
```

### Acceder a la aplicación
- **Interfaz web**: http://localhost:8000
- **Documentación API**: http://localhost:8000/api/docs
- **Documentación ReDoc**: http://localhost:8000/api/redoc

### Uso con Docker (opcional)
```bash
# Construir imagen
docker build -t ai-chat-assistant .

# Ejecutar contenedor
docker run -p 8000:8000 --env-file .env ai-chat-assistant
```

## Uso de la API

### Enviar mensaje
```bash
curl -X POST "http://localhost:8000/api/chat/send" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hola, ¿cómo estás?",
       "session_id": "session_123"
     }'
```

### Obtener historial
```bash
curl -X GET "http://localhost:8000/api/chat/history/session_123"
```

### WebSocket para tiempo real
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = function() {
    ws.send(JSON.stringify({
        type: 'message',
        message: 'Hola',
        session_id: 'session_123'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Respuesta:', data.message);
};
```

## Estructura del Proyecto

```
ai-chat-bot/
├── main.py                 # Aplicación principal
├── requirements.txt        # Dependencias Python
├── config.env             # Configuración de ejemplo
├── README.md              # Documentación
├── src/                   # Código fuente
│   ├── api/              # Endpoints de API
│   │   ├── chat.py       # API de chat
│   │   └── websocket.py  # WebSocket handlers
│   ├── core/             # Configuración central
│   │   ├── config.py     # Configuración de la app
│   │   └── database.py   # Gestión de base de datos
│   └── services/         # Servicios de negocio
│       ├── ai_service.py # Servicio de OpenAI
│       └── ml_service.py # Servicio de ML
├── static/               # Archivos estáticos
│   ├── css/             # Estilos CSS
│   │   ├── style.css    # Estilos principales
│   │   ├── notifications.css
│   │   └── animations.css
│   └── js/              # JavaScript
│       ├── app.js       # Aplicación principal
│       ├── chat.js      # Lógica de chat
│       ├── websocket.js # WebSocket client
│       └── ui.js        # Interfaz de usuario
├── templates/           # Plantillas HTML
│   └── index.html       # Página principal
└── models/              # Modelos de ML (se crean automáticamente)
```

## Personalización

### Temas
La aplicación soporta temas claro y oscuro. Puedes cambiar el tema desde la configuración o programáticamente:

```javascript
// Cambiar tema
window.chatApp.ui.applyTheme('dark');
```

### Personalidad del Asistente
Configura la personalidad del asistente en la configuración:
- **Profesional**: Respuestas formales y técnicas
- **Amigable**: Tono casual y cercano
- **Creativo**: Respuestas imaginativas y originales
- **Analítico**: Enfoque en datos y análisis

### Estilos CSS
Los estilos están organizados en módulos:
- `style.css`: Estilos principales y variables CSS
- `notifications.css`: Sistema de notificaciones
- `animations.css`: Animaciones y transiciones

## Desarrollo

### Estructura de Código
- **Backend**: Arquitectura modular con separación de responsabilidades
- **Frontend**: JavaScript modular con clases ES6
- **API**: RESTful con documentación automática
- **WebSocket**: Comunicación bidireccional en tiempo real

### Agregar Nuevas Funcionalidades

1. **Nuevo endpoint API**:
   ```python
   # En src/api/chat.py
   @chat_router.post("/nueva-funcionalidad")
   async def nueva_funcionalidad():
       # Tu código aquí
   ```

2. **Nueva funcionalidad ML**:
   ```python
   # En src/services/ml_service.py
   async def nueva_analisis(self, text: str):
       # Tu código aquí
   ```

3. **Nueva característica UI**:
   ```javascript
   // En static/js/ui.js
   nuevaFuncionalidad() {
       // Tu código aquí
   }
   ```

## Testing

### Ejecutar tests (cuando estén implementados)
```bash
# Tests unitarios
python -m pytest tests/

# Tests de integración
python -m pytest tests/integration/

# Coverage
python -m pytest --cov=src tests/
```

## Monitoreo y Logs

### Logs de la aplicación
Los logs se muestran en la consola. Para producción, configura un sistema de logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Métricas
- Tiempo de respuesta de la API
- Confianza de las respuestas del modelo
- Estadísticas de uso por sesión
- Métricas de WebSocket

## Despliegue

### Producción con Gunicorn
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Variables de entorno para producción
```env
DEBUG=False
SECRET_KEY=clave_super_secreta_y_larga
OPENAI_API_KEY=tu_clave_produccion
DATABASE_URL=postgresql://user:pass@localhost/chatbot
```

### Docker para producción
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Si tienes problemas o preguntas:

1. Revisa la [documentación de la API](http://localhost:8000/api/docs)
2. Busca en los [Issues existentes](https://github.com/tu-usuario/ai-chat-bot/issues)
3. Crea un nuevo issue con detalles del problema

## Agradecimientos

- [OpenAI](https://openai.com/) por los modelos de lenguaje
- [FastAPI](https://fastapi.tiangolo.com/) por el framework web
- [TensorFlow](https://tensorflow.org/) por las herramientas de ML
- [Font Awesome](https://fontawesome.com/) por los iconos
- [Google Fonts](https://fonts.google.com/) por la tipografía

## Roadmap

- [ ] Soporte para múltiples idiomas
- [ ] Integración con más modelos de IA
- [ ] Sistema de plugins
- [ ] Análisis de sentimientos avanzado
- [ ] Exportación de conversaciones
- [ ] Modo offline
- [ ] Integración con bases de datos externas
- [ ] Sistema de usuarios y autenticación
- [ ] API para desarrolladores
- [ ] Dashboard de administración

---

**Disfruta usando tu AI Chat Assistant**