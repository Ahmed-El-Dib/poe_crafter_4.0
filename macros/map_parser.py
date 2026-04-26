import re
from pyautogui import hotkey as send_keys
import pyperclip
from pywinauto import mouse
from pynput.keyboard import Key, Controller
keyboard = Controller()


import pyautogui
import pyperclip
import time

def copy_item():
    pyperclip.copy('')
    # time.sleep(0.01)


    pyautogui.hotkey('ctrl', 'alt', 'c')
    # time.sleep(0.01)

    return pyperclip.paste()

def parse_map_mods(item_location) -> list:
    """
    Parse a map description and extract mods with full text.
    
    Args:
        item_location (tuple): (x, y) coordinates to hover for tooltip
    
    Returns:
        list: List of dictionaries with mod info, including full text
    """
    mouse.move(coords=item_location)
    # time.sleep(0.05)  # small delay for tooltip
    description = copy_item()  # assumes this returns full clipboard text
    return read_map(description)

def read_map(description):
    lines = description.strip().split("\n")

    # --- SAFETY CHECK ---
    if not any("Item Class: Maps" in line for line in lines):
        return None
    
    stats = {
        "quantity": 0,
        "rarity": 0,
        "pack_size": 0,
        "more_maps": 0,
        "more_currency": 0,
        "more_scarabs": 0
    }

    mods = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # --- Extract map stats (UNCHANGED) ---
        stat_match = re.match(r'(.+?):\s*\+?(\d+)%', line)
        if stat_match:
            stat_name = stat_match.group(1).lower()
            value = int(stat_match.group(2))

            if "item quantity" in stat_name:
                stats["quantity"] = value
            elif "item rarity" in stat_name:
                stats["rarity"] = value
            elif "monster pack size" in stat_name:
                stats["pack_size"] = value
            elif "more maps" in stat_name:
                stats["more_maps"] = value
            elif "more currency" in stat_name:
                stats["more_currency"] = value
            elif "more scarabs" in stat_name:
                stats["more_scarabs"] = value

            i += 1
            continue

        # --- Match Prefix/Suffix modifiers (simplified + robust) ---
        mod_match = re.search(
            r'\{\s*(Prefix|Suffix) Modifier(?: "([^"]+)")?.*?\}',
            line
        )

        if mod_match:
            mod_type = mod_match.group(1).lower()
            mod_name = mod_match.group(2) if mod_match.group(2) else None

            # Collect mod text
            text_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()

                # Stop at next modifier or separator
                if re.search(r'\{\s*(Prefix|Suffix) Modifier', next_line) or '--------' in next_line:
                    break

                if next_line:
                    text_lines.append(next_line)

                i += 1

            mods.append({
                "type": mod_type,
                "name": mod_name,
                "text": "\n".join(text_lines)
            })
        else:
            i += 1

    return {
        "stats": stats,
        "mods": mods
    }

map_description = """
Item Class: Maps
Rarity: Rare
Death Artifice
Map (Tier 16)
--------
Item Quantity: +39% (augmented)
Item Rarity: +24% (augmented)
Monster Pack Size: +27% (augmented)
More Currency: +47% (augmented)
--------
Item Level: 84
--------
Monster Level: 83
--------
{ Implicit Modifier }
Area is Influenced by the Originator's Memories — Unscalable Value
--------
{ Prefix Modifier "Punishing" (Tier: 1) }
Monsters reflect 20% of Physical Damage
Monsters reflect 20% of Elemental Damage
{ Suffix Modifier "of Persistence" (Tier: 1) }
Rare monsters in area Temporarily Revive on death
{ Suffix Modifier "of Temporal Chains" — Caster, Curse }
Players are Cursed with Temporal Chains
(Temporal Chains is a Hex which reduces Action Speed by 15%, or 9% on Rare or Unique targets, and makes other effects on the target expire 40% slower. It has 50% less effect on Players and lasts 5 seconds)
--------
Travel to a Map of this tier or lower by using this in a personal Map Device. Maps can only be used once. 



    """

if __name__ == "__main__":
    print(read_map(map_description))