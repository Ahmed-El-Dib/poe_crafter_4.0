import pyautogui
import time
from macros.item_parser import copy_item
from images.image_utils import *
from images.img_paths import *
from config import *

START_COORDS = (24,145)
TILE_WIDTH = 24

def clear_crafting_area_and_move_to_tab(tab_image):
    # Move to crafting area and clear it
    pyautogui.moveTo(CURRENCY_CRAFT_COORDS[0], CURRENCY_CRAFT_COORDS[1])
    pyautogui.keyDown('ctrl')
    pyautogui.leftClick()  # Clear crafting area
    pyautogui.keyUp('ctrl')

    # Move to specified tab
    tab_coords = locate_center(tab_image, confidence=0.8)
    if tab_coords:
        pyautogui.moveTo(tab_coords[0], tab_coords[1])
        pyautogui.leftClick()
    else:
        print(f"{tab_image} not found")
        exit()

def find(item_class, idx = (0,0)):
    x0 = START_COORDS[0] + idx[0] * TILE_WIDTH
    y0 = START_COORDS[1] + idx[1] * TILE_WIDTH

    for col in range(24):          # left → right
        for row in range(24):      # top → bottom
            x = x0 + col * TILE_WIDTH
            y = y0 + row * TILE_WIDTH

            # Move mouse to tile
            pyautogui.moveTo(x, y)

            # Small delay so tooltip appears
            time.sleep(0.02)

            # Copy item text
            text = copy_item()

            if not text:
                continue

            # Extract item class line
            for line in text.split("\n"):
                if line.startswith("Item Class:"):
                    current_class = line.split(":", 1)[1].strip()

                    # Match target
                    if current_class.lower() == item_class.lower():
                        print(f"Found {item_class} at ({x}, {y})")

                        move_to_crafter((x, y))
                        return True

    print(f"{item_class} not found")
    return False

def move_to_crafter(coords):
    # Move mouse to item
    pyautogui.moveTo(coords[0], coords[1])

    # Right-click to pick up item
    pyautogui.leftClick()

    currency_tab_coords = locate_center(CURRENCY_TAB, confidence=0.8)
    if currency_tab_coords:
        pyautogui.moveTo(currency_tab_coords[0], currency_tab_coords[1])
        pyautogui.leftClick()
    else:
        print("Currency tab not found")
        exit()
    
    pyautogui.moveTo(CURRENCY_CRAFT_COORDS[0], CURRENCY_CRAFT_COORDS[1])
    pyautogui.leftClick()

def get_item(item_class, tab_image, idx=(0,0)):
    clear_crafting_area_and_move_to_tab(tab_image)
    return find(item_class, idx)