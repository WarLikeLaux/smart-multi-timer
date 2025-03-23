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
            takefocus=0,
        ).pack(side=tk.LEFT, padx=10)

        buttons_frame = ttk.Frame(header)
        buttons_frame.pack(side=tk.RIGHT)

        ttk.Button(
            buttons_frame,
            text="+ Добавить прием",
            style="Secondary.TButton",
            command=self.add_custom_intake,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame,
            text="Сбросить отметки",
            style="Secondary.TButton",
            command=self.reset_all_marks,
            takefocus=0,
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
        self.bind("<Map>", lambda e: self.after(500, self.update_intakes_display))
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
        self.canvas.itemconfig(self.canvas_frame, width=self.canvas.winfo_width())

    def create_intake_frame(self, parent, intake_name):
        """Создает фрейм для одного приема"""
        frame = ttk.LabelFrame(parent, text=intake_name, padding=10)

        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        if not self.compact_mode.get():
            if intake_name not in self.default_intakes:
                ttk.Button(
                    control_frame,
                    text="🗑",
                    width=3,
                    command=lambda: self.remove_intake(intake_name),
                    takefocus=0,
                ).pack(side=tk.RIGHT, padx=2)

            ttk.Button(
                control_frame,
                text="↑",
                width=3,
                command=lambda: self.move_intake(intake_name, -1),
                takefocus=0,
            ).pack(side=tk.LEFT, padx=2)

            ttk.Button(
                control_frame,
                text="↓",
                width=3,
                command=lambda: self.move_intake(intake_name, 1),
                takefocus=0,
            ).pack(side=tk.LEFT, padx=2)

        meds_frame = ttk.Frame(frame)
        meds_frame.pack(fill=tk.BOTH, expand=True)

        if not self.compact_mode.get():
            add_frame = ttk.Frame(frame)
            add_frame.pack(fill=tk.X, pady=(10, 0))

            entry = ttk.Entry(add_frame)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

            ttk.Button(
                add_frame,
                text="Добавить таблетку",
                command=lambda: self.add_medication(intake_name, entry),
                takefocus=0,
            ).pack(side=tk.LEFT, padx=5)

        # Создаем фрейм для размещения кнопок внизу
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Проверяем, все ли лекарства отмечены, чтобы установить правильный текст кнопки
        all_taken = False
        if intake_name in self.medications and self.medications[intake_name]:
            all_taken = all(med.get("taken", False) for med in self.medications[intake_name])
        
        button_text = "Сбросить все" if all_taken else "Отметить все"
        
        # Добавляем кнопку "Отметить все/Сбросить все"
        mark_all_button = ttk.Button(
            buttons_frame,
            text=button_text,
            command=lambda name=intake_name: self.toggle_all_medications(name),
            style="Secondary.TButton",
            takefocus=0,
        )
        mark_all_button.pack(side=tk.LEFT, padx=5)
        
        # Добавляем кнопку таймера в тот же фрейм
        timer_button = ttk.Button(
            buttons_frame,
            text="⏱ Таймер",
            command=lambda: self.start_timer_for_intake(intake_name),
            takefocus=0,
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

        width = self.winfo_width()
        if width < 600:
            max_cols = 1
        elif width < 900:
            max_cols = 2
        else:
            max_cols = 3

        current_row = None
        col_count = 0

        for intake in self.all_intakes:
            if col_count % max_cols == 0:
                current_row = ttk.Frame(self.intakes_frame)
                current_row.pack(fill=tk.X, expand=True, pady=5)

            frame = self.create_intake_frame(current_row, intake)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

            col_count += 1

    def update_display(self):
        """Обновляет состояние чекбоксов без полной перерисовки"""
        for intake_name, medications in self.medications.items():
            for widget in self.intakes_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if (
                            isinstance(child, ttk.LabelFrame)
                            and child.cget("text") == intake_name
                        ):
                            # Обновляем текст кнопки "Отметить все/Сбросить все"
                            for control_frame in child.winfo_children():
                                if isinstance(control_frame, ttk.Frame):
                                    for button in control_frame.winfo_children():
                                        if isinstance(button, ttk.Button) and (
                                            button.cget("text") == "Отметить все" or button.cget("text") == "Сбросить все"
                                        ):
                                            all_taken = all(med.get("taken", False) for med in self.medications[intake_name])
                                            button.configure(text="Сбросить все" if all_taken else "Отметить все")
                                            break
                            
                            # Обновляем состояние чекбоксов
                            meds_frame = None
                            for frame in child.winfo_children():
                                if (
                                    isinstance(frame, ttk.Frame)
                                    and not frame.winfo_children()
                                ):
                                    continue
                                if len(frame.winfo_children()) > 0 and isinstance(
                                    frame.winfo_children()[0], ttk.Frame
                                ):
                                    meds_frame = frame
                                    break

                            if meds_frame:
                                for i, med in enumerate(medications):
                                    if i < len(meds_frame.winfo_children()):
                                        med_frame = meds_frame.winfo_children()[i]
                                        for child in med_frame.winfo_children():
                                            if isinstance(child, ttk.Checkbutton):
                                                var = med.get("var")
                                                if var and hasattr(var, 'set'):  # Проверяем что var не строка и имеет метод set
                                                    var.set(med.get("taken", False))
                                    
    def update_medications_list(self, intake_name, frame):
        for widget in frame.winfo_children():
            widget.destroy()

        medications = self.medications.get(intake_name, [])

        if self.compact_mode.get():
            count = len(medications)

            layout = []
            if count <= 0:
                return
            elif count <= 3:
                layout = [1] * count
            elif count == 4:
                layout = [2, 2]
            elif count == 5:
                layout = [2, 2, 1]
            elif count == 6:
                layout = [3, 3]
            elif count == 7:
                layout = [3, 3, 1]
            elif count == 8:
                layout = [3, 3, 2]
            elif count == 9:
                layout = [3, 3, 3]
            else:
                layout = [3, 3, 3, count - 9]

            idx = 0
            for row_idx, cols in enumerate(layout):
                for col_idx in range(cols):
                    if idx < count:
                        med = medications[idx]
                        var = tk.BooleanVar(value=med.get("taken", False))
                        med["var"] = var

                        def make_update_func(medication, intake_name=intake_name):
                            def update():
                                medication["taken"] = medication["var"].get()
                                self.save_medications()
                                # Проверяем, все ли таблетки отмечены, и обновляем текст кнопки
                                self.update_mark_all_button(intake_name)

                            return update

                        check = ttk.Checkbutton(
                            frame,
                            text=med["name"],
                            variable=var,
                            command=make_update_func(med),
                        )

                        check.grid(
                            row=row_idx, column=col_idx, sticky="w", padx=5, pady=2
                        )

                        frame.grid_columnconfigure(col_idx, weight=1)
                        idx += 1
        else:
            for i, med in enumerate(medications):
                med_frame = ttk.Frame(frame)
                med_frame.pack(fill=tk.X, pady=2)

                var = tk.BooleanVar(value=med.get("taken", False))
                med["var"] = var

                def make_update_func(medication, intake_name=intake_name):
                    def update():
                        medication["taken"] = medication["var"].get()
                        self.save_medications()
                        # Проверяем, все ли таблетки отмечены, и обновляем текст кнопки
                        self.update_mark_all_button(intake_name)

                    return update

                check = ttk.Checkbutton(
                    med_frame,
                    text=med["name"],
                    variable=var,
                    command=make_update_func(med),
                )
                check.pack(side=tk.LEFT)

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

    def update_mark_all_button(self, intake_name):
        """Обновляет текст кнопки в зависимости от состояния всех лекарств в приеме"""
        if intake_name in self.medications:
            all_taken = all(med.get("taken", False) for med in self.medications[intake_name])
            
            # Ищем кнопку для этого приема
            for widget in self.intakes_frame.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.LabelFrame) and child.cget("text") == intake_name:
                            # Ищем кнопку в buttons_frame (последний фрейм)
                            for frame in child.winfo_children():
                                if isinstance(frame, ttk.Frame):
                                    for button in frame.winfo_children():
                                        if isinstance(button, ttk.Button) and (
                                            button.cget("text") == "Отметить все" or 
                                            button.cget("text") == "Сбросить все"
                                        ):
                                            button.configure(text="Сбросить все" if all_taken else "Отметить все")
                                            return

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
        dialog.geometry("500x750")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg="#f5f5f5")

        # Стили для современного UI
        style = ttk.Style()
        style.configure("Modern.TButton", font=("Segoe UI", 11), padding=8)
        style.configure("Preset.TButton", font=("Segoe UI", 11), padding=8)
        style.configure(
            "Header.TLabel", font=("Segoe UI", 14, "bold"), background="#f5f5f5"
        )
        style.configure("Subheader.TLabel", font=("Segoe UI", 12), background="#f5f5f5")
        # style.configure("TFrame", background="#f5f5f5")
        # style.configure("TLabelframe", background="#f5f5f5")
        # style.configure(
        #     "TLabelframe.Label", background="#f5f5f5", font=("Segoe UI", 11)
        # )

        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(
            main_frame, text=f"Напоминание о приеме лекарств", style="Header.TLabel"
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text=f"Выберите через сколько времени напомнить о приеме {intake_name}",
            style="Subheader.TLabel",
            wraplength=460,
        ).pack(pady=(0, 20))

        # Фрейм быстрых пресетов
        presets_frame = ttk.LabelFrame(
            main_frame, text="Быстрый выбор времени", padding=15
        )
        presets_frame.pack(fill=tk.X, pady=(0, 15))

        # Верхний ряд пресетов
        top_preset_frame = ttk.Frame(presets_frame)
        top_preset_frame.pack(fill=tk.X, pady=(0, 5))

        # Нижний ряд пресетов
        bottom_preset_frame = ttk.Frame(presets_frame)
        bottom_preset_frame.pack(fill=tk.X)

        presets_top = [("5 мин", 5), ("15 мин", 15), ("30 мин", 30)]

        presets_bottom = [("45 мин", 45), ("1 час", 60), ("2 часа", 120)]

        # Создаем кнопки верхнего ряда
        for label, minutes in presets_top:
            btn = ttk.Button(
                top_preset_frame,
                text=label,
                command=lambda m=minutes: self.create_intake_timer(
                    intake_name, m, dialog
                ),
                style="Preset.TButton",
                width=12,
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

        # Создаем кнопки нижнего ряда
        for label, minutes in presets_bottom:
            btn = ttk.Button(
                bottom_preset_frame,
                text=label,
                command=lambda m=minutes: self.create_intake_timer(
                    intake_name, m, dialog
                ),
                style="Preset.TButton",
                width=12,
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

        # Фрейм для собственного времени
        manual_frame = ttk.LabelFrame(main_frame, text="Своё время", padding=15)
        manual_frame.pack(fill=tk.X, pady=(0, 20))

        time_frame = ttk.Frame(manual_frame)
        time_frame.pack(fill=tk.X, pady=10)

        # Переменные для часов и минут
        hours_var = tk.StringVar(value="0")
        minutes_var = tk.StringVar(value="30")

        # Контейнер для часов
        hours_container = ttk.Frame(time_frame)
        hours_container.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(hours_container, text="Часы:", font=("Segoe UI", 11)).pack(
            anchor=tk.W, pady=(0, 5)
        )
        hours_spin = ttk.Spinbox(
            hours_container,
            from_=0,
            to=23,
            width=5,
            textvariable=hours_var,
            font=("Segoe UI", 11),
        )
        hours_spin.pack()

        # Контейнер для минут
        minutes_container = ttk.Frame(time_frame)
        minutes_container.pack(side=tk.LEFT)

        ttk.Label(minutes_container, text="Минуты:", font=("Segoe UI", 11)).pack(
            anchor=tk.W, pady=(0, 5)
        )
        minutes_spin = ttk.Spinbox(
            minutes_container,
            from_=0,
            to=59,
            width=5,
            textvariable=minutes_var,
            font=("Segoe UI", 11),
        )
        minutes_spin.pack()

        # Функция для запуска таймера с произвольным временем
        def start_custom_timer():
            try:
                total_minutes = int(hours_var.get()) * 60 + int(minutes_var.get())
                if total_minutes > 0:
                    self.create_intake_timer(intake_name, total_minutes, dialog)
                else:
                    messagebox.showwarning("Ошибка", "Время должно быть больше 0")
            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректное время")

        # Кнопка для запуска таймера
        start_btn = ttk.Button(
            manual_frame,
            text="Запустить таймер",
            style="Modern.TButton",
            command=start_custom_timer,
        )
        start_btn.pack(pady=(10, 0), padx=5, fill=tk.X)

        # Отображение лекарств для данного приема
        meds_frame = ttk.LabelFrame(main_frame, text="Лекарства для приема", padding=15)
        meds_frame.pack(fill=tk.X, expand=True)

        untaken_meds = [
            med["name"]
            for med in self.medications.get(intake_name, [])
            if not med.get("taken", False)
        ]

        if untaken_meds:
            meds_text = "• " + "\n• ".join(untaken_meds)
            ttk.Label(
                meds_frame, text=meds_text, wraplength=400, font=("Segoe UI", 11)
            ).pack(pady=5, anchor=tk.W)
        else:
            ttk.Label(
                meds_frame,
                text="Все лекарства отмечены как принятые",
                font=("Segoe UI", 11, "italic"),
            ).pack(pady=5)

        # Кнопки внизу
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            buttons_frame, text="Отмена", style="Modern.TButton", command=dialog.destroy
        ).pack(side=tk.RIGHT)

        # Обработка нажатия клавиш
        def on_key(event):
            if event.keysym == "Return":
                start_custom_timer()
            elif event.keysym == "Escape":
                dialog.destroy()

        dialog.bind("<Key>", on_key)

        # Центрируем окно
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")

        # Фокус на спинбоксе минут
        minutes_spin.focus_set()

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

        description = ""
        untaken_meds = [
            med["name"]
            for med in self.medications.get(intake_name, [])
            if not med.get("taken", False)
        ]

        if untaken_meds:
            description += "Выпить " + ", ".join(untaken_meds)
        else:
            description += "(все таблетки приняты)"

        timer.description.delete(0, tk.END)
        timer.description.insert(0, description)
        timer.hours.set(str(minutes // 60))
        timer.minutes.set(str(minutes % 60))
        timer.seconds.set("0")

        timer.update_presets_visibility()

        timer.start_timer()

        if dialog:
            dialog.destroy()

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

    def toggle_all_medications(self, intake_name):
        """Переключает состояние всех лекарств в приеме (отметить/сбросить все)"""
        if intake_name in self.medications:
            # Проверяем, все ли лекарства уже отмечены
            all_taken = all(med.get("taken", False) for med in self.medications[intake_name])
            
            # Если все отмечены, сбрасываем все, иначе отмечаем все
            new_state = not all_taken
            
            # Устанавливаем новое состояние для всех лекарств
            for med in self.medications[intake_name]:
                med["taken"] = new_state
                if "var" in med and hasattr(med["var"], 'set'):
                    med["var"].set(new_state)
            
            # Сохраняем изменения
            self.save_medications()
            
            # Обновляем интерфейс
            self.update_display()
