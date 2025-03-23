import os

from utils.resource_path import get_resource_path

RESOURCES_DIR = get_resource_path("")
IMAGES_DIR = os.path.join(RESOURCES_DIR, "images")
SOUNDS_DIR = os.path.join(RESOURCES_DIR, "sounds")

IMAGES = {
    "LEFT_IMAGE": os.path.join(IMAGES_DIR, "2.jpeg"),
    "RIGHT_IMAGE": os.path.join(IMAGES_DIR, "1.jpeg"),
    "TRAY_ICON": os.path.join(IMAGES_DIR, "tray_icon.ico"),
}

SOUNDS = {
    "HABIT_NOTIFICATION": os.path.join(SOUNDS_DIR, "habit.mp3"),
}
