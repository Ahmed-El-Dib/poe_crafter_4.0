from shop.shop_utils import *
from shop.shop_tab import collect_earnings
from stash.stash_utils import safe_place_in_completed_tab, create_default_completed_tab
from stash.tabs.grid_tab import GridStashTab
from utils.initiate_session import requires_game_ready
from macros.rpa_macros import *
from images.image_utils import locate_center
from images.img_paths import *
from inventory.inv_actions import dump_inventory
from inventory.price_from_inv import price_from_inv
from macros.map_parser import parse_map_mods
from pricers.map_pricer import price_map
@requires_game_ready()
def main():
    print(locate_center(INVENTORY_EMPTY))
    # exit()
    price_from_inv(parse_func=parse_map_mods, price_func=price_map, sell_tab = SHOP_TAB_3)

if __name__ == "__main__":
    main()