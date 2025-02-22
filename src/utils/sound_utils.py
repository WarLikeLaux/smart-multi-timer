import platform
import subprocess

from pygame import mixer


class SoundPlayer:
    def __init__(self):
        self.system = platform.system()
        self.init_mixer()

    def init_mixer(self):
        if not mixer.get_init():
            try:
                mixer.init()
            except Exception as e:
                print(f"Ошибка инициализации mixer: {e}")

    def play_beep(self, frequency=1000, duration=1000):
        """
        Воспроизводит звуковой сигнал
        frequency - частота (только для Windows)
        duration - длительность в миллисекундах
        """
        if self.system == "Windows":
            try:
                import winsound

                winsound.Beep(frequency, duration)
            except ImportError:
                print("\a")
        else:
            try:
                subprocess.run(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"]
                )
            except:
                print("\a")

    def play_notification(self):
        """Воспроизводит звук уведомления"""
        if self.system == "Windows":
            try:
                import winsound

                winsound.MessageBeep()
            except ImportError:
                print("\a")
        else:
            try:
                subprocess.run(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/message.oga"]
                )
            except:
                print("\a")

    def play_custom_sound(self, sound_file):
        """Воспроизводит пользовательский звуковой файл"""
        try:
            if mixer.get_init():
                sound = mixer.Sound(sound_file)
                sound.play()
            else:
                self.play_notification()
        except Exception as e:
            print(f"Ошибка воспроизведения звука: {e}")
            self.play_notification()
