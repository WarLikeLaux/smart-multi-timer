.PHONY: help venv install run dev test clean

help:
	@echo "Доступные команды:"
	@echo ""
	@echo "  make venv    - Создать виртуальное окружение"
	@echo "  make install - Установить зависимости из src/requirements.txt"
	@echo "  make run     - Запустить приложение (требует активированного venv)"
	@echo "  make test    - Запустить тесты"
	@echo "  make dev     - Создать venv, установить зависимости и запустить"
	@echo "  make clean   - Очистить артефакты сборки"
	@echo ""
	@echo "Быстрый старт:"
	@echo "  make dev     # Всё включено: venv, install, run"

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

test:
	@echo "Запуск тестов..."
	@echo ""
	@echo "Проверка pytest..."
	@python -m pytest --version >/dev/null 2>&1 || pip install pytest pytest-cov
	@echo "Запуск тестов с pytest..."
	python -m pytest tests/ -v

dev:
	@echo "Быстрый старт: venv + install + run..."
	@bash -c 'set -e; \
	if [ ! -d "venv" ]; then python -m venv venv; fi; \
	source venv/bin/activate; \
	pip install -r src/requirements.txt; \
	python src/main.py'

clean:
	@echo "Очистка артефактов сборки..."
	rm -rf build/
	rm -rf dist/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -f *.spec
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
