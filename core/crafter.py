"""
Main crafting orchestrator for Path of Exile jewel crafting (pywinauto / Win32).
"""

import time
import logging
import pyperclip
from typing import Optional, List

from config import *
# from images.img_paths import *  
from macros.currency_macros import *
from macros.rpa_macros import *
from macros.item_parser import parse_item_mods

logger = logging.getLogger(__name__)


class JewelCrafter:
    def __init__(self,
                 mandatory_mods: List[str] = None,
                 optional_mods: List[str] = None,
                 num_mandatory_required: int = 1,
                 num_optional_required: int = 0,
                 no_slam_mods: List[str] = None,
                 no_regal_mods: List[str] = None,
                 no_annul_mods: List[str] = None,
                 crafting_location = CURRENCY_CRAFT_COORDS):


        self.mandatory_mods = mandatory_mods
        self.optional_mods = optional_mods
        self.num_mandatory_required = num_mandatory_required
        self.num_optional_required = num_optional_required
        self.num_mods_needed = num_mandatory_required + num_optional_required

        self.no_slam_mods = no_slam_mods
        self.no_regal_mods = no_regal_mods
        self.no_annul_mods = no_annul_mods
        self.crafintg_location = crafting_location

        self.current_item_mods = []
        self.current_item_description = ""

        self.items_crafted = 0
        self.items_failed = 0

        self.spamming = False
    

    def _craft_item(self) -> bool:
        try:
            max_attempts = 3
            attempts = 0

            while attempts < max_attempts:
                if not self._read_item_state():
                    logger.error("Failed to read item state")
                    return False

                if self._check_requirements():
                    logger.info("Item meets crafting requirements")
                    return True

                action = self._determine_next_action()
                if not action:
                    logger.warning("No valid action found")
                    break

                if not self._execute_action(action):
                    logger.error(f"Failed to execute action: {action}")
                    break

                attempts += 1
                time.sleep(0.5)

            logger.warning(f"Failed to craft item after {attempts} attempts")
            return False

        except Exception as e:
            logger.error(f"Error in crafting process: {e}")
            return False

    def _read_item_state(self) -> bool:
        try:
            
            self.current_item_mods = parse_item_mods(self.crafintg_location)
            print(self.current_item_mods)
            logger.debug(f"Read item with {len(self.current_item_mods)} mods")
            return True

        except Exception as e:
            logger.error(f"Error reading item state: {e}")
            return False

    def _check_requirements(self) -> bool:
        try:
            mandatory_count = 0
            optional_count = 0

            for mod in self.current_item_mods:
                mod_name = mod['name'].lower()

                if any(mandatory.lower() in mod_name for mandatory in self.mandatory_mods):
                    print(f"Found mandatory mod: {mod_name}")
                    mandatory_count += 1

                # if any(optional.lower() in mod_name for optional in self.optional_mods):
                #     optional_count += 1

            meets_mandatory = mandatory_count >= self.num_mandatory_required
            meets_optional = optional_count >= self.num_optional_required

            logger.debug(f"Mandatory: {mandatory_count}/{self.num_mandatory_required}, "
                        f"Optional: {optional_count}/{self.num_optional_required}")

            return meets_mandatory and meets_optional

        except Exception as e:
            logger.error(f"Error checking requirements: {e}")
            return False

    def _determine_next_action(self) -> Optional[str]:
        try:
            num_mods = len(self.current_item_mods)
            good_mods = self._count_good_mods()

            if num_mods == 0:
                return 'transmute'

            if num_mods == 1 and good_mods == 1:
                return 'augment'

            if num_mods == 2:
                if good_mods >= 1:
                    return 'regal'
                else:
                    return 'scoure'

            if num_mods == 3:
                if good_mods == 3 and self.num_mods_needed == 4:
                    return 'slam'
                elif good_mods == 2 and self.num_mods_needed == 3:
                    return 'slam'
                elif good_mods == 3 and self.num_mods_needed == 4:
                    return 'annul'

            if num_mods == 4 and good_mods == 3:
                return 'annul'

            return 'alteration'

        except Exception as e:
            logger.error(f"Error determining next action: {e}")
            return None

    def _count_good_mods(self) -> int:
        try:
            count = 0
            for mod in self.current_item_mods:
                mod_name = mod['name'].lower()
                if (any(mandatory.lower() in mod_name for mandatory in self.mandatory_mods) or
                        any(optional.lower() in mod_name for optional in self.optional_mods)):
                    count += 1
            return count
        except Exception as e:
            logger.error(f"Error counting good mods: {e}")
            return 0

    def _execute_action(self, action: str) -> bool:
        try:
            if action == 'transmute':
                self.spamming = False
                return use_currency(TRANS)
            
            elif action == 'augment':
                if not self.spamming:
                    return use_currency(AUG)
                else:            
                    return alt_currency(AUG)
                
            elif action == 'alteration':
                if not self.spamming:
                    self.spamming = True
                    return use_currency(ALT)
                else:
                    return spam_currency(ALT)
                
            elif action == 'regal':
                return use_currency(REGAL)
            
            elif action == 'scoure':
                return use_currency(SCOURE)
            
            elif action == 'slam':
                return use_currency(EXALT)
            
            elif action == 'annul':
                return use_currency(ANNUL)
            
            else:
                logger.error(f"Unknown action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return False

    def run_crafting_session(self, max_items: int = None):
        try:
            logger.info("Starting crafting session...")



            items_processed = 0
            while max_items is None or items_processed < max_items:
                if not self._craft_item():
                    logger.info("No more items to craft")
                    break

                items_processed += 1
                logger.info(f"Processed {items_processed} items")

            self._print_statistics()

        except Exception as e:
            logger.error(f"Error in crafting session: {e}")

    def _print_statistics(self):
        logger.info("=== Crafting Session Statistics ===")
        logger.info(f"Items successfully crafted: {self.items_crafted}")
        logger.info(f"Items failed: {self.items_failed}")
        total = self.items_crafted + self.items_failed
        if total > 0:
            logger.info(f"Success rate: {self.items_crafted/total*100:.1f}%")
        else:
            logger.info("Success rate: n/a (no items finished)")


