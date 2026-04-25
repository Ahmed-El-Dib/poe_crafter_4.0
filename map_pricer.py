MAP_SUFFIX_TARGETS = [
    "of Collection",
    "of Splinters",
    "of Defiance",
    "of Imbibing",
    "of Persistence",
    "of Decaying"
]

MAP_PREFIX_TARGETS = [
    "Antagonist's",
    "Diluted",
    "Hungering",
    "Punishing",
    "Stalwart",
    "Valdo's",
]

def is_perfect_suffix(map):
    mods = map.get("mods", [])
    return sum(1 for mod in mods if mod["type"] == "suffix" and mod["name"] in MAP_SUFFIX_TARGETS) >= 3


def is_perfect_prefix(map):
    # has 3 target prefixes
    mods = map.get("mods", [])
    return sum(1 for mod in mods if mod["type"] == "prefix" and mod["name"] in MAP_PREFIX_TARGETS) >= 3


def price_map(map):
    quantity = map.get("stats", {}).get("quantity", 0)
    rarity = map.get("stats", {}).get("rarity", 0)
    pack_size = map.get("stats", {}).get("pack_size", 0)
    more_maps = map.get("stats", {}).get("more_maps", 0)
    more_currency = map.get("stats", {}).get("more_currency", 0)
    more_scarabs = map.get("stats", {}).get("more_scarabs", 0)

    prices = []

    if more_currency > 158 or pack_size > 69 or more_currency + pack_size > 180 or more_currency + quantity > 230:
        return None
    
    if pack_size > 61:
        prices.append(99)
    if pack_size > 59 and more_currency > 0 or more_scarabs > 0 or more_maps > 0:
        prices.append(79)
    if pack_size > 50:
        prices.append(49)
    if pack_size > 40:
        prices.append(34)

    if more_currency > 130:
        if pack_size > 40:
            prices.append(299)
        if pack_size > 30 or more_scarabs > 0 or more_maps > 0:
            prices.append(249)
        else:
            prices.append(199)
    if more_currency > 90:
        if pack_size > 70:
            prices.append(299)
        if pack_size + quantity > 150:
            prices.append(199)
        if pack_size + quantity > 130:
            prices.append(129)
        if pack_size + quantity > 120:
            prices.append(79)
        if pack_size + quantity > 110:
            prices.append(49)
        if more_maps > 0 or more_scarabs > 0:
            prices.append(34)
        else:
            print(map.get("stats", {}))
            return None   
        
    if is_perfect_prefix(map) or is_perfect_suffix(map):
        prices.append(149)

    return max(prices) if prices else None



# Stash Grid Configuration
STASH_GRID_ROWS = 12
STASH_GRID_COLS = 12
STASH_GRID_START_X = 24  # Starting X coordinate of the grid
STASH_GRID_START_Y = 145  # Starting Y coordinate of the grid
STASH_GRID_CELL_SIZE = 24 *2  # Size of each grid cell

from macros.map_parser import parse_map_mods
from focus_window import focus_window

# loop through a 12x12 grid of maps, parse the mods of each map, and price it using the price_map function
def price_maps_in_stash():
    for row in range(STASH_GRID_ROWS):
        for col in range(STASH_GRID_COLS):
            x = STASH_GRID_START_X + col * STASH_GRID_CELL_SIZE
            y = STASH_GRID_START_Y + row * STASH_GRID_CELL_SIZE
            map = parse_map_mods((x, y))
            if map:
                price = price_map(map)
                print(f"Map at ({row}, {col}) is priced at: {price}")
                print(f"stats: {map.get('stats', {})}")

if __name__ == "__main__":
    focus_window()
    price_maps_in_stash()