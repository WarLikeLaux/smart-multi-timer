@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:menu
cls
echo ========================================
echo Smart Multi-Timer - Главное меню
echo ========================================
echo.
echo 1. Запустить приложение
echo 2. Собрать exe файл
echo 0. Выход
echo.
set /p choice="Выберите действие (0-2): "

if "%choice%"=="1" goto run_app
if "%choice%"=="2" goto build_app
if "%choice%"=="0" goto end
echo.
echo ❌ Неверный выбор. Попробуйте снова.
timeout /t 2 >nul
goto menu

:run_app
cls
echo ========================================
echo Запуск приложения
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.x и добавьте в PATH
    echo.
    pause
    goto menu
)

echo ✓ Python найден
echo.
echo Запуск src\main.py...
echo.
python src\main.py
echo.
echo ========================================
echo Приложение завершено
echo ========================================
echo.
pause
goto menu

:build_app
cls
echo ========================================
echo Сборка exe файла
echo ========================================
echo.

REM Проверка Python
echo 1. Проверка зависимостей...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.x и добавьте в PATH
    echo.
    pause
    goto menu
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo    ✓ !PYTHON_VERSION! найден
echo.

REM Установка PyInstaller и зависимостей
echo 2. Установка PyInstaller и зависимостей...
pip install -r src\requirements.txt pyinstaller
if errorlevel 1 (
    echo ❌ Ошибка при установке зависимостей
    echo.
    pause
    goto menu
)

echo.
echo 3. Сборка exe с помощью PyInstaller...
pyinstaller app.spec
if errorlevel 1 (
    echo ❌ Ошибка при сборке
    echo.
    pause
    goto menu
)

echo.
echo ========================================
echo ✓ Сборка завершена
echo ========================================
echo.
echo Файл находится в: dist\
echo.
pause
goto menu

:end
echo.
echo До свидания!
timeout /t 1 >nul
exit /b 0
