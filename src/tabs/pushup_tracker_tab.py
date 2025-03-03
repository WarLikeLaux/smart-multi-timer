import json
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
from typing import Dict, List, Optional


class PushupStorage:
    def __init__(self):
        self._data: Dict[str, List[dict]] = {}
        self._modified: bool = False
        self._load()

    def add(self, date: str, count: int, time: str) -> None:
        if date not in self._data:
            self._data[date] = []
        self._data[date].append({"count": count, "time": time})
        self._modified = True

    def remove(self, date: str, index: int) -> None:
        if date in self._data and 0 <= index < len(self._data[date]):
            del self._data[date][index]
            self._modified = True

    def get_date_data(self, date: str) -> list:
        return self._data.get(date, [])

    def get_date_total(self, date: str) -> int:
        return sum(entry["count"] for entry in self.get_date_data(date))

    def save(self) -> None:
        if self._modified:
            with open("pushups.json", "w") as f:
                json.dump(self._data, f)
            self._modified = False

    def _load(self) -> None:
        try:
            with open("pushups.json", "r") as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._data = {}


class PushupTrackerTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.storage = PushupStorage()
        self.current_date = time.strftime("%Y-%m-%d")
        self.pushups_today = self.storage.get_date_total(self.current_date)
        self.setup_ui()
        self._load_today_data()

    def setup_ui(self):
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self._create_date_panel()

        self._create_stats_panel()

        self._create_quick_buttons()

        self._create_manual_input()

        self._create_history_panel()

    def _create_date_panel(self):
        date_frame = ttk.Frame(self.main_container)
        date_frame.pack(fill=tk.X, pady=(0, 10))

        self.date_var = tk.StringVar(value=self.current_date)
        date_entry = ttk.Entry(
            date_frame,
            textvariable=self.date_var,
            state="readonly",
            width=10,
            font=("Arial", 12),
        )
        date_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            date_frame, text="←", command=self._prev_day, width=3, takefocus=0
        ).pack(side=tk.LEFT)

        ttk.Button(
            date_frame, text="→", command=self._next_day, width=3, takefocus=0
        ).pack(side=tk.LEFT)

    def _create_stats_panel(self):
        stats_frame = ttk.LabelFrame(self.main_container, text="Статистика", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 15))

        total_frame = ttk.Frame(stats_frame)
        total_frame.pack(pady=10)

        ttk.Label(total_frame, text="Отжимания сегодня:", font=("Arial", 14)).pack()

        self.total_label = ttk.Label(
            total_frame, text=str(self.pushups_today), font=("Arial", 24, "bold")
        )
        self.total_label.pack(pady=5)

        self.last_set_time = ttk.Label(
            stats_frame, text="Последний сет: --:--", font=("Arial", 10)
        )
        self.last_set_time.pack()

    def _create_quick_buttons(self):
        buttons_frame = ttk.LabelFrame(
            self.main_container, text="Быстрый ввод", padding=10
        )
        buttons_frame.pack(fill=tk.X, pady=(0, 15))

        for count in [10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
            btn = ttk.Button(
                buttons_frame,
                text=f"{count}",
                command=lambda c=count: self.add_pushups(c),
                width=8,
                takefocus=0,
            )
            btn.pack(side=tk.LEFT, padx=5)

    def _create_manual_input(self):
        input_frame = ttk.Frame(self.main_container)
        input_frame.pack(fill=tk.X, pady=(0, 15))

        self.count_var = tk.StringVar()
        self.manual_entry = ttk.Spinbox(
            input_frame,
            from_=1,
            to=100,
            width=5,
            textvariable=self.count_var,
            font=("Arial", 12),
        )
        self.manual_entry.set("1")
        self.manual_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            input_frame,
            text="Добавить",
            command=self._add_pushups_from_entry,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=5)

    def _create_history_panel(self):
        history_frame = ttk.LabelFrame(self.main_container, text="История", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_text = tk.Text(
            history_frame, height=10, font=("Arial", 10), wrap=tk.WORD
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            history_frame, orient="vertical", command=self.history_text.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_text.config(yscrollcommand=scrollbar.set)

    def add_pushups(self, count: int) -> None:
        current_time = time.strftime("%H:%M")
        self.storage.add(self.current_date, count, current_time)
        self.pushups_today = self.storage.get_date_total(self.current_date)

        self.total_label.config(text=str(self.pushups_today))
        self.last_set_time.config(text=f"Последний сет: {current_time}")

        self._update_display()
        self.storage.save()

    def _add_pushups_from_entry(self):
        try:
            count = int(self.count_var.get())
            if 0 < count <= 100:
                self.add_pushups(count)
                self.count_var.set("1")
            else:
                messagebox.showwarning("Ошибка", "Количество должно быть от 1 до 100")
        except ValueError:
            messagebox.showwarning("Ошибка", "Введите корректное число")

    def _prev_day(self) -> None:
        current = datetime.strptime(self.current_date, "%Y-%m-%d")
        self.current_date = (current - timedelta(days=1)).strftime("%Y-%m-%d")
        self.date_var.set(self.current_date)
        self._load_today_data()

    def _next_day(self) -> None:
        current = datetime.strptime(self.current_date, "%Y-%m-%d")
        self.current_date = (current + timedelta(days=1)).strftime("%Y-%m-%d")
        self.date_var.set(self.current_date)
        self._load_today_data()

    def _load_today_data(self) -> None:
        self.pushups_today = self.storage.get_date_total(self.current_date)
        self.total_label.config(text=str(self.pushups_today))
        self._update_display()

    def _create_history_panel(self):
        history_frame = ttk.LabelFrame(self.main_container, text="История", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем таблицу
        columns = ("time", "count", "actions")
        self.history_tree = ttk.Treeview(
            history_frame, columns=columns, show="headings", style="Modern.Treeview"
        )

        # Настройка стилей
        style = ttk.Style()
        style.configure(
            "Modern.Treeview",
            background="#ffffff",
            foreground="#2c3e50",
            rowheight=35,
            fieldbackground="#ffffff",
            font=("Arial", 10),
        )
        style.configure(
            "Modern.Treeview.Heading", font=("Arial", 11, "bold"), padding=10
        )

        self.history_tree.heading("time", text="Время")
        self.history_tree.heading("count", text="Количество")
        self.history_tree.heading("actions", text="")

        self.history_tree.column("time", width=100, anchor="center")
        self.history_tree.column("count", width=150, anchor="center")
        self.history_tree.column("actions", width=50, anchor="center")

        scrollbar = ttk.Scrollbar(
            history_frame, orient="vertical", command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _update_display(self) -> None:
        entries = self.storage.get_date_data(self.current_date)

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for i, entry in enumerate(entries):
            item_id = self.history_tree.insert(
                "",
                "end",
                values=(entry["time"], f"{entry['count']} отжиманий", "✕"),
                tags=(f"row_{i}", "clickable"),
            )

            if i % 2 == 0:
                self.history_tree.tag_configure(f"row_{i}", background="#f8f9fa")

        self.history_tree.tag_bind("clickable", "<Button-1>", self._handle_tree_click)

    def _handle_tree_click(self, event):
        region = self.history_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.history_tree.identify_row(event.y)
            col = self.history_tree.identify_column(event.x)

            if col == "#3":
                idx = self.history_tree.index(item)
                self._remove_entry(idx)

    def _setup_tooltips(self):
        self.tooltip = None
        self.history_tree.bind("<Motion>", self._show_tree_tooltip)
        self.history_tree.bind("<Leave>", self._hide_tree_tooltip)

    def _show_tree_tooltip(self, event):
        region = self.history_tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.history_tree.identify_row(event.y)
            col = self.history_tree.identify_column(event.x)

            if col == "#3":
                if not self.tooltip:
                    self.tooltip = tk.Label(
                        self,
                        text="Удалить запись",
                        background="#2c3e50",
                        foreground="white",
                        relief="solid",
                        borderwidth=1,
                        font=("Arial", 9),
                    )
                x, y, _, _ = self.history_tree.bbox(item, col)
                self.tooltip.place(
                    x=x + self.winfo_rootx() + 40, y=y + self.winfo_rooty() - 20
                )

    def _hide_tree_tooltip(self, event):
        if self.tooltip:
            self.tooltip.place_forget()

    def _remove_entry(self, index: int) -> None:
        if messagebox.askyesno("Подтверждение", "Удалить эту запись?"):
            self.storage.remove(self.current_date, index)
            self.pushups_today = self.storage.get_date_total(self.current_date)
            self.total_label.config(text=str(self.pushups_today))
            self._update_display()
            self.storage.save()

    def show_fullscreen(self):
        """Показать полноэкранный режим для быстрого ввода"""
        fullscreen = tk.Toplevel(self)
        fullscreen.attributes("-fullscreen", True)
        fullscreen.title("Отжимания")

        exit_btn = ttk.Button(fullscreen, text="✕", command=fullscreen.destroy, width=3)
        exit_btn.place(x=20, y=20)

        counter_frame = ttk.Frame(fullscreen)
        counter_frame.place(relx=0.5, rely=0.4, anchor="center")

        ttk.Label(counter_frame, text="ОТЖИМАНИЯ СЕГОДНЯ", font=("Arial", 36)).pack()

        ttk.Label(
            counter_frame, text=str(self.pushups_today), font=("Arial", 120, "bold")
        ).pack(pady=20)

        buttons_frame = ttk.Frame(fullscreen)
        buttons_frame.place(relx=0.5, rely=0.8, anchor="center")

        for count in [10, 15, 20, 25, 30, 35, 40, 45, 50, 55]:
            btn = ttk.Button(
                buttons_frame,
                text=str(count),
                command=lambda c=count: (self.add_pushups(c), fullscreen.destroy()),
                width=10,
                style="Big.TButton",
            )
            btn.pack(side=tk.LEFT, padx=10)

        style = ttk.Style()
        style.configure("Big.TButton", padding=20, font=("Arial", 16))

        fullscreen.bind("<Escape>", lambda e: fullscreen.destroy())

        for i, count in enumerate([10, 15, 20, 25, 30, 35, 40, 45, 50, 55], 1):
            fullscreen.bind(
                str(i), lambda e, c=count: (self.add_pushups(c), fullscreen.destroy())
            )
