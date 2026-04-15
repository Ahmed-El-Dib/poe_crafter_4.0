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
    
    mods = []
    lines = description.strip().split("\n")
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for Prefix/Suffix modifier line
        mod_match = re.search(r'\ (Prefix|Suffix) Modifier "([^"]+)"(?: \(Tier:\s*(\d+)\))?', line)
        if mod_match:
            mod_type = mod_match.group(1).lower()      # prefix or suffix
            mod_name = mod_match.group(2)
            tier = mod_match.group(3)
            
            # Collect all lines **after this modifier** until:
            # - next modifier `{ ... }` OR
            # - separator `--------`
            text_lines = []
            i += 1  # move to next line
            while i < len(lines):
                next_line = lines[i].strip()
                if re.match(r'\{ (Prefix|Suffix) Modifier', next_line) or '--------' in next_line:
                    break
                text_lines.append(next_line)
                i += 1
            
            mods.append({
                'type': mod_type,
                'name': mod_name,
                'tier': tier,
                'text': "\n".join(text_lines)
            })
        else:
            i += 1  # no mod here, move on
    
    # print(f"Parsed mods: {mods}")
    return mods
