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

def parse_map_mods(item_location):
    """
    Parse a map description and extract mods with full text.

    Args:
        item_location (tuple): (x, y) coordinates to hover for tooltip

    Returns:
        List of dictionaries with mod info, including full text
    """
    mouse.move(coords=item_location)

    description = copy_item()

    if not description:
        print("Failed to copy item description.")
        return None

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

    price = None
    currency = None

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

        # --- Extract price note ---
        price_match = re.search(
            r'^Note:\s*~b/o\s+(\d+(?:\.\d+)?)\s+(\w+)',
            line,
            re.IGNORECASE
        )

        if price_match:
            price = float(price_match.group(1))
            currency = price_match.group(2).lower()
            i += 1
            continue

    result = {
    "stats": stats,
    "mods": mods
    }

    if price is not None and currency is not None:
        result["price"] = price
        result["currency"] = currency

    return result

map_description = """
Item Class: Maps
Rarity: Rare
Whispering Gambit
Map (Tier 16)
--------
Item Quantity: +113% (augmented)
Item Rarity: +67% (augmented)
Monster Pack Size: +43% (augmented)
--------
Item Level: 83
--------
Monster Level: 83
--------
{ Implicit Modifier }
Map contains Drox's Citadel
Item Quantity increases amount of Rewards Drox drops by 20% of its value — Unscalable Value
--------
{ Prefix Modifier "Unwavering" (Tier: 1) — Life }
26(25-30)% more Monster Life
Monsters cannot be Stunned — Unscalable Value
{ Prefix Modifier "Chaining" (Tier: 1) }
Monsters' skills Chain 2 additional times
{ Prefix Modifier "Antagonist's" (Tier: 1) }
22(20-30)% increased number of Rare Monsters
{ Prefix Modifier "Fecund" (Tier: 1) — Life }
46(40-49)% more Monster Life
{ Suffix Modifier "of Stasis" (Tier: 1) — Life, Mana, Defences, Energy Shield }
Players cannot Regenerate Life, Mana or Energy Shield — Unscalable Value
{ Suffix Modifier "of Vulnerability" (Tier: 1) — Caster, Curse }
Players are Cursed with Vulnerability
(Vulnerability is a Hex which increases Physical Damage taken by 15% and causes Hits to have +25% chance to inflict Bleeding on the target. It lasts 8 seconds)
{ Suffix Modifier "of Ice" (Tier: 1) }
Area has patches of Chilled Ground
(You are Chilled while standing in Chilled Ground)
{ Suffix Modifier "of Exposure" (Tier: 1) — Elemental, Resistance }
Players have -12(-12--9)% to all maximum Resistances
--------
Travel to a Map of this tier or lower by using this in a personal Map Device. Maps can only be used once. 
--------
Corrupted
--------
Note: ~b/o 22 chaos




    """

if __name__ == "__main__":
    print(read_map(map_description))