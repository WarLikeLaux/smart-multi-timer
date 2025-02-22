import time
import tkinter as tk
from tkinter import messagebox, ttk


class PushupTrackerTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        style = ttk.Style()
        style.configure("Accent.TButton", padding=5, font=("Arial", 10, "bold"))
        self.pushups_today = 0
        self.setup_ui()

    def setup_ui(self):
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)

        stats_frame = ttk.LabelFrame(main_container, text="Статистика", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 15))

        total_frame = ttk.Frame(stats_frame)
        total_frame.pack(pady=10)
        ttk.Label(total_frame, text="Отжимания сегодня:", font=("Arial", 14)).pack()
        self.total_label = ttk.Label(total_frame, text="0", font=("Arial", 24, "bold"))
        self.total_label.pack(pady=5)

        self.last_set_time = ttk.Label(
            stats_frame, text="Последний сет: --:--", font=("Arial", 10)
        )
        self.last_set_time.pack()

        actions_frame = ttk.LabelFrame(
            main_container, text="Добавить отжимания", padding=10
        )
        actions_frame.pack(fill=tk.X, pady=(0, 15))

        quick_btns_frame = ttk.Frame(actions_frame)
        quick_btns_frame.pack(fill=tk.X, pady=(0, 10))

        for count in [10, 15, 20, 25, 30]:
            btn = ttk.Button(
                quick_btns_frame,
                text=f"{count} отжиманий",
                command=lambda c=count: self.add_pushups(c),
                takefocus=0,
            )
            btn.pack(side=tk.LEFT, padx=5)

        manual_frame = ttk.Frame(actions_frame)
        manual_frame.pack(fill=tk.X)

        self.manual_entry = ttk.Spinbox(
            manual_frame, from_=1, to=100, width=5, font=("Arial", 12)
        )
        self.manual_entry.set("1")
        self.manual_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            manual_frame,
            text="Добавить",
            style="Accent.TButton",
            command=self.add_manual,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=5)

        history_frame = ttk.LabelFrame(
            main_container, text="История за сегодня", padding=10
        )
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_text = tk.Text(
            history_frame, height=8, font=("Arial", 10), wrap=tk.WORD, state=tk.DISABLED
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)

    def add_pushups(self, count):
        current_time = time.strftime("%H:%M")
        self.pushups_today += count
        self.total_label.config(text=str(self.pushups_today))
        self.last_set_time.config(text=f"Последний сет: {current_time}")

        self.history_text.config(state=tk.NORMAL)
        self.history_text.insert(
            "1.0", f"[{current_time}] Добавлено {count} отжиманий\n"
        )
        self.history_text.config(state=tk.DISABLED)

    def add_manual(self):
        try:
            count = int(self.manual_entry.get())
            self.add_pushups(count)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число")

    def remove_last(self):
        if messagebox.askyesno("Подтверждение", "Удалить последний set?"):
            try:
                last_value = int(self.manual_entry.get())
                self.pushups_today = max(0, self.pushups_today - last_value)
                self.total_label.config(text=str(self.pushups_today))
            except ValueError:
                messagebox.showerror("Ошибка", "Не удалось определить последний set")
