import json
import tkinter as tk
from tkinter import messagebox, ttk


class SettingsTab(ttk.Frame):
    """
    Вкладка настроек приложения.

    Управляет глобальными настройками, такими как поведение при закрытии окна.
    Настройки сохраняются в settings.json.
    """

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Создает UI вкладки настроек"""
        main_container = ttk.Frame(self)
        main_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Заголовок
        header = ttk.Label(
            main_container,
            text="⚙️ Настройки приложения",
            font=("Arial", 16, "bold")
        )
        header.pack(anchor=tk.W, pady=(0, 20))

        # Секция: Поведение окна
        window_section = ttk.LabelFrame(
            main_container,
            text="Поведение окна",
            padding=15
        )
        window_section.pack(fill=tk.X, pady=(0, 15))

        # Чекбокс: Закрывать при нажатии X
        self.close_on_exit_var = tk.BooleanVar(value=True)
        close_checkbox = ttk.Checkbutton(
            window_section,
            text="Закрывать приложение при нажатии ✕ (вместо сворачивания в трей)",
            variable=self.close_on_exit_var,
            command=self.on_setting_changed,
            takefocus=0
        )
        close_checkbox.pack(anchor=tk.W, pady=5)

        # Описание
        description = ttk.Label(
            window_section,
            text="Если включено: приложение полностью закроется при нажатии крестика.\n"
                 "Если выключено: приложение свернется в системный трей.",
            foreground="gray",
            font=("Arial", 9)
        )
        description.pack(anchor=tk.W, padx=(25, 0), pady=(0, 5))

        # Примечание для разработчиков
        dev_note = ttk.Label(
            window_section,
            text="💡 Для отладки удобно включать эту опцию, чтобы процесс не висел в фоне.",
            foreground="#555",
            font=("Arial", 9, "italic")
        )
        dev_note.pack(anchor=tk.W, padx=(25, 0), pady=(5, 0))

    def load_settings(self):
        """Загружает настройки из settings.json"""
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.close_on_exit_var.set(settings.get("close_on_exit", True))
        except FileNotFoundError:
            # Файл не существует - используем дефолтное значение True
            self.close_on_exit_var.set(True)
        except json.JSONDecodeError:
            messagebox.showwarning(
                "Предупреждение",
                "Файл settings.json поврежден. Используются настройки по умолчанию."
            )
            self.close_on_exit_var.set(True)
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось загрузить настройки: {str(e)}"
            )
            self.close_on_exit_var.set(True)

    def save_settings(self):
        """Сохраняет настройки в settings.json"""
        settings = {
            "close_on_exit": self.close_on_exit_var.get()
        }

        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось сохранить настройки: {str(e)}"
            )

    def on_setting_changed(self):
        """Вызывается при изменении любой настройки"""
        self.save_settings()

    def get_close_on_exit(self) -> bool:
        """Возвращает текущее значение настройки close_on_exit"""
        return self.close_on_exit_var.get()
