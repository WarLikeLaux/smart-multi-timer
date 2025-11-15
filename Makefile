.PHONY: help venv install run build build-win clean

help:
	@echo "Доступные команды:"
	@echo ""
	@echo "  make venv    - Создать виртуальное окружение"
	@echo "  make install - Установить зависимости (требует активного venv)"
	@echo "  make run     - Запустить приложение"
	@echo "  make build   - Собрать exe с помощью PyInstaller (только Windows)"
	@echo "  make build-win - Альтернатива для Windows CMD/Git Bash"
	@echo "  make clean   - Очистить артефакты сборки"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  1. make venv       # Создать виртуальное окружение"
	@echo "  2. source venv/bin/activate (Linux/macOS) или venv\\Scripts\\activate (Windows)"
	@echo "  3. make install    # Установить зависимости"
	@echo "  4. make run        # Запустить приложение"

venv:
	@echo "Создание виртуального окружения..."
	python -m venv venv
	@echo "✓ Виртуальное окружение создано"
	@echo "Для активации выполните:"
	@echo "  Linux/macOS: source venv/bin/activate"
	@echo "  Windows:     venv\\Scripts\\activate"

install:
	@echo "Установка зависимостей из src/requirements.txt..."
	pip install -r src/requirements.txt

run:
	@echo "Запуск приложения..."
	python src/main.py

build:
	@echo "⚠️  ВНИМАНИЕ: Сборка exe работает только на Windows"
	@echo "Если вы на Linux/macOS, используйте build-win или собирайте на Windows вручную"
	@echo ""
	@echo "Сборка exe с помощью PyInstaller..."
	pyinstaller app.spec

build-win:
	@echo "Сборка exe для Windows с помощью PyInstaller..."
	pyinstaller app.spec

clean:
	@echo "Очистка артефактов сборки..."
	rm -rf build/
	rm -rf dist/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -f *.spec
