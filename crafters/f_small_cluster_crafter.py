from focus_window import focus_window
from images.img_paths import *
from stash.tabs.grid_tab import GridStashTab
from stash.tabs.currency_tab import CurrencyTab
from utils.initiate_session import requires_game_ready
from macros.cluster_parser import parse_cluster, read_cluster
import time
from stash.stash_utils import safe_place_in_completed_tab, crafting_safe_retry

SMALL_CLUSTER_PREFIX_TARGETS = ["Powerful", "Introspection"]

SMALL_CLUSTER_SUFFIX_TARGETS = ["of the Tempest", "of the Rainbow", "of the Walrus", "of the Furnace",
                                "of Variegation", "of the Kaleidoscope", #t2-3 all res
                                "of the Thunderhead",  #t2-3 light res "of the Storm",
                                "of the Yeti",  #t2-3 cold res "of the Penguin",
                                "of the Kiln", #t2-3 fire res "of the Drake", 
                                ]

# SMALL_CLUSTER_MANDATORY_MODS = ["Powerful", "Introspection", "of the Rainbow","of Variegation", "of the Kaleidoscope"]
SMALL_CLUSTER_MANDATORY_MODS = ["Powerful", "Introspection", "of the Rainbow"]

@requires_game_ready()
def craft_small_clusters_batch(
    number_of_small_clusters: int = 50,
    source_tab=None,
    currency_tab=None,
    item_class: str = "Small Cluster",
    start_idx=(0, 0),
):
    crafted_count = 0

    while crafted_count < number_of_small_clusters and not source_tab.is_done(start_idx):
        next_idx = source_tab.move_next_item_to_crafter(
            item_class=item_class,
            crafting_tab=currency_tab,
            start_idx=start_idx,
        )

        if next_idx is None:
            break

        last_small_cluster_mods = None
        same_read_count = 0

        while True:
            max_attempts = 5
            delay = 0.5
            small_cluster_mods = None

            for attempt in range(1, max_attempts + 1):
                small_cluster_mods = parse_cluster(currency_tab.craft_coords)

                if small_cluster_mods:
                    break

                print(f"Attempt {attempt} failed to parse small cluster mods. Retrying...")
                time.sleep(delay)

            if not small_cluster_mods:
                print("Failed to parse small cluster mods after multiple attempts.")

                if not crafting_safe_retry(currency_tab.craft_coords):
                    print("Failed to move item to completed tab. Stopping.")
                    return

                break

            # Detect same small cluster being read repeatedly
            if small_cluster_mods == last_small_cluster_mods:
                same_read_count += 1
            else:
                last_small_cluster_mods = small_cluster_mods
                same_read_count = 1

            if same_read_count >= 10:
                print("Read the same small cluster 10 times in a row. Moving to completed tab.")

                if not crafting_safe_retry(currency_tab.craft_coords):
                    print("Failed to move repeated item to completed tab. Stopping.")
                    return

                break

            result = determine_next_action_small_cluster(
                small_cluster_mods,
                currency_tab,
            )

            if result == "DONE":
                # exit()
                break

        crafted_count += 1
        start_idx = next_idx

    print(f"Crafted {crafted_count} small clusters in this batch.")

    return {
        "crafted_count": crafted_count,
        "next_idx": start_idx,
    }


def determine_next_action_small_cluster(
    small_cluster,
    crafting_tab: CurrencyTab,
):
    if small_cluster is None:
        print("Failed to parse small cluster mods, retrying...")
        return "CONTINUE"

    mods = small_cluster.get("mods") or []
    stats = small_cluster.get("stats") or {}
    num_mods = len(mods)

    # return "DONE" #test
    # print(mods)
    # time.sleep(0.5)
    if good_to_keep_small_cluster(mods, stats):
        print("Perfect small cluster found, keeping.")
        return "DONE"

    if good_to_trans_small_cluster(mods, stats):
        print("Normal small cluster, using transmute.")
        crafting_tab.trans()
        return "CONTINUE"

    if good_to_aug_small_cluster(mods, stats):
        print("Good 1-mod magic small cluster, augmenting.")
        crafting_tab.aug()
        return "CONTINUE"

    if good_to_regal_small_cluster(mods, stats):
        print("Good 2-mod magic small cluster, regaling.")
        crafting_tab.regal()
        return "CONTINUE"

    if good_to_slam_small_cluster(mods, stats):
        slams_needed = 4 - num_mods
        print(f"Good {num_mods}-mod rare small cluster, slamming {slams_needed} times.")
        crafting_tab.slam(slams_needed)
        return "CONTINUE"
    if good_to_annul_small_cluster(mods, stats):
        print(f"3 good mod rare, trying to save, annulling.")
        crafting_tab.annul()
        return "CONTINUE"
    if good_to_scoure_small_cluster(mods, stats):
        print("Bad rare small cluster, scouring.")
        crafting_tab.scoure()
        return "CONTINUE"

    print("Defaulting to alteration.")
    crafting_tab.alt()
    return "CONTINUE"


