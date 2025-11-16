"""Тесты утилит проекта"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.resource_path import get_resource_path


class TestResourcePath:

    def test_get_resource_path_returns_string(self) -> None:
        result = get_resource_path("test.png")
        assert isinstance(result, str)

    def test_get_resource_path_with_simple_filename(self) -> None:
        result = get_resource_path("icon.png")
        assert "icon.png" in result

    def test_get_resource_path_with_subdirectory(self) -> None:
        result = get_resource_path("images/icon.png")
        assert "images" in result
        assert "icon.png" in result

    def test_get_resource_path_preserves_separator(self) -> None:
        result = get_resource_path("sounds/alert.mp3")
        assert "sounds" in result or "alert.mp3" in result

    @pytest.mark.skipif(
        not hasattr(sys, '_MEIPASS'),
        reason="Требуется окружение PyInstaller"
    )
    def test_get_resource_path_in_pyinstaller_bundle(self) -> None:
        """Работа в PyInstaller bundle - требует _MEIPASS"""
        result = get_resource_path("test.txt")
        assert sys._MEIPASS in result


class TestBasicUtilities:

    def test_import_constants(self) -> None:
        from utils import constants
        assert hasattr(constants, 'IMAGES') or hasattr(constants, 'SOUNDS')

    def test_import_sound_utils(self) -> None:
        from utils import sound_utils
        assert sound_utils is not None

    def test_import_timer_notification(self) -> None:
        from utils import timer_notification
        assert timer_notification is not None

    def test_import_habit_reminder(self) -> None:
        from utils import habit_reminder
        assert habit_reminder is not None
