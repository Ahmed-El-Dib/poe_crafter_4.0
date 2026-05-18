from .stash_utils import requires_stash_open
from images.img_paths import *
from config import *
from macros.rpa_macros import *


@requires_stash_open
def clear_crafting_area(tab_identifier_img=CURRENCY_TAB, crating_area_coords=CURRENCY_CRAFT_COORDS):
    """
    Clear the crafting area by navigating to the specified tab and ctrl-clicking the crafting area.
    """
    if not navigate_to_tab(tab_identifier_img):
        ctrl_click(crating_area_coords)
        print("Clearing crafting area in case of obstruction.")
    if not navigate_to_tab(tab_identifier_img):
        print(f"Failed to navigate to tab with identifier {tab_identifier_img} for clearing crafting area.")
        return False

    ctrl_click(crating_area_coords)


    return True
    
@requires_stash_open
def navigate_to_tab(tab_identifier_img, tab_open_img=None):
    """
    Navigate to a stash tab by clicking on its identifier image.
    """
    if not click_image(tab_identifier_img, confidence=0.8):
        print(f"Cannot see tab identifier {tab_identifier_img}.")
        return False
    if tab_open_img and not locate_center(tab_open_img, confidence=0.8):
        print(f"Tab {tab_identifier_img} clicked but open state {tab_open_img} not detected.")
        return False


    return True