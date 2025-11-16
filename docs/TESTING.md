# Руководство по тестированию Smart Multi-Timer

> Инструкции по написанию и запуску тестов для проекта

---

## 📋 Содержание

- [Общая информация](#-общая-информация)
- [Запуск тестов](#-запуск-тестов)
- [Структура тестов](#-структура-тестов)
- [Написание тестов](#-написание-тестов)
- [Лучшие практики](#-лучшие-практики)
- [Покрытие кодом](#-покрытие-кодом)

---

## 🎯 Общая информация

### Что тестируется?

В проекте Smart Multi-Timer мы тестируем:

1. **Бизнес-логику** (Storage классы, вычисления)
2. **Утилиты** (helpers, converters)
3. **Модели данных** (если есть сложная логика)

### Что НЕ тестируется напрямую?

- **Tkinter UI компоненты** — сложно и не приносит большой пользы
- **Интеграции с системным треем** — требует реальную ОС
- **Звуковые уведомления** — требует звуковую карту

### Используемые инструменты

- **pytest** — фреймворк для тестирования
- **unittest** — встроенная библиотека Python (опционально)

---

## 🚀 Запуск тестов

### Быстрый старт

```bash
# Linux/macOS
make test

# Windows
main.bat
# Выберите опцию "3. Запустить тесты"
```

### Ручной запуск

```bash
# Установить pytest (если еще не установлен)
pip install pytest

# Запустить все тесты
pytest tests/

# Запустить конкретный файл
pytest tests/test_calorie_storage.py

# Запустить с подробным выводом
pytest tests/ -v

# Запустить с покрытием кода
pytest tests/ --cov=src --cov-report=html
```

### Запуск из Python

```bash
python -m pytest tests/
```

---

## 📂 Структура тестов

```
smart-multi-timer/
├── src/                    # Исходный код
│   ├── tabs/
│   │   ├── calorie_storage.py
│   │   └── ...
│   └── utils/
│       └── ...
├── tests/                  # Директория тестов
│   ├── __init__.py
│   ├── test_calorie_storage.py  # Тесты для CalorieStorage
│   ├── test_utils.py            # Тесты для утилит
│   └── conftest.py              # Общие fixtures (если нужны)
└── pytest.ini              # Конфигурация pytest (опционально)
```

### Именование файлов и функций

- **Файлы тестов**: `test_*.py` или `*_test.py`
- **Классы тестов**: `Test*` (например, `TestCalorieStorage`)
- **Функции тестов**: `test_*` (например, `test_add_product`)

---

## 📝 Написание тестов

### Базовый пример

```python
# tests/test_calorie_storage.py
import pytest
import json
import os
from src.tabs.calorie_storage import CalorieStorage


class TestCalorieStorage:
    """Тесты для класса CalorieStorage"""

    @pytest.fixture
    def storage(self, tmp_path):
        """Создает временное хранилище для тестов"""
        # tmp_path - временная директория pytest
        test_file = tmp_path / "test_calories.json"
        storage = CalorieStorage(str(test_file))
        yield storage
        # Очистка после теста
        if test_file.exists():
            test_file.unlink()

    def test_add_product(self, storage):
        """Тест добавления продукта в базу"""
        storage.add_product_to_db(
            name="Яблоко",
            calories=52,
            protein=0.3,
            fat=0.2,
            carbs=14
        )

        products = storage.get_all_products()
        assert "Яблоко" in products
        assert products["Яблоко"]["calories"] == 52

    def test_calculate_meal_calories(self, storage):
        """Тест расчёта калорий приёма пищи"""
        storage.add_product_to_db("Рис", calories=130)
        storage.add_meal_entry(
            date="2025-01-01",
            meal_type="breakfast",
            product="Рис",
            amount=100,
            is_grams=True
        )

        total = storage.get_meal_total_calories("2025-01-01", "breakfast")
        assert total == 130
```

### Тестирование исключений

```python
def test_invalid_product_raises_error(self, storage):
    """Тест на ошибку при несуществующем продукте"""
    with pytest.raises(ValueError):
        storage.add_meal_entry(
            date="2025-01-01",
            meal_type="breakfast",
            product="НесуществующийПродукт",
            amount=100
        )
```

### Параметризованные тесты

```python
@pytest.mark.parametrize("calories,protein,fat,carbs", [
    (100, 10, 5, 15),
    (200, 20, 10, 30),
    (50, 5, 2, 7),
])
def test_macros_calculation(self, storage, calories, protein, fat, carbs):
    """Тест расчёта макронутриентов с разными значениями"""
    storage.add_product_to_db(
        name="Продукт",
        calories=calories,
        protein=protein,
        fat=fat,
        carbs=carbs
    )

    macros = storage.get_product_macros("Продукт")
    assert macros["protein"] == protein
    assert macros["fat"] == fat
    assert macros["carbs"] == carbs
```

---

## ✅ Лучшие практики

### 1. Используйте временные файлы

```python
@pytest.fixture
def temp_storage(tmp_path):
    """Всегда используйте tmp_path для тестовых файлов"""
    test_file = tmp_path / "test_data.json"
    storage = CalorieStorage(str(test_file))
    yield storage
    # Автоматическая очистка
```

### 2. Один тест = одна проверка

```python
# ✅ ХОРОШО
def test_add_product_creates_entry(self, storage):
    storage.add_product_to_db("Молоко", calories=60)
    assert "Молоко" in storage.get_all_products()

def test_add_product_stores_calories(self, storage):
    storage.add_product_to_db("Молоко", calories=60)
    assert storage.get_product("Молоко")["calories"] == 60

# ❌ ПЛОХО - слишком много проверок в одном тесте
def test_add_product(self, storage):
    storage.add_product_to_db("Молоко", calories=60)
    assert "Молоко" in storage.get_all_products()
    assert storage.get_product("Молоко")["calories"] == 60
    assert storage.get_product("Молоко")["protein"] == 0
    # ... ещё 10 проверок
```

### 3. Явные имена тестов

```python
# ✅ ХОРОШО - понятно что тестируется
def test_add_meal_entry_increases_day_total_calories(self, storage):
    ...

def test_remove_product_deletes_from_all_meals(self, storage):
    ...

# ❌ ПЛОХО - неясно что тестируется
def test_meal(self, storage):
    ...

def test_product_removal(self, storage):
    ...
```

### 4. Arrange-Act-Assert паттерн

```python
def test_example(self, storage):
    # Arrange (Подготовка)
    storage.add_product_to_db("Хлеб", calories=250)

    # Act (Действие)
    storage.add_meal_entry("2025-01-01", "breakfast", "Хлеб", 100, True)

    # Assert (Проверка)
    total = storage.get_day_total_calories("2025-01-01")
    assert total == 250
```

### 5. Не тестируйте детали реализации

```python
# ✅ ХОРОШО - тестируем публичный интерфейс
def test_storage_persists_data(self, storage):
    storage.add_product_to_db("Сыр", calories=360)
    storage.save()

    new_storage = CalorieStorage(storage.filepath)
    assert "Сыр" in new_storage.get_all_products()

# ❌ ПЛОХО - тестируем детали реализации
def test_internal_data_structure(self, storage):
    storage.add_product_to_db("Сыр", calories=360)
    assert storage._data["products"]["Сыр"]["calories"] == 360  # НЕ ДЕЛАЙТЕ ТАК!
```

---

## 📊 Покрытие кодом

### Установка coverage

```bash
pip install pytest-cov
```

### Запуск с покрытием

```bash
# Простой отчёт в терминале
pytest tests/ --cov=src

# HTML отчёт (откроется в браузере)
pytest tests/ --cov=src --cov-report=html
# Откройте htmlcov/index.html
```

### Целевые показатели

- **Бизнес-логика (Storage, Utils)**: 80%+ покрытие
- **UI компоненты**: не требуется (тестируются вручную)
- **Общий проект**: 50%+ покрытие

---

## 🛠️ Конфигурация pytest

Создайте `pytest.ini` в корне проекта:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Опции по умолчанию
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings

# Маркеры для группировки тестов
markers =
    slow: медленные тесты
    integration: интеграционные тесты
    unit: юнит-тесты
```

### Использование маркеров

```python
import pytest

@pytest.mark.unit
def test_fast_calculation():
    assert 2 + 2 == 4

@pytest.mark.slow
def test_large_dataset_processing():
    # Долгий тест
    pass
```

Запуск только быстрых тестов:
```bash
pytest tests/ -m "not slow"
```

---

## 🐛 Отладка тестов

### Использование print()

```python
def test_debug_example(self, storage):
    storage.add_product_to_db("Тест", calories=100)
    print(f"Products: {storage.get_all_products()}")  # Выведется при -s
    assert "Тест" in storage.get_all_products()
```

Запуск с выводом print:
```bash
pytest tests/ -s
```

### Использование pdb (отладчик)

```python
def test_with_breakpoint(self, storage):
    storage.add_product_to_db("Тест", calories=100)

    import pdb; pdb.set_trace()  # Точка остановки

    assert "Тест" in storage.get_all_products()
```

Или используйте встроенный `breakpoint()` (Python 3.7+):
```python
def test_with_breakpoint(self, storage):
    breakpoint()  # Современный способ
    ...
```

---

## 📚 Дополнительные ресурсы

### Документация

- [pytest документация](https://docs.pytest.org/)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

### Полезные плагины

```bash
pip install pytest-xdist    # Параллельный запуск тестов
pip install pytest-timeout  # Таймауты для тестов
pip install pytest-mock     # Удобные моки
```

---

## 🤝 Участие в разработке

При добавлении новых фич:

1. **Напишите тесты ПЕРЕД кодом** (TDD подход - опционально)
2. **Убедитесь что все тесты проходят** перед коммитом
3. **Добавьте тесты для новой функциональности**
4. **Обновите эту документацию** если меняется структура

---

## ❓ FAQ

**Q: Нужно ли тестировать Tkinter виджеты?**
A: Нет, тестируйте только бизнес-логику. UI тестируется вручную.

**Q: Как тестировать файловые операции?**
A: Используйте `tmp_path` fixture от pytest для временных файлов.

**Q: Что делать если тест падает только на CI/CD?**
A: Проверьте зависимости от ОС, используйте `platform.system()` checks.

**Q: Как запустить только один тест?**
A: `pytest tests/test_file.py::TestClass::test_method`

---

<div align="center">

**Сделано с ❤️ для Smart Multi-Timer**

[⬆ Наверх](#руководство-по-тестированию-smart-multi-timer)

</div>
