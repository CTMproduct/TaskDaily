@echo off
echo ========================================
echo DIAGNÓSTICO DEL SISTEMA
echo ========================================
echo.
echo 1. Directorio actual:
cd
echo.
echo 2. Archivos en el directorio:
dir *.py
echo.
echo 3. Versión de Python:
python --version
echo.
echo 4. Ruta de Python:
where python
echo.
echo 5. Probando import requests:
python -c "import requests; print('✅ requests OK')"
echo.
echo 6. Probando import pytz:
python -c "import pytz; print('✅ pytz OK')"
echo.
echo 7. Probando ejecución de main.py:
python main.py --help 2>nul
if errorlevel 1 (
    echo ❌ main.py no se puede ejecutar
) else (
    echo ✅ main.py responde
)
echo.
echo ========================================
echo Diagnóstico completado
pause