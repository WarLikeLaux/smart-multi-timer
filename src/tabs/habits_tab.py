import json
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from utils.habit_reminder import HabitReminder


class HabitsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.habits = []
        self.setup_ui()
        self.load_habits()
        self.reminder = HabitReminder(self)

    def setup_ui(self):
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        header = ttk.Frame(main_container)
        header.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header, text="Привычки", font=("Arial", 16, "bold")).pack(
            side=tk.LEFT
        )
        ttk.Button(
            header,
            text="+ Добавить привычку",
            command=self.add_habit_dialog,
            style="Accent.TButton",
        ).pack(side=tk.RIGHT)

        self.habits_frame = ttk.Frame(main_container)
        self.habits_frame.pack(fill=tk.BOTH, expand=True)

    def add_habit_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Новая привычка")
        dialog.geometry("400x350")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="20 15 20 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Название привычки:", font=("Segoe UI", 10)).pack(
            anchor=tk.W
        )
        name_entry = ttk.Entry(main_frame, width=40, font=("Segoe UI", 11))
        name_entry.pack(fill=tk.X, pady=(5, 15))

        ttk.Label(main_frame, text="Напоминать каждые:", font=("Segoe UI", 10)).pack(
            anchor=tk.W
        )
        interval_frame = ttk.Frame(main_frame)
        interval_frame.pack(fill=tk.X, pady=(5, 15))

        interval_entry = ttk.Spinbox(
            interval_frame, from_=1, to=999, width=8, font=("Segoe UI", 11)
        )
        interval_entry.set("30")
        interval_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(interval_frame, text="минут", font=("Segoe UI", 10)).pack(
            side=tk.LEFT
        )

        ttk.Label(main_frame, text="Время напоминаний:", font=("Segoe UI", 10)).pack(
            anchor=tk.W
        )
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=(5, 20))

        start_frame = ttk.Frame(time_frame)
        start_frame.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="С:", font=("Segoe UI", 10)).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        start_hour = ttk.Spinbox(
            start_frame, from_=0, to=23, width=3, font=("Segoe UI", 11)
        )
        start_hour.set("09")
        start_hour.pack(side=tk.LEFT)
        ttk.Label(start_frame, text=":", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        start_minute = ttk.Spinbox(
            start_frame, from_=0, to=59, width=3, font=("Segoe UI", 11)
        )
        start_minute.set("00")
        start_minute.pack(side=tk.LEFT)

        end_frame = ttk.Frame(time_frame)
        end_frame.pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(end_frame, text="До:", font=("Segoe UI", 10)).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        end_hour = ttk.Spinbox(
            end_frame, from_=0, to=23, width=3, font=("Segoe UI", 11)
        )
        end_hour.set("22")
        end_hour.pack(side=tk.LEFT)
        ttk.Label(end_frame, text=":", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        end_minute = ttk.Spinbox(
            end_frame, from_=0, to=59, width=3, font=("Segoe UI", 11)
        )
        end_minute.set("00")
        end_minute.pack(side=tk.LEFT)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        def save_habit():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название привычки")
                return

            habit = {
                "name": name,
                "interval": int(interval_entry.get()),
                "start_time": f"{start_hour.get()}:{start_minute.get()}",
                "end_time": f"{end_hour.get()}:{end_minute.get()}",
                "enabled": True,
                "last_reminder": None,
            }

            self.add_habit_to_list(habit)
            self.save_habits()
            dialog.destroy()

        ttk.Button(
            btn_frame, text="Отмена", style="Secondary.TButton", command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame, text="Сохранить", style="Accent.TButton", command=save_habit
        ).pack(side=tk.RIGHT)

    def add_habit_to_list(self, habit_data):
        habit_frame = ttk.Frame(self.habits_frame, style="Card.TFrame")
        habit_frame.pack(fill=tk.X, pady=5)

        enabled_var = tk.BooleanVar(value=habit_data["enabled"])
        enabled_check = ttk.Checkbutton(
            habit_frame,
            variable=enabled_var,
            command=lambda: self.toggle_habit(habit_data, enabled_var.get()),
            takefocus=0,
        )
        enabled_check.pack(side=tk.LEFT, padx=10)

        info_frame = ttk.Frame(habit_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=10)

        ttk.Label(
            info_frame, text=habit_data["name"], font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W)

        ttk.Label(
            info_frame,
            text=f"Каждые {habit_data['interval']} мин • {habit_data['start_time']} - {habit_data['end_time']}",
            font=("Segoe UI", 10),
        ).pack(anchor=tk.W)

        ttk.Button(
            habit_frame,
            text="✕",
            style="Delete.TButton",
            command=lambda: self.delete_habit(habit_frame, habit_data),
            takefocus=0,
        ).pack(side=tk.RIGHT, padx=10)

        self.habits.append(habit_data)

    def toggle_habit(self, habit, enabled):
        """Включает/выключает привычку"""
        habit["enabled"] = enabled
        self.save_habits()

    def delete_habit(self, habit_frame, habit):
        """Удаляет привычку"""
        if messagebox.askyesno("Подтверждение", "Удалить привычку?"):
            if habit in self.habits:
                self.habits.remove(habit)
            habit_frame.destroy()
            self.save_habits()

    def save_habits(self):
        habits_data = []
        for habit in self.habits:
            last_reminder = habit.get("last_reminder")
            if isinstance(last_reminder, datetime):
                last_reminder = last_reminder.isoformat()

            habits_data.append(
                {
                    "name": habit["name"],
                    "interval": habit["interval"],
                    "start_time": habit["start_time"],
                    "end_time": habit["end_time"],
                    "enabled": habit["enabled"],
                    "last_reminder": last_reminder,
                }
            )

        with open("habits.json", "w", encoding="utf-8") as f:
            json.dump(habits_data, f, ensure_ascii=False, indent=2)

    def load_habits(self):
        try:
            with open("habits.json", "r", encoding="utf-8") as f:
                habits_data = json.load(f)
                for habit_data in habits_data:
                    if not all(
                        key in habit_data
                        for key in [
                            "name",
                            "interval",
                            "start_time",
                            "end_time",
                            "enabled",
                        ]
                    ):
                        print(f"Пропущена привычка с неполными данными: {habit_data}")
                        continue

                    if "last_reminder" in habit_data and habit_data["last_reminder"]:
                        try:
                            habit_data["last_reminder"] = datetime.fromisoformat(
                                habit_data["last_reminder"]
                            )
                        except ValueError:
                            habit_data["last_reminder"] = None
                    else:
                        habit_data["last_reminder"] = None

                    self.add_habit_to_list(habit_data)

        except FileNotFoundError:
            print("Файл habits.json не найден. Создаем новый список привычек.")
        except json.JSONDecodeError:
            print("Ошибка чтения файла habits.json. Файл поврежден.")
        except Exception as e:
            print(f"Непредвиденная ошибка при загрузке привычек: {e}")
