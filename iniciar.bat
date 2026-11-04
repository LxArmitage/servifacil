@echo off
rem Inicia ServiFacil en esta computadora con datos de demostracion.
rem Doble clic en este archivo. Para detenerla: cerrar esta ventana.
cd /d "%~dp0"
title ServiFacil

where python >nul 2>nul
if errorlevel 1 (
    echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
    echo y marca "Add python.exe to PATH". La app tambien esta en linea:
    echo https://servifacil.onrender.com
    pause
    exit /b 1
)

if not exist .venv\Scripts\python.exe (
    echo Preparando la aplicacion, solo la primera vez...
    python -m venv .venv
    if errorlevel 1 goto error
)

.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto error

rem Contrasena del administrador solo para la copia local
if not defined ADMIN_PASSWORD set ADMIN_PASSWORD=admin1234

echo.
echo ServiFacil: http://127.0.0.1:5000
echo Administrador: admin@servifacil.com / %ADMIN_PASSWORD%
echo Cliente: cliente@servifacil.test / demo1234
echo Tecnico: tecnico@servifacil.test / demo1234
echo.
start "" /b cmd /c "timeout /t 4 >nul & start http://127.0.0.1:5000"
.venv\Scripts\python.exe run.py
pause
exit /b 0

:error
echo No se pudo preparar la aplicacion. Revisa tu conexion a internet.
pause
exit /b 1
