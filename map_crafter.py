from operator import is_

import pyautogui
import time

from macros.currency_macros import *
from macros.map_parser import parse_map_mods, copy_item
from images.image_utils import locate_center
from images.img_paths import *
from config import *
from focus_window import focus_window


# -----------------------------
# CONFIG
# -----------------------------


ITEM_CLASS = "Map"
CRAFTING_TAB = CURRENCY_TAB  # change if needed
CRAFTING_TAB_COORDS = locate_center(CURRENCY_TAB, confidence=0.7)
SRC_TAB = SOURCE_TAB_LAPOP  # change if needed


from utils.initiate_session import requires_game_ready


MAP_SUFFIX_TARGETS = [
    "of Collection",
    "of Splinters",
    "of Defiance",
    "of Imbibing",
    "of Persistence",
    "of Decaying"
]

MAP_PREFIX_TARGETS = [
    "Antagonist's",
    "Diluted",
    "Hungering",
    "Punishing",
    "Stalwart",
    "Valdo's",
]

# -----------------------------
# TARGET LOGIC
# -----------------------------

#  need count prefix and count suffix and check if they match targets

def count_prefix_targets(mods):
    return sum(any(target in mod.get('name', '') for target in MAP_PREFIX_TARGETS) and mod.get('type') == 'prefix' for mod in mods)

def count_suffix_targets(mods):
    return sum(any(target in mod.get('name', '') for target in MAP_SUFFIX_TARGETS) and mod.get('type') == 'suffix' for mod in mods)
   
def count_targets(mods):
    return count_prefix_targets(mods) + count_suffix_targets(mods)


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

# if valdo's and antagonist's are both present, return true, otherwise false
def has_valdos(mods):   return any("Valdo's" in mod.get('name', '') for mod in mods)
def has_antagonists(mods):    return any("Antagonist's" in mod.get('name', '') for mod in mods)
def good_scarabs(mods, stats):
    return stats.get("more_scarabs", 0) >= 80 and has_valdos(mods)

def good_rares(mods):
    return has_valdos(mods) and has_antagonists(mods)

def good_to_aug(mods, stats):
    return  len(mods)== 1 and (stats.get("more_currency", 0) >= 40 or stats.get("more_scarabs", 0) >= 30 or stats.get("pack_size", 0) >= 20)

def double_currency(stats):    return stats.get("more_currency", 0) >= 90
def double_pack_size(stats):    return stats.get("pack_size", 0) >= 40
def currency_and_pack_size(stats):    return stats.get("more_currency", 0) >40 and stats.get("pack_size", 0) >= 20
def good_to_regal(mods, stats):
    return len(mods) == 2 and (double_currency(stats) or double_pack_size(stats))

def good_to_keep(mods, stats):
    good_p = count_prefix_targets(mods) > 1
    good_s = count_suffix_targets(mods) > 1
    return good_scarabs(mods, stats) or good_rares(mods) or double_currency(stats) or double_pack_size(stats) or good_p or good_s

def stop_spamming():
    global spamming
    pyautogui.keyUp('shift')
    spamming = False

def tripple_slam():
    use_currency(EXALT, spammable=True)
    spam_currency(EXALT)
    spam_currency(EXALT)
    stop_spamming()

def determine_next_action_map(map):
    # time.sleep(1)
    global spamming
    global alts, scoures, exalts, regals, annuls
    mods = map.get('mods')
    stats = map.get('stats')
    num_mods = len(mods)
    print(stats)

    if good_to_keep(mods, stats) and num_mods == 6:
        print("Perfect map found, keeping.")
        stop_spamming()
        return "DONE"

    if good_to_keep(mods, stats):
        print("Good map, keeping.")
        stop_spamming()
        if num_mods == 2:                 
            use_currency(REGAL)
        tripple_slam()
        return "DONE"
    
    if num_mods == 0: # normal
        print("Normal map, using transmute.")
        stop_spamming()
        use_currency(TRANS)
    elif 0 < num_mods < 3: # magic
        if good_to_regal(mods, stats):
            stop_spamming()
            use_currency(REGAL)
            regals += 1

        elif good_to_aug(mods, stats):
            if spamming:
                alt_currency(AUG)
            else:
                stop_spamming()
                use_currency(AUG)
        else:
            if spamming:
                spam_alt()
            else:
                spamming = True
                use_alt()
    else: # rare
        stop_spamming()
        use_currency(SCOURE)

    return "CONTINUE"

    
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

GRID_SIZE = 24
START_COORDS = (28, 147)
TILE_WIDTH = 26
def find_item(item_class, idx):
    start_row, start_col = idx

    # flatten in COLUMN-major order
    start_pos = start_col * GRID_SIZE + start_row

    for pos in range(start_pos, GRID_SIZE * GRID_SIZE):
        col = pos // GRID_SIZE
        row = pos % GRID_SIZE

        x = START_COORDS[0] + col * TILE_WIDTH
        y = START_COORDS[1] + row * TILE_WIDTH

        pyautogui.moveTo(x, y)
        time.sleep(0.02)

        text = copy_item()
        if not text:
            continue

        if item_class.lower() in text.lower():
            print(f"Found {item_class} at idx ({row}, {col}) coords ({x}, {y})")
            move_to_crafter((x, y))
            return [row, col]

    return None

def get_item(item_class, tab_image, idx):
    clear_crafting_area_and_move_to_tab(tab_image)
    return find_item(item_class, idx)


# -----------------------------
# INDEX HANDLING
# -----------------------------



def advance_idx(idx):
    idx[0] += 1  # go down rows first

    if idx[0] >= GRID_SIZE:
        idx[0] = 0
        idx[1] += 1  # then next column

    return idx


def is_done(idx):
    return idx[1] >= GRID_SIZE


def main():
    focus_window("Path of Exile")
    clear_crafting_area_and_move_to_tab(CRAFTING_TAB)
    idx = [0, 0]
    count = 0

    while not is_done(idx):
        print(f"Searching from idx {tuple(idx)}")

        found_idx = get_item(ITEM_CLASS, SRC_TAB, tuple(idx))

        if found_idx is None:
            print("No more matching items found. Stopping.")
            break

        while True:
            map_mods = parse_map_mods(CURRENCY_CRAFT_COORDS)
            result = determine_next_action_map(map_mods)

            if result == "DONE":
                break

        idx = advance_idx(found_idx)
        count += 1

        if count >= 60:
            print("Processed 60 maps, stopping to avoid long runtime.")
            break

    print("Finished all items.")


# -----------------------------
# RUN
# -----------------------------

if __name__ == "__main__":
    main()