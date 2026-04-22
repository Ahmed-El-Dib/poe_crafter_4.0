from operator import is_

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
focus_window("Path of Exile")
time.sleep(1)
ITEM_CLASS = "Crimson Jewel"
CRAFTING_TAB = CURRENCY_TAB  # change if needed
CRAFTING_TAB_COORDS = locate_center(CURRENCY_TAB, confidence=0.8)
SRC_TAB = SOURCE_TAB_LAPOP  # change if needed

TARGETS = [
"Piercing",# one hand multi
"Rupturing", # two hand multi
"Vivid", # life
"Blunt", # staff speed
"Fencing", # sword speed
"of Potency", # global multi
"of Demolishing", # melee multi
"of the Phoenix", # max fire res
# "of the Krakenh", # max cold res    
# "of the Leviathan", # max lightning res
"of Zealousness", # fire dot multi
"of Exsanguinating", # physical dot multi

]





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
    pyautogui.leftClick()
    pyautogui.keyUp('ctrl')

    tab_coords = locate_center(tab_image, confidence=0.8)
    if not tab_coords:
        raise RuntimeError("Tab not found")

    pyautogui.moveTo(*tab_coords)
    pyautogui.click()


def move_to_crafter(coords):
    pyautogui.moveTo(*coords)
    pyautogui.click()

    tab_coords = locate_center(CURRENCY_TAB, confidence=0.8)
    if not tab_coords:
        raise RuntimeError("Currency tab not found")

    pyautogui.moveTo(*tab_coords)
    pyautogui.click()

    pyautogui.moveTo(*CURRENCY_CRAFT_COORDS)
    pyautogui.click()


# -----------------------------
# FIND ITEM IN GRID
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
# TARGET LOGIC
# -----------------------------
def count_maxroll_targets(mods):
    return sum(
        any(t.lower() in mod.get('name', '').lower() and is_max_roll(mod) for mod in mods)
        for t in TARGETS
    )

def count_targets_found(mods):

    return sum(
        any(t.lower() in mod.get('name', '').lower() for mod in mods)
        for t in TARGETS
    )

def is_max_roll(mod):
    if mod.get('max_roll') or mod.get('roll') is None:
        return True
    return False

# -----------------------------
# CRAFTING LOGIC
# -----------------------------

spamming = False
alts = 0
aug = 0
scoures = 0
exalts = 0
regals = 0
annuls = 0



def spam_alt():
    global alts
    if alts >= 14400:
        print("Alt limit reached, exiting.")
        exit()
    alts += 1
    spam_currency(ALT)

def use_alt():
    global alts
    if alts >= 4300:
        print("Alt limit reached, exiting.")
        exit()
    alts += 1
    if alts > 0:
        use_currency(ALT, spammable=True)
    elif alts > 700:
        use_currency(ALT_2, spammable=True)
    else:
        use_currency(ALT_3, spammable=True)


def determine_next_action_base_jewel(mods, max_roll = True):
    global spamming
    global alts, scoures, exalts, regals, annuls
    num_mods = len(mods)
    if max_roll:
        num_targets = count_maxroll_targets(mods)
    else:
        num_targets = count_targets_found(mods)

    # open_suffix = sum(mod.get('type') == 'suffix' for mod in mods) == 1
    # open_prefix = sum(mod.get('type') == 'prefix' for mod in mods) == 1
    
    # --- complete ---
    if num_targets == 2:
            pyautogui.keyUp('shift')
            spamming = False
            return "DONE"

    # --- rarity ---
    if num_mods == 0:
        rarity = "normal"
    elif num_mods < 3:
        rarity = "magic"
    else:
        rarity = "rare"

    # --- normal ---
    if rarity == "normal":
        spamming = False
        use_currency(TRANS)
        return "CONTINUE"

    # --- rare ---
    if rarity == "rare":
        spamming = False
        use_currency(SCOURE)
        return "CONTINUE"
    
    # --- magic ---
    if rarity == "magic":

        if num_targets == 0:
            if spamming:
               spam_alt()
            else:
                spamming = True
                use_alt()

        elif num_targets == 1 and num_mods == 1:
            if spamming:
                alt_currency(AUG)
            else:
                spamming = False
                use_currency(AUG)

        elif num_targets == 1 and num_mods == 2:
            if spamming:
                spam_alt()
            else:
                spamming = True
                use_alt()

        return "CONTINUE"

    

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

        # Craft loop
        while True:
            mods = parse_item_mods(CURRENCY_CRAFT_COORDS)
            result = determine_next_action_base_jewel(mods)
        
            if result == "DONE":
                break

        idx = advance_idx(idx)

    print("Finished all items.")


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":
    main()