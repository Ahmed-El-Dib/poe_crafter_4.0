from images.img_paths import *
from stash.tabs.grid_tab import GridStashTab
from stash.tabs.currency_tab import CurrencyTab
from utils.initiate_session import requires_game_ready
from macros.item_parser import parse_cluster_mods
import time
from stash.stash_utils import crafting_safe_retry


CLUSTER_TARGETS = [
    "Abecedarian's",
    "Dabbler's",
    "Alchemist's",
    "of Incision",
]

VALUABLE_COMBOS = [
    ("of Incision", "Abecedarian's"),
    ("of Incision", "Dabbler's"),
    ("of Incision", "Alchemist's"),
]


class ClusterCraftingState:
    def __init__(self, max_alts: int = 4500, max_scours: int = 750, max_exalts: int = 480):
        self.spamming = False
        self.alts = 0
        self.scours = 0
        self.exalts = 0
        self.max_alts = max_alts
        self.max_scours = max_scours
        self.max_exalts = max_exalts

    def reset_for_new_item(self):
        self.spamming = False


@requires_game_ready()
def craft_clusters_batch(
    number_of_clusters: int = 50,
    source_tab: GridStashTab = None,
    currency_tab: CurrencyTab = None,
    item_class: str = "Medium Cluster Jewel",
    start_idx=(0, 0),
):
    if source_tab is None:
        source_tab = GridStashTab(SOURCE_TAB)

    if currency_tab is None:
        currency_tab = CurrencyTab(CURRENCY_TAB)

    crafted_count = 0
    state = ClusterCraftingState()

    while crafted_count < number_of_clusters and not source_tab.is_done(start_idx):
        next_idx = source_tab.move_next_item_to_crafter(
            item_class=item_class,
            crafting_tab=currency_tab,
            start_idx=start_idx,
        )

        if next_idx is None:
            break

        state.reset_for_new_item()
        last_cluster_mods = None
        same_read_count = 0

        while True:
            max_attempts = 5
            delay = 0.5
            cluster_mods = None

            for attempt in range(1, max_attempts + 1):
                cluster_mods = parse_cluster_mods(currency_tab.craft_coords)

                if cluster_mods is not None:
                    break

                print(f"Attempt {attempt} failed to parse cluster mods. Retrying...")
                time.sleep(delay)

            if cluster_mods is None:
                print("Failed to parse cluster mods after multiple attempts.")

                if not crafting_safe_retry(currency_tab.craft_coords):
                    print("Failed to safely retry cluster item. Stopping.")
                    return {
                        "crafted_count": crafted_count,
                        "next_idx": start_idx,
                    }

                break

            # Detect reading the same unchanged item repeatedly, like the map crafter.
            if cluster_mods == last_cluster_mods:
                same_read_count += 1
            else:
                last_cluster_mods = cluster_mods
                same_read_count = 1

            if same_read_count >= 10:
                print("Read the same cluster 10 times in a row. Moving/retrying safely.")

                if not crafting_safe_retry(currency_tab.craft_coords):
                    print("Failed to safely retry repeated cluster item. Stopping.")
                    return {
                        "crafted_count": crafted_count,
                        "next_idx": start_idx,
                    }

                break

            result = determine_next_action_cluster(cluster_mods, currency_tab, state)

            if result == "DONE":
                break

        crafted_count += 1
        start_idx = next_idx

    print(f"Crafted {crafted_count} clusters in this batch.")
    return {
        "crafted_count": crafted_count,
        "next_idx": start_idx,
    }


