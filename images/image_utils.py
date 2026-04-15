import mss, pyautogui
from PIL import Image
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

