import logging
import time
import pyautogui

from images.img_paths import (
    SHOP_TEXT, SHOP_OPEN,
    SHOP_SELL_SIDE, SELL_SIDE_OPEN, SHOP_TAB_1, SHOP_TAB_2, SHOP_TAB_3, SHOP_TAB_4, SHOP_TAB_5,
    EARNINGS_SIDE, EARNINGS_SIDE_OPEN
)
from macros.rpa_macros import *
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------
# GENERIC HELPERS
# ------------------------



def retry(action, attempts=2, delay=1):
    for i in range(attempts):
        if action():
            return True
        time.sleep(delay)
    return False


# ------------------------
# SHOP CONTROL
# ------------------------

def requires_shop_open(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        if not ensure_shop_open():
            logger.error(f"{func.__name__}: shop not available")
            return False

        return func(*args, **kwargs)

    return wrapper


def is_shop_open() -> bool:
    return locate_center(SHOP_OPEN, confidence=0.8) is not None


def open_shop() -> bool:
    logger.info("Opening shop...")
    return ctrl_alt_click_image(SHOP_TEXT, confidence=0.8)


def ensure_shop_open() -> bool:
    if is_shop_open():
        return True

    if retry(lambda: open_shop() and is_shop_open()):
        return True

    logger.warning("Resetting UI and retrying shop open...")
    press("esc", times=5)
    time.sleep(1)

    return retry(lambda: open_shop() and is_shop_open())


# ------------------------
# SELL SIDE
# ------------------------

def is_sell_side_open() -> bool:
    return locate_center(SELL_SIDE_OPEN, confidence=0.95) is not None


def open_sell_side() -> bool:
    logger.info("Opening sell side...")
    return click_image(SHOP_SELL_SIDE, confidence=0.95)


def ensure_sell_side_open() -> bool:
    if is_sell_side_open():
        return True

    return retry(lambda: open_sell_side() and is_sell_side_open())

from utils.initiate_session import requires_game_ready
@requires_game_ready()
@requires_shop_open
def requires_sell_side(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not ensure_sell_side_open():
            logger.error(f"{func.__name__}: sell side not available")
            return False
        return func(*args, **kwargs)

    return wrapper


# ------------------------
# EARNINGS SIDE
# ------------------------

def is_earnings_side_open() -> bool:
    return locate_center(EARNINGS_SIDE_OPEN, confidence=0.95) is not None


def open_earnings_side() -> bool:
    logger.info("Opening earnings side...")
    return click_image(EARNINGS_SIDE, confidence=0.95)


def ensure_earnings_side_open() -> bool:
    if is_earnings_side_open():
        return True

    return retry(lambda: open_earnings_side() and is_earnings_side_open())


def requires_earnings_side(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not ensure_earnings_side_open():
            logger.error(f"{func.__name__}: earnings side not available")
            return False
        return func(*args, **kwargs)

    return wrapper


# ------------------------
# TABS (SELL SIDE)
# ------------------------

@requires_shop_open
@requires_sell_side
def open_shop_tab(shop_tab_image: str) -> bool:
    logger.info(f"Opening shop tab: {shop_tab_image}")
    return click_image(shop_tab_image, confidence=0.95)


# ------------------------
# EARNINGS TAB (if needed)
# ------------------------

@requires_shop_open
@requires_earnings_side
def open_earnings_tab() -> bool:
    logger.info("Opening earnings tab...")
    return click_image(EARNINGS_SIDE, confidence=0.95)

