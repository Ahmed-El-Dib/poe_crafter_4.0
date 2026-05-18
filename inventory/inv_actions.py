import logging
import time

from macros.rpa_macros import *
from images.img_paths import *
from stash.stash_actions import *

logger = logging.getLogger(__name__)

INVENTORY_ORIGIN = (1292, 612)
INVENTORY_CELL_SIZE = 53
INVENTORY_ROWS = 5
INVENTORY_COLS = 12

INV_BOUNDS_TL = (1263, 582)
INV_BOUNDS_BR = (1899, 848)


def mouse_in_inventory_bounds() -> bool:
    x, y = pyautogui.position()
    # if out of bounds, bring it to origin, wait 1 second, and check again to avoid false negatives from quick movements
    if not (INV_BOUNDS_TL[0] <= x <= INV_BOUNDS_BR[0] and INV_BOUNDS_TL[1] <= y <= INV_BOUNDS_BR[1]):
        pyautogui.moveTo(INVENTORY_ORIGIN)
        time.sleep(0.1)
        x, y = pyautogui.position()
    return (
        INV_BOUNDS_TL[0] <= x <= INV_BOUNDS_BR[0]
        and INV_BOUNDS_TL[1] <= y <= INV_BOUNDS_BR[1]
    )


def wait_until_mouse_in_inventory(max_retries=10, delay=1) -> bool:
    
    for _ in range(max_retries):
        if mouse_in_inventory_bounds():
            return True

        logger.warning("Mouse outside inventory bounds. Waiting...")
        time.sleep(delay)

    return False

def inventory_grid_coord(row: int, col: int) -> tuple[int, int]:
    return (
        INVENTORY_ORIGIN[0] + col * INVENTORY_CELL_SIZE,
        INVENTORY_ORIGIN[1] + row * INVENTORY_CELL_SIZE,
    )


def is_inventory_empty(confidence: float = 0.99) -> bool:
    empty = locate_center(INVENTORY_EMPTY, confidence=confidence) is not None
    logger.debug(f"is_inventory_empty -> {empty}")
    return empty


def dump_inventory(
    tab_identifier_img=COMPLETED_TAB_LOCATOR,
    tab_open_img=COMPLETED_TAB_OPEN,
    confidence: float = 0.9,
    click_delay: float = 0.05,
    pass_delay: float = 0.2,
    max_passes: int = 5,
) -> bool:
    logger.info("Starting inventory dump...")

    logger.info("Navigating to dump stash tab...")
    if not navigate_to_tab(tab_identifier_img, tab_open_img):
        logger.error("Failed to navigate to dump stash tab.")
        return False

    if is_inventory_empty(confidence):
        logger.info("Inventory already empty.")
        return True

    for pass_num in range(1, max_passes + 1):
        logger.info(f"Inventory not empty. Dump pass {pass_num}/{max_passes}...")

        for row in range(INVENTORY_ROWS):
            for col in range(INVENTORY_COLS):

                if is_inventory_empty(confidence):
                    logger.info(f"Inventory emptied during pass {pass_num}.")
                    return True

                if not wait_until_mouse_in_inventory():
                    logger.error("Mouse stayed outside inventory bounds. Stopping dump.")
                    return False

                coords = inventory_grid_coord(row, col)

                logger.debug(
                    f"Ctrl-right-clicking inventory cell ({row}, {col}) at {coords}"
                )

                ctrl_click(coords, button="right")
                time.sleep(click_delay)

        time.sleep(pass_delay)

        if is_inventory_empty(confidence):
            logger.info(f"Inventory emptied after pass {pass_num}.")
            return True

    logger.error("Inventory still not empty after maximum dump passes.")
    return False