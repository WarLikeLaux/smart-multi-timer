import platform
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pygame import mixer

from utils.sound_utils import SoundPlayer
from utils.timer_notification import TimerNotification
from windows.main_timer_window import MainTimerWindow

if platform.system() == "Windows":
    import winsound


class Timer(ttk.Frame):
    def __init__(self, parent, on_delete=None):
        super().__init__(parent)
        self.parent = parent
        self.on_delete = on_delete
        self.remaining_time = 0
        self.is_running = False
        self.custom_sound = None
        self.paused_time = 0
        self.initial_time = None
        self.main_window = None
        self.sound_player = SoundPlayer()
        self.emoji_window = None
        self.time_inputs_focused = False
        self.setup_ui()

    def safe_update_main_window(self):
        try:
            if self.main_window and self.main_window.winfo_exists():
                if hasattr(self.main_window, "time_label"):
                    self.main_window.time_label.configure(
                        text=self.time_label.cget("text")
                    )
                if hasattr(self.main_window, "description_label"):
                    self.main_window.description_label.configure(
                        text=self.description.get()
                    )
                if self.initial_time:
                    self.main_window.draw_progress()
        except (tk.TclError, AttributeError):
            pass

    def update_display(self):
        hours = self.remaining_time // 3600
        minutes = (self.remaining_time % 3600) // 60
        seconds = self.remaining_time % 60
        display_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        try:
            self.time_label.configure(text=display_text)
            self.safe_update_main_window()
        except tk.TclError:
            pass

    def show_main_screen(self):
        if not self.main_window or not self.main_window.winfo_exists():
            if not self.initial_time:
                self.initial_time = (
                    int(self.hours.get() or 0) * 3600
                    + int(self.minutes.get() or 0) * 60
                    + int(self.seconds.get() or 0)
                )

            self.main_window = MainTimerWindow(self.parent, self)
            self.main_window.attributes("-alpha", 0.0)

            def fade_in():
                try:
                    alpha = self.main_window.attributes("-alpha")
                    if alpha < 1.0:
                        self.main_window.attributes("-alpha", alpha + 0.1)
                        self.main_window.after(20, fade_in)
                except tk.TclError:
                    pass

            fade_in()

    def setup_ui(self):
        main_container = ttk.Frame(self)
        main_container["padding"] = (15, 10, 15, 10)
        main_container.pack(fill=tk.X, pady=5)

        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.X, expand=True)

        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))

        description_frame = ttk.Frame(left_frame)
        description_frame.pack(fill=tk.X, expand=True)

        self.description = ttk.Entry(description_frame, font=("Arial", 12))
        self.description.insert(0, "Описание таймера")
        self.description.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.context_menu = tk.Menu(self.description, tearoff=0)
        self.context_menu.add_command(label="Копировать", command=self.copy_text)
        self.context_menu.add_command(label="Вставить", command=self.paste_text)
        self.context_menu.add_command(label="Вырезать", command=self.cut_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Выбрать всё", command=self.select_all)

        self.description.bind("<Button-3>", self.show_context_menu)
        self.description.bind("<Control-c>", lambda e: self.copy_text())
        self.description.bind("<Control-v>", lambda e: self.paste_text())
        self.description.bind("<Control-x>", lambda e: self.cut_text())
        self.description.bind("<Control-a>", lambda e: self.select_all())

        self.emoji_button = ttk.Button(
            description_frame,
            text="😀",
            command=self.show_emoji_picker,
            width=3,
            takefocus=0,
        )
        self.emoji_button.pack(side=tk.RIGHT, padx=(5, 0))

        time_frame = ttk.Frame(content_frame)
        time_frame.pack(side=tk.LEFT, padx=15)

        self.time_label = ttk.Label(time_frame, font=("Arial", 16, "bold"))
        self.time_label.pack(pady=(0, 5))

        spinbox_container = ttk.Frame(time_frame)
        spinbox_container.pack()

        spinbox_style = {"width": 3, "font": ("Arial", 12), "justify": "center"}

        self.hours = ttk.Spinbox(spinbox_container, from_=0, to=23, **spinbox_style)
        self.hours.pack(side=tk.LEFT)

        ttk.Label(spinbox_container, text=":", font=("Arial", 12)).pack(
            side=tk.LEFT, padx=3
        )

        self.minutes = ttk.Spinbox(spinbox_container, from_=0, to=59, **spinbox_style)
        self.minutes.pack(side=tk.LEFT)

        ttk.Label(spinbox_container, text=":", font=("Arial", 12)).pack(
            side=tk.LEFT, padx=3
        )

        self.seconds = ttk.Spinbox(spinbox_container, from_=0, to=59, **spinbox_style)
        self.seconds.pack(side=tk.LEFT)

        self.hours.bind(
            "<<Increment>>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )
        self.hours.bind(
            "<<Decrement>>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )
        self.hours.bind(
            "<KeyRelease>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )

        self.minutes.bind(
            "<<Increment>>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )
        self.minutes.bind(
            "<<Decrement>>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )
        self.minutes.bind(
            "<KeyRelease>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )

        self.seconds.bind(
            "<<Increment>>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )
        self.seconds.bind(
            "<<Decrement>>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )
        self.seconds.bind(
            "<KeyRelease>",
            lambda e: (self.update_time_display(), self.update_presets_visibility()),
        )

        self.hours.bind("<FocusIn>", self.on_time_input_focus_in)
        self.hours.bind("<FocusOut>", self.on_time_input_focus_out)
        self.minutes.bind("<FocusIn>", self.on_time_input_focus_in)
        self.minutes.bind("<FocusOut>", self.on_time_input_focus_out)
        self.seconds.bind("<FocusIn>", self.on_time_input_focus_in)
        self.seconds.bind("<FocusOut>", self.on_time_input_focus_out)

        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(side=tk.RIGHT, padx=(15, 0))

        style = ttk.Style()
        style.configure(
            "Timer.Control.TButton",
            padding=5,
            width=5,
            font=("Arial", 12),
        )

        style.configure(
            "Timer.Utility.TButton",
            padding=5,
            width=4,
            font=("Arial", 12),
        )

        control_buttons_frame = ttk.Frame(btn_frame)
        control_buttons_frame.pack(side=tk.LEFT, padx=(0, 10))

        self.start_button = ttk.Button(
            control_buttons_frame,
            text="▶",
            command=self.start_timer,
            style="Timer.Control.TButton",
            takefocus=0,
        )
        self.start_button.pack(side=tk.LEFT, padx=4)

        self.pause_button = ttk.Button(
            control_buttons_frame,
            text="⏸",
            command=self.pause_timer,
            style="Timer.Control.TButton",
            takefocus=0,
        )
        self.pause_button.pack(side=tk.LEFT, padx=4)

        self.stop_button = ttk.Button(
            control_buttons_frame,
            text="⏹",
            command=self.stop_timer,
            style="Timer.Control.TButton",
            takefocus=0,
        )
        self.stop_button.pack(side=tk.LEFT, padx=4)

        utility_buttons_frame = ttk.Frame(btn_frame)
        utility_buttons_frame.pack(side=tk.LEFT)

        self.sound_button = ttk.Button(
            utility_buttons_frame,
            text="🔊",
            command=self.choose_sound,
            style="Timer.Utility.TButton",
            takefocus=0,
        )
        self.sound_button.pack(side=tk.LEFT, padx=4)

        self.delete_button = ttk.Button(
            utility_buttons_frame,
            text="✖",
            command=self.delete_timer,
            style="Timer.Utility.TButton",
            takefocus=0,
        )
        self.delete_button.pack(side=tk.LEFT, padx=4)

        self.fullscreen_button = ttk.Button(
            utility_buttons_frame,
            text="🔲",
            command=self.show_main_screen,
            style="Timer.Utility.TButton",
            takefocus=0,
        )
        self.fullscreen_button.pack(side=tk.LEFT, padx=4)

        self.presets_frame = ttk.Frame(main_container)
        self.presets_frame.pack(fill=tk.X, pady=(10, 0))

        self.presets_data = [
            ("5 минут", 5),
            ("10 минут", 10),
            ("15 минут", 15),
            ("17 минут", 17),
            ("25 минут", 25),
            ("30 минут", 30),
            ("45 минут", 45),
            ("52 минуты", 52),
            ("1 час", 60),
            ("2 часа", 120),
        ]

        self.preset_buttons = []
        for label, minutes in self.presets_data:
            btn = ttk.Button(
                self.presets_frame,
                text=label,
                command=lambda m=minutes: self.apply_preset(m),
                style="Secondary.TButton",
                width=10,
                takefocus=0,
            )
            self.preset_buttons.append(btn)

        self.presets_frame.bind("<Configure>", self.reflow_preset_buttons)
        self.reflow_preset_buttons()

        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill=tk.X, pady=(10, 0))

        self.update_time_display()
        self.update_presets_visibility()

    def start_timer(self):
        if not self.is_running:
            if self.paused_time > 0:
                self.remaining_time = self.paused_time
                self.paused_time = 0
            else:
                total_seconds = (
                    int(self.hours.get() or 0) * 3600
                    + int(self.minutes.get() or 0) * 60
                    + int(self.seconds.get() or 0)
                )
                self.remaining_time = total_seconds
                self.initial_time = total_seconds

            if self.remaining_time > 0:
                self.is_running = True
                self.start_button.state(["disabled"])
                self.hours.state(["disabled"])
                self.minutes.state(["disabled"])
                self.seconds.state(["disabled"])

                try:
                    if (
                        self.main_window
                        and self.main_window.winfo_exists()
                        and hasattr(self.main_window, "pause_btn")
                    ):
                        self.main_window.pause_btn.configure(text="⏸")
                except tk.TclError:
                    pass

                self.update_thread = threading.Thread(target=self.update_timer)
                self.update_thread.daemon = True
                self.update_thread.start()

    def update_timer(self):
        while self.is_running and self.remaining_time > 0:
            try:
                self.update_display()
                if hasattr(self, "main_window") and self.main_window:
                    self.main_window.draw_progress()
                time.sleep(1)
                self.remaining_time -= 1
            except tk.TclError:
                break

        if self.is_running:
            self.is_running = False
            self.play_alarm()
            self.show_notification()

    def pause_timer(self):
        if self.is_running:
            self.is_running = False
            self.paused_time = self.remaining_time
            self.start_button.config(text="▶")
            self.start_button.state(["!disabled"])

            try:
                if (
                    self.main_window
                    and self.main_window.winfo_exists()
                    and hasattr(self.main_window, "pause_btn")
                ):
                    self.main_window.pause_btn.configure(text="▶")
            except tk.TclError:
                pass

    def stop_timer(self):
        self.is_running = False
        total_seconds = (
            int(self.hours.get() or 0) * 3600
            + int(self.minutes.get() or 0) * 60
            + int(self.seconds.get() or 0)
        )
        self.remaining_time = total_seconds
        self.paused_time = 0
        self.initial_time = total_seconds

        self.start_button.state(["!disabled"])
        self.start_button.config(text="▶")
        self.hours.state(["!disabled"])
        self.minutes.state(["!disabled"])
        self.seconds.state(["!disabled"])

        try:
            if (
                self.main_window
                and self.main_window.winfo_exists()
                and not self.main_window.is_destroyed()
            ):
                if hasattr(self.main_window, "pause_btn"):
                    try:
                        self.main_window.pause_btn.configure(text="▶")
                    except tk.TclError:
                        pass

                try:
                    self.main_window.draw_progress()
                except tk.TclError:
                    pass
        except (tk.TclError, AttributeError):
            pass

        self.update_display()
        self.update_presets_visibility()

    def update_time_display(self):
        try:
            hours = int(self.hours.get() or 0)
            minutes = int(self.minutes.get() or 0)
            seconds = int(self.seconds.get() or 0)
            display_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.time_label.configure(text=display_text)
        except (ValueError, tk.TclError):
            self.time_label.configure(text="00:00:00")

    def apply_preset(self, minutes):
        self.hours.set("0")
        self.minutes.set(str(minutes))
        self.seconds.set("0")
        self.update_time_display()
        self.update_presets_visibility()

    def update_presets_visibility(self):
        total_seconds = (
            int(self.hours.get() or 0) * 3600
            + int(self.minutes.get() or 0) * 60
            + int(self.seconds.get() or 0)
        )

        if total_seconds == 0 or self.time_inputs_focused:
            self.presets_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.presets_frame.pack_forget()

    def on_time_input_focus_in(self, event):
        self.time_inputs_focused = True
        self.update_presets_visibility()

    def on_time_input_focus_out(self, event):
        self.time_inputs_focused = False
        self.update_presets_visibility()

    def reflow_preset_buttons(self, event=None):
        frame_width = self.presets_frame.winfo_width()

        if frame_width <= 1:
            return

        button_width = 85
        buttons_per_row = max(1, frame_width // button_width)

        for i in range(100):
            self.presets_frame.columnconfigure(i, weight=0)

        row, col = 0, 0
        for btn in self.preset_buttons:
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
            col += 1
            if col >= buttons_per_row:
                col = 0
                row += 1

        for i in range(buttons_per_row):
            self.presets_frame.columnconfigure(i, weight=1)

    def choose_sound(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("MP3 files", "*.mp3"), ("WAV files", "*.wav")]
        )
        if file_path:
            self.custom_sound = file_path
            self.sound_button.config(text="🔊 ✓")

    def play_alarm(self):
        def sound_thread():
            if not hasattr(self, "alarm_active"):
                self.alarm_active = True

            if (
                hasattr(self, "custom_sound")
                and self.custom_sound
                and self.alarm_active
            ):
                try:
                    mixer.init()
                    mixer.music.load(self.custom_sound)
                    mixer.music.play(-1)
                except Exception as e:
                    print(f"Ошибка воспроизведения custom sound: {e}")
                    if self.alarm_active:
                        self.beep_alarm()
            else:
                if self.alarm_active:
                    self.beep_alarm()

        self.alarm_active = True
        self.sound_thread = threading.Thread(target=sound_thread, daemon=True)
        self.sound_thread.start()

    def beep_alarm(self):
        def beep_thread():
            while self.is_running and getattr(self, "alarm_active", True):
                try:
                    self.sound_player.play_beep()
                    time.sleep(0.5)
                except:
                    break

        self.is_running = True
        self.alarm_active = True
        self.beep_thread = threading.Thread(target=beep_thread, daemon=True)
        self.beep_thread.start()

    def stop_alarm(self):
        self.alarm_active = False
        self.is_running = False

        try:
            if mixer.get_init():
                mixer.music.stop()
                mixer.stop()
                mixer.quit()
        except:
            pass

        if hasattr(self, "sound_player"):
            self.sound_player.stop()

    def show_notification(self):
        try:
            next_timers = []
            if hasattr(self.parent, "timers"):
                next_timers = [t for t in self.parent.timers if t != self]

            notification = TimerNotification(
                self.parent, self.description.get(), next_timers, current_timer=self
            )

            self.wait_window(notification)

            if hasattr(notification, "result") and notification.result == "snooze":
                return

            self.stop_alarm()
            self.is_running = False
            self.stop_timer()

        except tk.TclError:
            pass

    def delete_timer(self):
        if messagebox.askyesno("Подтверждение", "Действительно удалить таймер?"):
            if self.on_delete:
                self.on_delete(self)

    def to_dict(self):
        return {
            "description": self.description.get(),
            "hours": self.hours.get(),
            "minutes": self.minutes.get(),
            "seconds": self.seconds.get(),
            "custom_sound": (
                self.custom_sound if hasattr(self, "custom_sound") else None
            ),
        }

    def copy_text(self):
        try:
            self.description.clipboard_clear()
            if self.description.selection_get():
                self.description.clipboard_append(self.description.selection_get())
        except tk.TclError:
            pass

    def paste_text(self):
        try:
            self.description.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        try:
            self.description.insert(tk.INSERT, self.description.clipboard_get())
        except tk.TclError:
            pass

    def cut_text(self):
        try:
            self.copy_text()
            self.description.delete("sel.first", "sel.last")
        except tk.TclError:
            pass

    def select_all(self):
        self.description.select_range(0, tk.END)
        self.description.icursor(tk.END)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def show_emoji_picker(self):
        if self.emoji_window and self.emoji_window.winfo_exists():
            self.emoji_window.destroy()

        self.emoji_window = tk.Toplevel(self)
        self.emoji_window.title("Выбор эмодзи")
        self.emoji_window.transient(self)
        self.emoji_window.grab_set()

        categories = {
            "Действия": ["⏰", "☕", "🍽️", "📚", "💼", "🏃", "🧘", "🛌", "🎮", "📱", "🎧", "📝"],
            "Перерывы": ["🍵", "🧋", "🍰", "🍪", "🍎", "🥗", "🚶", "💆", "🌿", "🧠", "🍦", "🍺"],
            "Состояния": ["💤", "⚡", "🔥", "💪", "🎭", "💡", "🎯", "✅", "❌", "⭐", "🏆", "🎖️"],
            "Работа": [
                "💻",
                "📊",
                "📈",
                "📞",
                "📧",
                "👨‍💻",
                "👩‍💻",
                "📁",
                "🗂️",
                "🖋️",
                "🔍",
                "🎓",
            ],
            "Прочее": [
                "🏠",
                "🌳",
                "👨‍👩‍👧‍👦",
                "👥",
                "🐱",
                "🐶",
                "🚗",
                "🚲",
                "🛒",
                "🧹",
                "🎁",
                "💰",
            ],
        }

        notebook = ttk.Notebook(self.emoji_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for category, emojis in categories.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=category)

            row, col = 0, 0
            for emoji in emojis:
                button = ttk.Button(
                    frame,
                    text=emoji,
                    width=3,
                    command=lambda e=emoji: self.insert_emoji(e),
                )
                button.grid(row=row, column=col, padx=5, pady=5)

                col += 1
                if col > 5:
                    col = 0
                    row += 1

        custom_frame = ttk.Frame(self.emoji_window)
        custom_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(custom_frame, text="Свой эмодзи:").pack(side=tk.LEFT)

        custom_emoji = ttk.Entry(custom_frame, width=5, font=("Arial", 12))
        custom_emoji.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Button(
            custom_frame,
            text="Добавить",
            command=lambda: self.insert_emoji(custom_emoji.get()),
        ).pack(side=tk.LEFT)

        self.emoji_window.update_idletasks()
        width = self.emoji_window.winfo_width()
        height = self.emoji_window.winfo_height()
        x = (self.emoji_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.emoji_window.winfo_screenheight() // 2) - (height // 2)
        self.emoji_window.geometry(f"{width}x{height}+{x}+{y}")
        self.emoji_window.minsize(300, 200)

    def insert_emoji(self, emoji):
        if emoji:
            current_position = self.description.index(tk.INSERT)
            self.description.insert(current_position, emoji)
            if self.emoji_window and self.emoji_window.winfo_exists():
                self.emoji_window.destroy()
