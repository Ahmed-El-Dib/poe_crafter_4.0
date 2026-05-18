from inventory.inv_actions import dump_inventory
from macros.currency_parser import parse_currency
from macros.rpa_macros import click, click_image, ctrl_click, locate_center
from shop.shop_utils import *

GRID_ORIGIN = (37, 189)   # center of cell 0,0
GRID_CELL_SIZE = 53
GRID_SIZE = 12


def grid_coords(x: int, y: int) -> tuple[int, int]:
    return (
        GRID_ORIGIN[0] + x * GRID_CELL_SIZE,
        GRID_ORIGIN[1] + y * GRID_CELL_SIZE,
    )

@requires_earnings_side
@requires_shop_open
def earnings_slot_has_currency(coords: tuple[int, int] = GRID_ORIGIN) -> bool:
    currency = parse_currency(coords)
    return currency is not None


@requires_shop_open
def collect_earnings() -> bool:
    """
    Opens earnings side and ctrl-clicks earnings from tab 1.

    Earnings transfer downward into the first tab as withdrawn, so this keeps
    checking from the origin until nothing is found there.
    """
    logger.info("Collecting earnings...")

    origin = grid_coords(0, 0)
    collected_any = False

    while earnings_slot_has_currency(origin):
        logger.info("Currency found at earnings origin. Collecting...")
        ctrl_click(origin, button="right")
        collected_any = True
        time.sleep(0.25)
        dump_inventory()
    if collected_any:
        logger.info("Finished collecting earnings.")
    else:
        logger.info("No earnings found.")

    return collected_any

