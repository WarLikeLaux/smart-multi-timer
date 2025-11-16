"""
Тесты для модуля CalorieStorage

Проверяет функциональность хранилища калорий:
- Управление базой продуктов (добавление, обновление, удаление)
- Расчёт калорий и макронутриентов
- Персистентность данных
"""

import json
import os
import tempfile
from pathlib import Path

import pytest


# Импортируем CalorieStorage, добавив src в путь
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tabs.calorie_storage import CalorieStorage


class TestCalorieStorage:
    """Тесты для класса CalorieStorage"""

    @pytest.fixture
    def temp_dir(self):
        """Создает временную директорию для тестов"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Очистка после теста
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def storage(self, temp_dir, monkeypatch):
        """Создает CalorieStorage с временным файлом"""
        # Меняем текущую директорию на временную
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        # Создаём storage
        storage = CalorieStorage()

        yield storage

        # Возвращаем исходную директорию
        os.chdir(original_dir)

    def test_init_creates_empty_storage(self, storage):
        """Тест: инициализация создаёт пустое хранилище"""
        assert storage.get_all_products() == {}

    def test_add_product_to_db(self, storage):
        """Тест: добавление продукта в базу"""
        storage.add_product_to_db(
            name="Яблоко",
            calories=52,
            protein=0,
            fat=0,
            carbs=14
        )

        products = storage.get_all_products()
        assert "Яблоко" in products
        assert products["Яблоко"]["calories"] == 52
        assert products["Яблоко"]["carbs"] == 14

    def test_add_product_with_serving_size(self, storage):
        """Тест: добавление продукта с размером порции"""
        storage.add_product_to_db(
            name="Рис",
            calories=130,
            serving_size=100
        )

        products = storage.get_all_products()
        assert products["Рис"]["serving_size"] == 100

    def test_add_product_calculates_calories_per_100g(self, storage):
        """Тест: автоматический расчёт калорий на 100г"""
        storage.add_product_to_db(
            name="Хлеб",
            calories=0,  # Не указано
            calories_per_serving=250,
            serving_size=100
        )

        products = storage.get_all_products()
        # (250 / 100) * 100 = 250
        assert products["Хлеб"]["calories"] == 250

    def test_update_product_in_db(self, storage):
        """Тест: обновление существующего продукта"""
        storage.add_product_to_db("Молоко", calories=60)
        storage.update_product_in_db(
            old_name="Молоко",
            name="Молоко 3.2%",
            calories=64
        )

        products = storage.get_all_products()
        assert "Молоко" not in products
        assert "Молоко 3.2%" in products
        assert products["Молоко 3.2%"]["calories"] == 64

    def test_remove_product_from_db(self, storage):
        """Тест: удаление продукта из базы"""
        storage.add_product_to_db("Сыр", calories=360)
        storage.remove_product_from_db("Сыр")

        products = storage.get_all_products()
        assert "Сыр" not in products

    def test_get_all_products_returns_copy(self, storage):
        """Тест: get_all_products возвращает копию (не изменяет внутреннее состояние)"""
        storage.add_product_to_db("Тест", calories=100)

        products = storage.get_all_products()
        products["Тест"]["calories"] = 999  # Попытка изменения

        # Внутреннее состояние не должно измениться
        original = storage.get_all_products()
        assert original["Тест"]["calories"] == 100

    def test_add_meal_entry(self, storage):
        """Тест: добавление записи приёма пищи"""
        storage.add_product_to_db("Овсянка", calories=88)
        storage.add_meal_entry(
            date="2025-01-15",
            meal_type="breakfast",
            product="Овсянка",
            amount=100,
            is_grams=True
        )

        day_data = storage.get_day_data("2025-01-15")
        assert "breakfast" in day_data
        assert len(day_data["breakfast"]) == 1
        assert day_data["breakfast"][0]["product"] == "Овсянка"

    def test_calculate_meal_total_calories_grams(self, storage):
        """Тест: расчёт калорий приёма пищи (в граммах)"""
        storage.add_product_to_db("Гречка", calories=123)
        storage.add_meal_entry(
            date="2025-01-15",
            meal_type="lunch",
            product="Гречка",
            amount=200,  # 200 грамм
            is_grams=True
        )

        total = storage.get_meal_total_calories("2025-01-15", "lunch")
        # (123 / 100) * 200 = 246
        assert total == 246

    def test_calculate_meal_total_calories_servings(self, storage):
        """Тест: расчёт калорий приёма пищи (в порциях по 100г)"""
        storage.add_product_to_db(
            "Йогурт",
            calories=60,
            serving_size=150
        )
        storage.add_meal_entry(
            date="2025-01-15",
            meal_type="snack",
            product="Йогурт",
            amount=2,  # 2 порции по 100г (т.к. is_grams=False означает множитель)
            is_grams=False
        )

        total = storage.get_meal_total_calories("2025-01-15", "snack")
        # При is_grams=False: calories * amount = 60 * 2 = 120
        assert total == 120

    def test_get_day_total_calories(self, storage):
        """Тест: расчёт общих калорий за день"""
        storage.add_product_to_db("Хлеб", calories=250)
        storage.add_product_to_db("Масло", calories=748)

        storage.add_meal_entry("2025-01-15", "breakfast", "Хлеб", 100, True)
        storage.add_meal_entry("2025-01-15", "breakfast", "Масло", 10, True)
        storage.add_meal_entry("2025-01-15", "lunch", "Хлеб", 50, True)

        total = storage.get_day_total_calories("2025-01-15")
        # 250 + (748/100)*10 + (250/100)*50 = 250 + 74.8 + 125 = 449.8 ≈ 449
        assert total == 449

    def test_get_meal_total_macros(self, storage):
        """Тест: расчёт БЖУ для приёма пищи"""
        storage.add_product_to_db(
            "Курица",
            calories=165,
            protein=31,
            fat=4,
            carbs=0
        )
        storage.add_meal_entry(
            date="2025-01-15",
            meal_type="dinner",
            product="Курица",
            amount=150,
            is_grams=True
        )

        macros = storage.get_meal_total_macros("2025-01-15", "dinner")
        # (31 / 100) * 150 = 46.5 ≈ 46
        assert macros["protein"] == 46
        # (4 / 100) * 150 = 6
        assert macros["fat"] == 6
        assert macros["carbs"] == 0

    def test_get_day_total_macros(self, storage):
        """Тест: расчёт общего БЖУ за день"""
        storage.add_product_to_db("Рис", calories=130, protein=3, fat=1, carbs=28)
        storage.add_product_to_db("Курица", calories=165, protein=31, fat=4, carbs=0)

        storage.add_meal_entry("2025-01-15", "lunch", "Рис", 100, True)
        storage.add_meal_entry("2025-01-15", "lunch", "Курица", 100, True)

        macros = storage.get_day_total_macros("2025-01-15")
        # Рис: Б3 Ж1 У28 + Курица: Б31 Ж4 У0
        assert macros["protein"] == 34
        assert macros["fat"] == 5
        assert macros["carbs"] == 28

    def test_remove_meal_entry(self, storage):
        """Тест: удаление записи приёма пищи"""
        storage.add_product_to_db("Тест", calories=100)
        storage.add_meal_entry("2025-01-15", "breakfast", "Тест", 100, True)
        storage.add_meal_entry("2025-01-15", "breakfast", "Тест", 50, True)

        storage.remove_meal_entry("2025-01-15", "breakfast", 0)

        day_data = storage.get_day_data("2025-01-15")
        assert len(day_data["breakfast"]) == 1
        assert day_data["breakfast"][0]["amount"] == 50

    def test_update_meal_entry(self, storage):
        """Тест: обновление записи приёма пищи"""
        storage.add_product_to_db("Банан", calories=89)
        storage.add_meal_entry("2025-01-15", "snack", "Банан", 100, True)

        storage.update_meal_entry(
            date="2025-01-15",
            meal_type="snack",
            index=0,
            product="Банан",
            amount=150,
            is_grams=True
        )

        day_data = storage.get_day_data("2025-01-15")
        assert day_data["snack"][0]["amount"] == 150

    def test_remove_product_deletes_from_all_meals(self, storage):
        """Тест: удаление продукта удаляет его из всех приёмов пищи"""
        storage.add_product_to_db("УдалитьЭто", calories=100)
        storage.add_meal_entry("2025-01-15", "breakfast", "УдалитьЭто", 100, True)
        storage.add_meal_entry("2025-01-16", "lunch", "УдалитьЭто", 50, True)

        storage.remove_product_from_db("УдалитьЭто")

        day1 = storage.get_day_data("2025-01-15")
        day2 = storage.get_day_data("2025-01-16")
        assert len(day1.get("breakfast", [])) == 0
        assert len(day2.get("lunch", [])) == 0

    @pytest.mark.parametrize("date,meal_type", [
        ("2025-01-15", "breakfast"),
        ("2025-01-15", "lunch"),
        ("2025-01-15", "dinner"),
        ("2025-01-15", "snack"),
    ])
    def test_supports_all_meal_types(self, storage, date, meal_type):
        """Тест: поддержка всех типов приёмов пищи"""
        storage.add_product_to_db("Тест", calories=100)
        storage.add_meal_entry(date, meal_type, "Тест", 100, True)

        day_data = storage.get_day_data(date)
        assert meal_type in day_data
        assert len(day_data[meal_type]) == 1

    def test_get_day_data_returns_empty_for_nonexistent_date(self, storage):
        """Тест: несуществующая дата возвращает пустой словарь"""
        day_data = storage.get_day_data("2099-12-31")
        assert day_data == {}

    def test_get_meal_total_calories_returns_zero_for_empty_meal(self, storage):
        """Тест: пустой приём пищи возвращает 0 калорий"""
        total = storage.get_meal_total_calories("2025-01-15", "breakfast")
        assert total == 0

    def test_macros_with_none_values(self, storage):
        """Тест: продукт с незаполненными БЖУ возвращает None для макросов"""
        storage.add_product_to_db(
            "ПростойПродукт",
            calories=100,
            protein=None,
            fat=None,
            carbs=None
        )
        storage.add_meal_entry("2025-01-15", "lunch", "ПростойПродукт", 100, True)

        macros = storage.get_meal_total_macros("2025-01-15", "lunch")
        # Если нет данных, _calculate_macros должен вернуть None для каждого макроса
        assert macros["protein"] is None
        assert macros["fat"] is None
        assert macros["carbs"] is None


class TestCalorieStoragePersistence:
    """Тесты персистентности CalorieStorage"""

    @pytest.fixture
    def temp_dir(self):
        """Создает временную директорию для тестов"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_save_and_load_products(self, temp_dir):
        """Тест: сохранение и загрузка базы продуктов"""
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Создаём первое хранилище и добавляем продукт
            storage1 = CalorieStorage()
            storage1.add_product_to_db("Яблоко", calories=52, protein=0, fat=0, carbs=14)
            storage1.save()

            # Создаём второе хранилище из того же файла
            storage2 = CalorieStorage()
            products = storage2.get_all_products()

            assert "Яблоко" in products
            assert products["Яблоко"]["calories"] == 52
            assert products["Яблоко"]["carbs"] == 14
        finally:
            os.chdir(original_dir)

    def test_save_and_load_meal_entries(self, temp_dir):
        """Тест: сохранение и загрузка записей приёмов пищи"""
        original_dir = os.getcwd()
        os.chdir(temp_dir)

        try:
            storage1 = CalorieStorage()
            storage1.add_product_to_db("Рис", calories=130)
            storage1.add_meal_entry("2025-01-15", "lunch", "Рис", 200, True)
            storage1.save()

            storage2 = CalorieStorage()
            day_data = storage2.get_day_data("2025-01-15")

            assert "lunch" in day_data
            assert len(day_data["lunch"]) == 1
            assert day_data["lunch"][0]["product"] == "Рис"
            assert day_data["lunch"][0]["amount"] == 200
        finally:
            os.chdir(original_dir)
