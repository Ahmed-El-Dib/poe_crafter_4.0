import logging
from images.img_paths import *
from macros.rpa_macros import *
from functools import wraps
from macros.item_parser import copy_item
# Configure logging (adjust level as needed)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def is_stash_open() -> bool:
    result = locate_center(STASH_OPEN, confidence=0.8) is not None
    logger.debug(f"is_stash_open -> {result}")
    return result


def open_stash() -> bool:
    """
    Only call this when stash is known to be closed.
    """
    logger.info("Attempting to open stash...")
    result = click_image(STASH_TEXT, confidence=0.8)
    time.sleep(1)
    logger.debug(f"open_stash click result -> {result}")
    return result


def ensure_stash_open() -> bool:
    """
    Safe to call anytime.
    """
    logger.info("Ensuring stash is open...")

    if is_stash_open():
        logger.info("Stash already open.")
        return True

    logger.info("Stash not open. Trying to open...")
    if open_stash() and is_stash_open():
        logger.info("Stash opened successfully.")
        return True

    logger.warning("First attempt failed. Sending ESC to reset UI...")
    press("esc", times=5)
    time.sleep(1)

    logger.info("Retrying to open stash...")
    success = open_stash() and is_stash_open()

    if success:
        logger.info("Stash opened successfully after retry.")
    else:
        logger.error("Failed to open stash after retry.")

    return success



def requires_stash_open(func):
    # @requires_game_ready()
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Running '{func.__name__}' with stash requirement...")

        if not ensure_stash_open():
            logger.error(f"Cannot run {func.__name__}: stash is not open.")
            return False

        logger.info(f"Stash confirmed open. Executing '{func.__name__}'...")
        result = func(*args, **kwargs)

        logger.debug(f"{func.__name__} returned -> {result}")
        return result

    return wrapper
import time
import win32api
import win32con

MODIFIER_KEYS = [
    win32con.VK_SHIFT,
    win32con.VK_CONTROL,
    win32con.VK_MENU,  # Alt
]

def key_down(vk):
    win32api.keybd_event(vk, 0, 0, 0)

def key_up(vk):
    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
def is_key_down(vk):
    return bool(win32api.GetAsyncKeyState(vk) & 0x8000)
def reset_modifier_keys():
    print("Shift:", is_key_down(win32con.VK_SHIFT))
    print("Ctrl:", is_key_down(win32con.VK_CONTROL))
    print("Alt:", is_key_down(win32con.VK_MENU))
    # force down
    for vk in MODIFIER_KEYS:
        key_down(vk)

    time.sleep(0.05)

    # release
    for vk in MODIFIER_KEYS:
        key_up(vk)

    time.sleep(0.05)

    # release again for safety
    for vk in MODIFIER_KEYS:
        key_up(vk)

def crafting_retry_inplace(crafting_coords):
    move_mouse_from_view()
    pyautogui.click()  # click to ensure focus and release any held keys
    pyautogui.moveTo(*crafting_coords,0.2)
    # release all keys
    reset_modifier_keys()

    original_description = copy_item()

    if original_description is None or original_description.strip() == "":
        logger.error("Failed to copy item description for in-place retry.")
        return False
    time.sleep(0.5)
    logger.info("In-place crafting retry completed successfully.")
    return True

def crafting_safe_retry(crafting_coords, max_attempts: int = 5, delay: float = 0.5) -> bool:
    move_mouse_from_view()
    pyautogui.click()  # click to ensure focus and release any held keys
    pyautogui.moveTo(*crafting_coords,0.2)
    # release all keys
    reset_modifier_keys()

    original_description = copy_item()

    if original_description is None or original_description.strip() == "":
        logger.error("Failed to copy item description. Attempting to drop item.")
        pyautogui.click()  # left-click to drop item

        recovered_description = None

        for attempt in range(1, max_attempts + 1):
            time.sleep(delay)

            recovered_description = copy_item()

            if recovered_description and recovered_description.strip():
                logger.info(f"Recovered item description on attempt {attempt}.")
                break

            logger.warning(f"Attempt {attempt} failed to recover item description.")

        if not recovered_description or recovered_description.strip() == "":
            logger.error("Failed to recover item description after dropping item.")
            return False

        original_description = recovered_description

        # Pick item back up
        pyautogui.click()
        time.sleep(delay)

    # Place item in completed tab
    if not safe_place_in_completed_tab():
        logger.error("Failed to place item in completed tab.")
        return False

    time.sleep(delay)

    # Verify item in completed tab
    placed_description = copy_item()

    if not placed_description or placed_description.strip() == "":
        logger.error("Failed to read item after placing in completed tab.")
        return False

    if placed_description.strip() != original_description.strip():
        logger.error("Placed item does not match original item description.")
        return False

    logger.info("Safe retry completed successfully.")
    return True


def create_default_completed_tab():
    from stash.tabs.grid_tab import GridStashTab
    return GridStashTab(
        name="Completed",
        navigation_image=COMPLETED_TAB_LOCATOR,
        open_image=COMPLETED_TAB_OPEN,
        confidence=0.95,
    )

def safe_place_in_completed_tab():
    comp_tab = create_default_completed_tab()
    if not comp_tab.ensure_open():
        logger.error("Failed to open Completed tab for placing item.")
        return False

    # click first empty slot in completed tab
    if not comp_tab.click_first_empty_slot():
        logger.error("Failed to find empty slot in Completed tab.")
        return False

    logger.info("Item placed in Completed tab successfully.")
    return True