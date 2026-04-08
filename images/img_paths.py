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
# CHAOS = img("chaos")
# EXALT = img("exalt")
# REGAL = img("regal")
# ANNUL = img("annul")
# TRANS = img("trans")
# AUG = img("aug")
# ALT = img("alt")
# SCOURE = img("scoure")
# ENKINDLE = img("enkindle")