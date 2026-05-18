from images.img_paths import *
from stash.tabs.grid_tab import GridStashTab
from stash.tabs.currency_tab import CurrencyTab
from utils.initiate_session import requires_game_ready
from macros.map_parser import parse_map_mods
import time
from stash.stash_utils import safe_place_in_completed_tab, crafting_safe_retry
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



@requires_game_ready()
def craft_maps_batch(
    number_of_maps: int = 50,
    source_tab=None,
    currency_tab=None,
    item_class: str = "Map",
    start_idx=(0, 0),
):
    crafted_count = 0

    while crafted_count < number_of_maps and not source_tab.is_done(start_idx):
        next_idx = source_tab.move_next_item_to_crafter(
            item_class=item_class,
            crafting_tab=currency_tab,
            start_idx=start_idx,
        )

        if next_idx is None:
            break

        last_map_mods = None
        same_read_count = 0

        while True:
            max_attempts = 5
            delay = 0.5
            map_mods = None

            for attempt in range(1, max_attempts + 1):
                map_mods = parse_map_mods(currency_tab.craft_coords)

                if map_mods:
                    break

                print(f"Attempt {attempt} failed to parse map mods. Retrying...")
                time.sleep(delay)

            if not map_mods:
                print("Failed to parse map mods after multiple attempts.")

                if not crafting_safe_retry(currency_tab.craft_coords):
                    print("Failed to move item to completed tab. Stopping.")
                    return

                break

            # Detect same map being read repeatedly
            if map_mods == last_map_mods:
                same_read_count += 1
            else:
                last_map_mods = map_mods
                same_read_count = 1

            if same_read_count >= 10:
                print("Read the same map 10 times in a row. Moving to completed tab.")

                if not crafting_safe_retry(currency_tab.craft_coords):
                    print("Failed to move repeated item to completed tab. Stopping.")
                    return

                break

            result = determine_next_action_map(map_mods, currency_tab)

            if result == "DONE":
                break

        crafted_count += 1
        start_idx = next_idx
    print(f"Crafted {crafted_count} maps in this batch.")
    return {
        "crafted_count": crafted_count,
        "next_idx": start_idx,
    }

def determine_next_action_map(map, crafting_tab: CurrencyTab):
    if map is None:
        print("Failed to parse map mods, retrying...")
        return "CONTINUE"

    mods = map.get("mods") or []
    stats = map.get("stats") or {}
    num_mods = len(mods)

    print(stats)

    if good_to_keep(mods, stats) and num_mods == 6:
        print("Perfect map found, keeping.")
        return "DONE"

    if good_to_trans(mods, stats):
        print("Normal map, using transmute.")
        crafting_tab.trans()
        return "CONTINUE"

    if good_to_aug(mods, stats):
        print("Good 1-mod magic map, augmenting.")
        crafting_tab.aug()
        return "CONTINUE"

    if good_to_regal(mods, stats):
        print("Good 2-mod magic map, regaling.")
        crafting_tab.regal()
        return "CONTINUE"

    if good_to_slam(mods, stats):
        slams_needed = 6 - num_mods
        print(f"Good {num_mods}-mod rare map, slamming {slams_needed} times.")
        crafting_tab.slam(slams_needed)
        return "CONTINUE"

    if good_to_scoure(mods, stats):
        print("Bad rare map, scouring.")
        crafting_tab.scoure()
        return "CONTINUE"

    print("Defaulting to alteration.")
    crafting_tab.alt()
    return "CONTINUE"

def good_to_aug(mods, stats):
    return  len(mods)== 1 and (stats.get("more_currency", 0) >= 40  or stats.get("pack_size", 0) >= 20)
def good_to_regal(mods, stats):
    return len(mods) == 2 and (double_currency(stats) or double_pack_size(stats))
def good_to_trans(mods, stats): return len(mods) == 0
def good_to_slam(mods, stats): return len(mods) >= 3 and len(mods) < 6 and good_to_keep(mods, stats)
def good_to_scoure(mods, stats): return len(mods) >= 3 and not good_to_keep(mods, stats)

# if valdo's and antagonist's are both present, return true, otherwise false
def has_valdos(mods):   return any("Valdo's" in mod.get('name', '') for mod in mods)
def has_antagonists(mods):    return any("Antagonist's" in mod.get('name', '') for mod in mods)
def good_scarabs(mods, stats):
    return stats.get("more_scarabs", 0) >= 80 and has_valdos(mods)

def good_rares(mods):
    return has_valdos(mods) and has_antagonists(mods)


def double_currency(stats):    return stats.get("more_currency", 0) >= 90
def double_pack_size(stats):    return stats.get("pack_size", 0) >= 40
def currency_and_pack_size(stats):    return stats.get("more_currency", 0) >40 and stats.get("pack_size", 0) >= 20

    # or double_pack_size(stats)
def good_to_keep(mods, stats):
    good_p = count_prefix_targets(mods) > 1
    good_s = count_suffix_targets(mods) > 1
    return  double_currency(stats) or double_pack_size(stats) or good_p or good_s



#  need count prefix and count suffix and check if they match targets

def count_prefix_targets(mods):
    return sum(any(target in mod.get('name', '') for target in MAP_PREFIX_TARGETS) and mod.get('type') == 'prefix' for mod in mods)

def count_suffix_targets(mods):
    return sum(any(target in mod.get('name', '') for target in MAP_SUFFIX_TARGETS) and mod.get('type') == 'suffix' for mod in mods)
   
def count_targets(mods):
    return count_prefix_targets(mods) + count_suffix_targets(mods)