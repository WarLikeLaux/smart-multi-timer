import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk
from pygame import mixer

from utils.constants import IMAGES


class TimerNotification(tk.Toplevel):
    def __init__(self, parent, description, next_timers=None, current_timer=None):
        super().__init__(parent)
        self.parent = parent
        self.next_timers = next_timers
        self.current_timer = current_timer
        self.timer_list = self.find_timer_list(parent)
        self.result = None

        style = ttk.Style()
        style.configure(
            "BigTimer.TButton", padding=(20, 15), font=("Segoe UI", 14), width=40
        )

        self.title("")
        self.attributes("-topmost", True)
        self.attributes("-fullscreen", True)
        self.configure(bg="white")

        style = ttk.Style()
        style.configure("White.TFrame", background="white")

        main_frame = ttk.Frame(self, style="White.TFrame")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)

        left_image_frame = tk.Frame(main_frame, bg="white")
        left_image_frame.place(relx=0.1, rely=0.5, anchor="center")

        right_image_frame = tk.Frame(main_frame, bg="white")
        right_image_frame.place(relx=0.9, rely=0.5, anchor="center")

        try:
            left_pil = Image.open(IMAGES["LEFT_IMAGE"]).convert("RGBA")
            right_pil = Image.open(IMAGES["RIGHT_IMAGE"]).convert("RGBA")

            new_size = (1000, 1400)

            def resize_image(image, max_size):
                ratio = min(max_size[0] / image.size[0], max_size[1] / image.size[1])
                new_size = tuple(int(dim * ratio) for dim in image.size)
                return image.resize(new_size, Image.Resampling.LANCZOS)

            left_pil = Image.open(IMAGES["LEFT_IMAGE"]).convert("RGBA")
            right_pil = Image.open(IMAGES["RIGHT_IMAGE"]).convert("RGBA")

            def process_transparency(image):
                data = image.getdata()
                new_data = [
                    (30, 30, 30, 0) if item[:3] == (30, 30, 30) else item
                    for item in data
                ]
                image.putdata(new_data)
                return image

            left_pil = process_transparency(left_pil)
            right_pil = process_transparency(right_pil)

            left_image = ImageTk.PhotoImage(left_pil)
            right_image = ImageTk.PhotoImage(right_pil)

            left_label = tk.Label(
                left_image_frame,
                image=left_image,
                bd=0,
                highlightthickness=0,
            )
            left_label.pack()

            right_label = tk.Label(
                right_image_frame,
                image=right_image,
                bd=0,
                highlightthickness=0,
            )
            right_label.pack()

            self.left_image = left_image
            self.right_image = right_image

        except Exception as e:
            print(f"Error loading images: {e}")

        close_btn = tk.Button(
            main_frame,
            text="✕",
            font=("Segoe UI", 16),
            bg="#1e1e1e",
            fg="white",
            activebackground="#404040",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.close_notification,
            width=3,
            height=1,
        )
        close_btn.place(relx=1.0, x=-20, y=10, anchor="ne")

        sound_btn = tk.Button(
            main_frame,
            text="🔊",
            font=("Segoe UI", 16),
            bg="#1e1e1e",
            fg="white",
            activebackground="#404040",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.toggle_sound,
            width=3,
            height=1,
        )
        sound_btn.place(relx=1.0, x=-70, y=10, anchor="ne")
        self.sound_btn = sound_btn
        self.sound_enabled = True

        shortcuts_frame = ttk.Frame(main_frame, style="White.TFrame")
        shortcuts_frame.place(relx=0.5, y=10, anchor="n")

        shortcuts_label = ttk.Label(
            shortcuts_frame,
            text="ESC - закрыть    |    CTRL + (1-9) - выбрать таймер    |    ALT + P - отжимания    |    ALT + M - звук    |    Кликните если клавиши не работают",
            font=("Segoe UI", 10),
            background="white",
            foreground="black",
        )
        shortcuts_label.pack()

        center_frame = ttk.Frame(main_frame, style="White.TFrame")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        top_frame = ttk.Frame(center_frame, style="White.TFrame")
        top_frame.pack(fill=tk.X, pady=(0, 30))

        check_label = ttk.Label(
            top_frame,
            text="✓",
            font=("Segoe UI", 72),
            background="white",
            foreground="#4CAF50",
        )
        check_label.pack(pady=(0, 20))

        title_label = ttk.Label(
            top_frame,
            text="Таймер завершен!",
            font=("Segoe UI", 32, "bold"),
            wraplength=700,
            background="white",
            foreground="black",
        )
        title_label.pack(pady=(0, 10))

        desc_label = ttk.Label(
            top_frame,
            text=description,
            font=("Segoe UI", 18),
            wraplength=700,
            background="white",
            foreground="black",
        )
        desc_label.pack(pady=(0, 20))

        pushup_frame = ttk.Frame(center_frame, style="White.TFrame")
        pushup_frame.pack(fill=tk.X, pady=(0, 30))

        pushup_btn = tk.Button(
            pushup_frame,
            text="Сделал отжимания? Верим, не забудь записать (ALT + P)",
            command=self.quick_pushup,
            font=("Segoe UI", 12),
            bg="#1e4d2b",
            fg="white",
            activebackground="#2d724f",
            activeforeground="white",
            relief="flat",
            height=2,
            padx=10,
            cursor="hand2",
        )
        pushup_btn.pack(fill=tk.X, padx=100)

        self.bind("<KeyPress>", self.handle_hotkey)

        def on_enter(e, b=pushup_btn):
            b.configure(bg="#2d724f")

        def on_leave(e, b=pushup_btn):
            b.configure(bg="#1e4d2b")

        pushup_btn.bind("<Enter>", on_enter)
        pushup_btn.bind("<Leave>", on_leave)

        if next_timers and len(next_timers) > 0:
            ttk.Separator(center_frame, orient="horizontal").pack(fill=tk.X, pady=20)
            timer_frame = ttk.Frame(center_frame, style="White.TFrame")
            timer_frame.pack(fill=tk.X, pady=(0, 30))

            ttk.Label(
                timer_frame,
                text="Запустить следующий таймер:",
                font=("Segoe UI", 16, "bold"),
                background="white",
                foreground="black",
            ).pack(pady=(0, 20))

            buttons_container = ttk.Frame(timer_frame, style="White.TFrame")
            buttons_container.pack(expand=True)

            row_size = 4
            for i, timer in enumerate(next_timers):
                row = i // row_size
                col = i % row_size

                button_frame = ttk.Frame(buttons_container)
                button_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                button_frame.grid_columnconfigure(0, weight=1)

                hours = int(timer.hours.get() or 0)
                minutes = int(timer.minutes.get() or 0)
                seconds = int(timer.seconds.get() or 0)
                time_str = f"{hours}:{minutes:02d}:{seconds:02d}"

                shortcut_num = i + 1
                btn = tk.Button(
                    button_frame,
                    text=f"{timer.description.get()}\n{time_str}\nCTRL + {shortcut_num}",
                    command=lambda t=timer: self.start_next_timer(t),
                    font=("Segoe UI", 12),
                    bg="#2C2C2C",
                    fg="white",
                    activebackground="#404040",
                    activeforeground="white",
                    relief="flat",
                    height=3,
                    width=25,
                    cursor="hand2",
                )
                btn.pack(fill=tk.BOTH)

                self.bind(
                    f"<Control-Key-{shortcut_num}>",
                    lambda e, t=timer: self.start_next_timer(t),
                )

                def on_enter(e, b=btn):
                    b.configure(bg="#404040")

                def on_leave(e, b=btn):
                    b.configure(bg="#2C2C2C")

                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)

                if shortcut_num >= 9:
                    break

                for i in range(row_size):
                    buttons_container.grid_columnconfigure(i, weight=1)

        self.focus_force()
        self.bind("<Button-1>", lambda e: self.focus_force())
        self.bind("<Escape>", lambda e: self.close_notification())

        self.attributes("-alpha", 0.0)
        self.fade_in()

    def handle_hotkey(self, event):
        if event.state == 131080 or event.state == 131082:
            if event.keycode == 77:
                self.toggle_sound()
            elif event.keycode == 80:
                self.quick_pushup()

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.sound_btn.configure(text="🔊" if self.sound_enabled else "🔈")

        if not self.sound_enabled:
            if mixer.get_init():
                mixer.music.stop()
            if self.current_timer:
                self.current_timer.is_running = False
        else:
            if self.current_timer:
                self.current_timer.is_running = True
                self.current_timer.play_alarm()

    def quick_pushup(self):
        input_window = tk.Toplevel(self)
        input_window.title("Сделал отжимания? Верим, не забудь записать")
        input_window.configure(bg="#1e1e1e")
        input_window.attributes("-topmost", True)
        input_window.resizable(False, False)

        window_width = 525
        window_height = 325
        screen_width = input_window.winfo_screenwidth()
        screen_height = input_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        input_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = ttk.Frame(input_window)
        main_frame.pack(fill=tk.BOTH, padx=30, pady=20)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X)

        ttk.Label(
            header_frame, text="Количество отжиманий", font=("Segoe UI", 16, "bold")
        ).pack(side=tk.TOP, anchor="center")

        hints_frame = ttk.Frame(main_frame)
        hints_frame.pack(fill=tk.X, pady=(5, 20))

        ttk.Label(
            hints_frame,
            text="Enter - подтвердить    |    ESC - отмена",
            font=("Segoe UI", 10),
            foreground="#666666",
        ).pack(side=tk.TOP, anchor="center")

        presets_frame = ttk.Frame(main_frame)
        presets_frame.pack(fill=tk.X, pady=(0, 20))

        presets = [20, 25, 30, 35, 40, 45]
        btn_width = 8
        for preset in presets:
            preset_btn = tk.Button(
                presets_frame,
                text=str(preset),
                command=lambda x=preset: submit(x),
                font=("Segoe UI", 11),
                bg="#2C2C2C",
                fg="white",
                activebackground="#404040",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                width=btn_width,
                height=1,
            )
            preset_btn.pack(side=tk.LEFT, padx=2)

            def on_enter(e, b=preset_btn):
                b.configure(bg="#404040")

            def on_leave(e, b=preset_btn):
                b.configure(bg="#2C2C2C")

            preset_btn.bind("<Enter>", on_enter)
            preset_btn.bind("<Leave>", on_leave)

        ttk.Label(
            main_frame,
            text="или введите своё значение",
            font=("Segoe UI", 10),
            foreground="#666666",
        ).pack(pady=(0, 10))

        spinbox = ttk.Spinbox(
            main_frame, from_=1, to=100, width=8, font=("Segoe UI", 14)
        )
        spinbox.set("10")
        spinbox.pack(pady=(0, 20))

        def submit(count=None):
            try:
                if count is None:
                    count = int(spinbox.get())
                main_window = self.find_main_window()
                if main_window and hasattr(main_window, "pushup_tracker"):
                    main_window.pushup_tracker.add_pushups(count)
                    self.show_pushup_added(count)
                input_window.destroy()
            except ValueError:
                pass

        submit_btn = tk.Button(
            main_frame,
            text="Записать",
            command=lambda: submit(),
            font=("Segoe UI", 12),
            bg="#1e4d2b",
            fg="white",
            activebackground="#2d724f",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=15,
            height=1,
        )
        submit_btn.pack(pady=(0, 20))

        def on_enter_submit(e):
            submit_btn.configure(bg="#2d724f")

        def on_leave_submit(e):
            submit_btn.configure(bg="#1e4d2b")

        submit_btn.bind("<Enter>", on_enter_submit)
        submit_btn.bind("<Leave>", on_leave_submit)

        input_window.bind("<Return>", lambda e: submit())
        input_window.bind("<Escape>", lambda e: input_window.destroy())

        spinbox.focus_set()
        input_window.focus_force()

    def find_main_window(self):
        current = self.parent
        while current:
            if hasattr(current, "pushup_tracker"):
                return current
            current = current.master
        return None

    def show_pushup_added(self, count):
        notification = tk.Toplevel(self)
        notification.overrideredirect(True)
        notification.attributes("-topmost", True)
        notification.configure(bg="#1e4d2b")

        x = self.winfo_screenwidth() - 300 - 20
        y = self.winfo_screenheight() - 100 - 20
        notification.geometry(f"300x100+{x}+{y}")

        ttk.Label(
            notification,
            text=f"✓ Записано {count} отжиманий",
            font=("Segoe UI", 14, "bold"),
            foreground="white",
            background="#1e4d2b",
        ).pack(expand=True)

        notification.after(2000, notification.destroy)

    def stop_timer(self):
        self.result = "stop"
        self.close_notification()

    def continue_timer(self):
        self.result = "continue"
        self.close_notification()

    def find_timer_list(self, widget):
        """Ищет объект, содержащий список таймеров"""
        current = widget
        while current:
            if hasattr(current, "timers"):
                return current
            current = current.master
        return None

    def start_next_timer(self, timer):
        self.result = "next"

        if (
            self.current_timer
            and hasattr(self.current_timer, "main_window")
            and self.current_timer.main_window
            and self.current_timer.main_window.winfo_exists()
        ):
            existing_window = self.current_timer.main_window
            self.current_timer.main_window = None
            timer.main_window = existing_window
            existing_window.timer = timer
            existing_window.description_label.configure(text=timer.description.get())
            existing_window.draw_progress()

        timer.start_timer()
        self.close_notification()

    def fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 1.0:
            self.attributes("-alpha", alpha + 0.1)
            self.after(20, self.fade_in)

    def close_notification(self):
        def fade_out():
            alpha = self.attributes("-alpha")
            if alpha > 0:
                self.attributes("-alpha", alpha - 0.1)
                self.after(20, fade_out)
            else:
                self.destroy()

        fade_out()
