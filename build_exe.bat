@echo off
title SaveYourStorage - Compilatore EXE
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo   SaveYourStorage - Build EXE (by Giuseppe Antonino Cotroneo)
echo ========================================================
echo.

python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installazione di PyInstaller in corso...
    python -m pip install pyinstaller
    if errorlevel 1 goto :build_error
)

if exist "dist\SaveYourStorage" (
    echo [INFO] Rimozione della build precedente...
    rmdir /s /q "dist\SaveYourStorage"
    if errorlevel 1 goto :build_error
)

echo [INFO] Compilazione in corso con PyInstaller...
python -m PyInstaller --noconfirm --clean --onedir --windowed ^
    --name "SaveYourStorage" ^
    --icon "assets\icon.ico" ^
    --add-data "web;web" ^
    --add-data "bin;bin" ^
    --add-data "assets;assets" ^
    --add-data "scanner.py;." ^
    --add-data "engine.py;." ^
    server.py

if errorlevel 1 goto :build_error

if exist "dist\SaveYourStorage\SaveYourStorage.exe" (
    echo.
    echo ========================================================
    echo  COMPILAZIONE COMPLETATA CON SUCCESSO!
    echo  Troverai il software in: dist\SaveYourStorage\
    echo ========================================================
    pause
    exit /b 0
) else (
    goto :build_error
)

:build_error
echo.
echo [ERRORE] Compilazione fallita. Controlla gli errori riportati sopra.
pause
exit /b 1

pause
