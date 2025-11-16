import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
from typing import List

from tabs.calorie_storage import CalorieStorage
from tabs.calorie_dialogs import ProductDatabaseDialog, CSVImportDialog
from tabs.calorie_meal_dialogs_impl import (
    show_add_product_dialog_impl,
    create_product_from_dialog_impl,
)


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
        on_save = self._update_all_displays if edit_mode else self._update_products_display
        ProductDatabaseDialog(self, self.storage, on_save, edit_mode, product_name)

    def _show_add_product_dialog(
        self, meal_type: str, edit_mode: bool = False, edit_index: int = -1
    ):
        """Диалог добавления продукта к приему пищи (делегируется в calorie_meal_dialogs_impl)"""
        show_add_product_dialog_impl(self, meal_type, edit_mode, edit_index)

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
        CSVImportDialog(self, self.storage, self._update_products_display)

    def _create_product_from_dialog(
        self, parent_dialog, meal_type: str, edit_mode: bool, edit_index: int
    ):
        """Быстрое создание продукта (делегируется в calorie_meal_dialogs_impl)"""
        create_product_from_dialog_impl(self, parent_dialog, meal_type, edit_mode, edit_index)
