import json
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
from typing import Dict, List, Optional


class CalorieStorage:
    """
    Хранилище для базы продуктов и дневных записей калорий.

    Структура данных:
    - products_db: база продуктов с калориями и опциональными БЖУ
    - daily_entries: записи по дням с разделением на приемы пищи
    """

    def __init__(self):
        self._products_db: Dict[str, dict] = {}
        self._daily_entries: Dict[str, Dict[str, List[dict]]] = {}
        self._modified: bool = False
        self._load()

    def add_product_to_db(
        self,
        name: str,
        calories: int,
        protein: Optional[int] = None,
        fat: Optional[int] = None,
        carbs: Optional[int] = None,
    ) -> None:
        """Добавляет продукт в базу"""
        self._products_db[name] = {
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
        }
        self._modified = True

    def remove_product_from_db(self, name: str) -> None:
        """Удаляет продукт из базы"""
        if name in self._products_db:
            del self._products_db[name]
            self._modified = True

    def get_all_products(self) -> Dict[str, dict]:
        """Возвращает всю базу продуктов"""
        return self._products_db.copy()

    def add_meal_entry(
        self, date: str, meal_type: str, product_name: str, portion: float = 1.0
    ) -> None:
        """
        Добавляет запись о приеме пищи.

        Args:
            date: дата в формате YYYY-MM-DD
            meal_type: тип приема пищи (breakfast, lunch, dinner, snack)
            product_name: название продукта из базы
            portion: размер порции (множитель, по умолчанию 1.0)
        """
        if date not in self._daily_entries:
            self._daily_entries[date] = {
                "breakfast": [],
                "lunch": [],
                "dinner": [],
                "snack": [],
            }

        if product_name not in self._products_db:
            return

        product = self._products_db[product_name]
        current_time = time.strftime("%H:%M")

        entry = {
            "product": product_name,
            "portion": portion,
            "calories": int(product["calories"] * portion),
            "protein": int(product["protein"] * portion) if product["protein"] else None,
            "fat": int(product["fat"] * portion) if product["fat"] else None,
            "carbs": int(product["carbs"] * portion) if product["carbs"] else None,
            "time": current_time,
        }

        self._daily_entries[date][meal_type].append(entry)
        self._modified = True

    def remove_meal_entry(self, date: str, meal_type: str, index: int) -> None:
        """Удаляет запись о приеме пищи"""
        if (
            date in self._daily_entries
            and meal_type in self._daily_entries[date]
            and 0 <= index < len(self._daily_entries[date][meal_type])
        ):
            del self._daily_entries[date][meal_type][index]
            self._modified = True

    def get_day_data(self, date: str) -> Dict[str, List[dict]]:
        """Возвращает все записи за день"""
        return self._daily_entries.get(
            date, {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
        )

    def get_day_total_calories(self, date: str) -> int:
        """Подсчитывает общее количество калорий за день"""
        day_data = self.get_day_data(date)
        total = 0
        for meal_entries in day_data.values():
            total += sum(entry["calories"] for entry in meal_entries)
        return total

    def get_meal_total_calories(self, date: str, meal_type: str) -> int:
        """Подсчитывает калории для конкретного приема пищи"""
        day_data = self.get_day_data(date)
        return sum(entry["calories"] for entry in day_data.get(meal_type, []))

    def save(self) -> None:
        """Сохраняет данные в JSON файл"""
        if not self._modified:
            return

        data = {"products": self._products_db, "entries": self._daily_entries}

        try:
            with open("calories.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._modified = False
        except Exception as e:
            print(f"Ошибка сохранения калорий: {e}")

    def _load(self) -> None:
        """Загружает данные из JSON файла"""
        try:
            with open("calories.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self._products_db = data.get("products", {})
                self._daily_entries = data.get("entries", {})
        except FileNotFoundError:
            self._products_db = {}
            self._daily_entries = {}
        except Exception as e:
            print(f"Ошибка загрузки калорий: {e}")
            self._products_db = {}
            self._daily_entries = {}


class CalorieTrackerTab(ttk.Frame):
    """
    Вкладка для отслеживания калорий с базой продуктов и приемами пищи.
    """

    def __init__(self, parent, settings_tab=None):
        super().__init__(parent)
        self.storage = CalorieStorage()
        self.settings_tab = settings_tab
        self.current_date = time.strftime("%Y-%m-%d")
        self.setup_ui()

    def get_target_calories(self) -> int:
        """Получает целевое количество калорий из настроек"""
        if self.settings_tab and hasattr(self.settings_tab, "get_target_calories"):
            return self.settings_tab.get_target_calories()
        return 2000

    def setup_ui(self):
        """Создает UI компоненты"""
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self._create_date_panel()
        self._create_stats_panel()
        self._create_meals_panel()
        self._create_products_panel()

        self._update_all_displays()

    def _create_date_panel(self):
        """Панель навигации по дням"""
        date_frame = ttk.Frame(self.main_container)
        date_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(date_frame, text="Дата:", font=("Arial", 12)).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        self.date_var = tk.StringVar(value=self.current_date)
        date_entry = ttk.Entry(
            date_frame,
            textvariable=self.date_var,
            state="readonly",
            width=12,
            font=("Arial", 12),
        )
        date_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            date_frame, text="←", command=self._prev_day, width=3, takefocus=0
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            date_frame, text="Сегодня", command=self._goto_today, takefocus=0
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            date_frame, text="→", command=self._next_day, width=3, takefocus=0
        ).pack(side=tk.LEFT, padx=2)

    def _create_stats_panel(self):
        """Панель статистики с прогресс-баром"""
        stats_frame = ttk.LabelFrame(
            self.main_container, text="Статистика за день", padding=10
        )
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        progress_container = ttk.Frame(stats_frame)
        progress_container.pack(fill=tk.X, pady=(0, 10))

        self.calories_label = ttk.Label(
            progress_container, text="0 / 2000 ккал (0%)", font=("Arial", 14, "bold")
        )
        self.calories_label.pack()

        self.progress_bar = ttk.Progressbar(
            progress_container, length=400, mode="determinate"
        )
        self.progress_bar.pack(pady=(5, 0))

        self.remaining_label = ttk.Label(
            stats_frame, text="Осталось: 2000 ккал", font=("Arial", 11)
        )
        self.remaining_label.pack()

    def _create_meals_panel(self):
        """Панель приемов пищи"""
        meals_frame = ttk.LabelFrame(
            self.main_container, text="Приемы пищи", padding=10
        )
        meals_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.meal_frames = {}
        meal_types = [
            ("breakfast", "🌅 Завтрак"),
            ("lunch", "☀️ Обед"),
            ("dinner", "🌙 Ужин"),
            ("snack", "🍎 Перекус"),
        ]

        for meal_type, label in meal_types:
            self._create_meal_section(meals_frame, meal_type, label)

    def _create_meal_section(
        self, parent: ttk.Frame, meal_type: str, label: str
    ) -> None:
        """Создает секцию для одного приема пищи"""
        section_frame = ttk.LabelFrame(parent, text=label, padding=5)
        section_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        header_frame = ttk.Frame(section_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        calories_label = ttk.Label(header_frame, text="0 ккал", font=("Arial", 10))
        calories_label.pack(side=tk.LEFT)

        add_button = ttk.Button(
            header_frame,
            text="+ Добавить",
            command=lambda: self._show_add_product_dialog(meal_type),
            takefocus=0,
        )
        add_button.pack(side=tk.RIGHT)

        tree_frame = ttk.Frame(section_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("product", "portion", "calories", "actions")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=3)

        tree.heading("product", text="Продукт")
        tree.heading("portion", text="Порция")
        tree.heading("calories", text="Ккал")
        tree.heading("actions", text="")

        tree.column("product", width=150)
        tree.column("portion", width=80, anchor="center")
        tree.column("calories", width=80, anchor="center")
        tree.column("actions", width=40, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree.bind("<Button-1>", lambda e: self._handle_meal_click(e, meal_type, tree))

        self.meal_frames[meal_type] = {
            "tree": tree,
            "calories_label": calories_label,
        }

    def _create_products_panel(self):
        """Панель управления базой продуктов"""
        products_frame = ttk.LabelFrame(
            self.main_container, text="База продуктов", padding=10
        )
        products_frame.pack(fill=tk.BOTH, expand=True)

        controls_frame = ttk.Frame(products_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            controls_frame,
            text="+ Добавить продукт",
            command=self._show_add_product_to_db_dialog,
            style="Accent.TButton",
            takefocus=0,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            controls_frame,
            text="Удалить выбранный",
            command=self._remove_selected_product,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=2)

        tree_frame = ttk.Frame(products_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "calories", "protein", "fat", "carbs")
        self.products_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=8
        )

        self.products_tree.heading("name", text="Название")
        self.products_tree.heading("calories", text="Ккал/100г")
        self.products_tree.heading("protein", text="Белки")
        self.products_tree.heading("fat", text="Жиры")
        self.products_tree.heading("carbs", text="Углев.")

        self.products_tree.column("name", width=200)
        self.products_tree.column("calories", width=80, anchor="center")
        self.products_tree.column("protein", width=60, anchor="center")
        self.products_tree.column("fat", width=60, anchor="center")
        self.products_tree.column("carbs", width=60, anchor="center")

        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.products_tree.yview
        )
        self.products_tree.configure(yscrollcommand=scrollbar.set)

        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _show_add_product_to_db_dialog(self):
        """Диалог добавления продукта в базу"""
        dialog = tk.Toplevel(self)
        dialog.title("Добавить продукт в базу")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()

        fields_frame = ttk.Frame(dialog, padding=20)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(fields_frame, text="Название продукта:", font=("Arial", 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        name_entry = ttk.Entry(fields_frame, width=30)
        name_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        name_entry.focus()

        ttk.Label(fields_frame, text="Калории (на 100г):", font=("Arial", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        calories_entry = ttk.Entry(fields_frame, width=30)
        calories_entry.grid(row=1, column=1, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="Белки (опционально):", font=("Arial", 10)).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        protein_entry = ttk.Entry(fields_frame, width=30)
        protein_entry.grid(row=2, column=1, pady=5, padx=(10, 0))

        ttk.Label(fields_frame, text="Жиры (опционально):", font=("Arial", 10)).grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        fat_entry = ttk.Entry(fields_frame, width=30)
        fat_entry.grid(row=3, column=1, pady=5, padx=(10, 0))

        ttk.Label(
            fields_frame, text="Углеводы (опционально):", font=("Arial", 10)
        ).grid(row=4, column=0, sticky=tk.W, pady=5)
        carbs_entry = ttk.Entry(fields_frame, width=30)
        carbs_entry.grid(row=4, column=1, pady=5, padx=(10, 0))

        def save_product():
            name = name_entry.get().strip()
            calories_str = calories_entry.get().strip()

            if not name or not calories_str:
                messagebox.showwarning(
                    "Ошибка", "Название и калории обязательны для заполнения"
                )
                return

            try:
                calories = int(calories_str)
                protein = (
                    int(protein_entry.get()) if protein_entry.get().strip() else None
                )
                fat = int(fat_entry.get()) if fat_entry.get().strip() else None
                carbs = int(carbs_entry.get()) if carbs_entry.get().strip() else None

                self.storage.add_product_to_db(name, calories, protein, fat, carbs)
                self.storage.save()
                self._update_products_display()
                dialog.destroy()

            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректные числовые значения")

        buttons_frame = ttk.Frame(fields_frame)
        buttons_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            buttons_frame, text="Сохранить", command=save_product, width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame, text="Отмена", command=dialog.destroy, width=15
        ).pack(side=tk.LEFT, padx=5)

        dialog.bind("<Return>", lambda e: save_product())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _show_add_product_dialog(self, meal_type: str):
        """Диалог добавления продукта к приему пищи"""
        products = self.storage.get_all_products()

        if not products:
            messagebox.showinfo(
                "База продуктов пуста",
                "Сначала добавьте продукты в базу в нижней части экрана",
            )
            return

        dialog = tk.Toplevel(self)
        dialog.title("Добавить продукт к приему пищи")
        dialog.geometry("350x200")
        dialog.transient(self)
        dialog.grab_set()

        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(content_frame, text="Выберите продукт:", font=("Arial", 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        product_var = tk.StringVar()
        product_combo = ttk.Combobox(
            content_frame,
            textvariable=product_var,
            values=sorted(products.keys()),
            state="readonly",
            width=25,
        )
        product_combo.grid(row=0, column=1, pady=5, padx=(10, 0))

        if products:
            product_combo.current(0)

        ttk.Label(content_frame, text="Порция (множитель):", font=("Arial", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        portion_entry = ttk.Entry(content_frame, width=27)
        portion_entry.insert(0, "1.0")
        portion_entry.grid(row=1, column=1, pady=5, padx=(10, 0))

        def add_product():
            product_name = product_var.get()
            portion_str = portion_entry.get().strip()

            if not product_name:
                messagebox.showwarning("Ошибка", "Выберите продукт")
                return

            try:
                portion = float(portion_str)
                if portion <= 0:
                    raise ValueError()

                self.storage.add_meal_entry(
                    self.current_date, meal_type, product_name, portion
                )
                self.storage.save()
                self._update_meal_display(meal_type)
                self._update_stats()
                dialog.destroy()

            except ValueError:
                messagebox.showwarning(
                    "Ошибка", "Введите корректное положительное число для порции"
                )

        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            buttons_frame, text="Добавить", command=add_product, width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame, text="Отмена", command=dialog.destroy, width=15
        ).pack(side=tk.LEFT, padx=5)

        dialog.bind("<Return>", lambda e: add_product())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _remove_selected_product(self):
        """Удаляет выбранный продукт из базы"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showinfo("Ошибка", "Выберите продукт для удаления")
            return

        item = selection[0]
        product_name = self.products_tree.item(item)["values"][0]

        if messagebox.askyesno(
            "Подтверждение", f'Удалить продукт "{product_name}" из базы?'
        ):
            self.storage.remove_product_from_db(product_name)
            self.storage.save()
            self._update_products_display()

    def _handle_meal_click(self, event, meal_type: str, tree: ttk.Treeview):
        """Обрабатывает клики по записям приемов пищи"""
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        item = tree.identify_row(event.y)
        col = tree.identify_column(event.x)

        if col == "#4" and item:
            index = tree.index(item)
            if messagebox.askyesno("Подтверждение", "Удалить эту запись?"):
                self.storage.remove_meal_entry(self.current_date, meal_type, index)
                self.storage.save()
                self._update_meal_display(meal_type)
                self._update_stats()

    def _prev_day(self):
        """Переход на предыдущий день"""
        current = datetime.strptime(self.current_date, "%Y-%m-%d")
        self.current_date = (current - timedelta(days=1)).strftime("%Y-%m-%d")
        self.date_var.set(self.current_date)
        self._update_all_displays()

    def _next_day(self):
        """Переход на следующий день"""
        current = datetime.strptime(self.current_date, "%Y-%m-%d")
        self.current_date = (current + timedelta(days=1)).strftime("%Y-%m-%d")
        self.date_var.set(self.current_date)
        self._update_all_displays()

    def _goto_today(self):
        """Переход на сегодняшний день"""
        self.current_date = time.strftime("%Y-%m-%d")
        self.date_var.set(self.current_date)
        self._update_all_displays()

    def _update_all_displays(self):
        """Обновляет все отображения"""
        self._update_stats()
        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            self._update_meal_display(meal_type)
        self._update_products_display()

    def _update_stats(self):
        """Обновляет панель статистики"""
        total_calories = self.storage.get_day_total_calories(self.current_date)
        target_calories = self.get_target_calories()

        percentage = min(100, int((total_calories / target_calories) * 100))
        remaining = max(0, target_calories - total_calories)

        self.calories_label.config(
            text=f"{total_calories} / {target_calories} ккал ({percentage}%)"
        )
        self.progress_bar["value"] = percentage

        if remaining > 0:
            self.remaining_label.config(
                text=f"Осталось: {remaining} ккал", foreground=""
            )
        else:
            excess = total_calories - target_calories
            self.remaining_label.config(
                text=f"Превышение: {excess} ккал", foreground="red"
            )

    def _update_meal_display(self, meal_type: str):
        """Обновляет отображение для конкретного приема пищи"""
        if meal_type not in self.meal_frames:
            return

        tree = self.meal_frames[meal_type]["tree"]
        calories_label = self.meal_frames[meal_type]["calories_label"]

        for item in tree.get_children():
            tree.delete(item)

        day_data = self.storage.get_day_data(self.current_date)
        entries = day_data.get(meal_type, [])

        for entry in entries:
            portion_text = f"{entry['portion']}x"
            tree.insert(
                "",
                "end",
                values=(
                    entry["product"],
                    portion_text,
                    f"{entry['calories']} ккал",
                    "✕",
                ),
            )

        total_calories = self.storage.get_meal_total_calories(
            self.current_date, meal_type
        )
        calories_label.config(text=f"{total_calories} ккал")

    def _update_products_display(self):
        """Обновляет отображение базы продуктов"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        products = self.storage.get_all_products()

        for name, data in sorted(products.items()):
            protein = data.get("protein") or "-"
            fat = data.get("fat") or "-"
            carbs = data.get("carbs") or "-"

            self.products_tree.insert(
                "", "end", values=(name, data["calories"], protein, fat, carbs)
            )
