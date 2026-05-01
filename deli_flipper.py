# Steps:
# class for deli stash tab {
# tab image
# confirm image for tab open
# location for each deli orb with count}
# functions for opening tab, checking for orbs, and picking up orbs

from macros.item_parser import parse_deli_orb
from map_pricer import place_item_in_shop
from focus_window import focus_window
import pyautogui
from images.img_paths import *
from images.image_utils import locate_center

focus_window("Path of Exile")
TARGETS = ["Diviner's"]
HORTI_CRAFT = (962, 606)
HORTI_ITEM = (963, 482)
HORTI_SEARCH = (535, 814)
HORTI_SELECT = (574, 327)



def good_to_keep(orb):
    orb_type = orb['type'].lower()
    return any(target.lower() in orb_type for target in TARGETS)

def setup_deli_craft():
    # click hort search, type deli, click horti select
    pyautogui.moveTo(HORTI_SEARCH[0], HORTI_SEARCH[1],duration=0.01)
    pyautogui.click()
    pyautogui.typewrite("deli")
    pyautogui.moveTo(HORTI_SELECT[0], HORTI_SELECT[1],duration=0.01)
    pyautogui.click()

def ctrl_click():
    pyautogui.keyDown('ctrl')
    pyautogui.click()
    pyautogui.keyUp('ctrl')
def flip_orb():
    COST_PER_TRY = 5
    VALUE_PER_SUCCESS = 330

    orb = parse_deli_orb(HORTI_ITEM)

    tries = 0
    success = False

    while orb and not good_to_keep(orb):
        if locate_center(OUT_OF_JUICE):
            print("Out of juice, stopping flips.")
            exit()

        pyautogui.moveTo(HORTI_CRAFT[0], HORTI_CRAFT[1], duration=0.01)
        pyautogui.click()

        tries += 1

        # re-read orb after crafting
        orb = parse_deli_orb(HORTI_ITEM)

    if orb and good_to_keep(orb):
        success = True
        pyautogui.moveTo(HORTI_ITEM[0], HORTI_ITEM[1], duration=0.01)
        ctrl_click()

    return {
        "tries": tries,
        "successes": 1 if success else 0,
        "cost": tries * COST_PER_TRY,
        "revenue": VALUE_PER_SUCCESS if success else 0,
        "profit": (VALUE_PER_SUCCESS if success else 0) - (tries * COST_PER_TRY),
    }


def orb_flipper():
    COST_PER_TRY = 5
    VALUE_PER_SUCCESS = 330

    # Inventory Grid Configuration
    INVENTORY_GRID_ROWS = 5
    INVENTORY_GRID_COLS = 12
    INVENTORY_GRID_START_X = 1292
    INVENTORY_GRID_START_Y = 612
    INVENTORY_GRID_CELL_SIZE = 53

    total_orbs = 0
    total_tries = 0
    total_successes = 0
    total_cost = 0
    total_revenue = 0
    total_profit = 0

    setup_deli_craft()

    for col in range(INVENTORY_GRID_COLS):
        for row in range(INVENTORY_GRID_ROWS):
            x = INVENTORY_GRID_START_X + col * INVENTORY_GRID_CELL_SIZE
            y = INVENTORY_GRID_START_Y + row * INVENTORY_GRID_CELL_SIZE

            orb = parse_deli_orb((x, y))

            if orb:
                total_orbs += 1

                if not good_to_keep(orb):
                    ctrl_click()
                    result = flip_orb()

                    total_tries += result["tries"]
                    total_successes += result["successes"]
                    total_cost += result["cost"]
                    total_revenue += result["revenue"]
                    total_profit += result["profit"]
                else:
                    total_successes += 1
                    total_revenue += VALUE_PER_SUCCESS
                    total_profit += VALUE_PER_SUCCESS

    success_chance = (total_successes / total_orbs * 100) if total_orbs else 0
    avg_cost_per_success = (total_cost / total_successes) if total_successes else 0
    roi = (total_profit / total_cost * 100) if total_cost else 0

    print("\n===== ORB FLIP KPI SUMMARY =====")
    print(f"Total orbs checked: {total_orbs}")
    print(f"Total tries: {total_tries}")
    print(f"Total successes: {total_successes}")
    print(f"Chance of success: {success_chance:.2f}%")
    print(f"Total cost: {total_cost}c")
    print(f"Total return: {total_revenue}c")
    print(f"Total profit: {total_profit}c")
    print(f"Average cost per success: {avg_cost_per_success:.2f}c")
    print(f"ROI: {roi:.2f}%")
    print("================================\n")


if __name__ == "__main__":
    orb_flipper()