#
# PLACEHOLDER FUNCTIONS
#

def good_to_keep_small_cluster(mods, stats):
    return count_small_cluster_mandatory_mods(mods) >= 2
# def good_to_keep_small_cluster(mods, stats):
#     return count_small_cluster_targets(mods) >= 4 and count_small_cluster_mandatory_mods(mods) >= 3

def good_to_trans_small_cluster(mods, stats):
    return len(mods) == 0


def good_to_aug_small_cluster(mods, stats):
    return len(mods) == 1
# def good_to_aug_small_cluster(mods, stats):
#     return len(mods) == 1 and count_small_cluster_targets(mods) == 1


def good_to_regal_small_cluster(mods, stats):
    return len(mods) == 2 and count_small_cluster_mandatory_mods(mods) > 0
# def good_to_regal_small_cluster(mods, stats):
#     return len(mods) == 2 and count_small_cluster_targets(mods) == 2 and count_small_cluster_mandatory_mods(mods) >= 1

def good_to_slam_small_cluster(mods, stats):
    return len(mods) == 3 and count_small_cluster_targets(mods) == 3 and count_small_cluster_mandatory_mods(mods) >= 2


def good_to_scoure_small_cluster(mods, stats):
    return len(mods) >= 3 and (count_small_cluster_targets(mods)  < 3 or count_small_cluster_mandatory_mods(mods) < 2)

def good_to_annul_small_cluster(mods, stats):
    if len(mods) == 4 and count_small_cluster_targets(mods) == 4 and count_small_cluster_mandatory_mods(mods) < 3:
        return True
    return len(mods) == 4 and count_small_cluster_targets(mods) < 4 and count_small_cluster_mandatory_mods(mods) >= 2


#
# OPTIONAL HELPERS
#

def count_small_cluster_prefix_targets(mods):
    return sum(
        any(target in mod.get("name", "") for target in SMALL_CLUSTER_PREFIX_TARGETS)
        and mod.get("type") == "prefix"
        for mod in mods
    )


def count_small_cluster_suffix_targets(mods):
    return sum(
        any(target in mod.get("name", "") for target in SMALL_CLUSTER_SUFFIX_TARGETS)
        and mod.get("type") == "suffix"
        for mod in mods
    )

def count_small_cluster_mandatory_mods(mods):
    return sum(
        any(target in mod.get("name", "") for target in SMALL_CLUSTER_MANDATORY_MODS)
        for mod in mods
    )
def count_small_cluster_targets(mods):
    return (
        count_small_cluster_prefix_targets(mods)
        + count_small_cluster_suffix_targets(mods)
    )

item = """
Item Class: Jewels
Rarity: Magic
Small Cluster Jewel of the Walrus
--------
Requirements:
Level: 67
--------
Item Level: 85
--------
Adds 3 Passive Skills (enchant)
(Added Passive Skills are never considered to be in Radius by other Jewels) (enchant)
(All Added Passive Skills are Small unless otherwise specified) (enchant)
Added Small Passive Skills grant: 6% increased Mana Reservation Efficiency of Skills (enchant)
(Passive Skills that are not Notable, Masteries, Keystones, or Jewel Sockets are Small) (enchant)
--------
{ Prefix Modifier "Introspection" (Tier: 1) — Elemental, Cold, Resistance }
Added Small Passive Skills also grant: +11(10-11)% to Cold Resistance
--------
{ Suffix Modifier "Dogshit" (Tier: 1) — Elemental, Cold, Resistance }
Added Small Passive Skills also grant: +11(10-11)% to Cold Resistance
Place into an allocated Small, Medium or Large Jewel Socket on the Passive Skill Tree. Added passives do not interact with jewel radiuses. Right click to remove from the Socket.
"""
if __name__ == "__main__":
    from stash.tabs.grid_tab import GridStashTab
    from stash.tabs.currency_tab import CurrencyTab
    # jewel = read_cluster(item)
    # print(len(jewel.get("mods", [])))
    # print(count_small_cluster_targets(jewel.get("mods", [])))
    # print(count_small_cluster_mandatory_mods(jewel.get("mods", [])))
    # print(good_to_regal_small_cluster(jewel.get("mods", []), jewel.get("stats", {})))
    # exit()
    # focus_window("Path of Exile")
    # time.sleep(1)
    source_tab = GridStashTab()
    currency_tab = CurrencyTab()

    craft_small_clusters_batch(
        number_of_small_clusters=50,
        source_tab=source_tab,
        currency_tab=currency_tab,
        item_class="Small Cluster",
        start_idx=(0, 0),
    )