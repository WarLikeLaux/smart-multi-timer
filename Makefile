.PHONY: help venv install run clean

help:
	@echo "Доступные команды:"
	@echo ""
	@echo "  make venv    - Создать виртуальное окружение"
	@echo "  make install - Установить зависимости из src/requirements.txt"
	@echo "  make run     - Запустить приложение"
	@echo "  make clean   - Очистить артефакты сборки"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  make venv && source venv/bin/activate && make install && make run"

venv:
	@echo "Создание виртуального окружения..."
	python -m venv venv
	@echo "✓ Виртуальное окружение создано"
	@echo "Для активации: source venv/bin/activate"

install:
	@echo "Установка зависимостей из src/requirements.txt..."
	pip install -r src/requirements.txt

run:
	@echo "Запуск приложения..."
	python src/main.py

clean:
	@echo "Очистка артефактов сборки..."
	rm -rf build/
	rm -rf dist/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -f *.spec