def determine_next_action_cluster(mods, crafting_tab: CurrencyTab, state: ClusterCraftingState):
    if mods is None:
        print("Failed to parse cluster mods, retrying...")
        return "CONTINUE"

    num_mods = len(mods)
    num_targets = count_targets_found(mods)

    has_prefix = any(mod.get("type") in ["prefix", "passive_skill"] for mod in mods)
    has_suffix = any(mod.get("type") == "suffix" for mod in mods)

    if num_mods == 0:
        rarity = "normal"
    elif num_mods <= 2:
        rarity = "magic"
    else:
        rarity = "rare"

    print({
        "rarity": rarity,
        "num_mods": num_mods,
        "num_targets": num_targets,
        "has_prefix": has_prefix,
        "has_suffix": has_suffix,
    })

    if rarity == "normal":
        print("Normal cluster, using transmute.")
        state.spamming = False
        crafting_tab.trans()
        return "CONTINUE"

    if rarity == "magic":
        if num_targets == 0:
            if has_prefix:
                state.alts += 1
                if state.alts >= state.max_alts:
                    raise RuntimeError("Alteration limit reached while crafting clusters.")

                print("Bad magic cluster with prefix, using alteration.")
                state.spamming = True
                crafting_tab.alt()
                return "CONTINUE"

            print("Magic cluster has no prefix/target, using augment.")
            state.spamming = False
            crafting_tab.aug()
            return "CONTINUE"

        if not has_suffix:
            print("Magic cluster has target but no suffix, using augment.")
            state.spamming = False
            crafting_tab.aug()
            return "CONTINUE"

        print("Good 2-mod magic cluster, using regal.")
        state.spamming = False
        crafting_tab.regal()
        return "CONTINUE"

    if rarity == "rare":
        state.spamming = False

        if any_valuable_combo_found(mods):
            print("Valuable combo found, keeping cluster.")
            return "DONE"

        num_prefixes = count_prefixes(mods)

        if num_targets == 1 and num_prefixes == 1:
            state.exalts += 1
            if state.exalts >= state.max_exalts:
                raise RuntimeError("Exalt/slam limit reached while crafting clusters.")

            print("Rare cluster has one target prefix, slamming once.")
            crafting_tab.slam(1)
            return "CONTINUE"

        state.scours += 1
        if state.scours >= state.max_scours:
            raise RuntimeError("Scour limit reached while crafting clusters.")

        print("Bad rare cluster, scouring.")
        crafting_tab.scoure()
        return "CONTINUE"

    print("Unknown cluster state, continuing.")
    return "CONTINUE"


def count_targets_found(mods):
    return sum(
        any(target.lower() in mod_text(mod).lower() for target in CLUSTER_TARGETS)
        for mod in mods
    )


def any_valuable_combo_found(mods):
    return any(
        all(any(target.lower() in mod_text(mod).lower() for mod in mods) for target in combo)
        for combo in VALUABLE_COMBOS
    )


def count_prefixes(mods):
    return sum(mod.get("type") in ["prefix", "passive_skill"] for mod in mods)


def mod_text(mod):
    return mod.get("text") or mod.get("name") or ""
from images.img_paths import *
from stash.tabs.grid_tab import GridStashTab
from stash.tabs.currency_tab import CurrencyTab
from utils.initiate_session import requires_game_ready
from macros.item_parser import parse_cluster_mods
import time
from stash.stash_utils import crafting_safe_retry


CLUSTER_TARGETS = [
    "Abecedarian's",
    "Dabbler's",
    "Alchemist's",
    "of Incision",
]

VALUABLE_COMBOS = [
    ("of Incision", "Abecedarian's"),
    ("of Incision", "Dabbler's"),
    ("of Incision", "Alchemist's"),
]


class ClusterCraftingState:
    def __init__(self, max_alts: int = 4500, max_scours: int = 750, max_exalts: int = 480):
        self.spamming = False
        self.alts = 0
        self.scours = 0
        self.exalts = 0
        self.max_alts = max_alts
        self.max_scours = max_scours
        self.max_exalts = max_exalts

    def reset_for_new_item(self):
        self.spamming = False


