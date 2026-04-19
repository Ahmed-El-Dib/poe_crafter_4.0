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
ITEM_CLASS = "Cluster Jewels"
CRAFTING_TAB = CURRENCY_TAB  # change if needed
CRAFTING_TAB_COORDS = locate_center(CURRENCY_TAB, confidence=0.8)
SRC_TAB = SOURCE_TAB_LAPOP  # change if needed

CLUSTER_TARGETS = [

"fuel the fight",
"surefooted striker",
"feed the fury",
"martial prowess",
"brutal infamy",
"calamitous",
# "titanic swings",
# "graceful execution",
# "heavy hitter",
"smite the weak",
"overlord",
]

VALUABLE_COMBOS = [
    ("Calamitous", "Feed the Fury", "Martial Prowess"),
    # ("Calamitous", "Feed the Fury", "Heavy Hitter"),
    # ("Calamitous", "Feed the Fury", "Smite the Weak"),
    ("Calamitous", "Fuel the Fight", "Martial Prowess"),
    # ("Calamitous", "Titanic Swings", "Smite the Weak"),
    ("Calamitous", "Titanic Swings", "Martial Prowess"),
    ("Calamitous", "Surefooted Striker", "Martial Prowess"),
    ("Calamitous", "Surefooted Striker", "Heavy Hitter"),
    ("Calamitous", "Surefooted Striker", "Smite the Weak"),
    ("Surefooted Striker", "Feed the Fury", "Martial Prowess"),
    ("Surefooted Striker", "Feed the Fury", "Heavy Hitter"),
    ("Surefooted Striker", "Feed the Fury", "Smite the Weak"),
    ("feed the fury", "martial prowess", "Fuel the Fight"),
    ("feed the fury", "titanic swings", "martial prowess"),
    ("Brutal Infamy", "Feed the Fury", "Martial Prowess"),
    ("Brutal Infamy", "Feed the Fury", "Heavy Hitter"),
    ("Brutal Infamy", "Feed the Fury", "Smite the Weak"),
    ("Drive the destruction", "Feed the Fury", "Martial Prowess"),
    ("feed the fury", "graceful execution", "martial prowess"),
    ("feed the fury", "Fearsome Warrior", "martial prowess"),
    ("feed the fury", "Fearsome Warrior", "Heavy Hitter"),
    ("feed the fury", "Fearsome Warrior", "martial prowess"),
    ("feed the fury", "Fearsome Warrior", "Smite the weak"),
    ("feed the fury", "Titanic swings", "Smite the weak"),
    ("Surefooted Striker", "Brutal Infamy", "Martial Prowess"),
    ("Surefooted Striker", "Brutal Infamy", "Heavy Hitter"),
    # ("Surefooted Striker", "Brutal Infamy", "Smite the Weak"),
    ("Calamitous", "Brutal Infamy", "Martial Prowess"),
    # ("Calamitous", "Brutal Infamy", "Heavy Hitter"),
    # ("Calamitous", "Brutal Infamy", "Smite the Weak"),
    ("Titanic Swings", "Fearsome Warrior", "martial prowess"),
    ("Titanic Swings", "Fearsome Warrior", "Heavy Hitter"),
    ("Titanic Swings", "Fearsome Warrior", "Smite the weak"),
    ("Surefooted Striker", "Fuel the Fight", "Martial Prowess"),
    ("Surefooted Striker", "Fuel the Fight", "Heavy Hitter"),
    ("Surefooted Striker", "Fuel the Fight", "Smite the Weak"),
    ("Calamitous", "Fuel the Fight", "Martial Prowess"),
    # ("Calamitous", "Fuel the Fight", "Heavy Hitter"),
    ("Calamitous", "Fuel the Fight", "Smite the Weak"),
    # ("feed the fury", "Fuel the Fight", "Heavy Hitter"),
    ("feed the fury", "Fuel the Fight", "martial prowess"),
    # ("feed the fury", "Fuel the Fight", "Smite the weak"),
]

GOOD_TO_SLAM = ["overlord"]

def is_good_to_slam(mods):
    return any(
        any(g.lower() in mod.get('text', '').lower() for mod in mods)
        for g in GOOD_TO_SLAM
    )


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

            if f"Large Cluster Jewel".lower() in text.lower():
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

def count_targets_found(mods):
    return sum(
        any(t.lower() in mod.get('text', '').lower() for mod in mods)
        for t in CLUSTER_TARGETS
    )


def any_valuable_combo_found(mods):
    for combo in VALUABLE_COMBOS:
        if all(
            any(t.lower() in mod.get('text', '').lower() for mod in mods)
            for t in combo
        ):
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

def slam():
    global exalts
    if exalts >= 590:
        print("Exalt limit reached, exiting.")
        exit()
    exalts += 1
    use_currency(EXALT)
    print(parse_item_mods(CURRENCY_CRAFT_COORDS))
 

def scoure():
    global scoures
    if scoures >= 1400:
        print("Scoure limit reached, exiting.")
        exit()
    scoures += 1
    use_currency(SCOURE)

def annul():
    global annuls
    if annuls >= 60:
        print("Annul limit reached, exiting.")
        exit()
    annuls += 1
    use_currency(ANNUL)

def spam_alt():
    max_alts = 5000
    global alts
    if alts >= max_alts:
        print("Alt limit reached, exiting.")
        exit()
    alts += 1
    spam_currency(ALT)

def use_alt():
    max_alts = 5000
    global alts
    if alts >= max_alts:
        print("Alt limit reached, exiting.")
        exit()
    alts += 1
    if alts > 0:
        use_currency(ALT, spammable=True)
    elif alts > max_alts-4950:
        use_currency(ALT_2, spammable=True)
    else:
        use_currency(ALT_3, spammable=True)

def regal():
    global regals
    if regals >= 1680:
        print("Regal limit reached, exiting.")
        exit()
    regals += 1
    use_currency(REGAL)

def determine_action_clusters(mods):
    global spamming
    global alts, scoures, exalts, regals, annuls
    num_mods = len(mods)
    num_targets = count_targets_found(mods)

    open_suffix = sum(mod.get('type') == 'suffix' for mod in mods) == 1
    open_prefix = sum(mod.get('type') == 'prefix' for mod in mods) == 1

    

    # --- rarity ---
    if num_mods == 0:
        rarity = "normal"
    elif num_mods <= 2:
        rarity = "magic"
    else:
        rarity = "rare"

    # --- normal ---
    if rarity == "normal":
        spamming = False
        use_currency(TRANS)
        return "CONTINUE"

    # --- magic ---
    if rarity == "magic":
        if is_good_to_slam(mods):
            print("✅ Good to slam found at magic tier!")
            return "DONE"
        
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

        else:
            spamming = False
            regal()
        return "CONTINUE"

    # --- rare ---
    if rarity == "rare":
        print()
        spamming = False

        if any_valuable_combo_found(mods) or (is_good_to_slam(mods) and num_targets == 3):
            print("✅ Valuable combo found!")
            return "DONE"
        
        #handle annull first
        if num_mods == 4:
            if is_good_to_slam(mods) and num_targets == 2:
                print("annuling")
                annul()
                return "CONTINUE"
            

        #handle slam
        if num_targets == 2: # only slam if have 2 targets
            if is_good_to_slam(mods) and open_suffix:
                slam()
            elif open_prefix:
                slam()
            else:     
                scoure()
                return "CONTINUE"
        
        else:
            scoure()
        
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
            result = determine_action_clusters(mods)
        
            if result == "DONE":
                break

        idx = advance_idx(idx)

    print("Finished all items.")


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":
    main()