import logging

from inventory.inv_actions import (
    INVENTORY_ROWS,
    INVENTORY_COLS,
    inventory_grid_coord,
    is_inventory_empty,
    wait_until_mouse_in_inventory,
)
from shop.shop_actions import place_item_in_shop

logger = logging.getLogger(__name__)

def price_from_inv(
    parse_func,
    price_func,
    discount_func=None,
    discount=None,
    discount_type="%",
    stop_on_empty=True,
    min_price=1,
) -> dict:
    total_price = 0
    priced_count = 0
    skipped_count = 0

    logger.info("Starting inventory pricing...")

    for col in range(INVENTORY_COLS):
        for row in range(INVENTORY_ROWS):

            if is_inventory_empty():
                avg_price = total_price / priced_count if priced_count else 0
                logger.info(
                    f"Inventory empty. Stopping early. "
                    f"Priced={priced_count}, skipped={skipped_count}, avg={avg_price:.2f}"
                )
                return {
                    "priced_count": priced_count,
                    "skipped_count": skipped_count,
                    "total_price": total_price,
                    "avg_price": avg_price,
                }

            coords = inventory_grid_coord(row, col)

            if not wait_until_mouse_in_inventory():
                logger.error("Mouse stayed outside inventory bounds. Stopping pricing.")
                return {
                    "priced_count": priced_count,
                    "skipped_count": skipped_count,
                    "total_price": total_price,
                    "avg_price": total_price / priced_count if priced_count else 0,
                }

            logger.debug(f"Parsing inventory cell ({row}, {col}) at {coords}")
            item = parse_func(coords)

            if item is None:
                logger.info(f"No item found at ({row}, {col}).")

                if stop_on_empty:
                    avg_price = total_price / priced_count if priced_count else 0
                    return {
                        "priced_count": priced_count,
                        "skipped_count": skipped_count,
                        "total_price": total_price,
                        "avg_price": avg_price,
                    }

                continue

            price = price_func(item)

            if price is None:
                skipped_count += 1
                logger.warning(f"No price returned for item at ({row}, {col}). Skipping.")
                continue

            if discount_func and discount is not None:
                price = discount_func(price, discount, discount_type, min_price)

            price = int(round(price))

            logger.info(f"Placing item at ({row}, {col}) with price: {price}")
            place_item_in_shop(coords[0], coords[1], price)

            total_price += price
            priced_count += 1

    avg_price = total_price / priced_count if priced_count else 0
    return {
        "priced_count": priced_count,
        "skipped_count": skipped_count,
        "total_price": total_price,
        "avg_price": avg_price,
    }