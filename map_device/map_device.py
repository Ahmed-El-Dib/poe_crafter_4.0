import logging
from dataclasses import dataclass

from ui.UIWindow import UIWindow, requires_ui_open
from macros.rpa_macros import click, click_image, locate_center, modified_click, press
from images.img_paths import *

logger = logging.getLogger(__name__)



@dataclass
class MapDeviceUI(UIWindow):
    name: str = "map_device"

    locator_image: str = MAP_DEVICE_LOCATOR
    open_image: str = MAP_DEVICE_OPEN

    locator_confidence: float = 0.8
    open_confidence: float = 0.8

    open_delay: float = 1.0
    retry_with_escape: bool = True
    
  
    @requires_ui_open
    def open_uber(self, uber_frag_img: str, confidence: float = 0.8) -> bool:
        self.open_inventory()
        coords = locate_center(uber_frag_img, confidence=confidence, retry_with_mouse_clear=False)

        if coords is None:
            logger.error(f"[{self.name}] Could not find uber fragment: {uber_frag_img}")
            return False

        modified_click(coords, hotkeys=["alt"], button="right")
        return True
    
    # add a temporary inventory helper - to be moved to a more appropriate location later
    def open_inventory(self) -> bool:
        if not locate_center(INVENTORY_OPEN, confidence=0.8, retry_with_mouse_clear=False):
            logger.error(f"[{self.name}] Could not find inventory open image")
            press("i")
        return locate_center(INVENTORY_OPEN, confidence=0.8, retry_with_mouse_clear=False) is not None   

    def activate(
        self,
        activation_img: str = ACTIVATE_READY,
        maven: bool = False,
        confidence: float = 0.9,
        grayscale: bool = False
    ) -> bool:
        coords = locate_center(
            activation_img,
            confidence=confidence,
            grayscale=grayscale,
            retry_with_mouse_clear=False
        )

        if coords is None:
            logger.error(f"[{self.name}] Could not find activation image: {activation_img}")
            return False

        if maven and not self.add_maven(confidence=confidence, grayscale=grayscale):
            logger.error(f"[{self.name}] Could not enable Maven")
            return False

        click(coords)
        return True
    
    def add_maven(
        self,
        maven_activation_img: str = MAVEN_ACTIVATE,
        maven_ready_img: str = MAVEN_ACTIVATE_READY,
        confidence: float = 0.95,
        grayscale: bool = False
    ) -> bool:
        if locate_center(maven_ready_img, confidence=confidence, grayscale=grayscale, retry_with_mouse_clear=False):
            logger.info(f"[{self.name}] Maven already active")
            return True

        coords = locate_center(
            maven_activation_img,
            confidence=confidence,
            grayscale=grayscale,
            retry_with_mouse_clear=False
        )

        if coords is None:
            logger.error(f"[{self.name}] Could not find Maven activation image: {maven_activation_img}")
            return False

        click(coords)

        return locate_center(
            maven_ready_img,
            confidence=confidence,
            grayscale=grayscale,
            retry_with_mouse_clear=False
        ) is not None
            
        