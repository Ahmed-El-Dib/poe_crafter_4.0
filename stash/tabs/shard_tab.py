import logging
from typing import Optional, Tuple
from dataclasses import dataclass
import pyautogui
from images.img_paths import *
from macros.rpa_macros import *
from macros.item_parser import copy_item
from stash.tabs.base_tab import StashTab, requires_tab_open
from stash.stash_actions import clear_crafting_area, navigate_to_tab
from stash.tabs.currency_tab import CurrencyTab
import time

@dataclass
class ShardTab(StashTab):
    name: str = "shard_tab"
    navigation_image: str = SHARD_TAB_LOCATOR
    open_image: str = SHARD_TAB_OPEN
    confidence: float = 0.95

    @requires_tab_open
    def open_general_tab(self) -> bool:
        return click_image(GENERAL_TAB, confidence=0.8)


    def get_frag(self, shard_img: str, num_frags: int = 1) -> bool:
        self.open_general_tab()
        
        coords = locate_center(shard_img, confidence=0.8)

        if coords is None:
            logging.error(f"[{ShardTab.name}] Could not find shard image: {shard_img}")
            return False
        
        for _ in range(num_frags):
            ctrl_click(coords)
            time.sleep(0.25)

        return True