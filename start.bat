@echo off
title SaveYourStorage - Media Optimizer & Trimmer
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo        SaveYourStorage - by Giuseppe Antonino Cotroneo
echo ========================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRORE] Python non e' installato o non e' presente nel PATH di sistema.
    echo Scarica Python da https://www.python.org/downloads/ e riprova.
    pause
    exit /b 1
)

:: 2. Check local FFmpeg or system FFmpeg
if not exist "bin\ffmpeg.exe" (
    echo [INFO] FFmpeg non trovato in bin\. Verifica automatica...
    python scripts\ensure_ffmpeg.py
)

:: 3. Kill any previously hanging server on port 5678
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5678" ^| find "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 4. Start Python background server
echo [INFO] Avvio server desktop locale su http://127.0.0.1:5678...
start /b python server.py 5678

:: Wait a brief second for server startup
timeout /t 1 /nobreak >nul

:: 5. Launch in Microsoft Edge App Mode (WinUI borderless desktop window)
set "EDGE_PATH=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE_PATH%" (
    set "EDGE_PATH=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
)

if exist "%EDGE_PATH%" (
    echo [INFO] Apertura finestra WinUI nativa...
    start "" "%EDGE_PATH%" --app=http://127.0.0.1:5678 --window-size=1160,860
) else (
    echo [INFO] Apertura nel browser predefinito...
    start http://127.0.0.1:5678
)

exit /b 0
