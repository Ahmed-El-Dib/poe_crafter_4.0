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

# Force exit
from pynput import keyboard
import os

import pyperclip
def on_press(key):
    global running
    if key == keyboard.Key.esc:
        pyautogui.keyUp('shift')
        print("Stopping...")
        os._exit(0)

listener = keyboard.Listener(on_press=on_press)
listener.start()


def is_perfect_suffix(map):
    mods = map.get("mods", [])
    return sum(1 for mod in mods if mod["type"] == "suffix" and mod["name"] in MAP_SUFFIX_TARGETS) >= 3


def is_perfect_prefix(map):
    # has 3 target prefixes
    mods = map.get("mods", [])
    return sum(1 for mod in mods if mod["type"] == "prefix" and mod["name"] in MAP_PREFIX_TARGETS) >= 3


def price_map(map):
    quantity = map.get("stats", {}).get("quantity", 0)
    rarity = map.get("stats", {}).get("rarity", 0)
    pack_size = map.get("stats", {}).get("pack_size", 0)
    more_maps = map.get("stats", {}).get("more_maps", 0)
    more_currency = map.get("stats", {}).get("more_currency", 0)
    more_scarabs = map.get("stats", {}).get("more_scarabs", 0)

    prices = []

    if more_currency > 158 or pack_size > 69 or more_currency + pack_size > 180 or more_currency + quantity > 230:
        print("too good to price")
        return None
    
    if pack_size > 61:
        prices.append(99)
    if pack_size > 59:
        if more_currency > 90:
             prices.append(169)
        if more_maps > 100 or more_scarabs > 100:
             prices.append(149)
        if more_currency > 0 or more_scarabs > 0 or more_maps > 0:
            prices.append(99)
        else:
            prices.append(79)
    if pack_size > 49:
        prices.append(84)
    if pack_size > 40:
        prices.append(34)

    if more_currency > 130:
        if pack_size > 40:
            prices.append(299)
        if pack_size > 30 or more_scarabs > 0 or more_maps > 0:
            prices.append(249)
        else:
            prices.append(199)

    if more_currency > 100:
        if quantity > 87 and pack_size > 30:
            prices.append(99)
        if more_scarabs > 100 or more_maps > 100:
            prices.append(169)
        if more_scarabs > 70 or more_maps > 70:
            prices.append(149)
        if pack_size > 40:
            if more_scarabs > 0 or more_maps > 0:
                prices.append(169)
            else :
                prices.append(149)
        elif pack_size > 30 and (more_scarabs > 0 or more_maps > 0):
            prices.append(149)
        else:
            prices.append(79)

    if more_currency > 90:
        p_q = pack_size + quantity
        print(f"total pack size + quantity: {p_q}")
        if pack_size > 70:
            prices.append(299)
        if p_q > 150:
            prices.append(199)
        if p_q > 135:
            prices.append(149)
        if p_q > 125:
            prices.append(79)
        if p_q > 112:
            prices.append(49)
        if more_maps > 0 or more_scarabs > 0:
            prices.append(34)

        return max(prices) if prices else None
        
    if is_perfect_prefix(map) or is_perfect_suffix(map):
        prices.append(599)

    return max(prices) if prices else None



# Stash Grid Configuration
STASH_GRID_ROWS = 12
STASH_GRID_COLS = 12
STASH_GRID_START_X = 24  # Starting X coordinate of the grid
STASH_GRID_START_Y = 145  # Starting Y coordinate of the grid
STASH_GRID_CELL_SIZE = 26 *2  # Size of each grid cell

import time

from macros.map_parser import parse_map_mods
from focus_window import focus_window

