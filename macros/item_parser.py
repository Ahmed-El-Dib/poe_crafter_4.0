import re
from pyautogui import hotkey as send_keys
import pyperclip
from pywinauto import mouse
import time
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


def parse_cluster_mods(item_location) -> list:
    """
    Parse item description and extract mods.

    Args:
        description (str): The item description text

    Returns:
        list: List of dictionaries containing mod information
    """
    mouse.move(coords=item_location)
    # time.sleep(0.01)  # Short delay to ensure the tooltip is visible
    description = copy_item()

    mods = []

    lines = description.strip().split('\n')

    for i, line in enumerate(lines):
        line = line.strip()

        if "1 added passive skill is" in line.lower():
            match = re.search(r'1 added passive skill is (.+?) —', line, re.IGNORECASE)
            if match:
                skill_name = match.group(1).strip()
                mods.append({
                    'type': 'passive_skill',
                    'name': skill_name,
                    'text': line
                })

        quote_match = re.search(r'"([^"]+)"', line)
        if quote_match:
            quoted_text = quote_match.group(1)
            if quoted_text.lower() != "notable":
                if "prefix modifier" in line.lower():
                    mod_type = "prefix"
                elif "suffix modifier" in line.lower():
                    mod_type = "suffix"
                else:
                    mod_type = "unknown"

                tier_match = re.search(r'\(Tier:\s*(\d+)\)', line)
                tier = tier_match.group(1) if tier_match else None

                mods.append({
                    'type': mod_type,
                    'name': quoted_text,
                    'tier': tier,
                    'text': line
                })
    print(f"Parsed mods: {mods}")
    return mods


def parse_item_mods(item_location) -> list:
    """
    Parse a boot item description and extract mods with full text.
    
    Args:
        item_location (tuple): (x, y) coordinates to hover for tooltip
    
    Returns:
        list: List of dictionaries with mod info, including full text
    """
    mouse.move(coords=item_location)
    # time.sleep(0.05)  # small delay for tooltip
    description = copy_item()  # assumes this returns full clipboard text
    return read_item(description)
    

def read_item(description):
    mods = []
    lines = description.strip().split("\n")
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Match modifier line inside {}
        mod_match = re.search(
            r'\{\s*(.*?)\b(Prefix|Suffix) Modifier "([^"]+)"(?: \(Tier:\s*(\d+)\))?(?:\s*—\s*(.*?))?\s*\}',
            line
        )
        
        if mod_match:
            preamble = mod_match.group(1).strip()  # e.g. "Fractured", "Crafted"
            mod_type = mod_match.group(2).lower()
            mod_name = mod_match.group(3)
            tier = mod_match.group(4)
            tags = mod_match.group(5)

            # Extract flags from preamble
            flags = preamble.split() if preamble else []

            # Collect text lines under this mod
            text_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                
                # Stop at next mod or separator
                if re.search(r'\{\s*.*\b(Prefix|Suffix) Modifier', next_line) or '--------' in next_line:
                    break
                
                if next_line:  # skip empty lines
                    text_lines.append(next_line)
                
                i += 1

            # --- NEW: Extract roll info ---
            roll = None
            max_roll = False

            for line_text in text_lines:
                roll_match = re.search(r'(-?\d+\.?\d*)\s*\((\d+\.?\d*)-(\d+\.?\d*)\)', line_text)
                if roll_match:
                    roll_val = float(roll_match.group(1))
                    min_val = float(roll_match.group(2))
                    max_val_val = float(roll_match.group(3))

                    roll = int(roll_val) if roll_val.is_integer() else roll_val
                    max_roll = roll_val == max_val_val
                    break  # only take first match

            mods.append({
                'type': mod_type,
                'name': mod_name,
                'tier': tier,
                'flags': flags,
                'tags': tags.split(", ") if tags else [],
                'text': "\n".join(text_lines),
                'roll': roll,
                'max_roll': max_roll
            })
        else:
            i += 1
    
    return mods

item = """
Item Class: Jewels
Rarity: Rare
Vivid Cut
Medium Cluster Jewel
--------
Requirements:
Level: 54
--------
Item Level: 83
--------
Adds 5 Passive Skills (enchant)
(Added Passive Skills are never considered to be in Radius by other Jewels) (enchant)
(All Added Passive Skills are Small unless otherwise specified) (enchant)
1 Added Passive Skill is a Jewel Socket (enchant)
Added Small Passive Skills grant: 10% increased Area Damage (enchant)
(Passive Skills that are not Notable, Masteries, Keystones, or Jewel Sockets are Small) (enchant)
--------
{ Prefix Modifier "Hazardous" (Tier: 2) — Damage }
Added Small Passive Skills also grant: 3% increased Damage
{ Prefix Modifier "Notable" (Tier: 1) — Damage, Attack }
1 Added Passive Skill is Titanic Swings — Unscalable Value
{ Suffix Modifier "of the Brute" (Tier: 3) — Attribute }
Added Small Passive Skills also grant: +3(2-3) to Strength
{ Suffix Modifier "of the Lizard" (Tier: 2) — Life }
Added Small Passive Skills also grant: Regenerate 0.15% of Life per Second
(Passive Skills that are not Notable, Masteries, Keystones, or Jewel Sockets are Small)
--------
Place into an allocated Medium or Large Jewel Socket on the Passive Skill Tree. Added passives do not interact with jewel radiuses. Right click to remove from the Socket.

"""

print(read_item(item))

