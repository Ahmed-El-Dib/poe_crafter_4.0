import pyautogui
import time

from macros.currency_macros import *
from macros.item_parser import parse_item_mods, copy_item
from images.image_utils import locate_center
from images.img_paths import *
from config import *
from focus_window import focus_window


# -----------------------------
# CONFIG
# -----------------------------
START_COORDS = (28, 147)
TILE_WIDTH = 26

ITEM_CLASS = "Large Cluster Jewel"
CRAFTING_TAB = CURRENCY_TAB
CRAFTING_TAB_COORDS = locate_center(CURRENCY_TAB, confidence=0.8)
SRC_TAB = SOURCE_TAB

TARGET = "Primordial Bond"


# -----------------------------
# STASH NAVIGATION
# -----------------------------

def clear_crafting_area_and_move_to_tab(tab_image):
    pyautogui.moveTo(*CRAFTING_TAB_COORDS)
    pyautogui.leftClick()

    pyautogui.moveTo(*CURRENCY_CRAFT_COORDS)
    pyautogui.keyDown('ctrl')
    time.sleep(0.1)
    pyautogui.leftClick()
    pyautogui.keyUp('ctrl')

    tab_coords = locate_center(tab_image, confidence=0.8)
    if not tab_coords:
        raise RuntimeError("Tab not found")

    pyautogui.moveTo(*tab_coords)
    pyautogui.leftClick()


def move_to_crafter(coords):
    pyautogui.moveTo(*coords)
    pyautogui.leftClick()


    pyautogui.moveTo(*CRAFTING_TAB_COORDS)
    pyautogui.leftClick()

    pyautogui.moveTo(*CURRENCY_CRAFT_COORDS)
    pyautogui.leftClick()


# -----------------------------
# FIND ITEM
# -----------------------------

def find_item(item_class, idx):
    x0 = START_COORDS[0] + idx[0] * TILE_WIDTH
    y0 = START_COORDS[1] + idx[1] * TILE_WIDTH

    for col in range(24):
        for row in range(24):
            x = x0 + col * TILE_WIDTH
            y = y0 + row * TILE_WIDTH

            pyautogui.moveTo(x, y)
            time.sleep(0.02)

            text = copy_item()
            if not text:
                continue

            if "Large Cluster Jewel".lower() in text.lower():
                print(f"Found {item_class} at ({x},{y})")
                move_to_crafter((x, y))
                return True

    return False


def get_item(item_class, tab_image, idx):
    clear_crafting_area_and_move_to_tab(tab_image)
    return find_item(item_class, idx)


# -----------------------------
# CRAFTING LOGIC (SINGLE TARGET)
# -----------------------------

spamming = False

def determine_action_single_suffix(mods):
    global spamming

    # ✅ Target found
    if any(TARGET.lower() in mod.get('text', '').lower() for mod in mods):
        print(f"✅ Found {TARGET}")
        pyautogui.keyUp('shift')  # release shift if it was held down
        spamming = False
        time.sleep(0.1)
        return "DONE"

    has_prefix = any(mod.get('type') == 'prefix' for mod in mods)
    has_suffix = any(mod.get('type') == 'suffix' for mod in mods)

    # Case 1: prefix only
    if has_prefix and not has_suffix:
        if spamming:
            alt_currency(AUG)
        else:
            spamming = False
            use_currency(AUG)

    # Case 2: has suffix
    elif has_suffix:
        if spamming:
            spam_currency(ALT)
        else:
            spamming = True
            use_currency(ALT, spammable=True)

    return "CONTINUE"


# -----------------------------
# GENERIC CRAFT RUNNER
# -----------------------------

def craft_item(craft_fn, parse_fn):
    while True:
        mods = parse_fn(CURRENCY_CRAFT_COORDS)
        result = craft_fn(mods)

        if result == "DONE":
            return


# -----------------------------
# INDEX HANDLING
# -----------------------------

def advance_idx(idx):
    idx[1] += 1
    if idx[1] >= 24:
        idx[1] = 0
        idx[0] += 1
    return idx


def is_done(idx):
    return idx[0] >= 24


# -----------------------------
# MAIN LOOP
# -----------------------------

def main():
    focus_window("Path of Exile")

    idx = [0, 0]

    while not is_done(idx):
        print(f"Searching at idx {tuple(idx)}")

        found = get_item(ITEM_CLASS, SRC_TAB, tuple(idx))
        if not found:
            print("No more items found. Stopping.")
            break

        # 🔥 Use your single-target crafter
        craft_item(determine_action_single_suffix, parse_item_mods)

        idx = advance_idx(idx)

    print("Finished all items.")


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":
    main()