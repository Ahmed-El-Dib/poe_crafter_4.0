from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict

import pyautogui

from stash.tabs.base_tab import StashTab, requires_tab_open
from macros.currency_parser import read_currency, copy_item
from macros.rpa_macros import locate_center
from images.img_paths import *
from config import *
import time

Coords = Tuple[int, int]


@dataclass
class CurrencyStack:
    name: str
    coords: Coords
    count: int


@dataclass
class CurrencyTab(StashTab):
    name: str = "currency"
    navigation_image: str = CURRENCY_TAB
    open_image: str = CURRENCY_TAB_OPEN
    craft_coords: Coords = CURRENCY_CRAFT_COORDS   
    confidence: float = 0.8

    spamming: bool = False

    currency_images: Dict[str, str] = field(default_factory=lambda: {
        "alteration": ALT_IMG,
        "augment": AUG_IMG,
        "transmute": TRANS_IMG,
        "exalt": EXALT_IMG,
        "scoure": SCOURE_IMG,
        "annul": ANNUL_IMG,
        "regal": REGAL_IMG,
    })

    stacks: Dict[str, CurrencyStack] = field(default_factory=dict)

    @requires_tab_open
    def load(self) -> bool:
        for currency_name in self.currency_images:
            self.refresh_stack(currency_name)

        return True

    def refresh_stack(
        self,
        currency_name: str,
        retries: int = 3,
        retry_delay: float = 0.25,
    ) -> bool:
        image = self.currency_images.get(currency_name)

        if image is None:
            print(f"No locator image registered for currency: {currency_name}")
            return False

        for attempt in range(1, retries + 1):
            coords = locate_center(image, confidence=self.confidence)

            if coords is None:
                print(
                    f"[Attempt {attempt}/{retries}] "
                    f"No visible stack found for: {currency_name}"
                )

                if attempt < retries:
                    time.sleep(retry_delay)
                continue

            parsed = self.parse_currency(coords)

            if parsed is None:
                print(
                    f"[Attempt {attempt}/{retries}] "
                    f"Could not parse currency at {coords}"
                )

                if attempt < retries:
                    time.sleep(retry_delay)
                continue

            if parsed["name"] != currency_name:
                print(
                    f"[Attempt {attempt}/{retries}] "
                    f"Expected {currency_name}, but parsed {parsed['name']}"
                )

                if attempt < retries:
                    time.sleep(retry_delay)
                continue

            self.stacks[currency_name] = CurrencyStack(
                name=currency_name,
                coords=coords,
                count=parsed["count"],
            )

            return True

        self.stacks.pop(currency_name, None)
        return False

    def get_stack(self, currency_name: str) -> Optional[CurrencyStack]:
        stack = self.stacks.get(currency_name)

        if stack is not None and stack.count > 0:
            return stack

        if self.refresh_stack(currency_name):
            return self.stacks[currency_name]

        return None

    def parse_currency(self, coords: Coords) -> Optional[dict]:
        pyautogui.moveTo(coords[0], coords[1])

        description = copy_item()
        return read_currency(description)

    def verify_stack(self, currency_name: str, stack: CurrencyStack) -> bool:
        parsed = self.parse_currency(stack.coords)

        if parsed is None:
            return False

        if parsed["name"] != currency_name:
            return False

        stack.count = parsed["count"]
        return stack.count > 0

    def count_all(self) -> dict:
        """
        Refresh every tracked currency and return counts.
        """
        counts = {}

        for currency_name in self.currency_images:
            if self.refresh_stack(currency_name):
                counts[currency_name] = self.stacks[currency_name].count
            else:
                counts[currency_name] = 0

        return counts

    @requires_tab_open
    def use(self, currency_name: str, spammable: bool = False) -> bool:
        stack = self.get_stack(currency_name)

        if stack is None:
            print(f"Out of {currency_name}.")
            return False

        if not self.verify_stack(currency_name, stack):
            print(f"Cached {currency_name} stack invalid. Refreshing.")

            if not self.refresh_stack(currency_name):
                print(f"Out of {currency_name}.")
                return False

            stack = self.stacks[currency_name]

        self.use_currency(stack.coords, spammable=spammable)
        self.decrement(currency_name)

        return True


    def use_many(self, currency_name: str, times: int, spammable: bool = True) -> bool:
        if times <= 0:
            return False

        stack = self.get_stack(currency_name)

        if stack is None or stack.count < times:
            print(f"Not enough {currency_name}. Need {times}, have {stack.count if stack else 0}.")
            return False

        self.use(currency_name, spammable=spammable)

        for _ in range(times - 1):
            self.spam_currency()
            self.decrement(currency_name)

        self.stop_spamming()
        return True


    def use_currency(
        self,
        stack_coords: Coords,
        target_coords: Coords = CURRENCY_CRAFT_COORDS,
        spammable: bool = False,
    ) -> None:
        pyautogui.keyUp("shift")

        if spammable:
            pyautogui.keyDown("shift")

        pyautogui.moveTo(stack_coords[0], stack_coords[1], duration=0.01)
        pyautogui.rightClick()

        pyautogui.moveTo(target_coords[0], target_coords[1], duration=0.01)
        pyautogui.leftClick()


    def spam_currency(self) -> None:
        pyautogui.leftClick()


    def alt_currency(self) -> None:
        pyautogui.keyDown("alt")
        pyautogui.leftClick()
        pyautogui.keyUp("alt")


    def stop_spamming(self) -> None:
        pyautogui.keyUp("shift")
        self.spamming = False

    def decrement(self, currency_name: str, amount: int = 1) -> None:
        stack = self.stacks.get(currency_name)

        if stack is None:
            return

        stack.count -= amount

        if stack.count <= 0:
            self.stacks.pop(currency_name, None)


    def trans(self) -> bool:
        self.stop_spamming()
        return self.use("transmute", spammable=False)


    def alt(self) -> bool:
        stack = self.get_stack("alteration")

        if stack is None:
            print("Out of alteration.")
            return False

        if self.spamming:
            self.spam_currency()
            self.decrement("alteration")
            return True

        self.spamming = True
        return self.use("alteration", spammable=True)


    def aug(self) -> bool:
        stack = self.get_stack("augment")

        if stack is None:
            print("Out of augment.")
            return False

        if self.spamming:
            self.alt_currency()
            self.decrement("augment")
            return True

        self.stop_spamming()
        return self.use("augment", spammable=False)


    def slam(self, times: int = 1) -> bool:
        self.stop_spamming()
        return self.use_many("exalt", times, spammable=True)


    def scoure(self) -> bool:
        self.stop_spamming()
        return self.use("scoure", spammable=False)


    def annul(self) -> bool:
        self.stop_spamming()
        return self.use("annul", spammable=False)


    def regal(self) -> bool:
        self.stop_spamming()
        return self.use("regal", spammable=False)


