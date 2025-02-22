import os
import platform
import sys


def normalize_path(path):
    """Нормализует путь в зависимости от операционной системы"""
    if platform.system() == "Windows":
        return path.replace("/", "\\")
    return path.replace("\\", "/")


def get_resource_path(relative_path):
    """Получает абсолютный путь к ресурсу"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    full_path = os.path.join(base_path, "resources", relative_path)
    return normalize_path(full_path)
