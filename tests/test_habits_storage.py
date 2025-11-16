"""Тесты HabitsTab storage - сохранение/загрузка привычек"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from typing import Generator

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import tkinter as tk
    from tabs.habits_tab import HabitsTab
    TKINTER_AVAILABLE = True
except (ImportError, Exception):
    TKINTER_AVAILABLE = False


@pytest.mark.skipif(not TKINTER_AVAILABLE, reason="Требуется tkinter")
class TestHabitsStorage:

    @pytest.fixture
    def temp_dir(self) -> Generator[str, None, None]:
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def root(self):
        root = tk.Tk()
        root.withdraw()
        yield root
        try:
            root.destroy()
        except tk.TclError:
            pass

    @pytest.fixture
    def habits_tab(self, root, temp_dir: str) -> Generator[HabitsTab, None, None]:
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        tab = HabitsTab(root)
        yield tab

        os.chdir(original_dir)
        try:
            tab.destroy()
        except tk.TclError:
            pass

    def test_save_creates_habits_file(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        habits_tab.save_habits()

        assert os.path.exists(os.path.join(temp_dir, "habits.json"))

    def test_save_and_load_empty_habits(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        habits_tab.save_habits()

        new_tab = HabitsTab(habits_tab.parent)
        new_tab.load_habits()

        assert set(new_tab.all_times) == set(habits_tab.default_times)
        assert len(new_tab.custom_times) == 0

        new_tab.destroy()

    def test_save_and_load_custom_time(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        """Сохранение и загрузка пользовательского времени"""
        custom_time = "Обед"
        habits_tab.custom_times.append(custom_time)
        habits_tab.all_times.append(custom_time)
        habits_tab.habits[custom_time] = []
        habits_tab.time_settings[custom_time] = {"quick_timer_minutes": None}

        habits_tab.save_habits()

        new_tab = HabitsTab(habits_tab.parent)
        new_tab.load_habits()

        assert custom_time in new_tab.all_times
        assert custom_time in new_tab.custom_times

        new_tab.destroy()

    def test_save_and_load_habit(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        habit = {
            "name": "Зарядка",
            "interval": 60,
            "start_time": "08:00",
            "end_time": "09:00",
            "enabled": True,
            "completed": False,
            "completed_repeats": 0,
            "repeats": 1,
            "notifications": True,
            "comment": "Утренняя зарядка",
            "last_reminder": None,
        }

        habits_tab.habits["Утро"].append(habit)
        habits_tab.save_habits()

        new_tab = HabitsTab(habits_tab.parent)
        new_tab.load_habits()

        assert len(new_tab.habits["Утро"]) == 1
        loaded_habit = new_tab.habits["Утро"][0]
        assert loaded_habit["name"] == "Зарядка"
        assert loaded_habit["interval"] == 60
        assert loaded_habit["enabled"] is True

        new_tab.destroy()

    def test_save_habit_with_repeats(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        habit = {
            "name": "Отжимания",
            "interval": 120,
            "start_time": "10:00",
            "end_time": "22:00",
            "enabled": True,
            "completed": False,
            "completed_repeats": 3,
            "repeats": 5,
            "notifications": True,
            "comment": "",
            "last_reminder": None,
        }

        habits_tab.habits["День"].append(habit)
        habits_tab.save_habits()

        new_tab = HabitsTab(habits_tab.parent)
        new_tab.load_habits()

        loaded_habit = new_tab.habits["День"][0]
        assert loaded_habit["completed_repeats"] == 3
        assert loaded_habit["repeats"] == 5

        new_tab.destroy()

    def test_save_multiple_habits_multiple_times(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        """Несколько привычек в разных временах"""
        morning_habit = {
            "name": "Медитация",
            "interval": 30,
            "start_time": "07:00",
            "end_time": "08:00",
            "enabled": True,
            "completed": False,
            "completed_repeats": 0,
            "repeats": 1,
            "notifications": True,
            "comment": "",
            "last_reminder": None,
        }

        evening_habit = {
            "name": "Чтение",
            "interval": 60,
            "start_time": "21:00",
            "end_time": "23:00",
            "enabled": True,
            "completed": False,
            "completed_repeats": 0,
            "repeats": 1,
            "notifications": False,
            "comment": "Книги перед сном",
            "last_reminder": None,
        }

        habits_tab.habits["Утро"].append(morning_habit)
        habits_tab.habits["Вечер"].append(evening_habit)
        habits_tab.save_habits()

        new_tab = HabitsTab(habits_tab.parent)
        new_tab.load_habits()

        assert len(new_tab.habits["Утро"]) == 1
        assert len(new_tab.habits["Вечер"]) == 1
        assert new_tab.habits["Утро"][0]["name"] == "Медитация"
        assert new_tab.habits["Вечер"][0]["name"] == "Чтение"

        new_tab.destroy()

    def test_save_time_settings(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        """Сохранение настроек быстрого таймера"""
        habits_tab.time_settings["Утро"]["quick_timer_minutes"] = 25

        habits_tab.save_habits()

        new_tab = HabitsTab(habits_tab.parent)
        new_tab.load_habits()

        assert new_tab.time_settings["Утро"]["quick_timer_minutes"] == 25

        new_tab.destroy()

    def test_json_format_utf8(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        """JSON файл должен быть UTF-8 с русскими символами"""
        habit = {
            "name": "Проверка кириллицы",
            "interval": 60,
            "start_time": "12:00",
            "end_time": "13:00",
            "enabled": True,
            "completed": False,
            "completed_repeats": 0,
            "repeats": 1,
            "notifications": True,
            "comment": "Тестирование UTF-8",
            "last_reminder": None,
        }

        habits_tab.habits["День"].append(habit)
        habits_tab.save_habits()

        with open(os.path.join(temp_dir, "habits.json"), "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)

        assert "Проверка кириллицы" in content
        assert data["habits"]["День"][0]["name"] == "Проверка кириллицы"

    def test_missing_file_creates_default_state(self, habits_tab: HabitsTab, temp_dir: str) -> None:
        """Отсутствие файла создает дефолтное состояние"""
        habits_tab.load_habits()

        assert set(habits_tab.all_times) == set(habits_tab.default_times)
        for time_period in habits_tab.default_times:
            assert time_period in habits_tab.habits
            assert isinstance(habits_tab.habits[time_period], list)
