#!/bin/bash
# Build script for Windows (Git Bash / WSL)
# Установка зависимостей и сборка exe через PyInstaller

set -e  # Exit on error

echo "========================================"
echo "Сборка exe для Windows"
echo "========================================"
echo ""

# Проверка зависимостей
echo "1. Проверка зависимостей..."
if ! command -v python &> /dev/null; then
    echo "❌ Python не найден. Установите Python 3.x и добавьте в PATH"
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ pip не найден. Переустановите Python"
    exit 1
fi

echo "   ✓ Python найден: $(python --version)"
echo ""

# Установка PyInstaller если не установлен
echo "2. Установка PyInstaller и зависимостей..."
pip install -r src/requirements.txt pyinstaller

echo ""
echo "3. Сборка exe с помощью PyInstaller..."
pyinstaller app.spec

echo ""
echo "========================================"
echo "✓ Сборка завершена!"
echo "========================================"
echo ""
echo "Файл находится в: dist/"
echo ""
