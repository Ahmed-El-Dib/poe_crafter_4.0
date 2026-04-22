
#create a currency exchange class to handle faustus exchanges
# first method to ensure currency exchange is open and ready to use
# look for exchange_open image, if not found, press esc untill you see faustus_person image, then ctrl click faustus_person image to open exchange, then look for exchange_open image again, if not found, repeat process

import time

from images.image_utils import locate_center, locate_order_entry, locate_from_text
from images.img_paths import *
from focus_window import focus_window
import pyautogui

def ensure_exchange_open():
    if focus_window("Path of Exile"):
        print("Window focused successfully.")
    else:
        print("Failed to focus window. Please ensure Path of Exile is running and try again.")
        return False
    
    exchange_coords = locate_center(EXCHANGE_OPEN_LAPTOP, confidence=0.8)
    if exchange_coords:
        return True
    
    print("Exchange not open, trying to open...")
    while True:
        faustus_coords = locate_center(FAUSTUS_PERSON_LAPTOP, confidence=0.8)
        if faustus_coords:
            pyautogui.moveTo(*faustus_coords)
            pyautogui.keyDown('ctrl')
            pyautogui.leftClick()
            pyautogui.keyUp('ctrl')
            print("Clicked on Faustus, waiting for exchange to open...")
            pyautogui.sleep(2)  # wait for exchange to open
            exchange_coords = locate_center(EXCHANGE_OPEN_LAPTOP, confidence=0.8)
            if exchange_coords:
                print("Exchange is now open!")
                return True
        else:
            print("Faustus not found, pressing ESC to reset...")
            pyautogui.press('esc')
            pyautogui.sleep(1)

#place a want or have order in the exchange, option is either "want" or "have", item is the name of the item you want to buy or sell, qty is the quantity you want to buy or sell, and confidence is the confidence level for locating the laptop images
def place_order(option, item_text, item_image, qty, confidence=0.8):
    if not ensure_exchange_open():
        print("Cannot place order because exchange is not open.")
        return False
    
    item_input, qty_input = locate_order_entry(option, confidence=confidence)
    
    # Click on item input and type item name
    pyautogui.moveTo(*item_input)
    pyautogui.leftClick()
    pyautogui.typewrite(item_text)
    time.sleep(1)  # wait for item suggestions to load

    # locate item coordinates based on image, click on it to select it
    item_coords = locate_center(item_image, confidence=confidence)
    if item_coords:
        pyautogui.moveTo(*item_coords)
        pyautogui.leftClick()
    else:
        print(f"Could not locate item image '{item_image}' on screen.")
        return False
    
    # Click on qty input and type quantity
    pyautogui.moveTo(*qty_input)
    pyautogui.leftClick()
    pyautogui.typewrite(str(qty))
    
    print(f"Placed {option} order for {qty}x {item_text}.")
    return True

place_order("have", "Exalted Orb", EXALT_EXCHANGE_LAPTOP, 5)