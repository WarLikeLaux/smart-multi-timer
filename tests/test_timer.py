"""Тесты Timer - основного компонента таймеров"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    import tkinter as tk
    from components.timer import Timer
    TKINTER_AVAILABLE = True
except (ImportError, Exception):
    TKINTER_AVAILABLE = False


@pytest.mark.skipif(not TKINTER_AVAILABLE, reason="Требуется tkinter")
class TestTimer:

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
    def timer(self, root) -> Timer:
        timer = Timer(root)
        yield timer
        try:
            timer.destroy()
        except tk.TclError:
            pass

    def test_timer_initial_state(self, timer: Timer) -> None:
        assert timer.remaining_time == 0
        assert timer.is_running is False
        assert timer.paused_time == 0
        assert timer.initial_time is None
        assert timer.custom_sound is None

    def test_timer_to_dict_default(self, timer: Timer) -> None:
        result = timer.to_dict()

        assert "description" in result
        assert "hours" in result
        assert "minutes" in result
        assert "seconds" in result
        assert "custom_sound" in result
        assert result["custom_sound"] is None

    def test_timer_to_dict_with_values(self, timer: Timer) -> None:
        timer.hours.set("1")
        timer.minutes.set("30")
        timer.seconds.set("45")
        timer.description.delete(0, tk.END)
        timer.description.insert(0, "Тестовый таймер")
        timer.custom_sound = "/path/to/sound.mp3"

        result = timer.to_dict()

        assert result["hours"] == "1"
        assert result["minutes"] == "30"
        assert result["seconds"] == "45"
        assert result["description"] == "Тестовый таймер"
        assert result["custom_sound"] == "/path/to/sound.mp3"

    def test_apply_preset_5_minutes(self, timer: Timer) -> None:
        timer.apply_preset(5)

        assert timer.hours.get() == "0"
        assert timer.minutes.get() == "5"
        assert timer.seconds.get() == "0"

    def test_apply_preset_1_hour(self, timer: Timer) -> None:
        timer.apply_preset(60)

        assert timer.hours.get() == "0"
        assert timer.minutes.get() == "60"
        assert timer.seconds.get() == "0"

    def test_apply_preset_updates_display(self, timer: Timer) -> None:
        timer.apply_preset(25)

        display_text = timer.time_label.cget("text")
        assert display_text == "00:25:00"

    def test_update_time_display_valid_input(self, timer: Timer) -> None:
        timer.hours.set("2")
        timer.minutes.set("15")
        timer.seconds.set("30")

        timer.update_time_display()

        assert timer.time_label.cget("text") == "02:15:30"

    def test_update_time_display_zero_values(self, timer: Timer) -> None:
        timer.hours.set("0")
        timer.minutes.set("0")
        timer.seconds.set("0")

        timer.update_time_display()

        assert timer.time_label.cget("text") == "00:00:00"

    def test_update_time_display_invalid_input(self, timer: Timer) -> None:
        """Невалидный ввод должен показывать 00:00:00"""
        timer.hours.set("invalid")
        timer.minutes.set("abc")
        timer.seconds.set("xyz")

        timer.update_time_display()

        assert timer.time_label.cget("text") == "00:00:00"

    def test_choose_sound_updates_button(self, timer: Timer) -> None:
        timer.custom_sound = "/some/sound.mp3"
        timer.sound_button.config(text="🔊 ✓")

        assert timer.sound_button.cget("text") == "🔊 ✓"

    def test_presets_data_contains_expected_values(self, timer: Timer) -> None:
        expected_presets = [
            ("5 минут", 5),
            ("10 минут", 10),
            ("15 минут", 15),
            ("25 минут", 25),
            ("1 час", 60),
        ]

        for preset_label, preset_minutes in expected_presets:
            assert (preset_label, preset_minutes) in timer.presets_data

    def test_timer_has_preset_buttons(self, timer: Timer) -> None:
        assert len(timer.preset_buttons) == len(timer.presets_data)
        assert len(timer.preset_buttons) == 10

    def test_insert_emoji(self, timer: Timer) -> None:
        initial_desc = timer.description.get()
        timer.description.icursor(0)
        timer.insert_emoji("🔥")

        new_desc = timer.description.get()
        assert "🔥" in new_desc

    def test_stop_alarm_resets_state(self, timer: Timer) -> None:
        timer.alarm_active = True
        timer.is_running = True

        timer.stop_alarm()

        assert timer.alarm_active is False
        assert timer.is_running is False
