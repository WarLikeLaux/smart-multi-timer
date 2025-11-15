@echo off
REM Build script for Windows (CMD)
REM Установка зависимостей и сборка exe через PyInstaller

setlocal enabledelayedexpansion

echo ========================================
echo Сборка exe для Windows
echo ========================================
echo.

REM Проверка Python
echo 1. Проверка зависимостей...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.x и добавьте в PATH
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo    ✓ %PYTHON_VERSION% найден
echo.

REM Установка PyInstaller и зависимостей
echo 2. Установка PyInstaller и зависимостей...
pip install -r src\requirements.txt pyinstaller
if errorlevel 1 (
    echo ❌ Ошибка при установке зависимостей
    pause
    exit /b 1
)

echo.
echo 3. Сборка exe с помощью PyInstaller...
pyinstaller app.spec
if errorlevel 1 (
    echo ❌ Ошибка при сборке
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✓ Сборка завершена!
echo ========================================
echo.
echo Файл находится в: dist\
echo.
pause
