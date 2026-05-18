from images.img_paths import *
from stash.tabs.grid_tab import GridStashTab
from stash.tabs.currency_tab import CurrencyTab
from utils.initiate_session import requires_game_ready
from macros.cluster_parser import parse_cluster
import time
from stash.stash_utils import crafting_safe_retry,crafting_retry_inplace
from mods_dict import LARGE_CLUSTER_MODS as CLUSTER_MODS
from stash.tabs.grid_tab import GridStashTab
from stash.tabs.currency_tab import CurrencyTab


COMBOS = [{"Assert Dominance", "Fasting", "Spiked Concoction", "of the Prodigy","of the Meteor"}]
# COMBOS = [
#     # armour stacker
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Life"][1],
#         # CLUSTER_MODS["Prefix"]["Life"][2],
#         # CLUSTER_MODS["Prefix"]["Life"][3],
#         CLUSTER_MODS["Suffix"]["All Attributes"][1],
#         CLUSTER_MODS["Suffix"]["Intelligence"][1],
 
#     },
    
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Damage"][1],
#         CLUSTER_MODS["Prefix"]["Damage"][2],
#         # CLUSTER_MODS["Prefix"]["Damage"][3],
#         CLUSTER_MODS["Suffix"]["All Attributes"][1],
#         CLUSTER_MODS["Suffix"]["Intelligence"][1],
#     },
# ]
# COMBOS = [
#     # armour stacker
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Notable"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][2],
#         CLUSTER_MODS["Suffix"]["Fire Res"][1],
#         CLUSTER_MODS["Suffix"]["Fire Res"][2],
#     },
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Notable"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][2],
#         CLUSTER_MODS["Suffix"]["Cold Res"][1],
#         CLUSTER_MODS["Suffix"]["Cold Res"][2],
#     },
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Notable"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][2],
#         CLUSTER_MODS["Suffix"]["Lightning Res"][1],
#         CLUSTER_MODS["Suffix"]["Lightning Res"][2],
#     },

#     # life chaos res flex
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Life"][1],
#         CLUSTER_MODS["Prefix"]["Life"][2],
#         CLUSTER_MODS["Suffix"]["Chaos Res"][1],
#         CLUSTER_MODS["Suffix"]["Chaos Res"][2],
#         CLUSTER_MODS["Suffix"]["All Res"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][2],
#     },
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Life"][1],
#         CLUSTER_MODS["Prefix"]["Life"][2],
#         CLUSTER_MODS["Suffix"]["Chaos Res"][1],
#         CLUSTER_MODS["Suffix"]["Chaos Res"][2],
#         CLUSTER_MODS["Suffix"]["Dexterity"][1],
#         CLUSTER_MODS["Suffix"]["Dexterity"][2],
#     },
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Life"][1],
#         CLUSTER_MODS["Prefix"]["Life"][2],
#         CLUSTER_MODS["Suffix"]["Chaos Res"][1],
#         CLUSTER_MODS["Suffix"]["Chaos Res"][2],
#         CLUSTER_MODS["Suffix"]["All Attributes"][1],
#         CLUSTER_MODS["Suffix"]["All Attributes"][2],
#     },

#     # str stacker
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Life"][1],
#         CLUSTER_MODS["Prefix"]["Life"][2],
#         CLUSTER_MODS["Suffix"]["All Attributes"][1],
#         CLUSTER_MODS["Suffix"]["All Attributes"][2],
#         CLUSTER_MODS["Suffix"]["Strength"][2],
#         CLUSTER_MODS["Suffix"]["Strength"][1],
#     },
  
#     {  # dex stacker
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Life"][1],
#         CLUSTER_MODS["Prefix"]["Life"][2],
#         CLUSTER_MODS["Suffix"]["All Attributes"][1],
#         CLUSTER_MODS["Suffix"]["All Attributes"][2],
#         CLUSTER_MODS["Suffix"]["Dexterity"][1],
#         CLUSTER_MODS["Suffix"]["Dexterity"][2],
#     },

#     {  # int stacker
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Energy Shield"][1],
#         CLUSTER_MODS["Prefix"]["Energy Shield"][2],
#         CLUSTER_MODS["Suffix"]["All Attributes"][1],
#         CLUSTER_MODS["Suffix"]["All Attributes"][2],
#         CLUSTER_MODS["Suffix"]["Intelligence"][1],
#         CLUSTER_MODS["Suffix"]["Intelligence"][2],
#     },

#     # es flex
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Energy Shield"][1],
#         CLUSTER_MODS["Prefix"]["Energy Shield"][2],
#         CLUSTER_MODS["Suffix"]["All Res"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][2],
#         CLUSTER_MODS["Suffix"]["Intelligence"][1],
#         CLUSTER_MODS["Suffix"]["Intelligence"][2],
#     },
    
#     {
#         CLUSTER_MODS["Prefix"]["Effect"][1],
#         CLUSTER_MODS["Prefix"]["Energy Shield"][1],
#         CLUSTER_MODS["Prefix"]["Energy Shield"][2],
#         CLUSTER_MODS["Suffix"]["All Attributes"][1],
#         CLUSTER_MODS["Suffix"]["All Attributes"][2],
#         CLUSTER_MODS["Suffix"]["All Res"][1],
#         CLUSTER_MODS["Suffix"]["All Res"][2],
#     },

