import logging

from shop.shop_tab import collect_earnings
from stash.tabs.currency_tab import CurrencyTab
from stash.tabs.grid_tab import GridStashTab
from utils.initiate_session import requires_game_ready
from crafters.map_crafter import craft_maps_batch
from workflows.sell_crafted_maps import sell_crafted_maps_from_inventory
from images.img_paths import SHOP_TAB_1, SHOP_TAB_2, SHOP_TAB_3, SHOP_TAB_4, SHOP_TAB_5
from pricers.map_pricer import MIN_PRICE

logger = logging.getLogger(__name__)


SELL_TABS = [
    SHOP_TAB_2,
    SHOP_TAB_3,
    # SHOP_TAB_5,
    # SHOP_TAB_4,
    # # 
    
    # SHOP_TAB_1,
    
   
]


@requires_game_ready()
def craft_and_sell_maps(
    maps_per_batch: int = 50,
    item_class: str = "Map",
    discount=10,
    discount_type="%",
    min_price=MIN_PRICE,
):
    logger.info("Starting craft-and-sell map workflow...")

    source_tab = GridStashTab()
    currency_tab = CurrencyTab()

    logger.info("Opening and loading currency tab...")
    currency_tab.open()
    currency_tab.load()

    logger.info(f"Currency tab contents: {currency_tab.count_all()}")

    logger.info("Opening source map tab...")
    source_tab.open()

    start_idx = (0, 0)
    batch_num = 0

    while not source_tab.is_done(start_idx):
        sell_tab_image = SELL_TABS[batch_num % len(SELL_TABS)]

        logger.info(
            f"Starting batch {batch_num + 1}. "
            f"Crafting up to {maps_per_batch} maps."
        )

        result = craft_maps_batch(
            number_of_maps=maps_per_batch,
            source_tab=source_tab,
            currency_tab=currency_tab,
            item_class=item_class,
            start_idx=start_idx,
        )

        if result is None:
            logger.info("Crafter returned no result. Stopping workflow.")
            break

        crafted_count = result.get("crafted_count", 0)
        next_idx = result.get("next_idx", start_idx)

        if crafted_count <= 0:
            logger.info("No maps crafted this batch. Stopping workflow.")
            break

        logger.info(
            f"Batch {batch_num + 1} crafted {crafted_count} maps. "
            f"Selling into shop tab {batch_num % len(SELL_TABS) + 3}."
        )

        sell_result = sell_crafted_maps_from_inventory(
            sell_tab_image=sell_tab_image,
            discount=discount,
            discount_type=discount_type,
            min_price=min_price,
        )

        logger.info(f"Sell result: {sell_result}")

        start_idx = next_idx
        batch_num += 1
        collect_earnings()
    logger.info("Craft-and-sell workflow complete.")
    return True


if __name__ == "__main__":
    craft_and_sell_maps()