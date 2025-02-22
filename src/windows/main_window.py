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
from tabs.pushup_tracker_tab import PushupTrackerTab
from tabs.telegram_tab import TelegramTab
from tabs.todo_list_tab import TodoListTab
from utils.constants import IMAGES


class MainWindow(ThemedTk):
    def __init__(self):
        super().__init__(theme="ubuntu")
        self.iconbitmap(default=IMAGES["TRAY_ICON"])
        self.setup_global_styles()
        self.title("Мульти-таймер")
        self.timers = []
        self.setup_ui()
        self.is_wsl = self.check_wsl()
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

    def setup_ui(self):
        self.notebook = ttk.Notebook(self, takefocus=0)
        self.notebook.configure(takefocus=0)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.timers_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.timers_tab, text="Таймеры")

        self.pushups_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pushups_tab, text="Отжимания")

        self.todo_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.todo_tab, text="Задачи")

        self.habits_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.habits_tab, text="Привычки")

        self.telegram_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.telegram_tab, text="Telegram")

        self.setup_timers_ui()

        self.pushup_tracker = PushupTrackerTab(self.pushups_tab)
        self.pushup_tracker.pack(expand=True, fill=tk.BOTH)

        self.habits_tracker = HabitsTab(self.habits_tab)
        self.habits_tracker.pack(expand=True, fill=tk.BOTH)

        self.todo_list = TodoListTab(self.todo_tab)
        self.todo_list.pack(expand=True, fill=tk.BOTH)

        self.telegram_integration = TelegramTab(self.telegram_tab)
        self.telegram_integration.pack(expand=True, fill=tk.BOTH)

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

        self.canvas = tk.Canvas(self.timers_frame)
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

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.configure("Accent.TButton", padding=8, font=("Arial", 10, "bold"))
        style.configure("Secondary.TButton", padding=8, font=("Arial", 10))

        self.add_default_timers()

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
        if self.is_wsl:
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

    def remove_timer(self, timer):
        if timer in self.timers:
            self.timers.remove(timer)
            timer.destroy()
