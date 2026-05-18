from focus_window import focus_window
from shop.shop_tab import collect_earnings
from workflows.craft_and_sell_maps import craft_and_sell_maps
from workflows.sell_crafted_maps import sell_crafted_maps_from_inventory
from images.img_paths import SHOP_TAB_1, SHOP_TAB_2, SHOP_TAB_3, SHOP_TAB_4, SHOP_TAB_5
from inventory.inv_actions import is_inventory_empty
from shop.shop_actions import reprice_maps_in_shop
import time



# collect_earnings()  
# reprice_maps_in_shop(discount=10, min_price=34)
# sell_crafted_maps_from_inventory(SHOP_TAB_1, discount=0, min_price=34)
craft_and_sell_maps()
# from shop.shop_tab import collect_earnings, earnings_slot_has_currency
# from inventory.inv_actions import dump_inventory
# while earnings_slot_has_currency():
#     dump_inventory()
#     collect_earnings()