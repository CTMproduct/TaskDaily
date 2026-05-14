@echo off
title AUTOMATIZACIÓN KOMMO - Leads con tareas
color 0A

:: Definir la ruta completa
set SCRIPT_DIR=C:\Users\PC\Desktop\Natalia Castro\desarrollo\TaskDaily
set SCRIPT_PATH=%SCRIPT_DIR%\main.py

echo ========================================
echo   AUTOMATIZACIÓN DE LEADS KOMMO
echo   Fecha: %date% %time%
echo ========================================
echo.

:: Verificar que el script existe
if not exist "%SCRIPT_PATH%" (
    echo ❌ ERROR: No se encuentra main.py
    echo Ruta buscada: %SCRIPT_PATH%
    echo.
    echo Verifica que el archivo exista en:
    echo %SCRIPT_DIR%
    pause
    exit /b 1
)

:: Ejecutar el script directamente con ruta completa
echo Ejecutando: python "%SCRIPT_PATH%"
echo.
python "%SCRIPT_PATH%"

if errorlevel 1 (
    echo.
    echo ❌ ERROR - El script falló
) else (
    echo.
    echo ✅ COMPLETADO EXITOSAMENTE
)

echo.
pause