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
echo 3. Запустить тесты
echo 0. Выход
echo.
set /p choice="Выберите действие (0-3): "

if "%choice%"=="1" goto run_app
if "%choice%"=="2" goto build_app
if "%choice%"=="3" goto run_tests
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

REM Обновление из git перед запуском
call :git_update
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

REM Обновление из git перед сборкой
call :git_update
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

:run_tests
cls
echo ========================================
echo Запуск тестов
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

REM Установка pytest если не установлен
echo Проверка pytest...
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo pytest не найден, устанавливаю...
    pip install pytest pytest-cov
    echo.
)

REM Запуск тестов
echo ========================================
echo Запуск тестов...
echo ========================================
echo.
python -m pytest tests/ -v
echo.
echo ========================================
echo Тесты завершены
echo ========================================
echo.
pause
goto menu

:git_update
echo ========================================
echo Проверка обновлений из Git
echo ========================================
echo.
git --version >nul 2>&1
if errorlevel 1 (
    echo ⚠ Git не найден, пропускаем обновление
    goto :eof
)

echo Текущая ветка:
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set CURRENT_BRANCH=%%i
if defined CURRENT_BRANCH (
    echo    ✓ !CURRENT_BRANCH!
) else (
    echo    ⚠ Не удалось определить ветку
    goto :eof
)

echo.
echo Обновление из репозитория...
git pull 2>&1 | findstr /V /C:"Already up to date" /C:"Уже актуально"
if errorlevel 1 (
    echo    ✓ Код обновлён
) else (
    echo    ✓ Код актуален
)
echo.
goto :eof

:end
echo.
echo До свидания!
timeout /t 1 >nul
exit /b 0
