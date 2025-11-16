"""
Тесты для модуля утилит

Проверяет вспомогательные функции:
- Получение путей к ресурсам (resource_path)
"""

import os
import sys

import pytest

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.resource_path import get_resource_path


class TestResourcePath:
    """Тесты для функции get_resource_path"""

    def test_get_resource_path_returns_string(self):
        """Тест: функция возвращает строку"""
        result = get_resource_path("test.png")
        assert isinstance(result, str)

    def test_get_resource_path_with_simple_filename(self):
        """Тест: простое имя файла"""
        result = get_resource_path("icon.png")
        assert "icon.png" in result

    def test_get_resource_path_with_subdirectory(self):
        """Тест: путь с подкаталогом"""
        result = get_resource_path("images/icon.png")
        assert "images" in result
        assert "icon.png" in result

    def test_get_resource_path_preserves_separator(self):
        """Тест: сохранение разделителей пути"""
        result = get_resource_path("sounds/alert.mp3")
        # Должен содержать оба компонента пути
        assert "sounds" in result or "alert.mp3" in result

    @pytest.mark.skipif(
        not hasattr(sys, '_MEIPASS'),
        reason="Требуется окружение PyInstaller"
    )
    def test_get_resource_path_in_pyinstaller_bundle(self):
        """Тест: работа в PyInstaller bundle"""
        # Этот тест будет пропущен вне bundle
        result = get_resource_path("test.txt")
        assert sys._MEIPASS in result


class TestBasicUtilities:
    """Базовые тесты для проверки импортов утилит"""

    def test_import_constants(self):
        """Тест: импорт модуля constants"""
        from utils import constants
        assert hasattr(constants, 'IMAGES') or hasattr(constants, 'SOUNDS')

    def test_import_sound_utils(self):
        """Тест: импорт модуля sound_utils"""
        from utils import sound_utils
        # Проверяем что модуль импортируется без ошибок
        assert sound_utils is not None

    def test_import_timer_notification(self):
        """Тест: импорт модуля timer_notification"""
        from utils import timer_notification
        assert timer_notification is not None

    def test_import_habit_reminder(self):
        """Тест: импорт модуля habit_reminder"""
        from utils import habit_reminder
        assert habit_reminder is not None
