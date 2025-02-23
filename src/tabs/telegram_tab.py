import asyncio
import json
import os
import random
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import DialogFilter


class TelegramTab(ttk.Frame):
    def setup_styles(self):
        style = ttk.Style()
        style.configure("Config.TFrame", padding=15)
        style.configure("Status.TLabel", padding=5)
        style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        style.configure("Status.TLabelframe", padding=10)

    def load_credentials(self):
        try:
            if os.path.exists("telegram_config.json"):
                with open("telegram_config.json", "r") as f:
                    config = json.load(f)
                    self.api_id_entry.insert(0, config.get("api_id", ""))
                    self.api_hash_entry.insert(0, config.get("api_hash", ""))
                    self.phone_entry.insert(0, config.get("phone", ""))
        except Exception as e:
            self.log(f"Ошибка загрузки настроек: {str(e)}")

    def save_credentials(self):
        config = {
            "api_id": self.api_id_entry.get(),
            "api_hash": self.api_hash_entry.get(),
            "phone": self.phone_entry.get(),
        }
        try:
            with open("telegram_config.json", "w") as f:
                json.dump(config, f)
            messagebox.showinfo("Успех", "Настройки сохранены")
        except Exception as e:
            self.log(f"Ошибка сохранения настроек: {str(e)}")
            messagebox.showerror("Ошибка", "Не удалось сохранить настройки")

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_status(self, status):
        self.status_label.config(text=status)

    def update_ui_state(self, is_running):
        state = tk.DISABLED if is_running else tk.NORMAL
        reverse_state = tk.NORMAL if is_running else tk.DISABLED

        self.api_id_entry.config(state=state)
        self.api_hash_entry.config(state=state)
        self.phone_entry.config(state=state)
        self.start_button.config(state=state)
        self.stop_button.config(state=reverse_state)

    def start_telegram_client(self):
        if not all(
            [self.api_id_entry.get(), self.api_hash_entry.get(), self.phone_entry.get()]
        ):
            messagebox.showerror("Ошибка", "Заполните все поля")
            return

        self.is_running = True
        self.update_ui_state(True)
        self.update_status("Запускается...")

        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.telegram_worker())

        thread = threading.Thread(target=run_async_loop, daemon=True)
        thread.start()

    def stop_telegram_client(self):
        self.is_running = False
        self.update_status("Останавливается...")
        self.log("Останавливаем клиент...")

    async def mark_messages_as_read(self):
        """
        Метод для отметки сообщений как прочитанных
        Здесь должна быть реализация из исходного кода
        """
        try:
            folder_chats = await self.get_folder_chats()
            marked_count = 0

            async for dialog in self.client.iter_dialogs():
                if not self.is_running:
                    break

                try:
                    chat_ids = self.get_chat_ids(dialog.entity)
                    in_folder = False

                    for chats in folder_chats.values():
                        if any(chat_id in chats for chat_id in chat_ids):
                            in_folder = True
                            break

                    if in_folder and dialog.unread_count > 0:
                        await self.mark_dialog_read(dialog)
                        marked_count += 1
                        self.log(f"Отмечено как прочитанное: {dialog.name}")
                        await asyncio.sleep(0.5)

                except Exception as e:
                    self.log(f"Ошибка обработки диалога {dialog.name}: {str(e)}")
                    continue

            self.log(f"Отмечено {marked_count} чатов как прочитанные")

        except Exception as e:
            self.log(f"Ошибка в mark_messages_as_read: {str(e)}")

    def get_chat_ids(self, entity):
        chat_ids = []
        try:
            chat_id = entity.id
            if hasattr(entity, "forum") and entity.forum:
                chat_ids.append(chat_id)
                if not str(chat_id).startswith("-100"):
                    chat_ids.append(int(f"-100{chat_id}"))
                if str(chat_id).startswith("-100"):
                    chat_ids.append(int(str(chat_id)[4:]))
            else:
                chat_ids.append(chat_id)
        except:
            pass
        return chat_ids

    async def get_folder_chats(self):
        folders = {}
        try:
            dialog_filters = await self.client(GetDialogFiltersRequest())
            filters = (
                dialog_filters.filters
                if hasattr(dialog_filters, "filters")
                else dialog_filters
            )

            for folder in filters:
                if isinstance(folder, DialogFilter) and hasattr(folder, "title"):
                    folder_chats = set()

                    if hasattr(folder, "pinned_peers"):
                        for peer in folder.pinned_peers:
                            if hasattr(peer, "channel_id"):
                                folder_chats.add(peer.channel_id)
                            elif hasattr(peer, "chat_id"):
                                folder_chats.add(peer.chat_id)

                    if hasattr(folder, "include_peers"):
                        for peer in folder.include_peers:
                            if hasattr(peer, "channel_id"):
                                folder_chats.add(peer.channel_id)
                            elif hasattr(peer, "chat_id"):
                                folder_chats.add(peer.chat_id)

                    folders[folder.title] = folder_chats

        except Exception as e:
            self.log(f"Ошибка получения папок: {str(e)}")

        return folders

    async def mark_dialog_read(self, dialog):
        try:
            await self.client.send_read_acknowledge(
                dialog.entity,
                max_id=dialog.message.id if dialog.message else 0,
                clear_mentions=True,
            )
            self.log(f"Чат {dialog.name} отмечен как прочитанный")
        except Exception as e:
            self.log(f"Ошибка отметки чата {dialog.name}: {str(e)}")

    def __init__(self, parent):
        super().__init__(parent)
        self.client = None
        self.is_running = False
        self.auth_dialog = None
        self.setup_styles()
        self.setup_ui()
        self.load_credentials()
        self.after(random.randint(3000, 6000), self.check_and_start)

    def check_and_start(self):
        if all(
            [self.api_id_entry.get(), self.api_hash_entry.get(), self.phone_entry.get()]
        ):
            self.start_telegram_client()
        else:
            self.log("Автозапуск пропущен - не все данные заполнены")

    def create_auth_dialog(self, message):
        """Создает диалоговое окно для ввода кода подтверждения"""
        dialog = tk.Toplevel(self)
        dialog.title("Подтверждение Telegram")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"+{x}+{y}")

        ttk.Label(dialog, text=message, wraplength=250, justify="center").pack(pady=10)

        code_var = tk.StringVar()
        code_entry = ttk.Entry(dialog, textvariable=code_var, show="*")
        code_entry.pack(pady=10)
        code_entry.focus()

        def toggle_code_visibility():
            code_entry.config(show="" if code_entry.cget("show") else "*")

        ttk.Checkbutton(
            dialog, text="Показать код", command=toggle_code_visibility
        ).pack()

        result = {"code": None}

        def submit():
            result["code"] = code_var.get()
            dialog.destroy()

        def on_enter(event):
            submit()

        code_entry.bind("<Return>", on_enter)

        ttk.Button(
            dialog, text="Подтвердить", command=submit, style="Accent.TButton"
        ).pack(pady=10)

        dialog.wait_window()
        return result["code"]

    def setup_ui(self):
        main_container = ttk.Frame(self, style="Config.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header_frame, text="Telegram Интеграция", style="Header.TLabel").pack(
            side=tk.LEFT
        )

        config_frame = ttk.LabelFrame(main_container, text="Настройки", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(config_frame, text="API ID:").pack(anchor=tk.W)
        self.api_id_entry = ttk.Entry(config_frame, show="*")
        self.api_id_entry.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(config_frame, text="API Hash:").pack(anchor=tk.W)
        self.api_hash_entry = ttk.Entry(config_frame, show="*")
        self.api_hash_entry.pack(fill=tk.X, pady=(0, 10))

        self.show_api_var = tk.BooleanVar()
        ttk.Checkbutton(
            config_frame,
            text="Показать API данные",
            variable=self.show_api_var,
            command=self.toggle_api_visibility,
        ).pack(anchor=tk.W)

        ttk.Label(config_frame, text="Номер телефона:").pack(anchor=tk.W)
        self.phone_entry = ttk.Entry(config_frame)
        self.phone_entry.pack(fill=tk.X, pady=(0, 10))

        control_frame = ttk.Frame(config_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))

        self.start_button = ttk.Button(
            control_frame,
            text="Запустить",
            command=self.start_telegram_client,
            style="Accent.TButton",
        )
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(
            control_frame,
            text="Остановить",
            command=self.stop_telegram_client,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame, text="Сохранить настройки", command=self.save_credentials
        ).pack(side=tk.LEFT, padx=5)

        status_frame = ttk.LabelFrame(main_container, text="Статус", padding=10)
        status_frame.pack(fill=tk.X)

        self.status_label = ttk.Label(
            status_frame, text="Не запущено", style="Status.TLabel"
        )
        self.status_label.pack(fill=tk.X)

        log_frame = ttk.LabelFrame(main_container, text="Лог", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        self.log_text = tk.Text(
            log_frame, height=10, wrap=tk.WORD, font=("Consolas", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def toggle_api_visibility(self):
        """Переключает видимость API данных"""
        show = "" if self.show_api_var.get() else "*"
        self.api_id_entry.config(show=show)
        self.api_hash_entry.config(show=show)

    async def telegram_worker(self):
        try:
            self.client = TelegramClient(
                "session_name",
                self.api_id_entry.get(),
                self.api_hash_entry.get(),
                system_version="4.16.30-vxCUSTOM",
                device_model="Linux x86_64",
                app_version="3.0.0",
            )

            async def code_callback():
                return self.create_auth_dialog(
                    "Пожалуйста, введите код подтверждения,\n"
                    "отправленный в Telegram:"
                )

            async def password_callback():
                return self.create_auth_dialog(
                    "Пожалуйста, введите пароль\n" "двухфакторной аутентификации:"
                )

            await self.client.start(
                phone=self.phone_entry.get(),
                code_callback=code_callback,
                password=password_callback,
            )

            self.log("Клиент Telegram запущен")
            self.update_status("Работает")

            while self.is_running:
                try:
                    await self.mark_messages_as_read()
                    await asyncio.sleep(60)
                except Exception as e:
                    self.log(f"Ошибка в основном цикле: {str(e)}")
                    await asyncio.sleep(60)

        except Exception as e:
            self.log(f"Критическая ошибка: {str(e)}")
            self.update_status("Ошибка")
        finally:
            if self.client:
                await self.client.disconnect()
            self.is_running = False
            self.update_ui_state(False)