#     # tester combos
#     # {"Powerful", "Glimmering", "of the Cloud", "of the Bear"},
# ]


@requires_game_ready()
def craft_small_clusters_batch(
    number_of_small_clusters: int = 50,
    source_tab=GridStashTab(),
    currency_tab=CurrencyTab(),
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

                if not crafting_retry_inplace(currency_tab.craft_coords):
                    print("Failed to move repeated item to completed tab. Stopping.")
                    return
                
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
    
    if good_to_keep(mods):
        print("Perfect small cluster found, keeping.")
        return "DONE"

    if good_to_trans(mods):
        print("Normal small cluster, using transmute.")
        crafting_tab.trans()
        return "CONTINUE"

    if good_to_aug(mods):
        # print("Good 1-mod magic small cluster, augmenting.")
        crafting_tab.aug()
        return "CONTINUE"

    if good_to_regal(mods):
        # print("Good 2-mod magic small cluster, regaling.")
        crafting_tab.regal()
        return "CONTINUE"

    if good_to_slam(mods):
        print(f"Good 3-mod rare small cluster, slamming.")
        crafting_tab.slam()
        print(f"hit {mods}")
        return "CONTINUE"
    
    if good_to_annul(mods):
        print(f"3 good mods on a 4 mod rare small cluster, trying to save, annulling.")
        print(mods)
        crafting_tab.annul()
        return "CONTINUE"
    
    if good_to_scoure(mods):
        print("Bad rare small cluster, scouring.")
        crafting_tab.scoure()
        return "CONTINUE"

    # print("Defaulting to alteration.")
    crafting_tab.alt()
    return "CONTINUE"

def determine_next_action_small_cluster_tester(
    small_cluster,
    crafting_tab: CurrencyTab,
):
    if small_cluster is None:
        print("Failed to parse small cluster mods, retrying...")
        exit()  # for testing, we want to know if parsing fails instead of retrying
        return "CONTINUE"

    mods = small_cluster.get("mods") or []
    print(mod_names(mods))
    if good_to_keep(mods):
        print("Perfect small cluster found, keeping.")
        # exit()  # for testing, we want to stop if we get a perfect cluster instead of continuing
        return "DONE"

    if good_to_trans(mods):
        print("Normal small cluster, using transmute.")
        exit()  # for testing, we want to stop if we get a normal cluster instead of continuing
        crafting_tab.trans()
        return "CONTINUE"

    if good_to_aug(mods):
        print("Good 1-mod magic small cluster, augmenting.")
        exit()  # for testing, we want to stop if we get a good 1-mod cluster instead of continuing
        crafting_tab.aug()
        return "CONTINUE"

    if good_to_regal(mods):
        print("Good 2-mod magic small cluster, regaling.")
        exit()  # for testing, we want to stop if we get a good 2-mod cluster instead of continuing
        crafting_tab.regal()
        return "CONTINUE"

    if good_to_slam(mods):
        print(f"Good 3-mod rare small cluster, slamming.")
        exit()  # for testing, we want to stop if we get a good 3-mod cluster instead of continuing
        crafting_tab.slam()
        return "CONTINUE"
    
    if good_to_annul(mods):
        print(f"3 good mods on a 4 mod rare small cluster, trying to save, annulling.")
        exit()  # for testing, we want to stop if we get a 4-mod cluster with 3 good mods instead of continuing
        crafting_tab.annul()
        return "CONTINUE"
    
    if good_to_scoure(mods):
        print("Bad rare small cluster, scouring.")
        exit()  # for testing, we want to stop if we get a bad cluster instead of continuing
        crafting_tab.scoure()
        return "CONTINUE"

    print("Defaulting to alteration.")
    exit()  # for testing, we want to stop if we have to default to alteration instead of continuing
    crafting_tab.alt()
    return "CONTINUE"
#
# PLACEHOLDER FUNCTIONS
#
def mod_names(mods):
    return {mod.get("name", "") for mod in mods}


def count_combo_hits(mods, combo):
    return len(mod_names(mods) & combo)


def best_combo_hits(mods, combos=COMBOS):
    names = mod_names(mods)
    return max(
        len(names & combo)
        for combo in combos
    )

def good_to_keep(mods):
    # required = {
    #     CLUSTER_MODS["Prefix"]["Effect"][1],
    #     CLUSTER_MODS["Suffix"]["All Attributes"][1],
    #     CLUSTER_MODS["Suffix"]["Intelligence"][1],
    # }
    # print(required)

    # return required.issubset(mod_names(mods))
    return len(mods) == 4 and best_combo_hits(mods) == 4

def good_to_trans(mods):
    return len(mods) == 0

def good_to_aug(mods):
    return len(mods) == 1 and best_combo_hits(mods) == 1

def good_to_regal(mods):
    return len(mods) == 2 and best_combo_hits(mods) == 2

def good_to_slam(mods):
    return len(mods) == 3 and best_combo_hits(mods) == 3

def good_to_annul(mods):
    return len(mods) == 4 and best_combo_hits(mods) == 3

def good_to_scoure(mods):
    return len(mods) >= 3 and best_combo_hits(mods) < 3



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


    