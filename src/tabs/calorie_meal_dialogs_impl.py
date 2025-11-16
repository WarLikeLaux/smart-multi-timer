"""
Временный модуль с реализацией больших диалогов приёмов пищи.

ВНИМАНИЕ: Этот файл создан как промежуточный шаг рефакторинга.
Содержит код "as is" для соблюдения лимита ≤500 строк в calorie_tracker_tab.py.
TODO: Разбить на классы согласно контракту в следующей итерации рефакторинга.

Функции:
- show_add_product_dialog_impl: диалог выбора продукта для приёма пищи
- create_product_from_dialog_impl: диалог быстрого создания продукта
"""

import tkinter as tk
from tkinter import messagebox, ttk


def show_add_product_dialog_impl(
    tab_instance,
    meal_type: str,
    edit_mode: bool = False,
    edit_index: int = -1
):
    """
    Реализация диалога добавления продукта к приему пищи.

    Принимает tab_instance для доступа к storage, current_date и методам.
    """
    products = tab_instance.storage.get_all_products()

    dialog = tk.Toplevel(tab_instance)
    dialog.title("Редактировать запись" if edit_mode else "Добавить продукт")
    dialog.geometry("750x550")

    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    x = (screen_width - 750) // 2
    y = (screen_height - 550) // 2
    dialog.geometry(f"750x550+{x}+{y}")

    dialog.resizable(False, False)
    dialog.transient(tab_instance)
    dialog.grab_set()

    content_frame = ttk.Frame(dialog, padding=20)
    content_frame.pack(fill=tk.BOTH, expand=True)

    edit_data = {}
    if edit_mode and edit_index >= 0:
        day_data = tab_instance.storage.get_day_data(tab_instance.current_date)
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
        command=lambda: create_product_from_dialog_impl(
            tab_instance, dialog, meal_type, edit_mode, edit_index
        ),
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
        row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
    )

    amount_entry = ttk.Entry(content_frame, width=20, font=("Arial", 10))
    amount_entry.grid(row=5, column=0, columnspan=2, pady=(0, 10))
    amount_entry.insert(0, str(edit_data.get("amount", "100")) if edit_mode else "100")

    mode_var = tk.StringVar(value="grams" if edit_data.get("is_grams", True) else "portions")

    ttk.Radiobutton(
        content_frame, text="Граммы", variable=mode_var, value="grams", takefocus=False
    ).grid(row=6, column=0, sticky=tk.W)

    ttk.Radiobutton(
        content_frame, text="Порции", variable=mode_var, value="portions", takefocus=False
    ).grid(row=6, column=1, sticky=tk.W)

    def save_entry():
        selection = product_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ошибка", "Выберите продукт")
            return

        product_name = product_listbox.get(selection[0])
        amount_str = amount_entry.get().strip()

        if not amount_str:
            messagebox.showwarning("Ошибка", "Введите количество")
            return

        try:
            amount = float(amount_str.replace(",", "."))
            is_grams = mode_var.get() == "grams"

            if edit_mode and edit_index >= 0:
                tab_instance.storage.update_meal_entry(
                    tab_instance.current_date,
                    meal_type,
                    edit_index,
                    product_name,
                    amount,
                    is_grams,
                )
            else:
                tab_instance.storage.add_meal_entry(
                    tab_instance.current_date,
                    meal_type,
                    product_name,
                    amount,
                    is_grams,
                )

            tab_instance.storage.save()
            tab_instance._update_all_displays()
            dialog.destroy()

        except ValueError:
            messagebox.showwarning("Ошибка", "Введите корректное числовое значение")

    buttons_frame = ttk.Frame(content_frame)
    buttons_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))

    ttk.Button(
        buttons_frame, text="Сохранить", command=save_entry, width=15
    ).pack(side=tk.LEFT, padx=5)

    ttk.Button(
        buttons_frame, text="Отмена", command=dialog.destroy, width=15
    ).pack(side=tk.LEFT, padx=5)

    dialog.bind("<Return>", lambda e: save_entry())
    dialog.bind("<Escape>", lambda e: dialog.destroy())


def create_product_from_dialog_impl(
    tab_instance,
    parent_dialog,
    meal_type: str,
    edit_mode: bool,
    edit_index: int
):
    """
    Реализация диалога быстрого создания продукта из приёма пищи.

    Принимает tab_instance для доступа к storage и методам.
    """
    parent_dialog.destroy()

    create_dialog = tk.Toplevel(tab_instance)
    create_dialog.title("Создать продукт")
    create_dialog.geometry("650x650")

    screen_width = create_dialog.winfo_screenwidth()
    screen_height = create_dialog.winfo_screenheight()
    x = (screen_width - 650) // 2
    y = (screen_height - 650) // 2
    create_dialog.geometry(f"650x650+{x}+{y}")

    create_dialog.resizable(False, False)
    create_dialog.transient(tab_instance)
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

    name_entry = None
    calories_entry = None
    calories_per_serving_entry = None
    serving_entry = None
    protein_entry = None
    fat_entry = None
    carbs_entry = None

    def parse_csv():
        nonlocal name_entry, calories_entry, calories_per_serving_entry
        nonlocal serving_entry, protein_entry, fat_entry, carbs_entry

        csv_text = csv_entry.get().strip()
        if not csv_text:
            return

        parts = csv_text.split(";")
        if len(parts) >= 3:
            name_entry.delete(0, tk.END)
            name_entry.insert(0, parts[0].strip())

            calories_per_serving_entry.delete(0, tk.END)
            calories_per_serving_entry.insert(0, parts[1].strip())

            serving_entry.delete(0, tk.END)
            serving_entry.insert(0, parts[2].strip())

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

            tab_instance.storage.add_product_to_db(
                name, calories, protein, fat, carbs, serving, calories_per_serving
            )
            tab_instance.storage.save()
            tab_instance._update_products_display()

            create_dialog.destroy()
            show_add_product_dialog_impl(tab_instance, meal_type, edit_mode, edit_index)

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
