import pyautogui
import time

from currency_manager import CurrencyManager
from macros.currency_macros import *
from macros.item_parser import parse_item_mods, copy_item
from images.image_utils import locate_center
from images.img_paths import *
from laptop_config import *
from focus_window import focus_window


# -----------------------------
# CONFIG
# -----------------------------

focus_window("Path of Exile")
START_COORDS = (28, 147)
TILE_WIDTH = 26
CRAFTING_TAB = CURRENCY_TAB
CRAFTING_TAB_COORDS = locate_center(CURRENCY_TAB, confidence=0.8)
SRC_TAB = SOURCE_TAB


ITEM_CLASS = "Abyss Jewel"

TARGET = ["of the Lightning Rod"]
# TARGET = ["Stalwart"]
SUFFIXES = ["of the Lightning Rod","of Potency","of the Assassin","of Opportunity","of Arcing", "of Glaciation","of Ashes"]
PREFIXES =["Electrocuting","Cremating","Entombing","Stalwart","Expediting"]
# TARGET_TYPE = "any" #prefix, suffix or any
cm = CurrencyManager(max_alts=2000)  # Initialize currency manager with default limits




# Force exit
from pynput import keyboard
import os
def on_press(key):
    global running
    if key == keyboard.Key.esc:
        pyautogui.keyUp('shift')
        print("Stopping...")
        os._exit(0)

listener = keyboard.Listener(on_press=on_press)
listener.start()


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

            if ITEM_CLASS.lower() in text.lower():
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

def count_prefixes(mods):
    return sum(1 for mod in mods if mod.get('type') == 'prefix' and any(prefix in mod.get('name', '') for prefix in PREFIXES))
def count_suffixes(mods):
    return sum(1 for mod in mods if mod.get('type') == 'suffix' and any(suffix in mod.get('name', '') for suffix in SUFFIXES))    
def count_good_mods(mods):
    # look in either target_prefixes or target_suffixes
    return count_prefixes(mods) + count_suffixes(mods)
def target_found(mods):
    return any(target in mod.get('name', '') for mod in mods for target in TARGET)

def open_suffix(mods):
    if len(mods) <= 2:
        return sum(mod.get('type') == 'suffix' for mod in mods) == 0
    return sum(mod.get('type') == 'suffix' for mod in mods) == 1 
def open_prefix(mods):
    if len(mods) <= 2:
        return sum(mod.get('type') == 'prefix' for mod in mods) == 0
    return sum(mod.get('type') == 'prefix' for mod in mods) == 1

def determine_next_action(mods):
    num_mods = len(mods)
    # ✅ Target found
    if target_found(mods) or count_good_mods(mods) >= 3:
        print("Target  found! Stopping.")
        return "DONE"
    # if count_good_mods(mods) >= 2:
    #     print("found 2 targeets, done")
    #     return "DONE"
    
    if num_mods == 4:
        cm.scoure()
        return

    if num_mods >= 3:
        if count_good_mods(mods) == 0:
            cm.scoure()
            return
        else:
            cm.slam()
            return

    if num_mods == 0:
        cm.trans()
        return
    
    if num_mods == 1:
        cm.aug()
        return
    
    if count_good_mods(mods) > 0:
        if num_mods == 2:
            cm.regal()
            return
    else: 
        cm.alt()
        return
    


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
        craft_item(determine_next_action, parse_item_mods)

        idx = advance_idx(idx)

    print("Finished all items.")


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":
    main()