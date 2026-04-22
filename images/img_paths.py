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
SOURCE_TAB_LAPOP = img("source_tab_laptop")
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