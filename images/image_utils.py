import mss, pyautogui
from PIL import Image
from images.img_paths import *
# import easyocr
# reader = easyocr.Reader(['en'])
# -----------------------------------------------------------
# Primitive: Locate the center of an image
# -----------------------------------------------------------
def locate_center(image_path, confidence=0.9):
    """
    Returns (x, y) center of image OR None.
    """
    template = Image.open(image_path)

    with mss.mss() as sct:
        for mon in sct.monitors[1:]:
            scr = sct.grab(mon)
            screenshot = Image.frombytes("RGB", (mon["width"], mon["height"]), scr.rgb)

            try:
                loc = pyautogui.locate(template, screenshot, confidence=confidence)
            except Exception as e:
                print(e)
                loc = None

            if loc:
                cx = mon["left"] + loc.left + loc.width // 2
                cy = mon["top"] + loc.top + loc.height // 2
                return (cx, cy)

    return None

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

#create a locate_from_text thats uses ocr to find the coordinates of a text string on the screen, returns the center coordinates of the text if found, None otherwise
import numpy as np

def locate_from_text(text, confidence=0.8):
    
    matches = []

    with mss.mss() as sct:
        for mon in sct.monitors[1:]:
            scr = sct.grab(mon)

            # Convert directly to numpy array
            img = np.array(scr)[:, :, :3]  # drop alpha channel

            result = reader.readtext(img)

            for (bbox, detected_text, prob) in result:
                if detected_text.lower() == text.lower() and prob >= confidence:
                    (top_left, top_right, bottom_right, bottom_left) = bbox

                    cx = int((top_left[0] + bottom_right[0]) / 2)
                    cy = int((top_left[1] + bottom_right[1]) / 2)

                    matches.append((top_left[1], top_left[0], cx, cy))

    if matches:
        matches.sort()
        _, _, cx, cy = matches[0]
        return (cx, cy)

    return None

