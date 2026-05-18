from macros.rpa_macros import *
from stash.tabs.currency_tab import CurrencyTab

from macros.item_parser import parse_item_mods, read_item
from utils.initiate_session import requires_game_ready
target_names = {"Alchemist's", "Experimenter's", "of the Cheetah", "of Incision", "of Runeblazing", "Dabbler's"}

def good_to_keep(mods):
    return sum(
    any(mod["name"] == target for mod in mods)
    for target in target_names
) >= 2

def has_a_mod(mods):
    return any(mod["name"] in target_names for mod in mods)


def good_to_aug(mods):
    return has_a_mod(mods) and len(mods)==1

def good_to_regal(mods):
    return len(mods)==3 and has_a_mod(mods)

def good_to_scoure(mods):
    return len(mods)>2 and not good_to_keep(mods)

example = """
Item Class: Boots
Rarity: Magic
Runic Sabatons of the Essence
--------
Quality: +20% (augmented)
Ward: 140 (augmented)
--------
Requirements:
Level: 69
Str: 46
Dex: 46
Int: 46
--------
Sockets: G-G-G-B 
--------
Item Level: 81
--------
{ Searing Exarch Implicit Modifier (Grand) }
5% increased Action Speed
{ Eater of Worlds Implicit Modifier (Lesser) }
33(33-35)% increased Armour from Equipped Helmet and Gloves
--------
{ Fractured Suffix Modifier "of the Essence" — Attribute }
+58(51-58) to Intelligence
Searing Exarch Item
Eater of Worlds Item
--------
Fractured Item
"""


@requires_game_ready()
def main():
    ct = CurrencyTab()
    while not good_to_keep(parse_item_mods(ct.craft_coords)):
        mods = parse_item_mods(ct.craft_coords)
        if good_to_keep(mods):
            exit()
        if good_to_aug(mods):
            ct.aug()
        elif good_to_regal(mods):
            ct.regal()
        elif good_to_scoure(mods):
            ct.scoure()
        else:
            ct.alt()




if __name__ == "__main__":    main()