@echo off
title Ctrx SaveStorage - Compilatore EXE
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================================
echo   Ctrx SaveStorage - Build EXE (by Giuseppe Antonino Cotroneo)
echo ========================================================
echo.

pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installazione di PyInstaller in corso...
    pip install pyinstaller
)

echo [INFO] Compilazione in corso con PyInstaller...
python -m PyInstaller --noconfirm --onedir --windowed ^
    --name "CtrxSaveStorage" ^
    --icon "assets\icon.ico" ^
    --add-data "web;web" ^
    --add-data "bin;bin" ^
    --add-data "assets;assets" ^
    --add-data "scanner.py;." ^
    --add-data "engine.py;." ^
    server.py

if exist "dist\CtrxSaveStorage\CtrxSaveStorage.exe" (
    echo.
    echo ========================================================
    echo  COMPILAZIONE COMPLETATA CON SUCCESSO!
    echo  Troverai il software in: dist\CtrxSaveStorage\
    echo ========================================================
) else (
    echo [ERRORE] Compilazione fallita.
)

pause
