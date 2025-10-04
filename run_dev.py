#!/usr/bin/env python3
"""
Script de inicio para AI Chat Assistant
Equivalente a 'npm run dev'
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    """Función principal"""
    
    print("🚀 AI Chat Assistant - Modo Desarrollo")
    print("=" * 50)
    
    # Verificar que estamos en el directorio correcto
    if not Path("main_simple.py").exists():
        print("❌ Error: No se encontró main_simple.py")
        print("   Asegúrate de estar en el directorio correcto")
        sys.exit(1)
    
    # Verificar dependencias
    try:
        import fastapi
        import uvicorn
        print("✅ Dependencias verificadas")
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("   Ejecuta: python -m pip install fastapi uvicorn python-dotenv jinja2 aiofiles websockets")
        sys.exit(1)
    
    print("📱 Abriendo navegador en 3 segundos...")
    print("🌐 URL: http://localhost:8000")
    print("🛑 Presiona Ctrl+C para detener")
    print("=" * 50)
    
    # Abrir navegador después de 3 segundos
    def open_browser():
        time.sleep(3)
        try:
            webbrowser.open("http://localhost:8000")
            print("✅ Navegador abierto")
        except Exception as e:
            print(f"⚠️ No se pudo abrir el navegador: {e}")
    
    # Iniciar navegador en segundo plano
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Ejecutar la aplicación
        subprocess.run([
            "C:\\Users\\Usuario\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\python.exe",
            "main_simple.py"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error ejecutando la aplicación: {e}")

if __name__ == "__main__":
    main()