# loop through a 12x12 grid of maps, parse the mods of each map, and price it using the price_map function
def price_maps_in_stash():
    for row in range(STASH_GRID_ROWS):
        for col in range(STASH_GRID_COLS):
            x = STASH_GRID_START_X + col * STASH_GRID_CELL_SIZE
            y = STASH_GRID_START_Y + row * STASH_GRID_CELL_SIZE
            map = parse_map_mods((x, y))
            if map:
                price = price_map(map)
                print(f"Map at ({row}, {col}) is priced at: {price}")
                print(f"stats: {map.get('stats', {})}")

def price_maps_in_inventory(offset=None):
    # Inventory Grid Configuration
    MIN_PRICE = 24
    INVENTORY_GRID_ROWS = 5
    INVENTORY_GRID_COLS = 12
    INVENTORY_GRID_START_X = 1292  # Starting X coordinate of the inventory grid
    INVENTORY_GRID_START_Y = 612  # Starting Y coordinate of the inventory grid
    INVENTORY_GRID_CELL_SIZE = 54  # Size of each grid cell

    for col in range(INVENTORY_GRID_COLS):
        for row in range(INVENTORY_GRID_ROWS):
            x = INVENTORY_GRID_START_X + col * INVENTORY_GRID_CELL_SIZE
            y = INVENTORY_GRID_START_Y + row * INVENTORY_GRID_CELL_SIZE
            map = parse_map_mods((x, y))
            if map:
                # price = max(price_map(map) - offset, MIN_PRICE)
                price = price_map(map)
                # print(price)
                if price:
                    place_item_in_shop(x, y, price)
            else:
                print(f"No map found at ({row}, {col}).")
                exit()
                
from images.image_utils import *

def open_sell_shop(SHOP_TAB_IMG):
    shop_coords = locate_center(SHOP_TAB_IMG, confidence=0.8)
    if shop_coords:
        pyautogui.moveTo(*shop_coords)
        pyautogui.leftClick()
        print("Clicked on shop tab.")
        return True
    else:
        print("Could not locate shop tab on screen.")
        return False
    
def place_item_in_shop(item_x, item_y, price):
    pyautogui.moveTo(item_x, item_y)
    pyautogui.keyDown('ctrl')
    pyautogui.leftClick()
    pyautogui.keyUp('ctrl')
    pyautogui.typewrite(str(price))
    pyautogui.press('tab')
    #assume chaos for now
    pyautogui.press('up')
    pyautogui.press('enter')
    pyautogui.press('enter')
    time.sleep(0.5)  # wait for the item to be listed
 

def reprice(percent):
    # Inventory Grid Configuration
    INVENTORY_GRID_ROWS = 12
    INVENTORY_GRID_COLS = 12
    INVENTORY_GRID_START_X = 37  # Starting X coordinate of the inventory grid
    INVENTORY_GRID_START_Y = 189  # Starting Y coordinate of the inventory grid
    INVENTORY_GRID_CELL_SIZE = 50  # Size of each grid cell
    MIN_PRICE = 24

    for col in range(INVENTORY_GRID_COLS):
        for row in range(INVENTORY_GRID_ROWS):
            x = INVENTORY_GRID_START_X + col * INVENTORY_GRID_CELL_SIZE
            y = INVENTORY_GRID_START_Y + row * INVENTORY_GRID_CELL_SIZE
            pyautogui.moveTo(x, y)
            map = parse_map_mods((x, y))
            if map:
                pyautogui.rightClick()
                curent_price = copy_price_from_clipboard()
                new_price = int(int(curent_price) * (1 - percent / 100))
                if new_price < MIN_PRICE:
                    print(f"Price for item at ({row}, {col}) is already at minimum. Skipping.")
                    pyautogui.typewrite(str(MIN_PRICE))
                    pyautogui.press('enter')
                else:
                    pyautogui.typewrite(str(new_price))
                    pyautogui.press('enter')

                
def copy_price_from_clipboard():
    pyperclip.copy('')
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    return pyperclip.paste()


if __name__ == "__main__":
    focus_window()
    price_maps_in_inventory(0)
    # reprice(25)