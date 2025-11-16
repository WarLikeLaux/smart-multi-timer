"""
Диалоговые окна для управления калориями.

Ответственность:
- ProductDatabaseDialog: добавление/редактирование продуктов в базе
- MealProductDialog: выбор продукта для приема пищи
- CSVImportDialog: массовый импорт через CSV
- QuickProductDialog: быстрое создание продукта из приема пищи
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from tabs.calorie_storage import CalorieStorage


class ProductDatabaseDialog:
    """Диалог добавления/редактирования продукта в базе"""

    def __init__(
        self,
        parent: tk.Widget,
        storage: CalorieStorage,
        on_save: Callable[[], None],
        edit_mode: bool = False,
        product_name: str = "",
    ):
        self.parent = parent
        self.storage = storage
        self.on_save = on_save
        self.edit_mode = edit_mode
        self.product_name = product_name

        self.dialog = tk.Toplevel(parent)
        self._setup_window()
        self._create_ui()

    def _setup_window(self) -> None:
        """Настраивает окно диалога"""
        title = "Редактировать продукт" if self.edit_mode else "Добавить продукт в базу"
        self.dialog.title(title)
        self.dialog.geometry("500x450")

        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 450) // 2
        self.dialog.geometry(f"500x450+{x}+{y}")

        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

    def _create_ui(self) -> None:
        """Создает UI компоненты"""
        fields_frame = ttk.Frame(self.dialog, padding=20)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        product_data = self._get_product_data()

        self.name_entry = self._create_field(
            fields_frame, 0, "Название продукта:",
            product_data.get("name", self.product_name if self.edit_mode else "")
        )
        self.name_entry.focus()

        self.calories_entry = self._create_field(
            fields_frame, 1, "Калории на 100г:",
            product_data.get("calories", "")
        )
        self._create_hint(fields_frame, 2, "(оставьте пустым если знаете ккал на порцию)")

        self.serving_entry = self._create_field(
            fields_frame, 3, "Размер порции г:",
            product_data.get("serving_size", "")
        )

        self.cal_serving_entry = self._create_field(
            fields_frame, 4, "Калории на порцию:",
            product_data.get("calories_per_serving", "")
        )
        self._create_hint(fields_frame, 5, "(автоматически вычислит ккал/100г)")

        ttk.Separator(fields_frame, orient="horizontal").grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=10
        )

        self.protein_entry = self._create_field(
            fields_frame, 7, "Белки г (опционально):",
            product_data.get("protein", "")
        )

        self.fat_entry = self._create_field(
            fields_frame, 8, "Жиры г (опционально):",
            product_data.get("fat", "")
        )

        self.carbs_entry = self._create_field(
            fields_frame, 9, "Углеводы г (опционально):",
            product_data.get("carbs", "")
        )

        self._create_buttons(fields_frame)
        self._setup_bindings()

    def _get_product_data(self) -> dict:
        """Получает данные продукта для редактирования"""
        if not self.edit_mode or not self.product_name:
            return {}

        products = self.storage.get_all_products()
        product = products.get(self.product_name, {})

        return {
            "name": self.product_name,
            "calories": str(product.get("calories", "")) if product.get("calories") else "",
            "serving_size": str(product.get("serving_size", "")) if product.get("serving_size") else "",
            "calories_per_serving": str(product.get("calories_per_serving", "")) if product.get("calories_per_serving") else "",
            "protein": str(product.get("protein", "")) if product.get("protein") else "",
            "fat": str(product.get("fat", "")) if product.get("fat") else "",
            "carbs": str(product.get("carbs", "")) if product.get("carbs") else "",
        }

    def _create_field(
        self, parent: ttk.Frame, row: int, label: str, value: str
    ) -> ttk.Entry:
        """Создает поле ввода с меткой"""
        ttk.Label(parent, text=label, font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        entry = ttk.Entry(parent, width=35)
        entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        if value:
            entry.insert(0, value)
        return entry

    def _create_hint(self, parent: ttk.Frame, row: int, text: str) -> None:
        """Создает подсказку"""
        ttk.Label(
            parent, text=text, font=("Arial", 8), foreground="gray"
        ).grid(row=row, column=1, sticky=tk.W, padx=(10, 0))

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Создает кнопки управления"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.grid(row=10, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            buttons_frame, text="Сохранить", command=self._save, width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame, text="Отмена", command=self.dialog.destroy, width=15
        ).pack(side=tk.LEFT, padx=5)

    def _setup_bindings(self) -> None:
        """Настраивает привязки клавиш"""
        self.dialog.bind("<Return>", lambda e: self._save())
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())

    def _save(self) -> None:
        """Сохраняет продукт в базу"""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Название обязательно для заполнения")
            return

        calories_str = self.calories_entry.get().strip()
        serving_str = self.serving_entry.get().strip()
        cal_serving_str = self.cal_serving_entry.get().strip()

        if not calories_str and not (cal_serving_str and serving_str):
            messagebox.showwarning(
                "Ошибка",
                "Укажите калории на 100г ИЛИ калории на порцию + размер порции"
            )
            return

        try:
            calories = int(calories_str) if calories_str else 0
            protein = int(self.protein_entry.get()) if self.protein_entry.get().strip() else None
            fat = int(self.fat_entry.get()) if self.fat_entry.get().strip() else None
            carbs = int(self.carbs_entry.get()) if self.carbs_entry.get().strip() else None
            serving = int(serving_str) if serving_str else None
            cal_serving = int(cal_serving_str) if cal_serving_str else None

            if self.edit_mode:
                self.storage.update_product_in_db(
                    self.product_name, name, calories, protein, fat, carbs, serving, cal_serving
                )
            else:
                self.storage.add_product_to_db(
                    name, calories, protein, fat, carbs, serving, cal_serving
                )

            self.storage.save()
            self.on_save()
            self.dialog.destroy()

        except ValueError:
            messagebox.showwarning("Ошибка", "Введите корректные числовые значения")


class CSVImportDialog:
    """Диалог массового импорта продуктов через CSV"""

    def __init__(
        self,
        parent: tk.Widget,
        storage: CalorieStorage,
        on_import: Callable[[], None],
    ):
        self.parent = parent
        self.storage = storage
        self.on_import = on_import

        self.dialog = tk.Toplevel(parent)
        self._setup_window()
        self._create_ui()

    def _setup_window(self) -> None:
        """Настраивает окно диалога"""
        self.dialog.title("Массовый импорт продуктов")
        self.dialog.geometry("700x500")

        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 500) // 2
        self.dialog.geometry(f"700x500+{x}+{y}")

        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

    def _create_ui(self) -> None:
        """Создает UI компоненты"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="Импорт продуктов из CSV",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text="Формат: название;калории;белки;жиры;углеводы (по одному на строку)",
            font=("Arial", 9)
        ).pack(pady=(0, 5))

        ttk.Label(
            main_frame,
            text="Пример: Яблоко;52;0;0;14",
            font=("Arial", 9),
            foreground="gray"
        ).pack(pady=(0, 10))

        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        text_scroll = ttk.Scrollbar(text_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(
            text_frame,
            height=15,
            font=("Courier New", 10),
            yscrollcommand=text_scroll.set
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.config(command=self.text_widget.yview)
        self.text_widget.focus()

        self._create_buttons(main_frame)
        self._setup_bindings()

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Создает кнопки управления"""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack()

        ttk.Button(
            buttons_frame, text="Импортировать", command=self._import_csv, width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame, text="Отмена", command=self.dialog.destroy, width=15
        ).pack(side=tk.LEFT, padx=5)

    def _setup_bindings(self) -> None:
        """Настраивает привязки клавиш"""
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())

    def _import_csv(self) -> None:
        """Импортирует продукты из CSV"""
        content = self.text_widget.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Ошибка", "Введите данные для импорта")
            return

        lines = content.split("\n")
        success_count = 0
        error_lines = []

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split(";")
            if len(parts) < 2:
                error_lines.append(f"Строка {i}: недостаточно данных")
                continue

            try:
                name = parts[0].strip()
                calories = int(parts[1].strip())
                protein = int(parts[2].strip()) if len(parts) > 2 and parts[2].strip() else None
                fat = int(parts[3].strip()) if len(parts) > 3 and parts[3].strip() else None
                carbs = int(parts[4].strip()) if len(parts) > 4 and parts[4].strip() else None

                self.storage.add_product_to_db(name, calories, protein, fat, carbs)
                success_count += 1

            except ValueError:
                error_lines.append(f"Строка {i}: некорректные числовые значения")

        self.storage.save()
        self.on_import()

        if error_lines:
            errors = "\n".join(error_lines[:10])
            if len(error_lines) > 10:
                errors += f"\n... и ещё {len(error_lines) - 10}"
            messagebox.showwarning(
                "Импорт завершён с ошибками",
                f"Импортировано: {success_count}\nОшибок: {len(error_lines)}\n\n{errors}"
            )
        else:
            messagebox.showinfo(
                "Импорт завершён",
                f"Успешно импортировано {success_count} продуктов"
            )

        self.dialog.destroy()
