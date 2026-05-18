import time
from pathlib import Path
from typing import Optional, Tuple

import pyautogui

from config import CURRENCY_CRAFT_COORDS


Coords = Tuple[int, int]

# Global baseline delay after every PyAutoGUI call
pyautogui.PAUSE = 0.05


def wait(extra: float = 0.0) -> None:
    if extra > 0:
        time.sleep(extra)


def send(text: str, extra_pause: float = 0.0) -> None:
    """
    Type literal text.
    """
    pyautogui.write(text, interval=0)
    wait(extra_pause)


def hotkey(*keys: str, extra_pause: float = 0.0) -> None:
    """
    Press a hotkey combo.
    """
    pyautogui.hotkey(*keys)
    wait(extra_pause)


def press(key: str, times: int = 1, extra_pause: float = 0.0) -> None:
    """
    Press a key multiple times.
    """
    pyautogui.press(key, presses=times, interval=0)
    wait(extra_pause)


def key_down_shift(extra_pause: float = 0.0) -> None:
    pyautogui.keyDown("shift")
    wait(extra_pause)


def key_up_shift(extra_pause: float = 0.0) -> None:
    pyautogui.keyUp("shift")
    wait(extra_pause)

def ctrl_alt_click(coords: Coords, extra_pause: float = 0.0, button: str = "left") -> None:
    """
    Ctrl + Alt + click.
    """
    pyautogui.keyDown("ctrl")
    pyautogui.keyDown("alt")
    try:
        pyautogui.moveTo(x=coords[0], y=coords[1],duration=0.1)
        pyautogui.click(x=coords[0], y=coords[1], button=button,interval=0.1)
    finally:
        pyautogui.keyUp("ctrl")
        pyautogui.keyUp("alt")

    wait(extra_pause)

def click(coords: Coords, extra_pause: float = 0.0, button: str = "left", confidence: float = 0.8, duration=0.1) -> None:
    """
    Mouse click.
    """
    pyautogui.moveTo(x=coords[0], y=coords[1],duration=duration)
    pyautogui.click(x=coords[0], y=coords[1], button=button,interval=duration)
    wait(extra_pause)

from typing import Optional, Iterable

def modified_click(
    coords: Coords,
    hotkeys: Optional[Iterable[str]] = None,
    button: str = "left",
    clicks: int = 1,
    move_duration: float = 0.1,
    click_interval: float = 0.1,
    extra_pause: float = 0.0,
) -> None:
    """
    Click with optional modifier keys.

    Examples:
        modified_click(coords)
        modified_click(coords, hotkeys=["ctrl"])
        modified_click(coords, hotkeys=["shift", "ctrl"])
        modified_click(coords, button="right")
    """

    hotkeys = list(hotkeys or [])

    for key in hotkeys:
        pyautogui.keyDown(key)

    try:
        pyautogui.moveTo(
            x=coords[0],
            y=coords[1],
            duration=move_duration
        )

        pyautogui.click(
            x=coords[0],
            y=coords[1],
            button=button,
            clicks=clicks,
            interval=click_interval
        )

    finally:
        for key in reversed(hotkeys):
            pyautogui.keyUp(key)

    wait(extra_pause)

def ctrl_click(coords: Coords, extra_pause: float = 0.0, button: str = "left") -> None:
    """
    Ctrl + click.
    """
    pyautogui.keyDown("ctrl")
    try:
        pyautogui.moveTo(x=coords[0], y=coords[1],duration=0.1)
        pyautogui.click(x=coords[0], y=coords[1], button=button,interval=0.1)
    finally:
        pyautogui.keyUp("ctrl")

    wait(extra_pause)

def move_mouse_from_view():
    pyautogui.moveTo(200, 1900)
    
from images.image_utils import locate_center
def click_image(
    image_path: str | Path,
    confidence: float = 0.9,
    extra_pause: float = 0.0,
    button: str = "left",
    grayscale: bool = True,
) -> bool:
    """
    Locate and click image.
    """
    coords = locate_center(
        image_path,
        confidence=confidence,
    )

    if coords is None:
        return False

    click(coords, extra_pause=extra_pause, button=button)
    return True

def ctrl_alt_click_image(
    image_path: str | Path,
    confidence: float = 0.9,
    extra_pause: float = 0.0,
    button: str = "left",
    grayscale: bool = True,
) -> bool:
    """
    Locate and Ctrl + Alt + click image.
    """
    coords = locate_center(
        image_path,
        confidence=confidence,
    )

    if coords is None:
        return False

    ctrl_alt_click(coords, extra_pause=extra_pause, button=button)
    return True