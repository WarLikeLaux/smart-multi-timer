import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk

from pygame import mixer

from utils.constants import SOUNDS
from utils.sound_utils import SoundPlayer


class HabitReminder:
    def __init__(self, parent):
        self.parent = parent
        self.sound_player = SoundPlayer()

        if not mixer.get_init():
            mixer.init()
        try:
            self.notification_sound = mixer.Sound(SOUNDS["HABIT_NOTIFICATION"])
        except:
            self.notification_sound = None
            print("Не удалось загрузить habit.mp3")

        self.check_thread = threading.Thread(target=self.check_habits, daemon=True)
        self.check_thread.start()

    def check_habits(self):
        while True:
            current_time = datetime.now()

            for habit in self.parent.habits:
                if not habit["enabled"]:
                    continue

                try:
                    start_time = datetime.strptime(habit["start_time"], "%H:%M").time()

                    if habit["end_time"] == "24:00":
                        end_time = datetime.strptime("23:59", "%H:%M").time()
                    else:
                        end_time = datetime.strptime(habit["end_time"], "%H:%M").time()

                    if start_time <= current_time.time() <= end_time:
                        last_reminder = habit.get("last_reminder")

                        if last_reminder is None:
                            habit["last_reminder"] = current_time
                            self.show_notification(habit)
                            self.parent.save_habits()
                        else:
                            if isinstance(last_reminder, str):
                                last_reminder = datetime.fromisoformat(last_reminder)

                            if (current_time - last_reminder).total_seconds() >= habit[
                                "interval"
                            ] * 60:
                                self.show_notification(habit)
                                habit["last_reminder"] = current_time
                                self.parent.save_habits()

                except ValueError as e:
                    print(f"Ошибка обработки привычки: {e}")
                    continue

            time.sleep(30)

    def show_notification(self, habit):
        try:
            if self.notification_sound:
                self.notification_sound.play(loops=-1)
            else:
                self.sound_player.play_notification()

            notification = tk.Toplevel(self.parent)
            notification.title("Напоминание")
            notification.geometry("400x200")
            notification.attributes("-topmost", True)

            screen_width = notification.winfo_screenwidth()
            screen_height = notification.winfo_screenheight()
            x = (screen_width - 400) // 2
            y = (screen_height - 200) // 2
            notification.geometry(f"400x200+{x}+{y}")

            main_frame = ttk.Frame(notification, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(main_frame, text="⏰", font=("Segoe UI", 36)).pack(pady=(0, 10))

            ttk.Label(
                main_frame, text=f"Время для привычки:", font=("Segoe UI", 12)
            ).pack()
            ttk.Label(
                main_frame,
                text=habit["name"],
                font=("Segoe UI", 14, "bold"),
                wraplength=300,
            ).pack(pady=(5, 15))

            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill=tk.X, pady=(10, 0))

            def close_notification():
                if self.notification_sound:
                    self.notification_sound.stop()
                notification.destroy()

            def snooze():
                if self.notification_sound:
                    self.notification_sound.stop()
                habit["last_reminder"] = datetime.now() - timedelta(
                    minutes=habit["interval"] - 5
                )
                self.parent.save_habits()
                notification.destroy()

            ttk.Button(
                btn_frame,
                text="Отложить на 5 минут",
                style="Secondary.TButton",
                command=snooze,
            ).pack(side=tk.LEFT, padx=(0, 10))

            ttk.Button(
                btn_frame, text="OK", style="Accent.TButton", command=close_notification
            ).pack(side=tk.LEFT)

            def auto_close():
                if self.notification_sound:
                    self.notification_sound.stop()
                notification.destroy()

            notification.protocol("WM_DELETE_WINDOW", close_notification)
            notification.after(30000, auto_close)

        except Exception as e:
            print(f"Ошибка при показе уведомления: {e}")
            if self.notification_sound:
                self.notification_sound.stop()

    def __del__(self):
        """Очистка ресурсов при удалении объекта"""
        try:
            if self.notification_sound:
                self.notification_sound.stop()
            if mixer.get_init():
                mixer.quit()
        except:
            pass
