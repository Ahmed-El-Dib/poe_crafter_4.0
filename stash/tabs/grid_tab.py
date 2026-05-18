import logging
from typing import Optional, Tuple
from dataclasses import dataclass
import pyautogui
from images.img_paths import *
from macros.rpa_macros import click
from macros.item_parser import copy_item
from stash.tabs.base_tab import StashTab, requires_tab_open
from stash.stash_actions import clear_crafting_area, navigate_to_tab
from stash.tabs.currency_tab import CurrencyTab
import time
Coords = Tuple[int, int]
GridIdx = Tuple[int, int]

logger = logging.getLogger(__name__)


@dataclass
class GridStashTab(StashTab):
    name: str = "source_tab"
    navigation_image: str = SOURCE_TAB_LOCATOR
    open_image: str = SOURCE_TAB_OPEN
    grid_origin: Optional[Coords] = (28, 147)
    cell_size: int = 26
    rows: int = 24
    cols: int = 24

    debug_cursor: bool = False

    def grid_coord(self, row: int, col: int) -> Coords:
        if self.grid_origin is None:
            raise ValueError(f"{self.name}: grid_origin is not set.")

        return (
            self.grid_origin[0] + col * self.cell_size,
            self.grid_origin[1] + row * self.cell_size,
        )

    def advance_idx(self, idx: GridIdx) -> GridIdx:
        row, col = idx
        row += 1

        if row >= self.rows:
            row = 0
            col += 1

        return row, col

    def is_done(self, idx: GridIdx) -> bool:
        return idx[1] >= self.cols

    def find_item(
        self,
        item_class: str,
        start_idx: GridIdx = (0, 0),
    ) -> Optional[tuple[GridIdx, Coords]]:
        logger.info(f"[{self.name}] Searching for '{item_class}' from {start_idx}")

        target = item_class.lower()
        start_row, start_col = start_idx
        start_pos = start_col * self.rows + start_row

        for pos in range(start_pos, self.rows * self.cols):
            col = pos // self.rows
            row = pos % self.rows
            coords = self.grid_coord(row, col)

            if self.debug_cursor:
                pyautogui.moveTo(*coords, duration=0.15)
            else:
                pyautogui.moveTo(*coords)

            text = copy_item()
            if not text:
                continue

            if target in text.lower():
                logger.info(f"[{self.name}] Found '{item_class}' at idx ({row}, {col}) coords {coords}")
                return (row, col), coords

        logger.info(f"[{self.name}] No '{item_class}' found")
        return None

    def find_empty_slot(
        self,
        start_idx: GridIdx = (0, 0),
    ) -> Optional[tuple[GridIdx, Coords]]:
        logger.info(f"[{self.name}] Searching for empty slot from {start_idx}")

        start_row, start_col = start_idx
        start_pos = start_col * self.rows + start_row

        for pos in range(start_pos, self.rows * self.cols):
            col = pos // self.rows
            row = pos % self.rows
            coords = self.grid_coord(row, col)

            if self.debug_cursor:
                pyautogui.moveTo(*coords, duration=0.15)
            else:
                pyautogui.moveTo(*coords)

            text = copy_item()

            # Empty slot condition
            if not text or not text.strip():
                logger.info(f"[{self.name}] Found empty slot at idx ({row}, {col}) coords {coords}")
                return (row, col), coords

        logger.info(f"[{self.name}] No empty slot found")
        return None

    def click_first_empty_slot(self) -> bool:
        result = self.find_empty_slot()
        if result is None:
            return False

        _, coords = result
        pyautogui.moveTo(*coords)
        time.sleep(0.5)  # small delay to ensure cursor is in place
        pyautogui.click()
        return True
    
    @requires_tab_open
    def pick_first_matching_item(
        self,
        item_class: str,
        start_idx: GridIdx = (0, 0),
    ) -> Optional[GridIdx]:
        found = self.find_item(item_class, start_idx)

        if found is None:
            return None

        idx, coords = found
        click(coords)
        return idx

    
    def move_next_item_to_crafter(
        self,
        item_class: str,
        crafting_tab: CurrencyTab,
        start_idx: GridIdx = (0, 0),
    ) -> Optional[GridIdx]:
        logger.info(f"[{self.name}] Moving next '{item_class}' to crafter from {start_idx}")

        if not clear_crafting_area(crafting_tab.navigation_image, crafting_tab.craft_coords):
            logger.error(f"[{self.name}] Failed to clear crafting area")
            return None

        if not self.ensure_open():
            logger.error(f"[{self.name}] Failed to return to source tab")
            return None

        found_idx = self.pick_first_matching_item(item_class, start_idx)

        if found_idx is None:
            logger.warning(f"[{self.name}] No matching item found")
            return None

        if not navigate_to_tab(crafting_tab.navigation_image):
            logger.error(f"[{self.name}] Failed to return to crafting tab")
            return None

        click(crafting_tab.craft_coords)

        next_idx = self.advance_idx(found_idx)
        logger.info(f"[{self.name}] Item moved. Next search starts at {next_idx}")

        return next_idx