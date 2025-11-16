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
    - products_db: база продуктов с калориями, БЖУ и размером порции
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
        serving_size: Optional[int] = None,
        calories_per_serving: Optional[int] = None,
    ) -> None:
        """
        Добавляет продукт в базу.

        Args:
            calories: калории на 100г (или вычисляется из calories_per_serving)
            serving_size: размер порции в граммах
            calories_per_serving: калории на порцию (опционально)
        """
        if calories_per_serving and serving_size and not calories:
            calories = int((calories_per_serving / serving_size) * 100)

        self._products_db[name] = {
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
            "serving_size": serving_size,
            "calories_per_serving": calories_per_serving,
        }
        self._modified = True

    def update_product_in_db(
        self,
        old_name: str,
        name: str,
        calories: int,
        protein: Optional[int] = None,
        fat: Optional[int] = None,
        carbs: Optional[int] = None,
        serving_size: Optional[int] = None,
        calories_per_serving: Optional[int] = None,
    ) -> None:
        """Обновляет продукт в базе и пересчитывает все связанные записи"""
        if old_name != name and old_name in self._products_db:
            del self._products_db[old_name]

        if calories_per_serving and serving_size and not calories:
            calories = int((calories_per_serving / serving_size) * 100)

        self._products_db[name] = {
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
            "serving_size": serving_size,
            "calories_per_serving": calories_per_serving,
        }
        self._modified = True

        self._recalculate_entries_for_product(old_name, name)

    def remove_product_from_db(self, name: str) -> None:
        """Удаляет продукт из базы и всех приемов пищи"""
        if name in self._products_db:
            del self._products_db[name]
            self._remove_product_from_all_meals(name)
            self._modified = True

    def _remove_product_from_all_meals(self, product_name: str) -> None:
        """Удаляет все записи с продуктом из всех дней и приемов пищи"""
        for date in self._daily_entries:
            for meal_type in self._daily_entries[date]:
                self._daily_entries[date][meal_type] = [
                    entry
                    for entry in self._daily_entries[date][meal_type]
                    if entry.get("product") != product_name
                ]
        self._modified = True

    def _recalculate_entries_for_product(
        self, old_name: str, new_name: str
    ) -> None:
        """Пересчитывает калории и БЖУ для всех записей с продуктом"""
        if new_name not in self._products_db:
            return

        product = self._products_db[new_name]

        for date in self._daily_entries:
            for meal_type in self._daily_entries[date]:
                for entry in self._daily_entries[date][meal_type]:
                    if entry.get("product") in [old_name, new_name]:
                        entry["product"] = new_name

                        amount = entry.get("amount", 1.0)
                        is_grams = entry.get("is_grams", False)

                        if is_grams:
                            multiplier = amount / 100.0
                        else:
                            multiplier = amount

                        entry["calories"] = int(product["calories"] * multiplier)
                        entry["protein"] = (
                            int(product["protein"] * multiplier)
                            if product["protein"]
                            else None
                        )
                        entry["fat"] = (
                            int(product["fat"] * multiplier)
                            if product["fat"]
                            else None
                        )
                        entry["carbs"] = (
                            int(product["carbs"] * multiplier)
                            if product["carbs"]
                            else None
                        )

        self._modified = True

    def get_all_products(self) -> Dict[str, dict]:
        """Возвращает всю базу продуктов"""
        return self._products_db.copy()

    def add_meal_entry(
        self,
        date: str,
        meal_type: str,
        product_name: str,
        amount: float = 1.0,
        is_grams: bool = False,
    ) -> None:
        """
        Добавляет запись о приеме пищи.

        Args:
            date: дата в формате YYYY-MM-DD
            meal_type: тип приема пищи (breakfast, lunch, dinner, snack)
            product_name: название продукта из базы
            amount: количество (порции или граммы)
            is_grams: True если amount в граммах, False если в порциях
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

        if is_grams:
            multiplier = amount / 100.0
        else:
            multiplier = amount

        entry = {
            "product": product_name,
            "amount": amount,
            "is_grams": is_grams,
            "calories": int(product["calories"] * multiplier),
            "protein": int(product["protein"] * multiplier)
            if product["protein"]
            else None,
            "fat": int(product["fat"] * multiplier) if product["fat"] else None,
            "carbs": int(product["carbs"] * multiplier) if product["carbs"] else None,
            "time": current_time,
        }

        self._daily_entries[date][meal_type].append(entry)
        self._modified = True

    def update_meal_entry(
        self,
        date: str,
        meal_type: str,
        index: int,
        product_name: str,
        amount: float,
        is_grams: bool,
    ) -> None:
        """Обновляет запись о приеме пищи"""
        if (
            date not in self._daily_entries
            or meal_type not in self._daily_entries[date]
            or index >= len(self._daily_entries[date][meal_type])
        ):
            return

        if product_name not in self._products_db:
            return

        product = self._products_db[product_name]

        if is_grams:
            multiplier = amount / 100.0
        else:
            multiplier = amount

        entry = self._daily_entries[date][meal_type][index]
        entry["product"] = product_name
        entry["amount"] = amount
        entry["is_grams"] = is_grams
        entry["calories"] = int(product["calories"] * multiplier)
        entry["protein"] = (
            int(product["protein"] * multiplier) if product["protein"] else None
        )
        entry["fat"] = int(product["fat"] * multiplier) if product["fat"] else None
        entry["carbs"] = (
            int(product["carbs"] * multiplier) if product["carbs"] else None
        )

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

    def get_day_total_macros(self, date: str) -> Dict[str, Optional[int]]:
        """Подсчитывает общее количество БЖУ за день"""
        day_data = self.get_day_data(date)
        totals = {"protein": 0, "fat": 0, "carbs": 0}
        has_data = {"protein": False, "fat": False, "carbs": False}

        for meal_entries in day_data.values():
            for entry in meal_entries:
                if entry.get("protein") is not None:
                    totals["protein"] += entry["protein"]
                    has_data["protein"] = True
                if entry.get("fat") is not None:
                    totals["fat"] += entry["fat"]
                    has_data["fat"] = True
                if entry.get("carbs") is not None:
                    totals["carbs"] += entry["carbs"]
                    has_data["carbs"] = True

        return {
            "protein": totals["protein"] if has_data["protein"] else None,
            "fat": totals["fat"] if has_data["fat"] else None,
            "carbs": totals["carbs"] if has_data["carbs"] else None,
        }

    def get_meal_total_calories(self, date: str, meal_type: str) -> int:
        """Подсчитывает калории для конкретного приема пищи"""
        day_data = self.get_day_data(date)
        return sum(entry["calories"] for entry in day_data.get(meal_type, []))

    def get_meal_total_macros(
        self, date: str, meal_type: str
    ) -> Dict[str, Optional[int]]:
        """Подсчитывает БЖУ для конкретного приема пищи"""
        day_data = self.get_day_data(date)
        entries = day_data.get(meal_type, [])

        totals = {"protein": 0, "fat": 0, "carbs": 0}
        has_data = {"protein": False, "fat": False, "carbs": False}

        for entry in entries:
            if entry.get("protein") is not None:
                totals["protein"] += entry["protein"]
                has_data["protein"] = True
            if entry.get("fat") is not None:
                totals["fat"] += entry["fat"]
                has_data["fat"] = True
            if entry.get("carbs") is not None:
                totals["carbs"] += entry["carbs"]
                has_data["carbs"] = True

        return {
            "protein": totals["protein"] if has_data["protein"] else None,
            "fat": totals["fat"] if has_data["fat"] else None,
            "carbs": totals["carbs"] if has_data["carbs"] else None,
        }

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
        """Создает UI компоненты с общим скроллом"""
        self.outer_canvas = tk.Canvas(self, highlightthickness=0)
        outer_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.outer_canvas.yview)

        self.main_container = ttk.Frame(self.outer_canvas)

        self.main_container.bind(
            "<Configure>", lambda e: self.outer_canvas.configure(scrollregion=self.outer_canvas.bbox("all"))
        )

        self.window_id = self.outer_canvas.create_window((0, 0), window=self.main_container, anchor="nw")
        self.outer_canvas.configure(yscrollcommand=outer_scrollbar.set)
        self.outer_canvas.bind("<Configure>", self._on_canvas_configure)

        outer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.outer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.outer_canvas.bind_all(
            "<MouseWheel>", lambda e: self.outer_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )

        content_frame = ttk.Frame(self.main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self._create_date_panel(content_frame)
        self._create_stats_panel(content_frame)
        self._create_meals_panel(content_frame)
        self._create_products_panel(content_frame)

        self._update_all_displays()

    def _on_canvas_configure(self, event):
        """Обновляет ширину окна при изменении размера canvas"""
        self.outer_canvas.itemconfig(self.window_id, width=event.width)
        self.outer_canvas.configure(scrollregion=self.outer_canvas.bbox("all"))

    def _create_date_panel(self, parent):
        """Панель навигации по дням"""
        date_frame = ttk.Frame(parent)
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

    def _create_stats_panel(self, parent):
        """Панель статистики с прогресс-баром и БЖУ"""
        stats_frame = ttk.LabelFrame(parent, text="Статистика за день", padding=10)
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

        self.macros_label = ttk.Label(stats_frame, text="", font=("Arial", 10))
        self.macros_label.pack(pady=(5, 0))

    def _create_meals_panel(self, parent):
        """Панель приемов пищи"""
        meals_frame = ttk.LabelFrame(parent, text="Приемы пищи", padding=10)
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

        stats_container = ttk.Frame(header_frame)
        stats_container.pack(side=tk.LEFT)

        calories_label = ttk.Label(stats_container, text="0 ккал", font=("Arial", 10))
        calories_label.pack(side=tk.LEFT)

        macros_label = ttk.Label(stats_container, text="", font=("Arial", 9))
        macros_label.pack(side=tk.LEFT, padx=(10, 0))

        add_button = ttk.Button(
            header_frame,
            text="+ Добавить",
            command=lambda: self._show_add_product_dialog(meal_type),
            takefocus=0,
        )
        add_button.pack(side=tk.RIGHT)

        tree_frame = ttk.Frame(section_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("product", "amount", "calories", "actions")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=3)

        tree.heading("product", text="Продукт")
        tree.heading("amount", text="Количество")
        tree.heading("calories", text="Ккал")
        tree.heading("actions", text="")

        tree.column("product", width=250)
        tree.column("amount", width=150, anchor="center")
        tree.column("calories", width=100, anchor="center")
        tree.column("actions", width=60, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree.bind("<Button-1>", lambda e: self._handle_meal_click(e, meal_type, tree))
        tree.bind(
            "<Double-Button-1>", lambda e: self._handle_meal_double_click(e, meal_type, tree)
        )

        self.meal_frames[meal_type] = {
            "tree": tree,
            "calories_label": calories_label,
            "macros_label": macros_label,
        }

    def _create_products_panel(self, parent):
        """Панель управления базой продуктов"""
        products_frame = ttk.LabelFrame(parent, text="База продуктов", padding=10)
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
            text="Изменить",
            command=self._edit_selected_product,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            controls_frame,
            text="Удалить",
            command=self._remove_selected_product,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            controls_frame,
            text="Импорт CSV",
            command=self._show_csv_import_dialog,
            takefocus=0,
        ).pack(side=tk.LEFT, padx=2)

        search_frame = ttk.Frame(products_frame)
        search_frame.pack(fill=tk.X, pady=(5, 5))

        ttk.Label(search_frame, text="Поиск:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.product_search_var = tk.StringVar()
        self.product_search_var.trace("w", lambda *args: self._filter_products())

        search_entry = ttk.Entry(search_frame, textvariable=self.product_search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            search_frame,
            text="Очистить",
            command=lambda: self.product_search_var.set(""),
            width=10,
            takefocus=0,
        ).pack(side=tk.LEFT)

        tree_frame = ttk.Frame(products_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "calories", "protein", "fat", "carbs", "serving")
        self.products_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=8
        )

        self.products_tree.heading("name", text="Название")
        self.products_tree.heading("calories", text="Ккал/100г")
        self.products_tree.heading("protein", text="Б")
        self.products_tree.heading("fat", text="Ж")
        self.products_tree.heading("carbs", text="У")
        self.products_tree.heading("serving", text="Порция")

        self.products_tree.column("name", width=180)
        self.products_tree.column("calories", width=80, anchor="center")
        self.products_tree.column("protein", width=50, anchor="center")
        self.products_tree.column("fat", width=50, anchor="center")
        self.products_tree.column("carbs", width=50, anchor="center")
        self.products_tree.column("serving", width=80, anchor="center")

        self.products_tree.tag_configure("selected", background="#0078D7", foreground="white")

        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.products_tree.yview
        )
        self.products_tree.configure(yscrollcommand=scrollbar.set)

        self.products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.products_tree.bind("<Double-Button-1>", lambda e: self._edit_selected_product())

    def _show_add_product_to_db_dialog(self, edit_mode: bool = False, product_name: str = ""):
        """Диалог добавления/редактирования продукта в базе"""
        dialog = tk.Toplevel(self)
        dialog.title("Редактировать продукт" if edit_mode else "Добавить продукт в базу")
        dialog.geometry("500x450")

        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 450) // 2
        dialog.geometry(f"500x450+{x}+{y}")

        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        fields_frame = ttk.Frame(dialog, padding=20)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        product_data = {}
        if edit_mode and product_name:
            products = self.storage.get_all_products()
            product_data = products.get(product_name, {})

        ttk.Label(fields_frame, text="Название продукта:", font=("Arial", 10)).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        name_entry = ttk.Entry(fields_frame, width=35)
        name_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        if edit_mode:
            name_entry.insert(0, product_name)
        name_entry.focus()

        ttk.Label(fields_frame, text="Калории на 100г:", font=("Arial", 10)).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        calories_entry = ttk.Entry(fields_frame, width=35)
        calories_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        if edit_mode and product_data.get("calories"):
            calories_entry.insert(0, str(product_data["calories"]))

        ttk.Label(
            fields_frame, text="(оставьте пустым если знаете ккал на порцию)", font=("Arial", 8), foreground="gray"
        ).grid(row=2, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(fields_frame, text="Размер порции г:", font=("Arial", 10)).grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        serving_entry = ttk.Entry(fields_frame, width=35)
        serving_entry.grid(row=3, column=1, pady=5, padx=(10, 0))
        if edit_mode and product_data.get("serving_size"):
            serving_entry.insert(0, str(product_data["serving_size"]))

        ttk.Label(fields_frame, text="Калории на порцию:", font=("Arial", 10)).grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        cal_serving_entry = ttk.Entry(fields_frame, width=35)
        cal_serving_entry.grid(row=4, column=1, pady=5, padx=(10, 0))
        if edit_mode and product_data.get("calories_per_serving"):
            cal_serving_entry.insert(0, str(product_data["calories_per_serving"]))

        ttk.Label(
            fields_frame, text="(автоматически вычислит ккал/100г)", font=("Arial", 8), foreground="gray"
        ).grid(row=5, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Separator(fields_frame, orient="horizontal").grid(
            row=6, column=0, columnspan=2, sticky="ew", pady=10
        )

        ttk.Label(fields_frame, text="Белки г (опционально):", font=("Arial", 10)).grid(
            row=7, column=0, sticky=tk.W, pady=5
        )
        protein_entry = ttk.Entry(fields_frame, width=35)
        protein_entry.grid(row=7, column=1, pady=5, padx=(10, 0))
        if edit_mode and product_data.get("protein"):
            protein_entry.insert(0, str(product_data["protein"]))

        ttk.Label(fields_frame, text="Жиры г (опционально):", font=("Arial", 10)).grid(
            row=8, column=0, sticky=tk.W, pady=5
        )
        fat_entry = ttk.Entry(fields_frame, width=35)
        fat_entry.grid(row=8, column=1, pady=5, padx=(10, 0))
        if edit_mode and product_data.get("fat"):
            fat_entry.insert(0, str(product_data["fat"]))

        ttk.Label(
            fields_frame, text="Углеводы г (опционально):", font=("Arial", 10)
        ).grid(row=9, column=0, sticky=tk.W, pady=5)
        carbs_entry = ttk.Entry(fields_frame, width=35)
        carbs_entry.grid(row=9, column=1, pady=5, padx=(10, 0))
        if edit_mode and product_data.get("carbs"):
            carbs_entry.insert(0, str(product_data["carbs"]))

        def save_product():
            name = name_entry.get().strip()
            calories_str = calories_entry.get().strip()
            serving_str = serving_entry.get().strip()
            cal_serving_str = cal_serving_entry.get().strip()

            if not name:
                messagebox.showwarning("Ошибка", "Название обязательно для заполнения")
                return

            if not calories_str and not (cal_serving_str and serving_str):
                messagebox.showwarning(
                    "Ошибка",
                    "Укажите калории на 100г ИЛИ калории на порцию + размер порции"
                )
                return

            try:
                calories = int(calories_str) if calories_str else 0
                protein = int(protein_entry.get()) if protein_entry.get().strip() else None
                fat = int(fat_entry.get()) if fat_entry.get().strip() else None
                carbs = int(carbs_entry.get()) if carbs_entry.get().strip() else None
                serving = int(serving_str) if serving_str else None
                cal_serving = int(cal_serving_str) if cal_serving_str else None

                if edit_mode:
                    self.storage.update_product_in_db(
                        product_name, name, calories, protein, fat, carbs, serving, cal_serving
                    )
                    self.storage.save()
                    self._update_all_displays()
                else:
                    self.storage.add_product_to_db(
                        name, calories, protein, fat, carbs, serving, cal_serving
                    )
                    self.storage.save()
                    self._update_products_display()

                dialog.destroy()

            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректные числовые значения")

        buttons_frame = ttk.Frame(fields_frame)
        buttons_frame.grid(row=10, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            buttons_frame, text="Сохранить", command=save_product, width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame, text="Отмена", command=dialog.destroy, width=15
        ).pack(side=tk.LEFT, padx=5)

        dialog.bind("<Return>", lambda e: save_product())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _show_add_product_dialog(
        self, meal_type: str, edit_mode: bool = False, edit_index: int = -1
    ):
        """Улучшенный диалог добавления продукта к приему пищи"""
        products = self.storage.get_all_products()

        dialog = tk.Toplevel(self)
        dialog.title("Редактировать запись" if edit_mode else "Добавить продукт")
        dialog.geometry("750x550")

        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 750) // 2
        y = (screen_height - 550) // 2
        dialog.geometry(f"750x550+{x}+{y}")

        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        edit_data = {}
        if edit_mode and edit_index >= 0:
            day_data = self.storage.get_day_data(self.current_date)
            entries = day_data.get(meal_type, [])
            if edit_index < len(entries):
                edit_data = entries[edit_index]

        product_header = ttk.Frame(content_frame)
        product_header.grid(row=0, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 10))

        ttk.Label(product_header, text="Выберите продукт:", font=("Arial", 11, "bold")).pack(
            side=tk.LEFT
        )

        ttk.Button(
            product_header,
            text="+ Создать новый",
            command=lambda: self._create_product_from_dialog(dialog, meal_type, edit_mode, edit_index),
            takefocus=0,
        ).pack(side=tk.RIGHT)

        search_frame = ttk.Frame(content_frame)
        search_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E, pady=(0, 5))

        ttk.Label(search_frame, text="Поиск:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 5))

        product_search = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=product_search, width=40, font=("Arial", 10))
        search_entry.pack(side=tk.LEFT, padx=(0, 5))

        listbox_frame = ttk.Frame(content_frame)
        listbox_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, pady=(0, 5))
        content_frame.grid_rowconfigure(2, weight=1)

        listbox_scroll = ttk.Scrollbar(listbox_frame, orient="vertical")
        product_listbox = tk.Listbox(
            listbox_frame,
            height=8,
            font=("Arial", 10),
            yscrollcommand=listbox_scroll.set,
        )
        listbox_scroll.config(command=product_listbox.yview)

        product_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        listbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        all_products = sorted(products.keys())
        for product in all_products:
            product_listbox.insert(tk.END, product)

        if edit_mode and edit_data:
            product_name = edit_data.get("product", "")
            if product_name in all_products:
                idx = all_products.index(product_name)
                product_listbox.selection_set(idx)
                product_listbox.see(idx)
        elif all_products:
            product_listbox.selection_set(0)

        def filter_products(*args):
            search_text = product_search.get().lower()
            product_listbox.delete(0, tk.END)

            filtered = [p for p in all_products if search_text in p.lower()]
            for product in filtered:
                product_listbox.insert(tk.END, product)

            if filtered:
                product_listbox.selection_set(0)

        product_search.trace("w", filter_products)

        ttk.Separator(content_frame, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=15
        )

        ttk.Label(content_frame, text="Количество:", font=("Arial", 11, "bold")).grid(
            row=4, column=0, sticky=tk.W, pady=(0, 10), columnspan=2
        )

        mode_var = tk.StringVar(value="grams")
        if edit_mode and edit_data:
            mode_var.set("grams" if edit_data.get("is_grams") else "portions")

        ttk.Radiobutton(
            content_frame, text="Граммы", variable=mode_var, value="grams", takefocus=False
        ).grid(row=5, column=0, sticky=tk.W)

        ttk.Radiobutton(
            content_frame, text="Порции", variable=mode_var, value="portions", takefocus=False
        ).grid(row=5, column=1, sticky=tk.W)

        amount_frame = ttk.Frame(content_frame)
        amount_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky=tk.W)

        amount_var = tk.StringVar(value="100")
        if edit_mode and edit_data:
            amount_var.set(str(edit_data.get("amount", 100)))

        amount_entry = ttk.Entry(amount_frame, textvariable=amount_var, width=15, font=("Arial", 12))
        amount_entry.pack(side=tk.LEFT, padx=(0, 10))

        unit_label = ttk.Label(amount_frame, text="г", font=("Arial", 10))
        unit_label.pack(side=tk.LEFT)

        def update_unit_label(*args):
            if mode_var.get() == "grams":
                unit_label.config(text="г")
            else:
                unit_label.config(text="порций")

        mode_var.trace("w", update_unit_label)
        update_unit_label()

        ttk.Label(content_frame, text="Быстрый выбор:", font=("Arial", 10)).grid(
            row=7, column=0, sticky=tk.W, pady=(10, 5), columnspan=2
        )

        quick_frame = ttk.Frame(content_frame)
        quick_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W)

        quick_values_grams = [30, 50, 100, 150, 200, 250, 300, 500]
        quick_values_portions = [0.5, 1, 1.5, 2, 2.5, 3]

        def set_quick_value(value):
            amount_var.set(str(value))

        def update_quick_buttons(*args):
            for widget in quick_frame.winfo_children():
                widget.destroy()

            if mode_var.get() == "grams":
                values = quick_values_grams
            else:
                values = quick_values_portions

            for val in values:
                btn = ttk.Button(
                    quick_frame,
                    text=str(val),
                    command=lambda v=val: set_quick_value(v),
                    width=6,
                )
                btn.pack(side=tk.LEFT, padx=2)

        mode_var.trace("w", update_quick_buttons)
        update_quick_buttons()

        def add_or_update_product():
            selection = product_listbox.curselection()
            if not selection:
                messagebox.showwarning("Ошибка", "Выберите продукт из списка")
                return

            product_name = product_listbox.get(selection[0])
            amount_str = amount_var.get().strip()

            if not product_name:
                messagebox.showwarning("Ошибка", "Выберите продукт")
                return

            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError()

                is_grams = mode_var.get() == "grams"

                if edit_mode:
                    self.storage.update_meal_entry(
                        self.current_date, meal_type, edit_index, product_name, amount, is_grams
                    )
                else:
                    self.storage.add_meal_entry(
                        self.current_date, meal_type, product_name, amount, is_grams
                    )

                self.storage.save()
                self._update_meal_display(meal_type)
                self._update_stats()
                dialog.destroy()

            except ValueError:
                messagebox.showwarning(
                    "Ошибка", "Введите корректное положительное число"
                )

        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.grid(row=9, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(
            buttons_frame,
            text="Сохранить" if edit_mode else "Добавить",
            command=add_or_update_product,
            width=15,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame, text="Отмена", command=dialog.destroy, width=15
        ).pack(side=tk.LEFT, padx=5)

        dialog.bind("<Return>", lambda e: add_or_update_product())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _edit_selected_product(self):
        """Редактирование выбранного продукта из базы"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showinfo("Ошибка", "Выберите продукт для редактирования")
            return

        item = selection[0]
        product_name = self.products_tree.item(item)["values"][0]
        self._show_add_product_to_db_dialog(edit_mode=True, product_name=product_name)

    def _remove_selected_product(self):
        """Удаляет выбранный продукт из базы"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showinfo("Ошибка", "Выберите продукт для удаления")
            return

        item = selection[0]
        product_name = self.products_tree.item(item)["values"][0]

        if messagebox.askyesno(
            "Подтверждение",
            f'Удалить продукт "{product_name}" из базы?\nОн будет удален из всех приемов пищи.',
        ):
            self.storage.remove_product_from_db(product_name)
            self.storage.save()
            self._update_all_displays()

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

    def _handle_meal_double_click(self, event, meal_type: str, tree: ttk.Treeview):
        """Обрабатывает двойной клик для редактирования записи"""
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        item = tree.identify_row(event.y)
        if not item:
            return

        index = tree.index(item)
        self._show_add_product_dialog(meal_type, edit_mode=True, edit_index=index)

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
        """Обновляет панель статистики с калориями и БЖУ"""
        total_calories = self.storage.get_day_total_calories(self.current_date)
        target_calories = self.get_target_calories()
        macros = self.storage.get_day_total_macros(self.current_date)

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

        if any(macros.values()):
            macro_parts = []
            if macros["protein"] is not None:
                macro_parts.append(f"Б: {macros['protein']}г")
            if macros["fat"] is not None:
                macro_parts.append(f"Ж: {macros['fat']}г")
            if macros["carbs"] is not None:
                macro_parts.append(f"У: {macros['carbs']}г")

            macro_text = " | ".join(macro_parts)
            self.macros_label.config(text=macro_text)
        else:
            self.macros_label.config(text="")

    def _update_meal_display(self, meal_type: str):
        """Обновляет отображение для конкретного приема пищи"""
        if meal_type not in self.meal_frames:
            return

        tree = self.meal_frames[meal_type]["tree"]
        calories_label = self.meal_frames[meal_type]["calories_label"]
        macros_label = self.meal_frames[meal_type]["macros_label"]

        for item in tree.get_children():
            tree.delete(item)

        day_data = self.storage.get_day_data(self.current_date)
        entries = day_data.get(meal_type, [])

        for entry in entries:
            is_grams = entry.get("is_grams", False)
            amount = entry.get("amount", 1.0)

            if is_grams:
                amount_text = f"{int(amount)}г"
            else:
                amount_text = f"{amount}x"

            tree.insert(
                "",
                "end",
                values=(
                    entry["product"],
                    amount_text,
                    f"{entry['calories']} ккал",
                    "✕",
                ),
            )

        total_calories = self.storage.get_meal_total_calories(
            self.current_date, meal_type
        )
        calories_label.config(text=f"{total_calories} ккал")

        macros = self.storage.get_meal_total_macros(self.current_date, meal_type)

        if any(macros.values()):
            macro_parts = []
            if macros["protein"] is not None:
                macro_parts.append(f"Б:{macros['protein']}")
            if macros["fat"] is not None:
                macro_parts.append(f"Ж:{macros['fat']}")
            if macros["carbs"] is not None:
                macro_parts.append(f"У:{macros['carbs']}")

            macro_text = " ".join(macro_parts)
            macros_label.config(text=macro_text)
        else:
            macros_label.config(text="")

    def _update_products_display(self, filter_text: str = ""):
        """Обновляет отображение базы продуктов с учетом фильтра"""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        products = self.storage.get_all_products()
        filter_lower = filter_text.lower()

        for name, data in sorted(products.items()):
            if filter_lower and filter_lower not in name.lower():
                continue

            protein = data.get("protein") or "-"
            fat = data.get("fat") or "-"
            carbs = data.get("carbs") or "-"
            serving = f"{data.get('serving_size')}г" if data.get("serving_size") else "-"

            self.products_tree.insert(
                "", "end", values=(name, data["calories"], protein, fat, carbs, serving)
            )

    def _filter_products(self):
        """Фильтрует продукты по поисковому запросу"""
        search_text = self.product_search_var.get()
        self._update_products_display(search_text)

    def _show_csv_import_dialog(self):
        """Диалог массового импорта продуктов через CSV"""
        dialog = tk.Toplevel(self)
        dialog.title("Массовый импорт продуктов (CSV)")
        dialog.geometry("700x500")

        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 500) // 2
        dialog.geometry(f"700x500+{x}+{y}")

        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="Формат CSV (через точку с запятой):",
            font=("Arial", 11, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))

        ttk.Label(
            main_frame,
            text="название;калории;белки;жиры;углеводы",
            font=("Arial", 10),
            foreground="gray",
        ).pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(
            main_frame,
            text="Примеры:",
            font=("Arial", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))

        examples_text = """Хлеб белый;265;8;3;50