@requires_game_ready()
def craft_clusters_batch(
    number_of_clusters: int = 50,
    source_tab: GridStashTab = None,
    currency_tab: CurrencyTab = None,
    item_class: str = "Medium Cluster Jewel",
    start_idx=(0, 0),
):
    if source_tab is None:
        source_tab = GridStashTab(SOURCE_TAB)

    if currency_tab is None:
        currency_tab = CurrencyTab(CURRENCY_TAB)

    crafted_count = 0
    state = ClusterCraftingState()

    while crafted_count < number_of_clusters and not source_tab.is_done(start_idx):
        next_idx = source_tab.move_next_item_to_crafter(
            item_class=item_class,
            crafting_tab=currency_tab,
            start_idx=start_idx,
        )

        if next_idx is None:
            break

        state.reset_for_new_item()
        last_cluster_mods = None
        same_read_count = 0

        while True:
            max_attempts = 5
            delay = 0.5
            cluster_mods = None

            for attempt in range(1, max_attempts + 1):
                cluster_mods = parse_cluster_mods(currency_tab.craft_coords)

                if cluster_mods is not None:
                    break

                print(f"Attempt {attempt} failed to parse cluster mods. Retrying...")
                time.sleep(delay)

            if cluster_mods is None:
                print("Failed to parse cluster mods after multiple attempts.")

                if not crafting_safe_retry(currency_tab.craft_coords):
                    print("Failed to safely retry cluster item. Stopping.")
                    return {
                        "crafted_count": crafted_count,
                        "next_idx": start_idx,
                    }

                break

            # Detect reading the same unchanged item repeatedly, like the map crafter.
            if cluster_mods == last_cluster_mods:
                same_read_count += 1
            else:
                last_cluster_mods = cluster_mods
                same_read_count = 1

            if same_read_count >= 10:
                print("Read the same cluster 10 times in a row. Moving/retrying safely.")

                if not crafting_safe_retry(currency_tab.craft_coords):
                    print("Failed to safely retry repeated cluster item. Stopping.")
                    return {
                        "crafted_count": crafted_count,
                        "next_idx": start_idx,
                    }

                break

            result = determine_next_action_cluster(cluster_mods, currency_tab, state)

            if result == "DONE":
                exit()
                break

        crafted_count += 1
        start_idx = next_idx

    print(f"Crafted {crafted_count} clusters in this batch.")
    return {
        "crafted_count": crafted_count,
        "next_idx": start_idx,
    }


def determine_next_action_cluster(mods, crafting_tab: CurrencyTab, state: ClusterCraftingState):
    if mods is None:
        print("Failed to parse cluster mods, retrying...")
        return "CONTINUE"

    if good_to_keep(mods):
        print("Good cluster found, keeping.")
        return "DONE"
    
    if good_to_trans(mods):
        print("Bad cluster with no targets, using transmute.")
        crafting_tab.trans()
        return "CONTINUE"
    
    if good_to_aug(mods):
        print("Good cluster for augment, using augment.")
       
        crafting_tab.aug()
        return "CONTINUE"
    
    print("Defaulting to alt")
    crafting_tab.alt()
    return "CONTINUE"

def good_to_trans(mods):
    return len(mods) == 0

def good_to_aug(mods):
    return  len(mods)== 1 and count_targets_found(mods) == 1

def good_to_keep(mods):
    return count_targets_found(mods) >= 2

def count_targets_found(mods):
    return sum(
        any(target.lower() in mod_text(mod).lower() for target in CLUSTER_TARGETS)
        for mod in mods
    )


def any_valuable_combo_found(mods):
    return any(
        all(any(target.lower() in mod_text(mod).lower() for mod in mods) for target in combo)
        for combo in VALUABLE_COMBOS
    )


def count_prefixes(mods):
    return sum(mod.get("type") in ["prefix", "passive_skill"] for mod in mods)


def mod_text(mod):
    return mod.get("text") or mod.get("name") or ""


if __name__ == "__main__":
    result = craft_clusters_batch(
        number_of_clusters=10,
        item_class="Iron Flask",
    )
    print(result)