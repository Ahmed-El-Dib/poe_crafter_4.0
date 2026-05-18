from pathlib import Path

# Root of the package
BASE_DIR = Path(__file__).resolve().parent.parent

IMAGES_DIR = BASE_DIR / "images" / "image_files"

# Helper to get any image by filename
def img(name: str) -> Path:
    name = name + ".png" 
    return IMAGES_DIR / name

SOURCE_TAB = img("source_tab")
COMPLETED_TAB = img("completed_tab")
CURRENCY_TAB = img("currency_tab")
STASH_OPEN = img("stash_open")
STASH_TEXT = img("stash_text")
ESSENCE_TAB = img("essence_tab")
# CHAOS = img("chaos")
# EXALT = img("exalt")
# REGAL = img("regal")
# ANNUL = img("annul")
# TRANS = img("trans")
# AUG = img("aug")
# ALT = img("alt")
# SCOURE = img("scoure")
# ENKINDLE = img("enkindle")

CURRENCY_TAB_LAPTOP = img("currency_tab_laptop")
SOURCE_TAB_LOCATOR = img("source_tab_laptop")
SOURCE_TAB_OPEN = img("source_tab_open")
SOURCE_TAB_LAPOP = img("source_tab_laptop")
COMPLETED_TAB_LOCATOR = img("completed_tab")
COMPLETED_TAB_OPEN = img("completed_tab_open")
STASH_TEXT_LAPTOP = img("stash_text")
STASH_OPEN_LAPTOP = img("stash_open")
FAUSTUS_PERSON_LAPTOP = img("faustus_person")
EXCHANGE_OPEN_LAPTOP = img("exchange_open")
I_WANT_LAPTOP = img("i_want")
I_HAVE_LAPTOP = img("i_have")
EXALT_EXCHANGE_LAPTOP = img("exalt_exchange")
ALT_EXCHANGE_LAPTOP = img("alt_exchange")
CHAOS_EXCHANGE_LAPTOP = img("chaos_exchange")
DIVINE_EXCHANGE_LAPTOP = img("divine_exchange")
UNMAKING_EXCHANGE_LAPTOP = img("unmaking_exchange")
OUT_OF_JUICE = img("out_of_juice")
CURRENCY_TAB_OPEN = img("currency_tab_open")

SHARD_TAB_LOCATOR = img("shard_tab")
SHARD_TAB_OPEN = img("shard_tab_open")
GENERAL_TAB = img("general_tab")
# UBER_ELDER_FRAG = img("uber_elder_frag")
UBER_ELDER_FRAG_STASH = img("uber_elder_frag_stash")
UBER_ELDER_FRAG_INV = img("uber_elder_frag_inv")
UBER_ELDER_PORTAL = img("uber_elder_portal")
UBER_ELDER_STEP_1 = img("elder_step_1")
# MAP DEVICE
GEN_PORTAL = img("gen_portal")
ZANA = img("zana")
MAP_DEVICE_LOCATOR = img("map_device_locator")
MAP_DEVICE_OPEN = img("map_device_open")
MAVEN_ACTIVATE = img("maven_activate")
MAVEN_ACTIVATE_READY = img("maven_activate_ready")
ACTIVATE_READY = img("activate_ready")
#MAPS
BARAN_MAP = img("baran_map")
VERATANIA_MAP = img("veratanian_map")
DROX_MAP = img("drox_map")
HAZMIN_MAP = img("hazmin_map")
ORIGINATOR_MAP = img("originator_map")

MERCH_OPEN = img("merch_open")
TRAVEL_HO_BUTTON = img("travel_ho_button")


ALT_IMG = img("alt_img")
AUG_IMG = img("aug_img")
CHAOS_IMG = img("chaos_img")
EXALT_IMG = img("exalt_img") 
REGAL_IMG = img("regal_img")
ANNUL_IMG = img("annul_img")
TRANS_IMG = img("trans_img")
SCOURE_IMG = img("scoure")
DIVINE_IMG = img("divine_img")

SHOP_OPEN = img("shop_open")
SHOP_TEXT = img("shop_text")


SHOP_TAB_1 = img("shop_tab_1")
SHOP_TAB_2 = img("shop_tab_2")
SHOP_TAB_3 = img("shop_tab_3")
SHOP_TAB_4 = img("shop_tab_4")
SHOP_TAB_5 = img("shop_tab_5")

SHOP_SELL_SIDE = img("shop_sell_tab")
SELL_SIDE_OPEN = img("sell_side_open")
EARNINGS_SIDE = img("earnings_tab")
EARNINGS_SIDE_OPEN = img("earnings_side_open")

INVENTORY_OPEN = img("inventory_open")
INVENTORY_EMPTY = img("inventory_empty")

ELDER_STEP_1 = img("elder_step_1")
ELDER_ARENA = img("elder_arena")
ELDER_STEP_2 = img("elder_step_2")

FLASK_WARNING = img("flask_warning")
QUANT_WARNING = img("quant_warning")
QUANT_RARITY_WARNING = img("quant_rarity_warning")
GRAND_WARNING = img("grand_warning")
GCP_WARNING = img("gcp_warning")
DUPE_WARNING = img("dupe_warning")
RES_WARNING = img("res_warning")
MINUS_WARNING = img("minus_warning")

STAIRS = img("stairs")