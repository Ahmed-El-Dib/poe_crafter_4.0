import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Dict
from functools import wraps
import pyautogui

from macros.rpa_macros import click_image, locate_center
from stash.stash_utils import ensure_stash_open
from utils.initiate_session import requires_game_ready

# -----------------------------
# LOGGER SETUP
# -----------------------------
logger = logging.getLogger(__name__)


# -----------------------------
# DECORATOR
# -----------------------------

@requires_game_ready()
def requires_tab_open(method):
    """
    Ensures:
    - stash is open
    - correct tab is open
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        logger.info(f"[{self.name}] Running '{method.__name__}' (ensure tab open)")

        if not self.ensure_open():
            logger.error(f"[{self.name}] Cannot run '{method.__name__}': tab not open")
            return False

        result = method(self, *args, **kwargs)

        logger.debug(f"[{self.name}] '{method.__name__}' returned -> {result}")
        return result

    return wrapper


# -----------------------------
# BASE TAB
# -----------------------------
Coords = Tuple[int, int]


@dataclass
class StashTab:
    name: str
    navigation_image: str | Path
    open_image: str | Path
    confidence: float = 0.95

    coords: Dict[str, Coords] = field(default_factory=dict)

    def is_open(self) -> bool:
        result = locate_center(self.open_image, confidence=self.confidence) is not None
        logger.debug(f"[{self.name}] is_open -> {result}")
        return result

    def open(self) -> bool:
        logger.info(f"[{self.name}] Attempting to open tab")

        if self.is_open():
            logger.debug(f"[{self.name}] Tab already open")
            return True

        if not ensure_stash_open():
            logger.error(f"[{self.name}] Cannot open tab: stash not open")
            return False

        if not click_image(self.navigation_image, confidence=self.confidence):
            logger.error(f"[{self.name}] Navigation image not found")
            return False

        if not self.is_open():
            logger.error(f"[{self.name}] Clicked tab but failed to verify open")
            return False

        logger.info(f"[{self.name}] Tab successfully opened")
        return True

    def ensure_open(self) -> bool:
        logger.debug(f"[{self.name}] ensure_open called")
        return self.open()

    def load(self) -> bool:
        logger.info(f"[{self.name}] load() called")
        return self.ensure_open()

    def get_coord(self, key: str) -> Optional[Coords]:
        coord = self.coords.get(key)
        logger.debug(f"[{self.name}] get_coord('{key}') -> {coord}")
        return coord

    def set_coord(self, key: str, coord: Coords) -> None:
        self.coords[key] = coord
        logger.debug(f"[{self.name}] set_coord('{key}') -> {coord}")