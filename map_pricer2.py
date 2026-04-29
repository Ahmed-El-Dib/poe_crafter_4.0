import pyautogui
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




def price_currency_map(more_currency, pack_size, quantity):
    price = 24 # base price for a map with no quantity, pack size, or more currency
    if more_currency > 158:
        return 999  # too good to price
    if more_currency > 150: #mostly 158s
        if pack_size >= 50 or quantity >= 98:
            price = 369
        if pack_size >= 40 or quantity >= 90:
            price = 329
        if pack_size >= 35 or quantity >= 84:
            price = 299
        else:           
            price = 229
        return price
    elif more_currency > 130:
        if pack_size >= 50 or quantity >= 98:
            price = 339
        if pack_size >= 40 or quantity >= 90:
            price = 279
        if pack_size >= 35 or quantity >= 84:
            price = 199
        else:           
            price = 169
        return price
    elif more_currency > 120:
        if pack_size >= 50 or quantity >= 98:
            price = 299
        if pack_size >= 40 or quantity >= 90:
            price = 249
        if pack_size >= 35 or quantity >= 84:
            price = 169
        else:           
            price = 129
        return price
    elif more_currency >= 111:
        if pack_size >= 50 or quantity >= 98:
            price = 299
        if pack_size >= 40 or quantity >= 90:
            price = 99
        if pack_size >= 35 or quantity >= 84:
            price = 59
        if pack_size >= 30 and quantity >= 80:
            price = 49
        else:           
            price = 34
        return price

    elif more_currency >= 90:
        if pack_size >= 50 or quantity >= 98:
            price = 119
        if pack_size >= 40 or quantity >= 90:
            price = 49
        if pack_size >= 35 and quantity >= 84:
            price = 39
        if pack_size >= 30 and quantity >= 80:
            price = 34
        else:           
            price = 24
    return price

def price_packsize_map(pack_size, quantity):
    price = 24 # base price for a map with no quantity, pack size, or more currency
    extra_quant = max(0, (quantity - 80) // 2)
    if pack_size >= 90:
        price = 449  # too good to price
    if pack_size >= 84:
        price = 289 + extra_quant
    elif pack_size >= 80:
        price = 249 + extra_quant
    elif pack_size >= 75:
        price = 129 + extra_quant
    elif pack_size >= 70:
        price = 109 + extra_quant
    elif pack_size >= 65:
        price = 99 + extra_quant
    elif pack_size >= 62:
        price = 84 + extra_quant
    elif pack_size >= 60:
        price = 79 + extra_quant    
    elif pack_size >= 55:        
        price = 69 + extra_quant
    elif pack_size >= 50:  
        price = 64 + extra_quant  
    elif pack_size >= 40:
        price = 34 + extra_quant
    return price

def price_other_map(more_maps, more_scarabs,more_currency, pack_size, quantity):
    price = 24 # base price for a map with no quantity, pack size, or more currency
    best_extra = max(more_maps, more_scarabs)
    if best_extra >= 100:
        if pack_size >= 40 or more_currency > 90 and quantity >= 80:
            price = 99
        elif pack_size > 30 or more_currency > 70 and quantity >= 80:
            price = 49
        else:
            price = 24
    return price



def price_map(map):
    stats = map.get("stats", {})

    quantity = stats.get("quantity", 0)
    pack_size = stats.get("pack_size", 0)
    more_maps = stats.get("more_maps", 0)
    more_currency = stats.get("more_currency", 0)
    more_scarabs = stats.get("more_scarabs", 0)

    # if too_good_to_price(quantity, pack_size, more_currency):
    #     print("too good to price")
    #     return None

    # Leave this as-is from your original script.
    if is_perfect_prefix(map) or is_perfect_suffix(map):
        return 599

    prices = []

    currency_price = price_currency_map(
        more_currency=more_currency,
        pack_size=pack_size,
        quantity=quantity,
    )
    if currency_price is not None:
        prices.append(currency_price)

    pack_size_price = price_packsize_map(
        pack_size=pack_size,
        quantity=quantity
    )
    if pack_size_price is not None:
        prices.append(pack_size_price)

    other_price = price_other_map(
        more_maps=more_maps,
        more_scarabs=more_scarabs,
        more_currency=more_currency,
        pack_size=pack_size,   
        quantity=quantity,)
    if other_price is not None:
        prices.append(other_price)

    return max(prices) + 20 if prices else None

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
    INVENTORY_GRID_CELL_SIZE = 53  # Size of each grid cell

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
                    print(f"Placing item at ({row}, {col}) with price: {price}")
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
    INVENTORY_GRID_ROWS = 13
    INVENTORY_GRID_COLS = 13
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
                # new_price = int(int(curent_price) * (1 - percent / 100))
                new_price = int(int(curent_price) - percent)
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
    # price_maps_in_inventory(0)
    reprice(25)