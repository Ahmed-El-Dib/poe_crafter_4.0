import pyautogui
import time
from images.img_paths import SHOP_TAB_1, SHOP_TAB_2, SHOP_TAB_3, SHOP_TAB_4, SHOP_TAB_5
from shop.shop_utils import requires_sell_side, open_shop_tab
from pricers.discount import get_discounted_price
from pricers.map_pricer import MIN_PRICE, price_map
from macros.map_parser import parse_map_mods
from shop.shop_tab import grid_coords, GRID_SIZE

@requires_sell_side
def place_item_in_shop(item_x, item_y, price, currency = "chaos"):
    pyautogui.moveTo(item_x, item_y)
    pyautogui.keyDown('ctrl')
    pyautogui.leftClick()
    pyautogui.keyUp('ctrl')
    pyautogui.typewrite(str(price))
    pyautogui.press('tab')
    #assume chaos for now
    if currency == "chaos":
        pyautogui.press('up')
    if currency == "divine":
        pyautogui.press('up')
        pyautogui.press('down')
    pyautogui.press('enter')
    pyautogui.press('enter')
    time.sleep(0.1)  # wait for the item to be listed


def price_item_in_shop(item_x, item_y, price, currency = "chaos"):
    pyautogui.moveTo(item_x, item_y)
    pyautogui.rightClick()
    pyautogui.typewrite(str(price))
    pyautogui.press('tab')
    #assume chaos for now
    if currency == "chaos":
        pyautogui.press('up')
    if currency == "divine":
        pyautogui.press('up')
        pyautogui.press('down')
    pyautogui.press('enter')
    pyautogui.press('enter')
    time.sleep(0.1)  # wait for the price to update

@requires_sell_side
def reprice_items_in_shop(
    
    parse_func,
    price_func,
    discount_func=None,
    discount=None,
    discount_type="%",
    min_price=1,
    from_regular_price=False,
):
    priced_count = 0
    skipped_count = 0
    total_price = 0

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            coords = grid_coords(row, col)
            item_data = parse_func(coords)
            if item_data is None:
                continue
            if from_regular_price:
                base_price = price_func(item_data)
            else:
                base_price = item_data.get("price")
            if base_price is None:
                skipped_count += 1
                continue
            discounted_price = discount_func(base_price, discount, discount_type, min_price) if discount_func else base_price
            price_item_in_shop(coords[0], coords[1], discounted_price)


@requires_sell_side
def reprice_maps_in_shop(
    shop_tabs = [SHOP_TAB_1, SHOP_TAB_2, SHOP_TAB_3, SHOP_TAB_4, SHOP_TAB_5],
    discount_func=get_discounted_price,
    discount=5,
    discount_type="%",
    min_price=MIN_PRICE,
):
    for shop in shop_tabs:
        if open_shop_tab(shop):
            print(f"Opened shop tab successfully.")
            reprice_items_in_shop(
                parse_func=parse_map_mods,
                price_func=price_map,
                discount_func=discount_func,
                discount=discount,
                discount_type=discount_type,
                min_price=min_price,
            )    
        else:
            print(f"Failed to open shop tab.")

            