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
            flags = []
            if preamble:
                flags = preamble.split()

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

            mods.append({
                'type': mod_type,
                'name': mod_name,
                'tier': tier,
                'flags': flags,          # e.g. ['Fractured']
                'tags': tags.split(", ") if tags else [],
                'text': "\n".join(text_lines)
            })
        else:
            i += 1
    
    return mods

item = """
Item Class: Jewels
Rarity: Magic
Notable Large Cluster Jewel of the Newt
--------
Item Level: 84
--------
Adds 8 Passive Skills (enchant)
(Added Passive Skills are never considered to be in Radius by other Jewels) (enchant)
(All Added Passive Skills are Small unless otherwise specified) (enchant)
2 Added Passive Skills are Jewel Sockets (enchant)
Added Small Passive Skills grant: 12% increased Damage with Two Handed Weapons (enchant)
(Passive Skills that are not Notable, Masteries, Keystones, or Jewel Sockets are Small) (enchant)
--------
{ Prefix Modifier "Notable" (Tier: 1) — Mana, Attack, Speed }
1 Added Passive Skill is Fuel the Fight — Unscalable Value
{ Suffix Modifier "of the Newt" (Tier: 3) — Life }
Added Small Passive Skills also grant: Regenerate 0.1% of Life per Second
(Passive Skills that are not Notable, Masteries, Keystones, or Jewel Sockets are Small)
--------
Place into an allocated Large Jewel Socket on the Passive Skill Tree. Added passives do not interact with jewel radiuses. Right click to remove from the Socket.
"""

print(read_item(item))