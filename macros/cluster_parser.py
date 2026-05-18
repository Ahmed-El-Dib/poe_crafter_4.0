
import re
from pyautogui import hotkey as send_keys
import pyperclip
from pywinauto import mouse

from pynput.keyboard import Key, Controller
keyboard = Controller()


import pyautogui
import pyperclip


def copy_item():
    pyperclip.copy('')
    # time.sleep(0.01)


    pyautogui.hotkey('ctrl', 'alt', 'c')
    # time.sleep(0.01)

    return pyperclip.paste()

def parse_cluster(item_location) -> dict:
    mouse.move(coords=item_location)
    description = copy_item()
    return read_cluster(description)


def read_cluster(description):
    mods = []
    lines = description.strip().split("\n")

    jewel_size = None
    added_passives = None

    # Extract cluster metadata
    for line in lines:
        line = line.strip()

        size_match = re.search(r'\b(Small|Medium|Large) Cluster Jewel\b', line)
        if size_match:
            jewel_size = size_match.group(1).lower()

        passive_match = re.search(r'Adds\s+(\d+)\s+Passive Skills', line)
        if passive_match:
            added_passives = int(passive_match.group(1))

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        mod_match = re.search(
            r'\{\s*(.*?)\b(Prefix|Suffix) Modifier "([^"]+)"(?: \(Tier:\s*(\d+)\))?(?:\s*—\s*(.*?))?\s*\}',
            line
        )

        if mod_match:
            preamble = mod_match.group(1).strip()
            mod_type = mod_match.group(2).lower()
            mod_name = mod_match.group(3)
            tier = mod_match.group(4)
            tags = mod_match.group(5)

            flags = preamble.split() if preamble else []

            text_lines = []
            i += 1

            while i < len(lines):
                next_line = lines[i].strip()

                if re.search(r'\{\s*.*\b(Prefix|Suffix) Modifier', next_line) or '--------' in next_line:
                    break

                if next_line:
                    text_lines.append(next_line)

                i += 1

            text = "\n".join(text_lines)

            # Override notable mod name with passive name
            if mod_name == "Notable":
                notable_match = re.search(
                    r'Added Passive Skill is\s+(.+?)(?:\s+—|$)',
                    text
                )
                if notable_match:
                    mod_name = notable_match.group(1).strip()

            roll = None
            max_roll = False

            for line_text in text_lines:
                roll_match = re.search(
                    r'(-?\d+\.?\d*)\s*\((\d+\.?\d*)-(\d+\.?\d*)\)',
                    line_text
                )

                if roll_match:
                    roll_val = float(roll_match.group(1))
                    max_val = float(roll_match.group(3))

                    roll = int(roll_val) if roll_val.is_integer() else roll_val
                    max_roll = roll_val == max_val
                    break

            mods.append({
                "type": mod_type, #prefix or suffix
                "name": mod_name,
                "tier": tier,
                "flags": flags,
                "tags": tags.split(", ") if tags else [],
                "text": text,
                "roll": roll,
                "max_roll": max_roll,
            })
        else:
            i += 1

    return {
        "jewel_size": jewel_size,
        "added_passives": added_passives,
        "mods": mods,
    }

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

print(read_cluster(item))