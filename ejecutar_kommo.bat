@echo off
title AUTOMATIZACIÓN KOMMO - Leads con tareas
color 0A

:: Cambiar al directorio donde está main.py
cd /d "C:\Users\PC\Desktop\Natalia Castro\desarrollo\TaskDaily"

:: Crear carpeta de logs
if not exist "logs" mkdir "logs"

:: Fecha para el log
set FECHA=%date:~10,4%%date:~4,2%%date:~7,2%
set HORA=%time:~0,2%%time:~3,2%%time:~6,2%
set HORA=%HORA: =0%
set LOG_FILE=logs\kommo_%FECHA%_%HORA%.log

echo ========================================
echo   AUTOMATIZACIÓN DE LEADS KOMMO
echo   Fecha: %date% %time%
echo ========================================
echo.

echo [1/3] Verificando Python...
python --version
if errorlevel 1 (
    echo ❌ Python no encontrado
    pause
    exit /b 1
)

echo [2/3] Verificando main.py...
if not exist "main.py" (
    echo ❌ main.py no encontrado en %cd%
    pause
    exit /b 1
)

echo [3/3] Ejecutando main.py...
echo.
echo === INICIO DE EJECUCIÓN === > "%LOG_FILE%"
echo Fecha: %date% %time% >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

python main.py >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo.
    echo ❌ ERROR - Revisa el log
    echo Log: %LOG_FILE%
    type "%LOG_FILE%"
) else (
    echo.
    echo ✅ COMPLETADO EXITOSAMENTE
)

echo.
echo Log guardado en: %LOG_FILE%
timeout /t 5 /nobreak >nul