import pyautogui
import time

from macros.currency_macros import *
from macros.item_parser import parse_cluster_mods, copy_item
from images.image_utils import locate_center
from images.img_paths import *
from config import *
from focus_window import focus_window


# -----------------------------
# CONFIG
# -----------------------------
START_COORDS = (28, 147)
TILE_WIDTH = 26

ITEM_CLASS = "Cluster Jewels"
CRAFTING_TAB = CURRENCY_TAB  # change if needed
CRAFTING_TAB_COORDS = locate_center(CURRENCY_TAB, confidence=0.8)
SRC_TAB = SOURCE_TAB  # change if needed

CLUSTER_TARGETS = [
    "Towering Threat",
    "Assert Dominance",
    # "Vast Power",
]

VALUABLE_COMBOS = [
    ("Towering Threat", "Assert Dominance"),
    # ("Vast Power", "Assert Dominance"),
    # ("Vast Power", "Towering Threat"),
    # ("Assert Dominance", "Magnifier"),
    # ("Assert Dominance", "Expansive Might"),

]


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

            if f"Medium Cluster Jewel".lower() in text.lower():
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

def determine_action_clusters(mods):
    global spamming
    alts = 0
    scoure = 0
    exalts = 0
    num_mods = len(mods)
    num_targets = count_targets_found(mods)

    has_prefix = any(mod.get('type') in ['prefix', 'passive_skill'] for mod in mods)
    has_suffix = any(mod.get('type') == 'suffix' for mod in mods)

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
        if num_targets == 0:
            if has_prefix:
                alts += 1
                if alts >= 4500:
                    exit()
                if spamming:
                    spam_currency(ALT)
                else:
                    spamming = True
                    
                    use_currency(ALT, spammable=True)
            else:
                if spamming:
                    alt_currency(AUG)
                else:
                    spamming = False
                    use_currency(AUG)

        else:
            if not has_suffix:
                if spamming:
                    alt_currency(AUG)
                else:
                    spamming = False
                    use_currency(AUG)
            else:
                spamming = False
                use_currency(REGAL)

        return "CONTINUE"

    # --- rare ---
    if rarity == "rare":
        spamming = False

        if any_valuable_combo_found(mods):
            print("✅ Valuable combo found!")
            return "DONE"

        num_prefixes = sum(mod.get('type') in ['prefix', 'passive_skill'] for mod in mods)

        if num_targets == 1 and num_prefixes == 1:
            if exalts >= 480:
                exit()
            exalts += 1
            use_currency(EXALT)
        else:
            if scoure >= 750:
                exit()
            scoure += 1
            use_currency(SCOURE)

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
            mods = parse_cluster_mods(CURRENCY_CRAFT_COORDS)
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