import tkinter as tk
from tkinter import ttk


class TimerNotification(tk.Toplevel):
    def __init__(self, parent, description, next_timers=None):
        super().__init__(parent)
        self.next_timers = next_timers
        self.result = None

        style = ttk.Style()
        style.configure(
            "BigTimer.TButton",
            padding=(20, 15),
            font=("Segoe UI", 14),
            width=40,
        )

        self.title("")
        self.attributes("-topmost", True)
        self.configure(bg="#1e1e1e")

        base_height = 600
        additional_height = 100 if next_timers else 0
        window_width = 800
        window_height = base_height + additional_height

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=40)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 30))

        check_label = ttk.Label(
            top_frame, text="✓", font=("Segoe UI", 72), foreground="#4CAF50"
        )
        check_label.pack(pady=(0, 20))

        title_label = ttk.Label(
            top_frame,
            text="Таймер завершен!",
            font=("Segoe UI", 32, "bold"),
            wraplength=700,
        )
        title_label.pack(pady=(0, 10))

        desc_label = ttk.Label(
            top_frame, text=description, font=("Segoe UI", 18), wraplength=700
        )
        desc_label.pack(pady=(0, 20))

        if next_timers and len(next_timers) > 0:
            timer_frame = ttk.Frame(main_frame)
            timer_frame.pack(fill=tk.X, pady=(0, 30))

            ttk.Label(
                timer_frame,
                text="Запустить следующий таймер:",
                font=("Segoe UI", 16, "bold"),
            ).pack(pady=(0, 20))

            buttons_frame = ttk.Frame(timer_frame)
            buttons_frame.pack(fill=tk.X)

            buttons_frame.grid_columnconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure(1, weight=1)

            row = 0
            col = 0
            for timer in next_timers:
                hours = int(timer.hours.get() or 0)
                minutes = int(timer.minutes.get() or 0)
                seconds = int(timer.seconds.get() or 0)
                time_str = f"{hours}:{minutes:02d}:{seconds:02d}"

                btn = tk.Button(
                    buttons_frame,
                    text=f"{timer.description.get()}\n{time_str}",
                    command=lambda t=timer: self.start_next_timer(t),
                    font=("Segoe UI", 14),
                    bg="#2C2C2C",
                    fg="white",
                    activebackground="#404040",
                    activeforeground="white",
                    relief="flat",
                    height=3,
                    width=30,
                    cursor="hand2",
                )
                btn.grid(row=row, column=col, padx=10, pady=8, sticky="nsew")

                def on_enter(e, b=btn):
                    b.configure(bg="#404040")

                def on_leave(e, b=btn):
                    b.configure(bg="#2C2C2C")

                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)

                col += 1
                if col > 1:
                    col = 0
                    row += 1

        self.attributes("-alpha", 0.0)
        self.fade_in()

    def stop_timer(self):
        self.result = "stop"
        self.close_notification()

    def continue_timer(self):
        self.result = "continue"
        self.close_notification()

    def start_next_timer(self, timer):
        self.result = "next"
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
