import json
import tkinter as tk
from tkinter import messagebox, ttk


class MedicationTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.medications = {}
        self.default_intakes = ["Утро", "Завтрак", "Обед", "Ужин", "Перед сном"]
        self.custom_intakes = []
        self.all_intakes = self.default_intakes.copy()

        for intake in self.default_intakes:
            self.medications[intake] = []

        self.setup_ui()
        self.load_medications()

    def setup_ui(self):
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        header = ttk.Frame(main_container)
        header.pack(fill=tk.X, pady=(0, 15))

        title_frame = ttk.Frame(header)
        title_frame.pack(side=tk.LEFT)

        ttk.Label(title_frame, text="Прием лекарств", font=("Arial", 16, "bold")).pack(
            side=tk.LEFT
        )

        self.compact_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            title_frame,
            text="Компактный режим",
            variable=self.compact_mode,
            command=self.toggle_compact_mode,
        ).pack(side=tk.LEFT, padx=10)

        buttons_frame = ttk.Frame(header)
        buttons_frame.pack(side=tk.RIGHT)

        ttk.Button(
            buttons_frame,
            text="+ Добавить прием",
            style="Secondary.TButton",
            command=self.add_custom_intake,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame,
            text="Сбросить отметки",
            style="Secondary.TButton",
            command=self.reset_all_marks,
        ).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(
            main_container, orient="vertical", command=self.canvas.yview
        )

        self.intakes_frame = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas_frame = self.canvas.create_window(
            (0, 0), window=self.intakes_frame, anchor="nw"
        )

        self.intakes_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.update_intakes_display()
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Обработка прокрутки колесиком мыши"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_frame_configure(self, event=None):
        """Обновляет скроллбар при изменении размера содержимого"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Растягивает фрейм по ширине канваса"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def toggle_compact_mode(self):
        """Переключает компактный режим отображения"""
        self.update_intakes_display()

    def create_intake_frame(self, intake_name):
        """Создает фрейм для одного приема"""
        frame = ttk.LabelFrame(self.intakes_frame, text=intake_name, padding=10)
        frame.pack(fill=tk.X, pady=5)

        if not self.compact_mode.get():
            control_frame = ttk.Frame(frame)
            control_frame.pack(fill=tk.X, pady=(0, 5))

            if intake_name not in self.default_intakes:
                ttk.Button(
                    control_frame,
                    text="🗑",
                    width=3,
                    command=lambda: self.remove_intake(intake_name),
                ).pack(side=tk.RIGHT, padx=2)

            ttk.Button(
                control_frame,
                text="↑",
                width=3,
                command=lambda: self.move_intake(intake_name, -1),
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                control_frame,
                text="↓",
                width=3,
                command=lambda: self.move_intake(intake_name, 1),
            ).pack(side=tk.LEFT, padx=2)

        meds_frame = ttk.Frame(frame)
        meds_frame.pack(fill=tk.X, expand=True)

        if not self.compact_mode.get():
            add_frame = ttk.Frame(frame)
            add_frame.pack(fill=tk.X, pady=(10, 0))

            entry = ttk.Entry(add_frame)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            ttk.Button(
                add_frame,
                text="Добавить таблетку",
                command=lambda: self.add_medication(intake_name, entry),
            ).pack(side=tk.LEFT, padx=5)

        timer_button = ttk.Button(
            frame,
            text="⏱ Таймер",
            command=lambda: self.start_timer_for_intake(intake_name),
        )
        timer_button.pack(side=tk.RIGHT, padx=5)

        self.update_medications_list(intake_name, meds_frame)
        return frame

    def move_intake(self, intake_name, direction):
        """Перемещает прием вверх/вниз в списке"""
        current_index = self.all_intakes.index(intake_name)
        new_index = current_index + direction

        if 0 <= new_index < len(self.all_intakes):
            self.all_intakes.remove(intake_name)
            self.all_intakes.insert(new_index, intake_name)
            self.update_intakes_display()
            self.save_medications()

    def move_medication(self, intake_name, med_name, direction):
        """Перемещает таблетку вверх/вниз в списке"""
        meds = self.medications[intake_name]
        for i, med in enumerate(meds):
            if med["name"] == med_name:
                if 0 <= i + direction < len(meds):
                    meds[i], meds[i + direction] = meds[i + direction], meds[i]
                    self.update_intakes_display()
                    self.save_medications()
                    break

    def update_intakes_display(self):
        """Обновляет отображение всех приемов"""
        for widget in self.intakes_frame.winfo_children():
            widget.destroy()

        for intake in self.all_intakes:
            self.create_intake_frame(intake)

    def update_medications_list(self, intake_name, frame):
        """Обновляет список таблеток для конкретного приема"""
        for widget in frame.winfo_children():
            widget.destroy()

        for med in self.medications.get(intake_name, []):
            med_frame = ttk.Frame(frame)
            med_frame.pack(fill=tk.X, pady=2)

            var = tk.BooleanVar(value=med.get("taken", False))

            def update_status(med=med):
                med["taken"] = var.get()
                self.save_medications()

            check = ttk.Checkbutton(
                med_frame, text=med["name"], variable=var, command=update_status
            )
            check.pack(side=tk.LEFT)

            ttk.Button(
                med_frame,
                text="✕",
                width=3,
                command=lambda m=med: self.remove_medication(intake_name, m),
            ).pack(side=tk.RIGHT)

    def add_medication(self, intake_name, entry):
        """Добавляет новую таблетку к приему"""
        name = entry.get().strip()
        if name:
            if intake_name not in self.medications:
                self.medications[intake_name] = []

            self.medications[intake_name].append({"name": name, "taken": False})

            entry.delete(0, tk.END)
            self.update_intakes_display()
            self.save_medications()

    def remove_medication(self, intake_name, medication):
        """Удаляет таблетку из приема"""
        if intake_name in self.medications:
            self.medications[intake_name].remove(medication)
            self.update_intakes_display()
            self.save_medications()

    def add_custom_intake(self):
        """Добавляет кастомный прием"""
        dialog = tk.Toplevel(self)
        dialog.title("Новый прием")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Название приема:").pack(pady=(20, 5))
        entry = ttk.Entry(dialog, width=40)
        entry.pack(pady=(0, 20))
        entry.focus()

        def save():
            name = entry.get().strip()
            if name:
                if name not in self.all_intakes:
                    self.custom_intakes.append(name)
                    self.all_intakes.append(name)
                    self.medications[name] = []
                    self.update_intakes_display()
                    self.save_medications()
                    dialog.destroy()
                else:
                    messagebox.showwarning("Ошибка", "Такой прием уже существует")
            else:
                messagebox.showwarning("Ошибка", "Введите название приема")

        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=5)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack(pady=5)

    def reset_all_marks(self):
        """Сбрасывает все отметки о приеме"""
        if messagebox.askyesno("Подтверждение", "Сбросить все отметки о приеме?"):
            for intake in self.medications:
                for med in self.medications[intake]:
                    med["taken"] = False
            self.update_intakes_display()
            self.save_medications()

    def start_timer_for_intake(self, intake_name):
        """Запускает таймер для приема"""
        dialog = tk.Toplevel(self)
        dialog.title(f"Таймер для приема: {intake_name}")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(
            dialog, text="Установите время для напоминания:", font=("Arial", 12)
        ).pack(pady=(20, 10))

        presets_frame = ttk.LabelFrame(dialog, text="Быстрые таймеры", padding=10)
        presets_frame.pack(fill=tk.X, padx=20, pady=10)

        presets = [("5 минут", 5), ("15 минут", 15), ("30 минут", 30), ("1 час", 60)]

        for label, minutes in presets:
            ttk.Button(
                presets_frame,
                text=label,
                command=lambda m=minutes: self.create_intake_timer(
                    intake_name, m, dialog
                ),
            ).pack(side=tk.LEFT, padx=5)

        manual_frame = ttk.LabelFrame(dialog, text="Свое время", padding=10)
        manual_frame.pack(fill=tk.X, padx=20, pady=10)

        time_frame = ttk.Frame(manual_frame)
        time_frame.pack(fill=tk.X)

        hours_var = tk.StringVar(value="0")
        minutes_var = tk.StringVar(value="30")

        ttk.Spinbox(time_frame, from_=0, to=23, width=5, textvariable=hours_var).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Label(time_frame, text="ч").pack(side=tk.LEFT)

        ttk.Spinbox(time_frame, from_=0, to=59, width=5, textvariable=minutes_var).pack(
            side=tk.LEFT, padx=5
        )

        ttk.Label(time_frame, text="мин").pack(side=tk.LEFT)

        def start_custom_timer():
            try:
                total_minutes = int(hours_var.get()) * 60 + int(minutes_var.get())
                if total_minutes > 0:
                    self.create_intake_timer(intake_name, total_minutes, dialog)
                else:
                    messagebox.showwarning("Ошибка", "Время должно быть больше 0")
            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректное время")

        ttk.Button(
            manual_frame,
            text="Запустить таймер",
            style="Accent.TButton",
            command=start_custom_timer,
        ).pack(pady=(10, 0))

    def remove_intake(self, intake_name):
        """Удаляет прием из списка"""
        if intake_name in self.default_intakes:
            messagebox.showwarning("Ошибка", "Нельзя удалить стандартный прием")
            return

        if messagebox.askyesno("Подтверждение", f"Удалить прием '{intake_name}'?"):
            if intake_name in self.custom_intakes:
                self.custom_intakes.remove(intake_name)
            if intake_name in self.all_intakes:
                self.all_intakes.remove(intake_name)
            if intake_name in self.medications:
                del self.medications[intake_name]

            self.update_intakes_display()
            self.save_medications()

    def create_intake_timer(self, intake_name, minutes, dialog=None):
        main_window = self.winfo_toplevel()

        main_window.add_timer()

        timer = main_window.timers[-1]

        description = f"💊 {intake_name}:\n"
        untaken_meds = [
            med["name"]
            for med in self.medications.get(intake_name, [])
            if not med.get("taken", False)
        ]

        if untaken_meds:
            description += "\n".join(f"• {med}" for med in untaken_meds)
        else:
            description += "(все таблетки приняты)"

        timer.description.delete(0, tk.END)
        timer.description.insert(0, description)
        timer.hours.set(str(minutes // 60))
        timer.minutes.set(str(minutes % 60))
        timer.seconds.set("0")

        timer.start_timer()

        if dialog:
            dialog.destroy()

    def update_medications_list(self, intake_name, frame):
        """Обновляет список таблеток для конкретного приема"""
        for widget in frame.winfo_children():
            widget.destroy()

        for i, med in enumerate(self.medications.get(intake_name, [])):
            med_frame = ttk.Frame(frame)
            med_frame.pack(fill=tk.X, pady=2)

            var = tk.BooleanVar(value=med.get("taken", False))

            def update_status(med=med):
                med["taken"] = var.get()
                self.save_medications()

            check = ttk.Checkbutton(
                med_frame, text=med["name"], variable=var, command=update_status
            )
            check.pack(side=tk.LEFT)

            if not self.compact_mode.get():
                buttons_frame = ttk.Frame(med_frame)
                buttons_frame.pack(side=tk.RIGHT)

                ttk.Button(
                    buttons_frame,
                    text="↑",
                    width=3,
                    command=lambda m=med["name"]: self.move_medication(
                        intake_name, m, -1
                    ),
                ).pack(side=tk.LEFT, padx=2)

                ttk.Button(
                    buttons_frame,
                    text="↓",
                    width=3,
                    command=lambda m=med["name"]: self.move_medication(
                        intake_name, m, 1
                    ),
                ).pack(side=tk.LEFT, padx=2)

                ttk.Button(
                    buttons_frame,
                    text="✕",
                    width=3,
                    command=lambda m=med: self.remove_medication(intake_name, m),
                ).pack(side=tk.LEFT, padx=2)

    def save_medications(self):
        """Сохраняет конфигурацию в файл"""
        data = {
            "medications": {},
            "all_intakes": self.all_intakes,
            "default_intakes": self.default_intakes,
            "custom_intakes": self.custom_intakes,
            "compact_mode": self.compact_mode.get(),
        }

        for intake_name, medications in self.medications.items():
            data["medications"][intake_name] = [
                {
                    "name": med["name"],
                    "taken": med.get("taken", False),
                }
                for med in medications
            ]

        try:
            with open("medications.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            messagebox.showerror("Ошибка", "Не удалось сохранить конфигурацию")

    def load_medications(self):
        """Загружает конфигурацию из файла"""
        try:
            with open("medications.json", "r", encoding="utf-8") as f:
                data = json.load(f)

                self.all_intakes = data.get("all_intakes", self.default_intakes.copy())
                self.default_intakes = data.get("default_intakes", self.default_intakes)
                self.custom_intakes = data.get("custom_intakes", [])

                self.compact_mode.set(data.get("compact_mode", False))

                self.medications = {}
                for intake_name, medications in data.get("medications", {}).items():
                    self.medications[intake_name] = [
                        {
                            "name": med["name"],
                            "taken": med.get("taken", False),
                        }
                        for med in medications
                    ]

                self.update_intakes_display()
        except FileNotFoundError:
            self.update_intakes_display()
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            messagebox.showerror("Ошибка", "Не удалось загрузить сохраненные данные")
