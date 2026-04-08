from macros.rpa_macros import *
from images.img_paths import *
from pynput.keyboard import Key, Controller
keyboard = Controller()

def use_currency(currency_coords, target_coords = CURRENCY_CRAFT_COORDS, spammable = False):
    """
    Clicks the currency item and then clicks the target item.
    Returns True if both actions succeeded, False otherwise.
    """
    pyautogui.keyUp('shift')
   
    if spammable:
        pyautogui.keyDown('shift')
        # time.sleep(0.01)  # small buffer
    pyautogui.moveTo(currency_coords[0], currency_coords[1],duration=0.01)
    pyautogui.rightClick()
    # print(f"Used currency - Regular")
    pyautogui.moveTo(target_coords[0], target_coords[1],duration=0.01)
    pyautogui.leftClick()
    


def spam_currency(currency, target_coords = CURRENCY_CRAFT_COORDS):
    """
    Spams the currency item on the target item by holding Shift.
    Returns True if both actions succeeded, False otherwise.
    """
    # print(f"Used currency - Spammable")
    pyautogui.leftClick()

def alt_currency(currency, target_coords = CURRENCY_CRAFT_COORDS):
    # Hold  ALT
    
    pyautogui.keyDown('alt')
    # time.sleep(0.01)  # small buffer
    pyautogui.leftClick()
    pyautogui.keyUp('alt')
    # print(f"Used currency - Altable")
  
