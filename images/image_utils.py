import mss, pyautogui
from PIL import Image
from images.img_paths import *
import time
# import easyocr
# reader = easyocr.Reader(['en'])
# -----------------------------------------------------------
# Primitive: Locate the center of an image
# -----------------------------------------------------------

# from utils.initiate_session import requires_game_ready


def locate_center(image_path, confidence=0.9, retry_with_mouse_clear=True,grayscale=False):
    """
    Returns (x, y) center of image OR None.
    Retries once after moving mouse if initial detection fails.
    """

    template = Image.open(image_path)

    def _search():
        with mss.mss() as sct:
            for mon in sct.monitors[1:]:
                scr = sct.grab(mon)
                screenshot = Image.frombytes(
                    "RGB",
                    (mon["width"], mon["height"]),
                    scr.rgb
                )

                try:
                    loc = pyautogui.locate(template, screenshot, confidence=confidence, grayscale=grayscale)
                except Exception:
                    loc = None

                if loc:
                    cx = mon["left"] + loc.left + loc.width // 2
                    cy = mon["top"] + loc.top + loc.height // 2
                    return (cx, cy)

        return None

    # First attempt
    coords = _search()
    if coords:
        return coords

    # Retry after clearing mouse obstruction
    if retry_with_mouse_clear:
        pyautogui.moveTo(200, 1900)
        time.sleep(0.1)
        return _search()

    return None

def locate_all_centers(image_path, confidence=0.9):
    """
    Returns [(x, y), ...] centers of every matching image on screen.
    Returns [] if none found.
    """

    template = Image.open(image_path)
    results = []

    with mss.mss() as sct:
        for mon in sct.monitors[1:]:
            scr = sct.grab(mon)

            screenshot = Image.frombytes(
                "RGB",
                (mon["width"], mon["height"]),
                scr.rgb
            )

            try:
                matches = pyautogui.locateAll(
                    template,
                    screenshot,
                    confidence=confidence
                )
            except Exception:
                matches = []

            for loc in matches:
                cx = mon["left"] + loc.left + loc.width // 2
                cy = mon["top"] + loc.top + loc.height // 2
                results.append((cx, cy))

    return results

from PIL import Image
import pyautogui
import mss

from config import  INV_TL, INV_BR, STASH_TL, STASH_BR, MERCH_TL, MERCH_BR, SHOP_TL, SHOP_BR
REGIONS = {
    "inv":   (INV_TL, INV_BR),
    "stash": (STASH_TL, STASH_BR),
    "merch": (MERCH_TL, MERCH_BR),
    "shop":  (SHOP_TL, SHOP_BR),
}


def locate_all_centers_region(
    image_path,
    region_name,
    confidence=0.9,
    min_distance=8,
    grayscale=True
):
    """
    region_name: "inv", "stash", "merch", or "shop"

    Returns [(x, y), ...] centers of all matches inside that region.
    """

    if region_name not in REGIONS:
        raise ValueError(f"Invalid region '{region_name}'. Use: {list(REGIONS.keys())}")

    top_left, bottom_right = REGIONS[region_name]

    x1, y1 = top_left
    x2, y2 = bottom_right

    width = x2 - x1
    height = y2 - y1

    if width <= 0 or height <= 0:
        return []

    template = Image.open(image_path)
    results = []

    with mss.mss() as sct:
        scr = sct.grab({
            "left": x1,
            "top": y1,
            "width": width,
            "height": height
        })

        screenshot = Image.frombytes(
            "RGB",
            (width, height),
            scr.rgb
        )

        try:
            matches = list(pyautogui.locateAll(
                template,
                screenshot,
                confidence=confidence,
                grayscale=grayscale
            ))
        except Exception:
            matches = []

        for loc in matches:
            cx = x1 + loc.left + loc.width // 2
            cy = y1 + loc.top + loc.height // 2

            is_duplicate = any(
                abs(cx - px) <= min_distance and abs(cy - py) <= min_distance
                for px, py in results
            )

            if not is_duplicate:
                results.append((cx, cy))

    return results

# def locate_center(image_path, confidence=0.9, region=None):
#     try:
#         kwargs = {"confidence": confidence}

#         if region is not None:
#             kwargs["region"] = region  # (x, y, width, height)

#         return pyautogui.locateCenterOnScreen(
#             image_path,
#             **kwargs
#         )

#     except Exception as e:
#         print(e)
#         return None
    
# import time

def wait_for_image(image_path, timeout=10, interval=0.3, confidence=0.9, region=None):
    """
    Waits until image appears on screen.

    Returns (x, y) center OR None if timeout.
    """
    start = time.time()

    while True:
        pos = locate_center(
            image_path,
            confidence=confidence,
            region=region
        )

        if pos:
            return pos

        if time.time() - start > timeout:
            return None

        time.sleep(interval)

    
# create a locate_order_entry function thats takes in want or have as options, returns item_input, qty_input based on an offset from the center of I_WANT_LAPTOP or I_HAVE_LAPTOP depending on the option passed in, and also takes in an optional confidence parameter for locating the laptop images
def locate_order_entry(option, confidence=0.8):
    if option == "want":
        base_coords = locate_center(I_WANT_LAPTOP, confidence=confidence)
    elif option == "have":
        base_coords = locate_center(I_HAVE_LAPTOP, confidence=confidence)
    else:
        raise ValueError("Option must be 'want' or 'have'")

    if not base_coords:
        raise RuntimeError(f"Could not locate {option} laptop image")

    #offsets are based on want vs have
    if option == "want":
        item_input = (base_coords[0], base_coords[1] + 50)
        qty_input = (base_coords[0] + 150, base_coords[1] + 50)
    else:
        item_input = (base_coords[0], base_coords[1] + 50)
        qty_input = (base_coords[0] - 150, base_coords[1] + 50)

    return item_input, qty_input



