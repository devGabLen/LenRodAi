# AI Chat Assistant - Comandos de desarrollo

.PHONY: dev start stop install clean

# Comando principal para desarrollo
dev:
	@echo "🚀 Iniciando AI Chat Assistant en modo desarrollo..."
	@echo "📱 Abriendo en: http://localhost:8000"
	@echo "🛑 Presiona Ctrl+C para detener"
	@echo ""
	python main_simple.py

# Comando alternativo
start: dev

# Instalar dependencias
install:
	@echo "📦 Instalando dependencias..."
	python -m pip install fastapi uvicorn python-dotenv jinja2 aiofiles websockets

# Limpiar archivos temporales
clean:
	@echo "🧹 Limpiando archivos temporales..."
	@if exist __pycache__ rmdir /s /q __pycache__
	@if exist *.pyc del /q *.pyc

# Ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  make dev     - Iniciar la aplicación"
	@echo "  make start   - Iniciar la aplicación (alias de dev)"
	@echo "  make install - Instalar dependencias"
	@echo "  make clean   - Limpiar archivos temporales"
	@echo "  make help    - Mostrar esta ayuda"
