import json
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
from pygame import mixer

from utils.habit_reminder import HabitReminder


class HabitsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.habits = {}
        self.default_times = ["Утро", "День", "Вечер", "Ночь"]
        self.custom_times = []
        self.all_times = self.default_times.copy()
        self.time_settings = {}
        self.toast_notification = None
        self.stats_window = None

        for time_period in self.default_times:
            self.habits[time_period] = []
            self.time_settings[time_period] = {"quick_timer_minutes": None}

        self.setup_ui()
        self.load_habits()
        self.reminder = HabitReminder(self)

    def setup_ui(self):
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        header = ttk.Frame(main_container)
        header.pack(fill=tk.X, pady=(0, 15))

        title_frame = ttk.Frame(header)
        title_frame.pack(side=tk.LEFT)

        ttk.Label(title_frame, text="Привычки", font=("Arial", 16, "bold")).pack(
            side=tk.LEFT
        )

        self.compact_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            title_frame,
            text="Компактный режим",
            variable=self.compact_mode,
            command=self.toggle_compact_mode,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=10)

        # Добавляем кнопку статистики
        ttk.Button(
            title_frame,
            text="Статистика",
            style="Secondary.TButton",
            command=self.show_stats,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=10)

        # Добавляем кнопку сброса всех отметок привычек
        ttk.Button(
            title_frame,
            text="Сбросить все отметки",
            style="Secondary.TButton",
            command=self.reset_all_habits,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=10)

        # Отображение количества выполненных привычек сегодня
        self.stats_label = ttk.Label(title_frame, text="", font=("Segoe UI", 9))
        self.stats_label.pack(side=tk.LEFT, padx=5)

        buttons_frame = ttk.Frame(header)
        buttons_frame.pack(side=tk.RIGHT)

        ttk.Button(
            buttons_frame,
            text="+ Добавить время",
            style="Secondary.TButton",
            command=self.add_custom_time,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=5)

        canvas_container = ttk.Frame(main_container)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        bg_color = self.winfo_toplevel().cget("bg")

        self.canvas = tk.Canvas(
            canvas_container, bg=bg_color, highlightthickness=0, bd=0
        )
        scrollbar = ttk.Scrollbar(
            canvas_container, orient="vertical", command=self.canvas.yview
        )

        self.times_frame = ttk.Frame(self.canvas)
        self.times_frame.configure(style="TFrame")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_frame = self.canvas.create_window(
            (0, 0), window=self.times_frame, anchor="nw"
        )

        self.times_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.bind("<Map>", lambda e: self.after(500, self.update_times_display))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Обновляем статистику при запуске
        self.update_stats_display()

    def _on_mousewheel(self, event):
        if not self.compact_mode.get():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_frame_configure(self, event=None):
        if not self.compact_mode.get():
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=width)

        if self.compact_mode.get():
            self.update_times_display()

    def toggle_compact_mode(self):
        self.update_times_display()

        is_compact = self.compact_mode.get()
        width = self.canvas.winfo_width()

        if is_compact:
            self.canvas.yview_moveto(0)
        else:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def create_time_frame(self, parent, time_name):
        frame = ttk.LabelFrame(parent, text=time_name, padding=10)

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        if not self.compact_mode.get():
            if time_name not in self.default_times:
                ttk.Button(
                    control_frame,
                    text="🗑",
                    width=3,
                    command=lambda: self.remove_time(time_name),
                    takefocus=0,
                ).pack(side=tk.RIGHT, padx=2)

            ttk.Button(
                control_frame,
                text="↑",
                width=3,
                command=lambda: self.move_time(time_name, -1),
                takefocus=0,
            ).pack(side=tk.LEFT, padx=2)
            ttk.Button(
                control_frame,
                text="↓",
                width=3,
                command=lambda: self.move_time(time_name, 1),
                takefocus=0,
            ).pack(side=tk.LEFT, padx=2)

            timer_settings_frame = ttk.Frame(control_frame)
            timer_settings_frame.pack(side=tk.RIGHT, padx=(10, 0))

            ttk.Label(timer_settings_frame, text="Быстрый таймер (мин):").pack(
                side=tk.LEFT
            )

            quick_timer_var = tk.StringVar(
                value=(
                    str(
                        self.time_settings.get(time_name, {}).get(
                            "quick_timer_minutes", ""
                        )
                    )
                    if self.time_settings.get(time_name, {}).get("quick_timer_minutes")
                    is not None
                    else ""
                )
            )

            quick_timer_entry = ttk.Spinbox(
                timer_settings_frame,
                from_=1,
                to=180,
                width=5,
                textvariable=quick_timer_var,
            )
            quick_timer_entry.pack(side=tk.LEFT, padx=5)

            def save_quick_timer_minutes(event=None):
                try:
                    value = quick_timer_var.get().strip()
                    if value:
                        self.time_settings[time_name]["quick_timer_minutes"] = int(
                            value
                        )
                    else:
                        self.time_settings[time_name]["quick_timer_minutes"] = None
                    self.save_habits()
                    self.update_times_display()
                except ValueError:
                    pass

            quick_timer_entry.bind("<FocusOut>", save_quick_timer_minutes)
            quick_timer_entry.bind("<Return>", save_quick_timer_minutes)

        habits_frame = ttk.Frame(frame)
        habits_frame.pack(fill=tk.BOTH, expand=True)

        if not self.compact_mode.get():
            add_frame = ttk.Frame(frame)
            add_frame.pack(fill=tk.X, pady=(10, 0))

            entry = ttk.Entry(add_frame)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            ttk.Button(
                add_frame,
                text="Добавить привычку",
                command=lambda: self.add_habit(time_name, entry),
                takefocus=0,
            ).pack(side=tk.LEFT, padx=5)

        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        buttons_right_frame = ttk.Frame(buttons_frame)
        buttons_right_frame.pack(side=tk.RIGHT)

        timer_button = ttk.Button(
            buttons_right_frame,
            text="⏱ Таймер",
            command=lambda: self.start_timer_for_time(time_name),
            takefocus=0,
        )
        timer_button.pack(side=tk.LEFT, padx=5)

        quick_timer_minutes = self.time_settings.get(time_name, {}).get(
            "quick_timer_minutes"
        )
        if quick_timer_minutes is not None:
            quick_timer_button = ttk.Button(
                buttons_right_frame,
                text=f"⏱ {quick_timer_minutes} мин",
                command=lambda minutes=quick_timer_minutes, name=time_name: self.create_quick_timer(
                    name, minutes
                ),
                takefocus=0,
            )
            quick_timer_button.pack(side=tk.LEFT, padx=5)

        self.update_habits_list(time_name, habits_frame)

        return frame

    def move_time(self, time_name, direction):
        current_index = self.all_times.index(time_name)
        new_index = current_index + direction

        if 0 <= new_index < len(self.all_times):
            self.all_times.remove(time_name)
            self.all_times.insert(new_index, time_name)
            self.update_times_display()
            self.save_habits()

    def move_habit(self, time_name, habit_name, direction):
        habits = self.habits[time_name]
        for i, habit in enumerate(habits):
            if habit["name"] == habit_name:
                if 0 <= i + direction < len(habits):
                    habits[i], habits[i + direction] = habits[i + direction], habits[i]
                    self.update_times_display()
                    self.save_habits()
                    break

    def update_times_display(self):
        for widget in self.times_frame.winfo_children():
            widget.destroy()

        bg_color = self.winfo_toplevel().cget("bg")
        self.canvas.configure(bg=bg_color)

        width = self.winfo_width()
        if width < 600:
            max_cols = 1
        elif width < 900:
            max_cols = 2
        else:
            max_cols = 3

        current_row = None
        col_count = 0

        for time_name in self.all_times:
            # В компактном режиме скрываем времена без включенных привычек
            if self.compact_mode.get():
                has_enabled_habits = False
                for habit in self.habits.get(time_name, []):
                    if habit.get("enabled", True):
                        has_enabled_habits = True
                        break
                if not has_enabled_habits:
                    continue

            if col_count % max_cols == 0:
                current_row = ttk.Frame(self.times_frame)
                current_row.pack(fill=tk.X, expand=True, pady=5)

            frame = self.create_time_frame(current_row, time_name)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            col_count += 1

        self.times_frame.update_idletasks()

        if not self.compact_mode.get():
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_habits_list(self, time_name, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        if time_name not in self.habits:
            self.habits[time_name] = []

        for habit in self.habits[time_name]:
            # В компактном режиме скрываем отключенные привычки
            if self.compact_mode.get() and not habit.get("enabled", True):
                continue

            habit_frame = ttk.Frame(frame)
            habit_frame.pack(fill=tk.X, pady=5)

            # Чекбокс для включения/отключения привычки - скрываем в компактном режиме
            if not self.compact_mode.get():
                enabled_var = tk.BooleanVar(value=habit.get("enabled", True))
                ttk.Checkbutton(
                    habit_frame,
                    variable=enabled_var,
                    command=lambda h=habit, v=enabled_var: self.toggle_habit(
                        h, v.get()
                    ),
                    takefocus=0,
                ).pack(side=tk.LEFT, padx=5)

            # Добавляем чекбоксы для отметки повторений
            repeats = habit.get("repeats", 1)
            completed_repeats = habit.get("completed_repeats", 0)
            completed = habit.get("completed", False)

            checkboxes_frame = ttk.Frame(habit_frame)
            checkboxes_frame.pack(side=tk.LEFT, padx=3)

            # Создаем чекбоксы для повторений (от 1 до 5)
            max_visible_repeats = min(repeats, 5)  # Показываем максимум 5 чекбоксов

            for i in range(max_visible_repeats):
                is_checked = i < completed_repeats or completed
                checkbox_var = tk.BooleanVar(value=is_checked)

                checkbox = ttk.Checkbutton(
                    checkboxes_frame,
                    variable=checkbox_var,
                    command=lambda h=habit, index=i, var=checkbox_var: self.toggle_repeat(
                        h, index, var.get()
                    ),
                    style="Orange.TCheckbutton",
                    takefocus=0,
                )
                checkbox.pack(side=tk.LEFT)

            # Если повторений больше 5, добавляем счетчик
            if repeats > 5:
                ttk.Label(
                    checkboxes_frame, text=f"+{repeats - 5}", font=("Segoe UI", 9)
                ).pack(side=tk.LEFT, padx=(2, 0))

            # Отключение уведомлений
            notifications_var = tk.BooleanVar(value=habit.get("notifications", True))
            notify_btn = ttk.Button(
                habit_frame,
                text="🔔" if notifications_var.get() else "🔕",
                width=3,
                command=lambda h=habit, v=notifications_var: self.toggle_notifications(
                    h, v
                ),
                takefocus=0,
            )
            notify_btn.pack(side=tk.LEFT, padx=3)

            info_frame = ttk.Frame(habit_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            name_label = ttk.Label(
                info_frame, text=habit["name"], font=("Segoe UI", 11)
            )

            # Используем серый цвет для выполненных привычек
            if habit.get("completed", False):
                name_label.configure(foreground="gray")
            name_label.pack(anchor=tk.W)

            # Отображаем дополнительную информацию
            info_text = ""

            # Показываем комментарий, если есть
            if habit.get("comment"):
                info_text += f"\"{habit['comment']}\" "

            # Отображаем интервал и время только если уведомления включены
            if habit.get("notifications", True):
                interval_text = f"Каждые {habit.get('interval', '')} мин"
                time_text = (
                    f"{habit.get('start_time', '')} - {habit.get('end_time', '')}"
                )
                if info_text:
                    info_text += f"• {interval_text} • {time_text}"
                else:
                    info_text = f"{interval_text} • {time_text}"

            if info_text:
                ttk.Label(
                    info_frame,
                    text=info_text,
                    font=("Segoe UI", 9),
                ).pack(anchor=tk.W)

            buttons_frame = ttk.Frame(habit_frame)
            buttons_frame.pack(side=tk.RIGHT)

            if not self.compact_mode.get():
                # Кнопка комментария
                ttk.Button(
                    buttons_frame,
                    text="💬",
                    width=2,
                    command=lambda h=habit: self.add_comment(h),
                    takefocus=0,
                ).pack(side=tk.LEFT, padx=2)

                # Кнопка редактирования
                ttk.Button(
                    buttons_frame,
                    text="✏️",
                    width=2,
                    command=lambda h=habit, tn=time_name: self.edit_habit(h, tn),
                    takefocus=0,
                ).pack(side=tk.LEFT, padx=2)

                ttk.Button(
                    buttons_frame,
                    text="↑",
                    width=2,
                    command=lambda n=habit["name"]: self.move_habit(time_name, n, -1),
                    takefocus=0,
                ).pack(side=tk.LEFT, padx=2)

                ttk.Button(
                    buttons_frame,
                    text="↓",
                    width=2,
                    command=lambda n=habit["name"]: self.move_habit(time_name, n, 1),
                    takefocus=0,
                ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                buttons_frame,
                text="✕",
                width=2,
                command=lambda h=habit: self.remove_habit(time_name, h),
                takefocus=0,
            ).pack(side=tk.LEFT, padx=2)

    def toggle_completion(self, habit):
        """Отмечает привычку как выполненную или нет, управляет счетчиком выполненных повторений"""
        if not habit["enabled"]:
            return

        max_repeats = habit.get("repeats", 1)
        completed_repeats = habit.get("completed_repeats", 0)

        # Если привычка уже полностью выполнена, сбрасываем ее
        if habit.get("completed", False) and completed_repeats >= max_repeats:
            habit["completed"] = False
            habit["completed_repeats"] = 0
            habit["comment"] = ""
        else:
            # Увеличиваем количество повторений
            habit["completed_repeats"] = completed_repeats + 1

            # Если достигнуто максимальное количество повторений, отмечаем как выполненную
            if habit["completed_repeats"] >= max_repeats:
                habit["completed"] = True

                # Запрашиваем комментарий, если его еще нет
                if not habit.get("comment"):
                    self.add_comment(habit)
            else:
                habit["completed"] = False

        # Сохраняем изменения и обновляем отображение
        self.save_habits()
        self.update_times_display()
        self.update_stats_display()  # Обновляем статистику

    def reset_completion(self):
        """Сбрасывает статус выполнения привычек каждый день в полночь"""
        current_date = datetime.now().date()

        # Проверяем, не изменилась ли дата с прошлого запуска
        last_reset_date = self.get_last_reset_date()

        if last_reset_date != current_date:
            # Сбрасываем выполнение для всех привычек
            for time_name, habits_list in self.habits.items():
                for habit in habits_list:
                    habit["completed"] = False
                    habit["completed_repeats"] = 0
                    habit["comment"] = ""

            # Обновляем дату последнего сброса
            self.set_last_reset_date(current_date)
            self.save_habits()
            self.update_times_display()
            self.update_stats_display()  # Обновляем статистику

    def get_last_reset_date(self):
        """Возвращает дату последнего сброса привычек"""
        try:
            config = self.load_json("habits_config.json")
            date_str = config.get("last_reset_date")
            if date_str:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            pass
        return datetime.now().date()

    def set_last_reset_date(self, date):
        """Устанавливает дату последнего сброса привычек"""
        try:
            config = self.load_json("habits_config.json")
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        config["last_reset_date"] = date.strftime("%Y-%m-%d")
        self.save_json("habits_config.json", config)

    def toggle_notifications(self, habit, notify_var):
        """Включает/выключает уведомления для привычки"""
        notifications = not habit.get("notifications", True)
        habit["notifications"] = notifications
        notify_var.set(notifications)
        self.save_habits()
        self.update_times_display()

    def edit_habit(self, habit, time_name):
        """Открывает диалог редактирования привычки"""
        dialog = tk.Toplevel(self)
        dialog.title("Редактировать привычку")
        dialog.geometry("500x700")  # Увеличенный размер окна
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="20 20 20 20")  # Увеличенные отступы
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Название привычки:", font=("Segoe UI", 11)).pack(
            anchor=tk.W
        )
        name_entry = ttk.Entry(main_frame, width=40, font=("Segoe UI", 11))
        name_entry.insert(0, habit["name"])
        name_entry.pack(fill=tk.X, pady=(5, 20))  # Увеличенный отступ снизу
        self.add_copy_paste_menu(name_entry)

        # Секция для настройки повторений
        repeats_frame = ttk.Frame(main_frame)
        repeats_frame.pack(fill=tk.X, pady=(0, 20))  # Увеличенный отступ снизу

        ttk.Label(repeats_frame, text="Повторений:", font=("Segoe UI", 11)).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        repeats_var = tk.StringVar(value=str(habit.get("repeats", 1)))
        repeats_entry = ttk.Spinbox(
            repeats_frame,
            from_=1,
            to=100,
            width=5,
            font=("Segoe UI", 11),
            textvariable=repeats_var,
        )
        repeats_entry.pack(side=tk.LEFT)
        self.add_copy_paste_menu(repeats_entry)

        ttk.Label(main_frame, text="Напоминать каждые:", font=("Segoe UI", 11)).pack(
            anchor=tk.W
        )
        interval_frame = ttk.Frame(main_frame)
        interval_frame.pack(fill=tk.X, pady=(5, 20))  # Увеличенный отступ снизу

        interval_entry = ttk.Spinbox(
            interval_frame, from_=1, to=999, width=8, font=("Segoe UI", 11)
        )
        interval_entry.set(str(habit["interval"]))
        interval_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.add_copy_paste_menu(interval_entry)

        ttk.Label(interval_frame, text="минут", font=("Segoe UI", 11)).pack(
            side=tk.LEFT
        )

        ttk.Label(main_frame, text="Время напоминаний:", font=("Segoe UI", 11)).pack(
            anchor=tk.W
        )
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=(5, 20))  # Увеличенный отступ снизу

        start_frame = ttk.Frame(time_frame)
        start_frame.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="С:", font=("Segoe UI", 11)).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        start_time = habit["start_time"].split(":")
        start_hour = ttk.Spinbox(
            start_frame, from_=0, to=23, width=3, font=("Segoe UI", 11)
        )
        start_hour.set(start_time[0])
        start_hour.pack(side=tk.LEFT)
        self.add_copy_paste_menu(start_hour)

        ttk.Label(start_frame, text=":", font=("Segoe UI", 11)).pack(side=tk.LEFT)
        start_minute = ttk.Spinbox(
            start_frame, from_=0, to=59, width=3, font=("Segoe UI", 11)
        )
        start_minute.set(start_time[1])
        start_minute.pack(side=tk.LEFT)
        self.add_copy_paste_menu(start_minute)

        end_frame = ttk.Frame(time_frame)
        end_frame.pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(end_frame, text="До:", font=("Segoe UI", 11)).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        end_time = habit["end_time"].split(":")
        end_hour = ttk.Spinbox(
            end_frame, from_=0, to=23, width=3, font=("Segoe UI", 11)
        )
        end_hour.set(end_time[0])
        end_hour.pack(side=tk.LEFT)
        self.add_copy_paste_menu(end_hour)

        ttk.Label(end_frame, text=":", font=("Segoe UI", 11)).pack(side=tk.LEFT)
        end_minute = ttk.Spinbox(
            end_frame, from_=0, to=59, width=3, font=("Segoe UI", 11)
        )
        end_minute.set(end_time[1])
        end_minute.pack(side=tk.LEFT)
        self.add_copy_paste_menu(end_minute)

        # Настройки уведомлений
        notifications_frame = ttk.Frame(main_frame)
        notifications_frame.pack(fill=tk.X, pady=(5, 15))  # Увеличенный отступ снизу

        notifications_var = tk.BooleanVar(value=habit.get("notifications", True))
        ttk.Checkbutton(
            notifications_frame,
            text="Отправлять уведомления",
            variable=notifications_var,
            takefocus=0,
            style="Orange.TCheckbutton",  # Оранжевый стиль чекбокса
        ).pack(anchor=tk.W)

        # Комментарий
        ttk.Label(
            main_frame, text="Комментарий (необязательно):", font=("Segoe UI", 11)
        ).pack(anchor=tk.W, pady=(10, 5))

        comment_text = tk.Text(
            main_frame, height=4, width=40, wrap=tk.WORD, font=("Segoe UI", 11)
        )
        if habit.get("comment"):
            comment_text.insert("1.0", habit["comment"])
        comment_text.pack(fill=tk.X, pady=(0, 15))  # Увеличенный отступ снизу
        self.add_copy_paste_menu(comment_text)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        def save_edited_habit():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название привычки")
                return

            # Проверка на дублирование названия привычки (исключая текущую)
            for h in self.habits.get(time_name, []):
                if h["name"] == name and h != habit:
                    messagebox.showwarning(
                        "Ошибка", f"Привычка '{name}' уже существует"
                    )
                    return

            # Получаем количество повторений
            try:
                repeats = int(repeats_var.get())
                if repeats < 1:
                    repeats = 1
            except ValueError:
                repeats = 1

            start_time = f"{start_hour.get().zfill(2)}:{start_minute.get().zfill(2)}"
            end_time = f"{end_hour.get().zfill(2)}:{end_minute.get().zfill(2)}"

            comment = comment_text.get("1.0", tk.END).strip()

            # Обновляем данные привычки
            habit["name"] = name
            habit["interval"] = int(interval_entry.get())
            habit["start_time"] = start_time
            habit["end_time"] = end_time
            habit["notifications"] = notifications_var.get()
            habit["repeats"] = repeats
            habit["comment"] = comment

            # Если текущее количество выполнений больше нового максимума, сбрасываем
            if habit.get("completed_repeats", 0) > repeats:
                habit["completed_repeats"] = repeats

            # Проверяем, не нужно ли изменить статус выполнения привычки
            if habit.get("completed_repeats", 0) >= repeats:
                habit["completed"] = True
            else:
                habit["completed"] = False

            self.update_times_display()
            self.update_stats_display()  # Обновляем статистику
            self.save_habits()
            dialog.destroy()

        # Увеличенные размеры кнопок
        ttk.Button(
            btn_frame,
            text="Отмена",
            style="Secondary.TButton",
            command=dialog.destroy,
            width=15,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame,
            text="Сохранить",
            style="Accent.TButton",
            command=save_edited_habit,
            width=15,
        ).pack(side=tk.RIGHT)

        # Центрирование диалога
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")

    def add_habit(self, time_name, entry):
        habit_name = entry.get().strip()
        if not habit_name:
            messagebox.showwarning("Ошибка", "Введите название привычки")
            return

        self.add_habit_dialog(time_name, habit_name)
        entry.delete(0, tk.END)

    def add_habit_dialog(self, time_name, habit_name):
        dialog = tk.Toplevel(self)
        dialog.title("Новая привычка")
        dialog.geometry("500x700")  # Увеличенный размер окна
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="20 20 20 20")  # Увеличенные отступы
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Название привычки:", font=("Segoe UI", 11)).pack(
            anchor=tk.W
        )
        name_entry = ttk.Entry(main_frame, width=40, font=("Segoe UI", 11))
        name_entry.insert(0, habit_name)
        name_entry.pack(fill=tk.X, pady=(5, 20))  # Увеличенный отступ снизу
        self.add_copy_paste_menu(name_entry)

        # Секция для настройки повторений
        repeats_frame = ttk.Frame(main_frame)
        repeats_frame.pack(fill=tk.X, pady=(0, 20))  # Увеличенный отступ снизу

        ttk.Label(repeats_frame, text="Повторений:", font=("Segoe UI", 11)).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        repeats_var = tk.StringVar(value="1")
        repeats_entry = ttk.Spinbox(
            repeats_frame,
            from_=1,
            to=100,
            width=5,
            font=("Segoe UI", 11),
            textvariable=repeats_var,
        )
        repeats_entry.pack(side=tk.LEFT)
        self.add_copy_paste_menu(repeats_entry)

        ttk.Label(main_frame, text="Напоминать каждые:", font=("Segoe UI", 11)).pack(
            anchor=tk.W
        )
        interval_frame = ttk.Frame(main_frame)
        interval_frame.pack(fill=tk.X, pady=(5, 20))  # Увеличенный отступ снизу

        interval_entry = ttk.Spinbox(
            interval_frame, from_=1, to=999, width=8, font=("Segoe UI", 11)
        )
        interval_entry.set("30")
        interval_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.add_copy_paste_menu(interval_entry)

        ttk.Label(interval_frame, text="минут", font=("Segoe UI", 11)).pack(
            side=tk.LEFT
        )

        ttk.Label(main_frame, text="Время напоминаний:", font=("Segoe UI", 11)).pack(
            anchor=tk.W
        )
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=(5, 20))  # Увеличенный отступ снизу

        start_frame = ttk.Frame(time_frame)
        start_frame.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="С:", font=("Segoe UI", 11)).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        start_hour = ttk.Spinbox(
            start_frame, from_=0, to=23, width=3, font=("Segoe UI", 11)
        )
        start_hour.set("09")
        start_hour.pack(side=tk.LEFT)
        self.add_copy_paste_menu(start_hour)

        ttk.Label(start_frame, text=":", font=("Segoe UI", 11)).pack(side=tk.LEFT)
        start_minute = ttk.Spinbox(
            start_frame, from_=0, to=59, width=3, font=("Segoe UI", 11)
        )
        start_minute.set("00")
        start_minute.pack(side=tk.LEFT)
        self.add_copy_paste_menu(start_minute)

        end_frame = ttk.Frame(time_frame)
        end_frame.pack(side=tk.LEFT, padx=(20, 0))
        ttk.Label(end_frame, text="До:", font=("Segoe UI", 11)).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        end_hour = ttk.Spinbox(
            end_frame, from_=0, to=23, width=3, font=("Segoe UI", 11)
        )
        end_hour.set("22")
        end_hour.pack(side=tk.LEFT)
        self.add_copy_paste_menu(end_hour)

        ttk.Label(end_frame, text=":", font=("Segoe UI", 11)).pack(side=tk.LEFT)
        end_minute = ttk.Spinbox(
            end_frame, from_=0, to=59, width=3, font=("Segoe UI", 11)
        )
        end_minute.set("00")
        end_minute.pack(side=tk.LEFT)
        self.add_copy_paste_menu(end_minute)

        # Настройки уведомлений
        notifications_frame = ttk.Frame(main_frame)
        notifications_frame.pack(fill=tk.X, pady=(5, 15))  # Увеличенный отступ снизу

        notifications_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            notifications_frame,
            text="Отправлять уведомления",
            variable=notifications_var,
            takefocus=0,
            style="Orange.TCheckbutton",  # Оранжевый стиль чекбокса
        ).pack(anchor=tk.W)

        # Начальный комментарий
        ttk.Label(
            main_frame, text="Комментарий (необязательно):", font=("Segoe UI", 11)
        ).pack(anchor=tk.W, pady=(10, 5))

        comment_text = tk.Text(
            main_frame, height=4, width=40, wrap=tk.WORD, font=("Segoe UI", 11)
        )
        comment_text.pack(fill=tk.X, pady=(0, 15))  # Увеличенный отступ снизу
        self.add_copy_paste_menu(comment_text)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        def save_habit():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название привычки")
                return

            # Проверка на дублирование названия привычки
            for habit in self.habits.get(time_name, []):
                if habit["name"] == name:
                    messagebox.showwarning(
                        "Ошибка", f"Привычка '{name}' уже существует"
                    )
                    return

            # Получаем количество повторений
            try:
                repeats = int(repeats_var.get())
                if repeats < 1:
                    repeats = 1
            except ValueError:
                repeats = 1

            start_time = f"{start_hour.get().zfill(2)}:{start_minute.get().zfill(2)}"
            end_time = f"{end_hour.get().zfill(2)}:{end_minute.get().zfill(2)}"

            comment = comment_text.get("1.0", tk.END).strip()

            habit = {
                "name": name,
                "interval": int(interval_entry.get()),
                "start_time": start_time,
                "end_time": end_time,
                "enabled": True,
                "completed": False,
                "completed_repeats": 0,
                "repeats": repeats,
                "notifications": notifications_var.get(),
                "comment": comment,
                "last_reminder": None,
            }

            if time_name not in self.habits:
                self.habits[time_name] = []

            self.habits[time_name].append(habit)
            self.update_times_display()
            self.update_stats_display()  # Обновляем статистику
            self.save_habits()
            dialog.destroy()

        # Увеличенные размеры кнопок
        ttk.Button(
            btn_frame,
            text="Отмена",
            style="Secondary.TButton",
            command=dialog.destroy,
            width=15,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame,
            text="Сохранить",
            style="Accent.TButton",
            command=save_habit,
            width=15,
        ).pack(side=tk.RIGHT)

        # Центрирование диалога
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")

    def add_custom_time(self):
        dialog = tk.Toplevel(self)
        dialog.title("Добавить новое время")
        dialog.geometry("400x200")  # Увеличенный размер окна
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="20 20 20 20")  # Увеличенные отступы
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Название времени:", font=("Segoe UI", 11)).pack(
            anchor=tk.W
        )

        name_entry = ttk.Entry(main_frame, width=40, font=("Segoe UI", 11))
        name_entry.pack(fill=tk.X, pady=(10, 20))  # Увеличенные отступы
        name_entry.focus_set()

        # Добавляем контекстное меню для копирования/вставки
        self.add_copy_paste_menu(name_entry)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Ошибка", "Введите название времени")
                return

            if name in self.all_times:
                messagebox.showwarning("Ошибка", f"Время '{name}' уже существует")
                return

            self.custom_times.append(name)
            self.all_times.append(name)
            self.habits[name] = []
            self.time_settings[name] = {"quick_timer_minutes": None}

            self.update_times_display()
            self.save_habits()
            dialog.destroy()

        # Увеличенные размеры кнопок
        ttk.Button(
            btn_frame,
            text="Отмена",
            style="Secondary.TButton",
            command=dialog.destroy,
            width=15,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame, text="Сохранить", style="Accent.TButton", command=save, width=15
        ).pack(side=tk.RIGHT)

        # Центрирование диалога
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")

    def toggle_habit(self, habit, enabled):
        """Включает/выключает привычку"""
        habit["enabled"] = enabled
        self.save_habits()

    def remove_habit(self, time_name, habit):
        """Удаляет привычку"""
        if messagebox.askyesno("Подтверждение", f"Удалить привычку '{habit['name']}'?"):
            if time_name in self.habits and habit in self.habits[time_name]:
                self.habits[time_name].remove(habit)
                self.update_times_display()
            self.save_habits()

    def remove_time(self, time_name):
        """Удаляет время и все привычки в нем"""
        if messagebox.askyesno(
            "Подтверждение", f"Удалить '{time_name}' и все привычки в нем?"
        ):
            if time_name in self.all_times:
                self.all_times.remove(time_name)
            if time_name in self.custom_times:
                self.custom_times.remove(time_name)
            if time_name in self.habits:
                del self.habits[time_name]
            if time_name in self.time_settings:
                del self.time_settings[time_name]

            self.update_times_display()
            self.save_habits()

    def start_timer_for_time(self, time_name):
        """Запускает таймер для группы привычек"""
        dialog = tk.Toplevel(self)
        dialog.title(f"Таймер для '{time_name}'")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="20 15 20 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame, text="Установите таймер:", font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.CENTER, pady=(0, 15))

        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=(5, 20))

        hour_var = tk.StringVar(value="0")
        minute_var = tk.StringVar(value="5")
        second_var = tk.StringVar(value="0")

        ttk.Label(time_frame, text="Часы:", font=("Segoe UI", 10)).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        hour_spinner = ttk.Spinbox(
            time_frame,
            from_=0,
            to=23,
            width=3,
            textvariable=hour_var,
            font=("Segoe UI", 11),
        )
        hour_spinner.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(time_frame, text="Минуты:", font=("Segoe UI", 10)).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        minute_spinner = ttk.Spinbox(
            time_frame,
            from_=0,
            to=59,
            width=3,
            textvariable=minute_var,
            font=("Segoe UI", 11),
        )
        minute_spinner.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(time_frame, text="Секунды:", font=("Segoe UI", 10)).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        second_spinner = ttk.Spinbox(
            time_frame,
            from_=0,
            to=59,
            width=3,
            textvariable=second_var,
            font=("Segoe UI", 11),
        )
        second_spinner.pack(side=tk.LEFT)

        presets_frame = ttk.Frame(main_frame)
        presets_frame.pack(fill=tk.X, pady=(0, 20))

        preset_buttons = [
            ("5 мин", 5),
            ("10 мин", 10),
            ("15 мин", 15),
            ("30 мин", 30),
            ("1 час", 60),
        ]

        for text, minutes in preset_buttons:
            ttk.Button(
                presets_frame,
                text=text,
                command=lambda m=minutes: (
                    hour_var.set(str(m // 60)),
                    minute_var.set(str(m % 60)),
                    second_var.set("0"),
                ),
                style="Secondary.TButton",
                takefocus=0,
            ).pack(side=tk.LEFT, padx=5, pady=5)

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        def start_custom_timer():
            try:
                hours = int(hour_var.get())
                minutes = int(minute_var.get())
                seconds = int(second_var.get())

                if hours == 0 and minutes == 0 and seconds == 0:
                    messagebox.showwarning("Ошибка", "Время должно быть больше нуля")
                    return

                total_minutes = hours * 60 + minutes + (1 if seconds > 0 else 0)
                self.create_time_timer(time_name, total_minutes, dialog)

            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректное время")

        ttk.Button(
            buttons_frame,
            text="Отмена",
            style="Secondary.TButton",
            command=dialog.destroy,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            buttons_frame,
            text="Запустить",
            style="Accent.TButton",
            command=start_custom_timer,
        ).pack(side=tk.RIGHT)

        dialog.bind("<Return>", lambda e: start_custom_timer())

        # Позиционирование окна по центру основного окна
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def create_time_timer(self, time_name, minutes, dialog=None):
        """Создает таймер для группы привычек"""
        if dialog:
            dialog.destroy()

        main_window = self.winfo_toplevel()
        main_window.add_timer()
        timer = main_window.timers[-1]

        timer_name = f"Привычки: {time_name}"
        timer.description.delete(0, tk.END)
        timer.description.insert(0, timer_name)
        timer.hours.set(str(minutes // 60))
        timer.minutes.set(str(minutes % 60))
        timer.seconds.set("0")

        timer.update_presets_visibility()
        timer.start_timer()

        self.show_toast_notification(
            f"Таймер для '{time_name}' запущен на {minutes} мин"
        )

    def create_quick_timer(self, time_name, minutes):
        """Создает быстрый таймер для группы привычек"""
        self.create_time_timer(time_name, minutes)

    def show_toast_notification(self, message, duration=3000):
        """Показывает всплывающее уведомление"""
        # Закрыть предыдущее уведомление, если оно открыто
        if self.toast_notification and self.toast_notification.winfo_exists():
            self.toast_notification.destroy()

        root = self.winfo_toplevel()

        # Создаем новое окно уведомления
        self.toast_notification = tk.Toplevel(root)
        self.toast_notification.overrideredirect(True)
        self.toast_notification.attributes("-topmost", True)

        frame = ttk.Frame(self.toast_notification, style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=message, font=("Segoe UI", 10), padding=10).pack()

        # Размещаем уведомление в нижней правой части основного окна
        self.toast_notification.update_idletasks()
        width = self.toast_notification.winfo_width()
        height = self.toast_notification.winfo_height()

        root_x = root.winfo_x()
        root_y = root.winfo_y()
        root_width = root.winfo_width()
        root_height = root.winfo_height()

        x = root_x + root_width - width - 20
        y = root_y + root_height - height - 20

        self.toast_notification.geometry(f"+{x}+{y}")

        # Закрываем уведомление через duration миллисекунд
        self.toast_notification.after(duration, self.toast_notification.destroy)

    def save_habits(self):
        """Сохраняет данные о привычках в файл"""
        habits_data = {
            "times": self.all_times,
            "custom_times": self.custom_times,
            "time_settings": self.time_settings,
            "habits": {},
        }

        for time_name, habits_list in self.habits.items():
            habits_data["habits"][time_name] = []
            for habit in habits_list:
                last_reminder = habit.get("last_reminder")
                if isinstance(last_reminder, datetime):
                    last_reminder = last_reminder.isoformat()

                # Сохраняем все необходимые поля привычки
                habit_data = {
                    "name": habit["name"],
                    "interval": habit["interval"],
                    "start_time": habit["start_time"],
                    "end_time": habit["end_time"],
                    "enabled": habit.get("enabled", True),
                    "completed": habit.get("completed", False),
                    "completed_repeats": habit.get("completed_repeats", 0),
                    "repeats": habit.get("repeats", 1),
                    "notifications": habit.get("notifications", True),
                    "comment": habit.get("comment", ""),
                    "last_reminder": last_reminder,
                }

                # Если есть время завершения, также сохраняем его
                if "completed_time" in habit:
                    habit_data["completed_time"] = habit["completed_time"]

                habits_data["habits"][time_name].append(habit_data)

        try:
            # Проверяем, что данные можно сериализовать в JSON
            json_data = json.dumps(habits_data, ensure_ascii=False, indent=2)

            # Если все в порядке, сохраняем в файл
            with open("habits.json", "w", encoding="utf-8") as f:
                f.write(json_data)
        except Exception as e:
            print(f"Ошибка при сохранении данных о привычках: {e}")
            # Можно здесь добавить логику для восстановления из резервной копии

    def load_habits(self):
        """Загружает данные о привычках из файла"""
        try:
            with open("habits.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)

                    # Проверка формата данных
                    if isinstance(data, list):
                        # Старый формат - преобразуем в новый
                        old_habits = data

                        # Разместим все старые привычки в категорию "Общие"
                        general_time = "Общие"
                        if general_time not in self.all_times:
                            self.all_times.append(general_time)
                            self.custom_times.append(general_time)
                            self.habits[general_time] = []
                            self.time_settings[general_time] = {
                                "quick_timer_minutes": None
                            }

                        for habit_data in old_habits:
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
                                print(
                                    f"Пропущена привычка с неполными данными: {habit_data}"
                                )
                                continue

                            if (
                                "last_reminder" in habit_data
                                and habit_data["last_reminder"]
                            ):
                                try:
                                    habit_data["last_reminder"] = (
                                        datetime.fromisoformat(
                                            habit_data["last_reminder"]
                                        )
                                    )
                                except ValueError:
                                    habit_data["last_reminder"] = None
                            else:
                                habit_data["last_reminder"] = None

                            self.habits[general_time].append(habit_data)
                    else:
                        # Новый формат
                        if "times" in data:
                            self.all_times = data["times"]
                        if "custom_times" in data:
                            self.custom_times = data["custom_times"]
                        if "time_settings" in data:
                            self.time_settings = data["time_settings"]

                        # Загрузка привычек для каждого времени
                        if "habits" in data:
                            for time_name, habits_list in data["habits"].items():
                                if time_name not in self.habits:
                                    self.habits[time_name] = []

                                for habit_data in habits_list:
                                    if (
                                        "last_reminder" in habit_data
                                        and habit_data["last_reminder"]
                                    ):
                                        try:
                                            habit_data["last_reminder"] = (
                                                datetime.fromisoformat(
                                                    habit_data["last_reminder"]
                                                )
                                            )
                                        except ValueError:
                                            habit_data["last_reminder"] = None
                                    else:
                                        habit_data["last_reminder"] = None

                                    self.habits[time_name].append(habit_data)

                    # Проверка, что у каждого времени есть настройки таймера
                    for time_name in self.all_times:
                        if time_name not in self.time_settings:
                            self.time_settings[time_name] = {
                                "quick_timer_minutes": None
                            }
                        if time_name not in self.habits:
                            self.habits[time_name] = []

                    self.update_times_display()

                    # После загрузки данных проверим completed для каждой привычки
                    # Если привычка отмечена как выполненная, проверим не нужно ли сбросить статус
                    # (если completed_time относится к предыдущему дню)
                    current_date = datetime.now().date()

                    for time_name, habits_list in self.habits.items():
                        for habit in habits_list:
                            if habit.get("completed", False) and habit.get(
                                "completed_time"
                            ):
                                try:
                                    completed_time = datetime.fromisoformat(
                                        habit["completed_time"]
                                    )
                                    if completed_time.date() < current_date:
                                        habit["completed"] = False
                                        habit["completed_time"] = None
                                except:
                                    habit["completed"] = False
                                    habit["completed_time"] = None

                except json.JSONDecodeError:
                    print("Ошибка чтения файла habits.json. Файл поврежден.")

        except FileNotFoundError:
            print("Файл habits.json не найден. Создаем новый список привычек.")
        except Exception as e:
            print(f"Непредвиденная ошибка при загрузке привычек: {e}")

    def add_copy_paste_menu(self, widget):
        """Добавляет контекстное меню с функциями копирования/вставки к виджету"""
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Вырезать", command=lambda: self.cut_text(widget))
        menu.add_command(label="Копировать", command=lambda: self.copy_text(widget))
        menu.add_command(label="Вставить", command=lambda: self.paste_text(widget))

        # Привязка меню к правой кнопке мыши
        widget.bind("<Button-3>", lambda e: self.show_popup_menu(e, menu))

        # Стандартные сочетания клавиш
        widget.bind("<Control-x>", lambda e: self.cut_text(widget))
        widget.bind("<Control-c>", lambda e: self.copy_text(widget))
        widget.bind("<Control-v>", lambda e: self.paste_text(widget))

    def show_popup_menu(self, event, menu):
        """Показывает контекстное меню по координатам события"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def cut_text(self, widget):
        """Вырезает выделенный текст из виджета в буфер обмена"""
        try:
            widget.event_generate("<<Cut>>")
        except:
            # Если стандартная функция не работает, делаем вручную
            self.copy_text(widget)
            try:
                widget.delete("sel.first", "sel.last")
            except:
                pass

    def copy_text(self, widget):
        """Копирует выделенный текст из виджета в буфер обмена"""
        try:
            widget.event_generate("<<Copy>>")
        except:
            # Если стандартная функция не работает, делаем вручную
            try:
                selected_text = widget.selection_get()
                self.clipboard_clear()
                self.clipboard_append(selected_text)
            except:
                pass

    def paste_text(self, widget):
        """Вставляет текст из буфера обмена в виджет на место курсора"""
        try:
            widget.event_generate("<<Paste>>")
        except:
            # Если стандартная функция не работает, делаем вручную
            try:
                text = self.clipboard_get()
                if "sel.first" in widget.index("sel.first"):
                    widget.delete("sel.first", "sel.last")
                widget.insert("insert", text)
            except:
                pass

    def show_stats(self):
        """Показывает детальную статистику по привычкам"""
        if self.stats_window and self.stats_window.winfo_exists():
            self.stats_window.focus_force()
            return

        self.stats_window = tk.Toplevel(self)
        self.stats_window.title("Статистика привычек")
        self.stats_window.geometry("600x500")  # Увеличенный размер окна
        self.stats_window.transient(self.winfo_toplevel())

        main_frame = ttk.Frame(
            self.stats_window, padding="20 20 20 20"
        )  # Увеличенные отступы
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame, text="Статистика привычек", font=("Segoe UI", 18, "bold")
        ).pack(
            pady=(0, 20)
        )  # Увеличенный шрифт и отступы

        # Создаем фрейм для отображения статистики
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True)

        # Подсчитываем статистику
        total_habits = 0
        completed_habits = 0
        total_repeats = 0
        completed_repeats = 0

        # Словарь для статистики по времени дня
        time_stats = {}

        # Собираем статистику по всем привычкам
        for time_name, habits_list in self.habits.items():
            time_stats[time_name] = {
                "total": 0,
                "completed": 0,
                "total_repeats": 0,
                "completed_repeats": 0,
            }

            for habit in habits_list:
                if habit.get("enabled", True):
                    repeats = habit.get("repeats", 1)
                    time_stats[time_name]["total"] += 1
                    time_stats[time_name]["total_repeats"] += repeats
                    total_habits += 1
                    total_repeats += repeats

                    if habit.get("completed", False):
                        time_stats[time_name]["completed"] += 1
                        time_stats[time_name]["completed_repeats"] += repeats
                        completed_habits += 1
                        completed_repeats += repeats
                    else:
                        time_stats[time_name]["completed_repeats"] += habit.get(
                            "completed_repeats", 0
                        )
                        completed_repeats += habit.get("completed_repeats", 0)

        # Отображаем общую статистику
        ttk.Label(
            stats_frame, text="Общая статистика:", font=("Segoe UI", 14, "bold")
        ).pack(
            anchor=tk.W, pady=(0, 10)
        )  # Увеличенный шрифт и отступы

        if total_habits > 0:
            completion_percentage = int((completed_habits / total_habits) * 100)
            repeats_percentage = (
                int((completed_repeats / total_repeats) * 100)
                if total_repeats > 0
                else 0
            )

            ttk.Label(
                stats_frame,
                text=f"Выполнено {completed_habits} из {total_habits} привычек ({completion_percentage}%)",
                font=("Segoe UI", 12),
            ).pack(
                anchor=tk.W
            )  # Увеличенный шрифт

            ttk.Label(
                stats_frame,
                text=f"Выполнено {completed_repeats} из {total_repeats} повторений ({repeats_percentage}%)",
                font=("Segoe UI", 12),
            ).pack(
                anchor=tk.W, pady=(0, 15)
            )  # Увеличенный шрифт и отступы
        else:
            ttk.Label(
                stats_frame, text="Нет активных привычек", font=("Segoe UI", 12)
            ).pack(
                anchor=tk.W, pady=(0, 15)
            )  # Увеличенный шрифт и отступы

        # Отображаем статистику по времени дня
        ttk.Label(
            stats_frame,
            text="Статистика по времени дня:",
            font=("Segoe UI", 14, "bold"),
        ).pack(
            anchor=tk.W, pady=(5, 10)
        )  # Увеличенный шрифт и отступы

        for time_name in self.all_times:
            if time_name in time_stats and time_stats[time_name]["total"] > 0:
                time_completion = int(
                    (
                        time_stats[time_name]["completed"]
                        / time_stats[time_name]["total"]
                    )
                    * 100
                )
                time_repeats = (
                    int(
                        (
                            time_stats[time_name]["completed_repeats"]
                            / time_stats[time_name]["total_repeats"]
                        )
                        * 100
                    )
                    if time_stats[time_name]["total_repeats"] > 0
                    else 0
                )

                ttk.Label(
                    stats_frame,
                    text=f"{time_name}: {time_stats[time_name]['completed']}/{time_stats[time_name]['total']} привычек ({time_completion}%), "
                    + f"{time_stats[time_name]['completed_repeats']}/{time_stats[time_name]['total_repeats']} повторений ({time_repeats}%)",
                    font=("Segoe UI", 11),
                ).pack(
                    anchor=tk.W, pady=(0, 5)
                )  # Увеличенный шрифт и отступы

        # Добавляем кнопку закрытия с увеличенным размером
        ttk.Button(
            main_frame,
            text="Закрыть",
            command=self.stats_window.destroy,
            width=15,
            style="Accent.TButton",
        ).pack(pady=(20, 0))

        # Центрирование окна
        self.stats_window.update_idletasks()
        width = self.stats_window.winfo_width()
        height = self.stats_window.winfo_height()
        x = (self.stats_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.stats_window.winfo_screenheight() // 2) - (height // 2)
        self.stats_window.geometry(f"+{x}+{y}")

    def update_stats_display(self):
        """Обновляет отображение статистики привычек"""
        total_habits = 0
        completed_habits = 0
        total_repeats = 0
        completed_repeats = 0

        # Собираем статистику по всем привычкам
        for time_name, habits_list in self.habits.items():
            for habit in habits_list:
                if habit.get("enabled", True):
                    repeats = habit.get("repeats", 1)
                    total_habits += 1
                    total_repeats += repeats

                    if habit.get("completed", False):
                        completed_habits += 1
                        completed_repeats += repeats
                    else:
                        completed_repeats += habit.get("completed_repeats", 0)

        # Обновляем текст в label
        if total_habits > 0:
            completion_percentage = int((completed_habits / total_habits) * 100)
            repeats_percentage = (
                int((completed_repeats / total_repeats) * 100)
                if total_repeats > 0
                else 0
            )
            stats_text = f"Сегодня: {completed_habits}/{total_habits} привычек ({completion_percentage}%), {completed_repeats}/{total_repeats} повторений ({repeats_percentage}%)"
            self.stats_label.configure(text=stats_text)
        else:
            self.stats_label.configure(text="Нет активных привычек")

    def add_comment(self, habit):
        """Открывает диалог для добавления комментария к привычке"""
        dialog = tk.Toplevel(self)
        dialog.title("Добавить комментарий")
        dialog.geometry("500x300")  # Увеличенный размер окна
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding="20 20 20 20")  # Увеличенные отступы
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text=f"Добавить комментарий к привычке: {habit['name']}",
            font=("Segoe UI", 11),
        ).pack(
            anchor=tk.W, pady=(0, 15)
        )  # Увеличенные отступы

        comment_text = tk.Text(
            main_frame, height=6, width=45, wrap=tk.WORD, font=("Segoe UI", 11)
        )  # Увеличенные размеры текстового поля
        if habit.get("comment"):
            comment_text.insert("1.0", habit["comment"])
        comment_text.pack(
            fill=tk.BOTH, expand=True, pady=(0, 15)
        )  # Увеличенные отступы
        self.add_copy_paste_menu(comment_text)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        def save_comment():
            comment = comment_text.get("1.0", tk.END).strip()
            habit["comment"] = comment
            self.save_habits()
            dialog.destroy()

        def skip_comment():
            dialog.destroy()

        # Увеличенные размеры кнопок
        ttk.Button(
            btn_frame,
            text="Пропустить",
            style="Secondary.TButton",
            command=skip_comment,
            width=15,
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame,
            text="Сохранить",
            style="Accent.TButton",
            command=save_comment,
            width=15,
        ).pack(side=tk.RIGHT)

        # Центрирование диалога
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")

    def update_habit_button_style(self, button, habit):
        """Обновляет стиль кнопки привычки в зависимости от статуса"""
        if not habit["enabled"]:
            button.config(style="Disabled.TButton")
            return

        if habit.get("completed", False):
            # Полностью выполнено (все повторения)
            button.config(style="Completed.TButton")
        elif habit.get("completed_repeats", 0) > 0:
            # Частично выполнено (некоторые повторения)
            button.config(style="PartiallyCompleted.TButton")
        else:
            # Не выполнено
            button.config(style="Regular.TButton")

        # Обновляем текст кнопки чтобы показать прогресс повторений
        if habit.get("repeats", 1) > 1:
            button.config(
                text=f"{habit['name']} ({habit.get('completed_repeats', 0)}/{habit.get('repeats', 1)})"
            )
        else:
            button.config(text=habit["name"])

    def create_custom_styles(self):
        """Создает стили для элементов интерфейса"""
        style = ttk.Style()

        # Создаем оранжевый стиль для чекбоксов
        style.configure(
            "Orange.TCheckbutton",
            background="#ffffff",
            indicatorcolor="#ff7700",
            indicatorbackground="#ffffff",
            indicatorrelief=tk.RAISED,
        )

        # Стандартная кнопка
        style.configure(
            "Regular.TButton",
            padding=5,
            foreground="#333333",
            background="#f0f0f0",
            font=("Segoe UI", 10),
        )

        # Кнопка выполненной привычки (все повторения)
        style.configure(
            "Completed.TButton",
            padding=5,
            foreground="#FFFFFF",
            background="#28a745",
            font=("Segoe UI", 10),
        )

        # Кнопка частично выполненной привычки (некоторые из повторений)
        style.configure(
            "PartiallyCompleted.TButton",
            padding=5,
            foreground="#333333",
            background="#ffc107",
            font=("Segoe UI", 10),
        )

        # Кнопка отключенной привычки
        style.configure(
            "Disabled.TButton",
            padding=5,
            foreground="#999999",
            background="#dddddd",
            font=("Segoe UI", 10),
        )

        # Дополнительная кнопка (вторичная)
        style.configure(
            "Secondary.TButton",
            padding=5,
            foreground="#333333",
            background="#e2e2e2",
            font=("Segoe UI", 10),
        )

        # Акцентированная кнопка
        style.configure(
            "Accent.TButton",
            padding=5,
            foreground="#ffffff",
            background="#007bff",
            font=("Segoe UI", 10),
        )

    def toggle_repeat(self, habit, index, checked):
        """Отмечает конкретное повторение привычки как выполненное/невыполненное"""
        if not habit["enabled"]:
            return

        repeats = habit.get("repeats", 1)

        # Если чекбокс отмечен
        if checked:
            # Увеличиваем счетчик выполненных повторений
            current_repeats = habit.get("completed_repeats", 0)
            if index >= current_repeats:
                habit["completed_repeats"] = index + 1
        else:
            # Уменьшаем счетчик выполненных повторений
            if index < habit.get("completed_repeats", 0):
                habit["completed_repeats"] = index

        # Проверяем, все ли повторения выполнены
        if habit.get("completed_repeats", 0) >= repeats:
            habit["completed"] = True
            if not habit.get("comment"):
                self.after(100, lambda: self.add_comment(habit))
        else:
            habit["completed"] = False

        # Сохраняем изменения и обновляем отображение
        self.save_habits()
        self.update_times_display()
        self.update_stats_display()

    def reset_all_habits(self):
        """Сбрасывает все отметки выполнения привычек и их комментарии"""
        if messagebox.askyesno(
            "Подтверждение", "Сбросить все отметки выполнения привычек и комментарии?"
        ):
            for time_name, habits_list in self.habits.items():
                for habit in habits_list:
                    habit["completed"] = False
                    habit["completed_repeats"] = 0
                    habit["comment"] = ""

            self.save_habits()
            self.update_times_display()
            self.update_stats_display()
            messagebox.showinfo(
                "Выполнено", "Все отметки привычек и комментарии сброшены"
            )
