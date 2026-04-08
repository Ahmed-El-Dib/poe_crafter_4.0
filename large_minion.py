from macros.currency_macros import *
from config import *    
from macros.item_parser import parse_boot_mods, parse_item_mods
from focus_window import focus_window

focus_window("Path of Exile")





item_mods = []
target = "Primordial Bond"
spamming = False

def found():
    return any(target.lower() in mod.get('text', '').lower() for mod in item_mods)

def determine_action_single_suffix(mods):
    global spamming
    # Check if target mod is found
    if found():
        print("good job!")
        exit() # or exit() if you really want to stop execution

    has_prefix = any(mod.get('type') == 'prefix' for mod in mods)
    has_suffix = any(mod.get('type') == 'suffix' for mod in mods)

    # Case 1: prefix only
    if has_prefix and not has_suffix:
        if spamming:
            return alt_currency(AUG)
        else:
            spamming = False
            return use_currency(AUG)
        

    # Case 2: both prefix and suffix
    if has_suffix:
        if spamming:
            return spam_currency(ALT)
        else:
            spamming = True
            return use_currency(ALT, spammable=True)
            
        

while True:
    item_mods = parse_item_mods(CURRENCY_CRAFT_COORDS)  # update global
    determine_action_single_suffix(item_mods)


 
    


