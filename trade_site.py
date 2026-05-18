from images.image_utils import *
from images.img_paths import *
from focus_window import focus_window, focus_window_partial
from macros.rpa_macros import *
from macros.map_parser import *

focus_window_partial("Trade - Path of Exile")
time.sleep(1)
click_image(TRAVEL_HO_BUTTON, confidence=0.8)
focus_window()
while not locate_center(MERCH_OPEN, confidence=0.9):
    time.sleep(0.5)

time.sleep(1)
print(locate_all_centers_region(ORIGINATOR_MAP, "merch", confidence=0.95))
# 



def buy_map(coords):
    map = parse_map_mods(coords)
    print(map.get("price"))


for coords in locate_all_centers_region(ORIGINATOR_MAP, "merch", confidence=0.95):
    buy_map(coords)

press("esc", times=2)
focus_window_partial("trade_site.py")