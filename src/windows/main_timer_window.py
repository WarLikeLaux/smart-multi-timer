import tkinter as tk
from tkinter import ttk


class MainTimerWindow(tk.Toplevel):
    def __init__(self, parent, timer):
        super().__init__(parent)
        self.timer = timer
        self.setup_window()
        self.setup_ui()
        self.setup_bindings()

        if not self.timer.initial_time:
            self.timer.initial_time = (
                int(self.timer.hours.get() or 0) * 3600
                + int(self.timer.minutes.get() or 0) * 60
                + int(self.timer.seconds.get() or 0)
            )

        self.draw_progress()

    def is_destroyed(self):
        """Проверяет, было ли окно уничтожено"""
        try:
            self.winfo_exists()
            return False
        except tk.TclError:
            return True

    def draw_progress(self):
        try:
            self.canvas.delete("progress")

            if self.timer.initial_time and self.timer.initial_time > 0:
                progress = self.timer.remaining_time / self.timer.initial_time
            else:
                progress = 1.0

            progress = max(0, min(1, progress))

            padding = 20
            x0 = padding
            y0 = padding
            x1 = self.canvas_size - padding
            y1 = self.canvas_size - padding

            self.progress_arc = self.canvas.create_arc(
                x0,
                y0,
                x1,
                y1,
                start=90,
                extent=-359.999 * (1 - progress),
                fill="#4A90E2",
                width=2,
                tags="progress",
            )

            if hasattr(self, "time_label"):
                hours = self.timer.remaining_time // 3600
                minutes = (self.timer.remaining_time % 3600) // 60
                seconds = self.timer.remaining_time % 60
                self.time_label.configure(
                    text=f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                )

        except (tk.TclError, AttributeError, TypeError) as e:
            print(f"Ошибка в draw_progress: {e}")

    def setup_window(self):
        self.title("")
        self.attributes("-topmost", True)

        self.minsize(400, 400)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_size = min(screen_width, screen_height) // 3

        x = (screen_width - window_size) // 2
        y = (screen_height - window_size) // 2
        self.geometry(f"{window_size}x{window_size}+{x}+{y}")

        self.style = ttk.Style()

        self.configure(bg="#1A1A1A")

        self.style.configure("Timer.TFrame", background="#1A1A1A")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        canvas_frame = ttk.Frame(self.main_frame)
        canvas_frame.pack(expand=True, fill=tk.BOTH)

        self.minsize(400, 400)

        self.canvas_size = 300
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="#1e1e1e",
            highlightthickness=0,
        )

        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        padding = 20
        x0 = padding
        y0 = padding
        x1 = self.canvas_size - padding
        y1 = self.canvas_size - padding

        self.background_arc = self.canvas.create_arc(
            x0,
            y0,
            x1,
            y1,
            start=90,
            extent=359.999,
            fill="#2D2D2D",
            width=2,
            tags="static",
        )

        self.progress_arc = self.canvas.create_arc(
            x0, y0, x1, y1, start=90, extent=0, fill="#4A90E2", width=2, tags="progress"
        )

        inner_padding = padding + 10
        self.inner_circle = self.canvas.create_oval(
            inner_padding,
            inner_padding,
            self.canvas_size - inner_padding,
            self.canvas_size - inner_padding,
            fill="#1A1A1A",
            tags="static",
        )

        self.time_label = tk.Label(
            self.canvas,
            font=("Roboto", 48, "bold"),
            bg="#1e1e1e",
            fg="white",
        )
        self.time_label.place(relx=0.5, rely=0.45, anchor="center")

        self.description_label = tk.Label(
            self.canvas,
            font=("Roboto", 14),
            bg="#1e1e1e",
            fg="white",
            text=self.timer.description.get(),
        )
        self.description_label.place(relx=0.5, rely=0.6, anchor="center")

        self.controls_frame = ttk.Frame(self.main_frame)
        self.controls_frame.pack(fill=tk.X, pady=(20, 0))

        style = ttk.Style()
        style.configure(
            "Timer.Custom.TButton",
            font=("Segoe UI", 12),
            padding=5,
            anchor="center",
        )

        button_height = 40

        left_container = ttk.Frame(self.controls_frame, height=button_height)
        left_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        left_container.pack_propagate(False)

        middle_container = ttk.Frame(self.controls_frame, height=button_height)
        middle_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        middle_container.pack_propagate(False)

        right_container = ttk.Frame(self.controls_frame, height=button_height)
        right_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        right_container.pack_propagate(False)

        self.pause_btn = ttk.Button(
            left_container,
            text="Пауза",
            command=self.toggle_pause,
            style="Timer.Custom.TButton",
            takefocus=0,
        )
        self.pause_btn.place(relx=0.5, rely=0.5, anchor="center", relwidth=1)

        self.stop_btn = ttk.Button(
            middle_container,
            text="Сброс",
            command=self.reset_timer,
            style="Timer.Custom.TButton",
            takefocus=0,
        )
        self.stop_btn.place(relx=0.5, rely=0.5, anchor="center", relwidth=1)

        self.close_btn = ttk.Button(
            right_container,
            text="Закрыть",
            command=self.on_close,
            style="Timer.Custom.TButton",
            takefocus=0,
        )
        self.close_btn.place(relx=0.5, rely=0.5, anchor="center", relwidth=1)

        for btn in [self.pause_btn, self.stop_btn, self.close_btn]:
            btn.bind("<Enter>", self.on_button_enter)
            btn.bind("<Leave>", self.on_button_leave)

    def reset_timer(self):
        """Сброс таймера без закрытия окна"""
        self.timer.stop_timer()
        self.draw_progress()
        self.pause_btn.configure(text="Пауза")

    def on_button_enter(self, event):
        """Эффект при наведении на кнопку"""
        button = event.widget
        if button == self.pause_btn:
            button.configure(bg="#357ABD")
        elif button == self.stop_btn:
            button.configure(bg="#C0392B")
        else:
            button.configure(bg="#404040")

    def on_button_leave(self, event):
        """Возврат к обычному цвету"""
        button = event.widget
        if button == self.pause_btn:
            button.configure(bg="#4A90E2")
        elif button == self.stop_btn:
            button.configure(bg="#E74C3C")
        else:
            button.configure(bg="#2D2D2D")

    def setup_bindings(self):
        self.bind("<Configure>", self.on_resize)

        self.bind("<space>", lambda e: self.toggle_pause())
        self.bind("<Escape>", lambda e: self.destroy())

        for btn in [self.pause_btn, self.stop_btn, self.close_btn]:
            btn.bind("<Enter>", self.on_button_hover)
            btn.bind("<Leave>", self.on_button_leave)

    def on_button_hover(self, event):
        try:
            button = event.widget
            button.configure(style="Modern.Timer.TButton.Hover")
        except tk.TclError:
            pass

    def on_button_leave(self, event):
        try:
            button = event.widget
            button.configure(style="Modern.Timer.TButton")
        except tk.TclError:
            pass

    def on_resize(self, event):
        if event.widget == self:
            window_width = event.width
            window_height = event.height

            new_size = min(window_width, window_height) - 100
            self.canvas_size = max(300, new_size)

            self.canvas.configure(width=self.canvas_size, height=self.canvas_size)

            self.canvas.delete("static")
            self.canvas.delete("progress")

            padding = 20
            x0 = padding
            y0 = padding
            x1 = self.canvas_size - padding
            y1 = self.canvas_size - padding

            self.background_arc = self.canvas.create_arc(
                x0,
                y0,
                x1,
                y1,
                start=90,
                extent=359.999,
                fill="#2D2D2D",
                width=2,
                tags="static",
            )

            inner_padding = padding + 10
            self.inner_circle = self.canvas.create_oval(
                inner_padding,
                inner_padding,
                self.canvas_size - inner_padding,
                self.canvas_size - inner_padding,
                fill="#1A1A1A",
                tags="static",
            )

            self.draw_progress()

            self.update_ui()

    def update_ui(self):
        self.time_label.place(relx=0.5, rely=0.45, anchor="center")
        self.description_label.place(relx=0.5, rely=0.6, anchor="center")

        font_size = int(self.canvas_size / 8)
        self.time_label.configure(font=("Roboto", font_size, "bold"))
        self.description_label.configure(font=("Roboto", int(font_size / 3)))

    def toggle_pause(self):
        try:
            if self.timer.is_running:
                self.timer.pause_timer()
                self.pause_btn.configure(text="Продолжить", bg="#2ECC71")
            else:
                self.timer.start_timer()
                self.pause_btn.configure(text="Пауза", bg="#4A90E2")
        except tk.TclError:
            pass

    def stop_timer(self):
        self.timer.stop_timer()
        self.destroy()

    def on_close(self):
        try:

            def fade_out():
                try:
                    if not self.is_destroyed():
                        alpha = self.attributes("-alpha")
                        if alpha > 0:
                            self.attributes("-alpha", alpha - 0.1)
                            self.after(20, fade_out)
                        else:
                            self.destroy()
                            if hasattr(self.timer, "main_window"):
                                self.timer.main_window = None
                except tk.TclError:
                    pass

            fade_out()
        except tk.TclError:
            if hasattr(self.timer, "main_window"):
                self.timer.main_window = None
            self.destroy()
