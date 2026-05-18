import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Dict
from functools import wraps

from macros.rpa_macros import click_image, locate_center, press
from utils.initiate_session import requires_game_ready

logger = logging.getLogger(__name__)

Coords = Tuple[int, int]


@dataclass
class UIWindow:
    name: str
    locator_image: str | Path
    open_image: str | Path

    locator_confidence: float = 0.8
    open_confidence: float = 0.9
    open_delay: float = 1.0
    retry_with_escape: bool = True

    coords: Dict[str, Coords] = field(default_factory=dict)

    def is_open(self) -> bool:
        result = locate_center(
            self.open_image,
            confidence=self.open_confidence
        ) is not None

        logger.debug(f"[{self.name}] is_open -> {result}")
        return result

    def open(self) -> bool:
        logger.info(f"[{self.name}] Attempting to open UI")

        if self.is_open():
            logger.info(f"[{self.name}] Already open")
            return True

        if not click_image(self.locator_image, confidence=self.locator_confidence):
            logger.error(f"[{self.name}] Locator image not found")
            return False

        time.sleep(self.open_delay)

        if self.is_open():
            logger.info(f"[{self.name}] Opened successfully")
            return True

        if not self.retry_with_escape:
            logger.error(f"[{self.name}] Clicked locator but failed to verify open")
            return False

        logger.warning(f"[{self.name}] First open attempt failed. Resetting UI")
        press("esc", times=5)
        time.sleep(1)

        if not click_image(self.locator_image, confidence=self.locator_confidence):
            logger.error(f"[{self.name}] Locator image not found on retry")
            return False

        time.sleep(self.open_delay)

        result = self.is_open()

        if result:
            logger.info(f"[{self.name}] Opened successfully after retry")
        else:
            logger.error(f"[{self.name}] Failed to open after retry")

        return result

    def ensure_open(self) -> bool:
        return self.open()

    def load(self) -> bool:
        return self.ensure_open()

    def get_coord(self, key: str) -> Optional[Coords]:
        return self.coords.get(key)

    def set_coord(self, key: str, coord: Coords) -> None:
        self.coords[key] = coord

def requires_ui_open(method):
    @requires_game_ready()
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        logger.info(f"[{self.name}] Running '{method.__name__}' with UI requirement")

        if not self.ensure_open():
            logger.error(f"[{self.name}] Cannot run '{method.__name__}': UI not open")
            return False

        return method(self, *args, **kwargs)

    return wrapper