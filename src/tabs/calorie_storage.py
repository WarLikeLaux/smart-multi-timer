"""
Хранилище данных для трекинга калорий.

Ответственность:
- Управление базой продуктов (CRUD)
- Управление записями приемов пищи
- Персистентность в JSON
- Автоматический пересчет при изменении продуктов
"""

import json
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
        """Добавляет продукт в базу с автоматическим расчётом калорий"""
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
        """Обновляет продукт и пересчитывает все записи"""
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
        if name not in self._products_db:
            return

        del self._products_db[name]
        self._remove_product_from_all_meals(name)
        self._modified = True

    def _remove_product_from_all_meals(self, product_name: str) -> None:
        """Удаляет все записи с продуктом"""
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
                    if entry.get("product") not in [old_name, new_name]:
                        continue

                    entry["product"] = new_name
                    multiplier = self._calculate_multiplier(
                        entry.get("amount", 1.0), entry.get("is_grams", False)
                    )
                    self._update_entry_nutrients(entry, product, multiplier)

        self._modified = True

    def _calculate_multiplier(self, amount: float, is_grams: bool) -> float:
        """Вычисляет множитель для расчёта калорий и БЖУ"""
        return amount / 100.0 if is_grams else amount

    def _update_entry_nutrients(
        self, entry: dict, product: dict, multiplier: float
    ) -> None:
        """Обновляет питательные значения записи"""
        entry["calories"] = int(product["calories"] * multiplier)
        entry["protein"] = (
            int(product["protein"] * multiplier) if product["protein"] else None
        )
        entry["fat"] = int(product["fat"] * multiplier) if product["fat"] else None
        entry["carbs"] = (
            int(product["carbs"] * multiplier) if product["carbs"] else None
        )

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
        """Добавляет запись о приеме пищи"""
        if product_name not in self._products_db:
            return

        if date not in self._daily_entries:
            self._daily_entries[date] = {
                "breakfast": [],
                "lunch": [],
                "dinner": [],
                "snack": [],
            }

        product = self._products_db[product_name]
        multiplier = self._calculate_multiplier(amount, is_grams)

        entry = self._create_meal_entry(
            product_name, amount, is_grams, product, multiplier
        )
        self._daily_entries[date][meal_type].append(entry)
        self._modified = True

    def _create_meal_entry(
        self,
        product_name: str,
        amount: float,
        is_grams: bool,
        product: dict,
        multiplier: float,
    ) -> dict:
        """Создает запись о приеме пищи"""
        import time

        return {
            "product": product_name,
            "amount": amount,
            "is_grams": is_grams,
            "calories": int(product["calories"] * multiplier),
            "protein": (
                int(product["protein"] * multiplier) if product["protein"] else None
            ),
            "fat": int(product["fat"] * multiplier) if product["fat"] else None,
            "carbs": int(product["carbs"] * multiplier) if product["carbs"] else None,
            "time": time.strftime("%H:%M"),
        }

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
        if not self._is_valid_meal_entry(date, meal_type, index):
            return

        if product_name not in self._products_db:
            return

        product = self._products_db[product_name]
        multiplier = self._calculate_multiplier(amount, is_grams)

        entry = self._daily_entries[date][meal_type][index]
        entry["product"] = product_name
        entry["amount"] = amount
        entry["is_grams"] = is_grams
        self._update_entry_nutrients(entry, product, multiplier)
        self._modified = True

    def _is_valid_meal_entry(self, date: str, meal_type: str, index: int) -> bool:
        """Проверяет валидность индекса записи"""
        return (
            date in self._daily_entries
            and meal_type in self._daily_entries[date]
            and 0 <= index < len(self._daily_entries[date][meal_type])
        )

    def remove_meal_entry(self, date: str, meal_type: str, index: int) -> None:
        """Удаляет запись о приеме пищи"""
        if not self._is_valid_meal_entry(date, meal_type, index):
            return

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
        return sum(
            sum(entry["calories"] for entry in meal_entries)
            for meal_entries in day_data.values()
        )

    def get_day_total_macros(self, date: str) -> Dict[str, Optional[int]]:
        """Подсчитывает общее количество БЖУ за день"""
        day_data = self.get_day_data(date)
        return self._calculate_macros(
            [entry for entries in day_data.values() for entry in entries]
        )

    def get_meal_total_calories(self, date: str, meal_type: str) -> int:
        """Подсчитывает калории для конкретного приема пищи"""
        day_data = self.get_day_data(date)
        return sum(entry["calories"] for entry in day_data.get(meal_type, []))

    def get_meal_total_macros(
        self, date: str, meal_type: str
    ) -> Dict[str, Optional[int]]:
        """Подсчитывает БЖУ для конкретного приема пищи"""
        day_data = self.get_day_data(date)
        return self._calculate_macros(day_data.get(meal_type, []))

    def _calculate_macros(self, entries: List[dict]) -> Dict[str, Optional[int]]:
        """Вычисляет суммарные БЖУ для списка записей"""
        totals = {"protein": 0, "fat": 0, "carbs": 0}
        has_data = {"protein": False, "fat": False, "carbs": False}

        for entry in entries:
            for macro in ["protein", "fat", "carbs"]:
                if entry.get(macro) is not None:
                    totals[macro] += entry[macro]
                    has_data[macro] = True

        return {
            macro: totals[macro] if has_data[macro] else None
            for macro in ["protein", "fat", "carbs"]
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
