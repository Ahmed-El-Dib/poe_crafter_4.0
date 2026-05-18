import os
import pyautogui
from functools import wraps
from pynput import keyboard

from focus_window import focus_window


_listener = None


def on_press(key):
    if key == keyboard.Key.backspace:
        pyautogui.keyUp("shift")
        print("Stopping...")
        os._exit(0)


def ensure_exit_listener() -> bool:
    global _listener

    if _listener is not None:
        return True

    _listener = keyboard.Listener(on_press=on_press)
    _listener.daemon = True
    _listener.start()
    return True


def requires_game_ready(window_title: str = "Path of Exile"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not ensure_exit_listener():
                return False

            if not focus_window(window_title):
                return False

            return func(*args, **kwargs)

        return wrapper

    return decorator