from pywinauto.keyboard import send_keys
import time
from pywinauto import mouse
import pywinauto

import mss, pyautogui
from PIL import Image

from config import CURRENCY_CRAFT_COORDS

def send(sequence: str, pause: float = 0.2, *, literal: bool = False, with_spc=True) -> None:
    """
    literal=True  → treat sequence as literal text
    literal=False → treat sequence as SendKeys syntax
    """

    seq = sequence

    if literal:
        # Escape ALL SendKeys metacharacters
        replacements = {
            "+": "{+}",
            "%": "{%}",
            "^": "{^}",
            "~": "{~}",
        }
        for k, v in replacements.items():
            seq = seq.replace(k, v)

    send_keys(seq, with_spaces=with_spc)

    if pause and pause > 0:
        time.sleep(pause)


def press(sequence: str, times: int = 1, pause: float = 0.1):
    """
    Press a pywinauto key sequence N times.
    Example sequences:
        '{TAB}'
        '+{TAB}'
        '{DOWN}'
        '{UP}'
        '{ENTER}'
        '^c'
    """
    for _ in range(times):
        send(sequence, pause=pause)

def key_down_shift() -> None:
    send_keys("{VK_LSHIFT down}", pause=0.1)

def key_up_shift() -> None:
    send_keys("{VK_LSHIFT up}", pause=0.1)

def click(coords: tuple, pause: float = 0, button: str = "left"):
    """
    Basic mouse click primitive.

    coords: (x, y) tuple on the screen
    pause:  delay after click
    clicks: number of clicks (1=single, 2=double)
    button: 'left' or 'right'
    """
    pyautogui.moveTo(coords[0], coords[1],duration=0.01  )
    mouse.click(coords=coords, button=button)
    if pause > 0:
        time.sleep(pause)

def ctrl_click(coords: tuple, pause: float = 0.1, button: str = "left"):
    """
    Ctrl + mouse click primitive.

    coords: (x, y) tuple on the screen
    pause:  delay after click
    clicks: number of clicks (1=single, 2=double)
    button: 'left' or 'right'
    """
    with pywinauto.keyboard.KeyAction("ctrl"):
        mouse.click(coords=coords, button=button)
        if pause > 0:
            time.sleep(pause)

def locate_center(image_path, confidence=0.9):
    """
    Returns (x, y) center of image OR None.
    """
    template = Image.open(image_path)

    with mss.mss() as sct:
        for mon in sct.monitors[1:]:
            scr = sct.grab(mon)
            screenshot = Image.frombytes("RGB", (mon["width"], mon["height"]), scr.rgb)

            try:
                loc = pyautogui.locate(template, screenshot, confidence=confidence)
            except Exception:
                loc = None

            if loc:
                cx = mon["left"] + loc.left + loc.width // 2
                cy = mon["top"] + loc.top + loc.height // 2
                return (cx, cy)

    return None

def click_image(image_path, confidence=0.9, pause=0.2, button="left"):
    """
    Locate an image on the screen and click its center.
    Returns True if found and clicked, False otherwise.
    """
    coords = locate_center(image_path, confidence)
    if coords:
        click(coords, pause=pause, button=button)
        return True
    return False



