.PHONY: run build clean help

help:
	@echo "Доступные команды:"
	@echo "  make run     - Запустить приложение"
	@echo "  make build   - Собрать exe с помощью PyInstaller"
	@echo "  make clean   - Очистить артефакты сборки"

run:
	@echo "Запуск приложения..."
	python src/main.py

build:
	@echo "Сборка exe с помощью PyInstaller..."
	pyinstaller app.spec

clean:
	@echo "Очистка артефактов сборки..."
	rm -rf build/
	rm -rf dist/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -f *.spec
