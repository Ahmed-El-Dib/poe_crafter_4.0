import logging

from images.img_paths import SHOP_TAB_3
from shop.shop_utils import ensure_shop_open, open_shop_tab
from pricers.price_from_inv import price_from_inv
from pricers.map_pricer import price_map, MIN_PRICE
from macros.map_parser import parse_map_mods
from pricers.discount import get_discounted_price
from utils.initiate_session import requires_game_ready

logger = logging.getLogger(__name__)

@requires_game_ready()
def sell_crafted_maps_from_inventory(
    sell_tab_image,
    discount=None,
    discount_type="%",
    min_price=MIN_PRICE,
):
    logger.info("Starting crafted map selling workflow...")

    if not ensure_shop_open():
        logger.error("Could not open shop.")
        return False

    if not open_shop_tab(sell_tab_image):
        logger.error("Could not open requested sell tab.")
        return False

    result = price_from_inv(
        parse_func=parse_map_mods,
        price_func=price_map,
        discount_func=get_discounted_price,
        discount=discount,
        discount_type=discount_type,
        min_price=MIN_PRICE,
        stop_on_empty=False,  # Continue through entire inventory
    )

    logger.info(
        f"Finished selling crafted maps. "
        f"Priced={result['priced_count']}, "
        f"Skipped={result['skipped_count']}, "
        f"Avg={result['avg_price']:.2f}"
    )

    return result

if __name__ == "__main__":
    sell_crafted_maps_from_inventory(SHOP_TAB_3, discount=10, discount_type="%")