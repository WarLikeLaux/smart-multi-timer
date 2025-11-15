import json
import platform
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import pystray
from PIL import Image, ImageTk
from pygame import mixer
from ttkthemes import ThemedTk

from components.timer import Timer
from tabs.habits_tab import HabitsTab
from tabs.medication_tab import MedicationTab
from tabs.pushup_tracker_tab import PushupTrackerTab
from tabs.settings_tab import SettingsTab
from tabs.todo_list_tab import TodoListTab
from utils.constants import IMAGES


class MainWindow(ThemedTk):
    def __init__(self):
        try:
            with open("theme_settings.json", "r") as f:
                settings = json.load(f)
                initial_theme = settings.get("theme", "ubuntu")
        except:
            initial_theme = "ubuntu"

        super().__init__(theme=initial_theme)
        self.selected_theme = initial_theme
        self.create_theme_menu()
        self.is_wsl = self.check_wsl()

        if platform.system() == "Windows" and not self.is_wsl:
            self.iconbitmap(default=IMAGES["TRAY_ICON"])

        self.setup_global_styles()
        self.title("Мульти-таймер")
        self.timers = []
        self.setup_ui()

        if not self.is_wsl:
            self.create_tray_icon()

        window_width = 1050
        window_height = 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        if self.is_wsl:
            self.protocol("WM_DELETE_WINDOW", self.quit_app)
        else:
            self.protocol("WM_DELETE_WINDOW", self.hide_window)

    def create_theme_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        theme_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Тема", menu=theme_menu)

        for theme in self.get_themes():
            theme_menu.add_radiobutton(
                label=theme.capitalize(),
                value=theme,
                variable=self.selected_theme,
                command=lambda t=theme: self.change_theme(t),
            )

    def change_theme(self, theme_name):
        try:
            self.set_theme(theme_name)
            self.selected_theme = theme_name
            self.setup_global_styles()
            with open("theme_settings.json", "w") as f:
                json.dump({"theme": theme_name}, f)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось применить тему: {str(e)}")

    @staticmethod
    def check_wsl():
        if platform.system() == "Linux":
            try:
                with open("/proc/version", "r") as f:
                    if "microsoft" in f.read().lower():
                        return True
            except:
                pass
        return False

    def setup_global_styles(self):
        style = ttk.Style(self)
        style.layout(
            "TNotebook.Tab",
            [
                (
                    "Notebook.tab",
                    {
                        "sticky": "nswe",
                        "children": [
                            (
                                "Notebook.padding",
                                {
                                    "side": "top",
                                    "sticky": "nswe",
                                    "children": [
                                        ("Notebook.label", {"sticky": "nswe"})
                                    ],
                                },
                            )
                        ],
                    },
                )
            ],
        )

        style.configure("TNotebook", takefocus=0)
        style.configure("TNotebook.Tab", focuscolor="none", takefocus=0)

    def setup_ui(self):
        self.notebook = ttk.Notebook(self, takefocus=0)
        self.notebook.configure(takefocus=0)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.timers_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.timers_tab, text="Таймеры")

        self.pushups_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pushups_tab, text="Отжимания")

        self.medication_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.medication_tab, text="Таблетки")

        self.todo_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.todo_tab, text="Задачи")

        self.habits_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.habits_tab, text="Привычки")

        self.settings_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab_frame, text="Настройки")

        self.setup_timers_ui()

        self.pushup_tracker = PushupTrackerTab(self.pushups_tab)
        self.pushup_tracker.pack(expand=True, fill=tk.BOTH)

        self.habits_tracker = HabitsTab(self.habits_tab)
        self.habits_tracker.pack(expand=True, fill=tk.BOTH)

        self.todo_list = TodoListTab(self.todo_tab)
        self.todo_list.pack(expand=True, fill=tk.BOTH)

        self.medication_tracker = MedicationTab(self.medication_tab)
        self.medication_tracker.pack(expand=True, fill=tk.BOTH)

        self.settings_tab = SettingsTab(self.settings_tab_frame, self)
        self.settings_tab.pack(expand=True, fill=tk.BOTH)

        style = ttk.Style()
        style.configure("TNotebook.Tab", focuscolor="none")

        self.timers_tab_index = self.notebook.index(self.timers_tab)

    def setup_timers_ui(self):
        self.main_frame = ttk.Frame(self.timers_tab)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=15)

        header = ttk.Frame(self.main_frame)
        header.pack(fill=tk.X, pady=(0, 15))

        header_left = ttk.Frame(header)
        header_left.pack(side=tk.LEFT, fill=tk.Y)
        ttk.Label(
            header_left, text="Управление фокусом", font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT)

        header_right = ttk.Frame(header)
        header_right.pack(side=tk.RIGHT)

        ttk.Button(
            header_right,
            text="⏱ Добавить таймер",
            style="Accent.TButton",
            command=self.add_timer,
            takefocus=0,
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            header_right,
            text="⚡️ Быстрый фокус (25+5)",
            style="Secondary.TButton",
            command=self.add_pomodoro_preset,
            takefocus=0,
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            header_right,
            text="⏳ Длинный фокус (52+17)",
            style="Secondary.TButton",
            command=self.add_long_focus_preset,
            takefocus=0,
        ).pack(side=tk.RIGHT, padx=5)

        self.timers_frame = ttk.Frame(self.main_frame)
        self.timers_frame.pack(expand=True, fill=tk.BOTH)

        self.canvas = tk.Canvas(self.timers_frame, bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self.timers_frame, orient="vertical", command=self.canvas.yview
        )

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw",
            width=self.timers_frame.winfo_width(),
        )
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Accent.TButton", padding=8, font=("Arial", 10, "bold"))
        style.configure("Secondary.TButton", padding=8, font=("Arial", 10))

        self.load_timers()

    def _on_mousewheel(self, event):
        """Обработка прокрутки колесиком мыши"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_default_timers(self):
        work_timer = Timer(self, on_delete=self.remove_timer)
        work_timer.pack(in_=self.scrollable_frame, fill=tk.X)
        work_timer.description.delete(0, tk.END)
        work_timer.description.insert(0, "🎯 Глубокий фокус")
        work_timer.hours.set("1")
        work_timer.minutes.set("0")
        work_timer.seconds.set("0")
        work_timer.update_presets_visibility()
        work_timer.update_time_display()
        self.timers.append(work_timer)

        break_timer = Timer(self, on_delete=self.remove_timer)
        break_timer.pack(in_=self.scrollable_frame, fill=tk.X)
        break_timer.description.delete(0, tk.END)
        break_timer.description.insert(0, "🌿 Перерыв")
        break_timer.hours.set("0")
        break_timer.minutes.set("5")
        break_timer.seconds.set("0")
        break_timer.update_presets_visibility()
        break_timer.update_time_display()
        self.timers.append(break_timer)

    def add_pomodoro_preset(self):
        work_timer = Timer(self, on_delete=self.remove_timer)
        work_timer.pack(in_=self.scrollable_frame, fill=tk.X)
        work_timer.description.delete(0, tk.END)
        work_timer.description.insert(0, "🍅 Помодоро")
        work_timer.hours.set("0")
        work_timer.minutes.set("25")
        work_timer.seconds.set("0")
        work_timer.update_presets_visibility()
        work_timer.update_time_display()
        self.timers.append(work_timer)

        break_timer = Timer(self, on_delete=self.remove_timer)
        break_timer.pack(in_=self.scrollable_frame, fill=tk.X)
        break_timer.description.delete(0, tk.END)
        break_timer.description.insert(0, "☕️ Короткий перерыв")
        break_timer.hours.set("0")
        break_timer.minutes.set("5")
        break_timer.seconds.set("0")
        break_timer.update_presets_visibility()
        break_timer.update_time_display()
        self.timers.append(break_timer)

    def add_long_focus_preset(self):
        work_timer = Timer(self, on_delete=self.remove_timer)
        work_timer.pack(in_=self.scrollable_frame, fill=tk.X)
        work_timer.description.delete(0, tk.END)
        work_timer.description.insert(0, "🔋 Глубокий фокус")
        work_timer.hours.set("0")
        work_timer.minutes.set("52")
        work_timer.seconds.set("0")
        work_timer.update_presets_visibility()
        work_timer.update_time_display()
        self.timers.append(work_timer)

        break_timer = Timer(self, on_delete=self.remove_timer)
        break_timer.pack(in_=self.scrollable_frame, fill=tk.X)
        break_timer.description.delete(0, tk.END)
        break_timer.description.insert(0, "🌳 Длинный перерыв")
        break_timer.hours.set("0")
        break_timer.minutes.set("17")
        break_timer.seconds.set("0")
        break_timer.update_presets_visibility()
        break_timer.update_time_display()
        self.timers.append(break_timer)

    def create_tray_icon(self):
        icon = Image.open(IMAGES["TRAY_ICON"])
        icon = icon.resize((32, 32))

        menu = (
            pystray.MenuItem("Показать", self.show_window),
            pystray.MenuItem("Выход", self.quit_app),
        )

        self.icon = pystray.Icon("timer", icon, "Мульти-таймер", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self):
        self.icon.stop()
        self.deiconify()
        self.create_tray_icon()

    def hide_window(self):
        """
        Обрабатывает закрытие окна.

        Проверяет настройку close_on_exit:
        - Если True или WSL: полностью закрывает приложение
        - Если False: сворачивает в системный трей
        """
        if self.is_wsl:
            self.quit_app()
            return

        close_on_exit = self.settings_tab.get_close_on_exit()

        if close_on_exit:
            self.quit_app()
        else:
            self.withdraw()
            messagebox.showinfo(
                "Умный (верим?) мульти-таймер",
                "Приложение продолжает работать в трее.\n"
                + "Нажмите на иконку в трее, чтобы открыть окно.",
            )

    def quit_app(self):
        """Полностью закрывает приложение"""
        self.save_timers()

        if hasattr(self, "icon") and self.icon:
            self.icon.stop()

        for timer in self.timers:
            if hasattr(timer, "is_running"):
                timer.is_running = False

        try:
            mixer.quit()
        except:
            pass

        self.quit()

    def add_timer(self):
        timer = Timer(self, on_delete=self.remove_timer)
        timer.pack(in_=self.scrollable_frame, fill=tk.X)
        self.timers.append(timer)
        self.save_timers()

    def remove_timer(self, timer):
        """Безопасное удаление таймера"""
        try:
            if timer in self.timers:
                self.timers.remove(timer)
            if hasattr(timer, "is_running"):
                timer.is_running = False
            if hasattr(timer, "stop_timer"):
                timer.stop_timer()
            if timer.winfo_exists():
                timer.destroy()
        except Exception as e:
            print(f"Ошибка при удалении таймера: {e}")
        self.save_timers()

    def save_timers(self):
        """Сохраняет состояние таймеров в JSON файл"""
        timers_data = []
        for timer in self.timers:
            timers_data.append(timer.to_dict())

        try:
            with open("timers.json", "w", encoding="utf-8") as f:
                json.dump(timers_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения таймеров: {e}")

    def load_timers(self):
        """Загружает таймеры из JSON файла"""
        try:
            with open("timers.json", "r", encoding="utf-8") as f:
                timers_data = json.load(f)

            for timer_data in timers_data:
                timer = Timer(self, on_delete=self.remove_timer)
                timer.pack(in_=self.scrollable_frame, fill=tk.X)

                timer.description.delete(0, tk.END)
                timer.description.insert(0, timer_data["description"])

                timer.hours.set(timer_data["hours"])
                timer.minutes.set(timer_data["minutes"])
                timer.seconds.set(timer_data["seconds"])

                if timer_data.get("custom_sound"):
                    timer.custom_sound = timer_data["custom_sound"]
                    timer.sound_button.config(text="🔊 ✓")

                timer.update_presets_visibility()
                timer.update_time_display()
                self.timers.append(timer)

        except FileNotFoundError:
            self.add_default_timers()
        except Exception as e:
            print(f"Ошибка загрузки таймеров: {e}")
            self.add_default_timers()
