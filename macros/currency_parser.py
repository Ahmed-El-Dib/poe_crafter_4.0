import re
import time
from typing import Optional
from pywinauto import mouse
import pyautogui
import pyperclip    

def copy_item() -> str:
    pyperclip.copy("")
    pyautogui.hotkey("ctrl", "alt", "c")
    return pyperclip.paste()


def parse_stack_count(line: str) -> Optional[int]:
    match = re.search(r"Stack Size:\s*([\d,]+)\s*/\s*[\d,]+", line)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def normalize_currency_name(raw_name: str) -> str:
    mapping = {
        "Orb of Alteration": "alteration",
        "Orb of Augmentation": "augment",
        "Orb of Transmutation": "transmute",
        "Exalted Orb": "exalt",
        "Orb of Scouring": "scoure",
        "Orb of Annulment": "annul",
        "Regal Orb": "regal",
    }
    return mapping.get(raw_name, raw_name.lower())


def read_currency(description: str) -> Optional[dict]:
    lines = [l.strip() for l in description.strip().splitlines() if l.strip()]

    if "Item Class: Stackable Currency" not in lines:
        return None

    name = None
    count = None

    for i, line in enumerate(lines):
        if line == "Rarity: Currency" and i + 1 < len(lines):
            name = normalize_currency_name(lines[i + 1])

        c = parse_stack_count(line)
        if c is not None:
            count = c

    if name is None or count is None:
        return None

    return {
        "name": name,
        "count": count
    }


def parse_currency(coords):
    pyautogui.moveTo(*coords,duration=0.2)
    time.sleep(0.1)
    description = copy_item()
    return read_currency(description)