
from images.img_paths import *
from stash.tabs.grid_tab import GridStashTab
from stash.tabs.currency_tab import CurrencyTab
from crafters.map_crafter import craft_maps
from utils.initiate_session import requires_game_ready

@requires_game_ready()
def craft_maps(number_of_maps: int = 50):
    item_class = "Map"

    source_tab = GridStashTab(
    )

    currency_tab = CurrencyTab(
    )

    currency_tab.open()
    currency_tab.load()

    print(currency_tab.count_all())

    source_tab.open()

    craft_maps(source_tab, currency_tab, item_class)


if __name__ == "__main__":
    craft_maps()

