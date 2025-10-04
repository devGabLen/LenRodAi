@echo off
title AI Chat Assistant - Con OpenAI
echo ========================================
echo    AI Chat Assistant - CON OPENAI
echo ========================================
echo.
echo Verificando configuracion de OpenAI...
echo.
if not exist config_temp.env (
    echo ERROR: No se encontro config_temp.env
    echo Por favor, crea el archivo con tu API key
    pause
    exit
)
echo Archivo de configuracion encontrado
echo.
echo Iniciando servidor con OpenAI...
echo Abriendo en: http://localhost:8000
echo.
C:\Users\Usuario\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe main_with_openai.py
echo.
echo Servidor detenido.
pause