Куриная грудка;113;23;2;0
Рис отварной;130;3;1;28
Яйцо куриное;157;13;11;1"""

        examples_label = ttk.Label(
            main_frame,
            text=examples_text,
            font=("Courier", 9),
            foreground="gray",
        )
        examples_label.pack(anchor=tk.W, pady=(0, 15))

        ttk.Label(
            main_frame,
            text="Введите данные (каждый продукт с новой строки):",
            font=("Arial", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))

        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        text_widget = tk.Text(text_frame, height=15, font=("Courier", 10))
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=text_scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def import_csv():
            content = text_widget.get("1.0", tk.END).strip()
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

                    if not name:
                        error_lines.append(f"Строка {i}: пустое название")
                        continue

                    self.storage.add_product_to_db(name, calories, protein, fat, carbs)
                    success_count += 1

                except ValueError:
                    error_lines.append(f"Строка {i}: некорректные числовые значения")

            self.storage.save()
            self._update_products_display()

            result_msg = f"Успешно импортировано: {success_count} продуктов"
            if error_lines:
                result_msg += f"\n\nОшибки:\n" + "\n".join(error_lines[:10])
                if len(error_lines) > 10:
                    result_msg += f"\n... и еще {len(error_lines) - 10}"

            messagebox.showinfo("Результат импорта", result_msg)
            if success_count > 0:
                dialog.destroy()

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)

        ttk.Button(
            buttons_frame, text="Импортировать", command=import_csv, width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame, text="Отмена", command=dialog.destroy, width=15
        ).pack(side=tk.LEFT, padx=5)

    def _create_product_from_dialog(
        self, parent_dialog, meal_type: str, edit_mode: bool, edit_index: int
    ):
        """Создает новый продукт из диалога добавления к приему пищи"""
        parent_dialog.destroy()

        create_dialog = tk.Toplevel(self)
        create_dialog.title("Создать продукт")
        create_dialog.geometry("650x650")

        screen_width = create_dialog.winfo_screenwidth()
        screen_height = create_dialog.winfo_screenheight()
        x = (screen_width - 650) // 2
        y = (screen_height - 650) // 2
        create_dialog.geometry(f"650x650+{x}+{y}")

        create_dialog.resizable(False, False)
        create_dialog.transient(self)
        create_dialog.grab_set()

        fields_frame = ttk.Frame(create_dialog, padding=20)
        fields_frame.pack(fill=tk.BOTH, expand=True)

        row = 0

        ttk.Label(
            fields_frame,
            text="Быстрый ввод CSV (название;ккал_на_порцию;размер_порции;б;ж;у):",
            font=("Arial", 10, "bold"),
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        row += 1

        csv_entry = ttk.Entry(fields_frame, width=50)
        csv_entry.grid(row=row, column=0, columnspan=2, pady=5, sticky=tk.W+tk.E)
        csv_entry.focus()
        row += 1

        ttk.Label(
            fields_frame,
            text="Пример: Яйцо;78;50;13;11;1 (авто-расчёт ккал на 100г)",
            font=("Arial", 8),
            foreground="gray",
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1

        def parse_csv():
            csv_text = csv_entry.get().strip()
            if not csv_text:
                return

            parts = csv_text.split(";")
            if len(parts) >= 3:
                # Формат: название;ккал_на_порцию;размер_порции;б;ж;у
                name_entry.delete(0, tk.END)
                name_entry.insert(0, parts[0].strip())

                calories_per_serving_entry.delete(0, tk.END)
                calories_per_serving_entry.insert(0, parts[1].strip())

                serving_entry.delete(0, tk.END)
                serving_entry.insert(0, parts[2].strip())

                # Оставляем calories пустым для автоматического расчёта
                calories_entry.delete(0, tk.END)

                if len(parts) > 3 and parts[3].strip():
                    protein_entry.delete(0, tk.END)
                    protein_entry.insert(0, parts[3].strip())

                if len(parts) > 4 and parts[4].strip():
                    fat_entry.delete(0, tk.END)
                    fat_entry.insert(0, parts[4].strip())

                if len(parts) > 5 and parts[5].strip():
                    carbs_entry.delete(0, tk.END)
                    carbs_entry.insert(0, parts[5].strip())

        ttk.Button(
            fields_frame,
            text="Заполнить из CSV",
            command=parse_csv,
            width=20,
        ).grid(row=row, column=0, columnspan=2, pady=(0, 10))
        row += 1

        ttk.Separator(fields_frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        row += 1

        ttk.Label(fields_frame, text="Название продукта:", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        name_entry = ttk.Entry(fields_frame, width=35)
        name_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        ttk.Label(fields_frame, text="Калории на 100г (авто):", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        calories_entry = ttk.Entry(fields_frame, width=35)
        calories_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        ttk.Label(fields_frame, text="Калории на порцию (опц):", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        calories_per_serving_entry = ttk.Entry(fields_frame, width=35)
        calories_per_serving_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        ttk.Label(fields_frame, text="Размер порции г (опц):", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        serving_entry = ttk.Entry(fields_frame, width=35)
        serving_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        ttk.Separator(fields_frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        row += 1

        ttk.Label(fields_frame, text="БЖУ (опционально):", font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5)
        )
        row += 1

        ttk.Label(fields_frame, text="Белки г:", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        protein_entry = ttk.Entry(fields_frame, width=35)
        protein_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        ttk.Label(fields_frame, text="Жиры г:", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        fat_entry = ttk.Entry(fields_frame, width=35)
        fat_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        ttk.Label(fields_frame, text="Углеводы г:", font=("Arial", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        carbs_entry = ttk.Entry(fields_frame, width=35)
        carbs_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        def save_and_reopen():
            name = name_entry.get().strip()
            calories_str = calories_entry.get().strip()
            calories_per_serving_str = calories_per_serving_entry.get().strip()
            serving_str = serving_entry.get().strip()

            # Проверка: либо калории на 100г, либо калории на порцию + размер порции
            if not name:
                messagebox.showwarning("Ошибка", "Название обязательно")
                return

            if not calories_str and not (calories_per_serving_str and serving_str):
                messagebox.showwarning(
                    "Ошибка",
                    "Укажите либо калории на 100г, либо калории на порцию + размер порции"
                )
                return

            try:
                calories = int(calories_str) if calories_str else 0
                calories_per_serving = int(calories_per_serving_str) if calories_per_serving_str else None
                protein = int(protein_entry.get()) if protein_entry.get().strip() else None
                fat = int(fat_entry.get()) if fat_entry.get().strip() else None
                carbs = int(carbs_entry.get()) if carbs_entry.get().strip() else None
                serving = int(serving_str) if serving_str else None

                self.storage.add_product_to_db(
                    name, calories, protein, fat, carbs, serving, calories_per_serving
                )
                self.storage.save()
                self._update_products_display()

                create_dialog.destroy()
                self._show_add_product_dialog(meal_type, edit_mode, edit_index)

            except ValueError:
                messagebox.showwarning("Ошибка", "Введите корректные числовые значения")

        buttons_frame = ttk.Frame(fields_frame)
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        row += 1

        ttk.Button(
            buttons_frame, text="Создать и продолжить", command=save_and_reopen, width=20
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            buttons_frame, text="Отмена", command=create_dialog.destroy, width=15
        ).pack(side=tk.LEFT, padx=5)

        create_dialog.bind("<Return>", lambda e: save_and_reopen())
        create_dialog.bind("<Escape>", lambda e: create_dialog.destroy())
