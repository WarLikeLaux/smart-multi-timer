import platform
import os
import time
import threading
import pygame
from pygame import mixer
import subprocess

if platform.system() == "Windows":
    import winsound


class SoundPlayer:
    def __init__(self):
        self.system = platform.system()
        self.init_mixer()
        self.is_playing = False
        self.stop_flag = False

    def init_mixer(self):
        if not mixer.get_init():
            try:
                mixer.init()
            except Exception as e:
                print(f"Ошибка инициализации mixer: {e}")

    def play_beep(self, frequency=1000, duration=1000):
        self.is_playing = True
        self.stop_flag = False
        
        if self.system == "Windows":
            try:
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
                
        if not self.stop_flag:
            self.is_playing = False
                
    def stop(self):
        self.stop_flag = True
        self.is_playing = False
        
        try:
            if mixer.get_init():
                mixer.music.stop()
                mixer.stop()
                mixer.quit()
        except:
            pass
            
        try:
            mixer.init()
            mixer.music.stop()
            mixer.stop()
            mixer.quit()
        except:
            pass

    def play_notification(self):
        if self.system == "Windows":
            try:
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
        try:
            if mixer.get_init():
                sound = mixer.Sound(sound_file)
                sound.play()
            else:
                self.play_notification()
        except Exception as e:
            print(f"Ошибка воспроизведения звука: {e}")
            self.play_notification()
