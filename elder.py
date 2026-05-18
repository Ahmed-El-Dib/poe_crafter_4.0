from macros.rpa_macros import *
from images.image_utils import *
from images.img_paths import *
from stash.tabs.currency_tab import *
from stash.tabs.grid_tab import *
from inventory.inv_actions import *
from stash.tabs.shard_tab import *
from map_device.map_device import MapDeviceUI



# shard_tab = ShardTab()

# shard_tab.get_frag(UBER_ELDER_FRAG_STASH, num_frags=4)

# map_device = MapDeviceUI()

# map_device.open_uber(UBER_ELDER_FRAG_INV)
# map_device.activate(maven=True)

def enter_arena(portal_img: str = UBER_ELDER_PORTAL, confidence: float = 0.8, grayscale: bool = False) -> bool:
    # while not locate_center(portal_img, confidence=confidence, grayscale=grayscale,retry_with_mouse_clear=False):
    #     time.sleep(0.5)
    # coords = locate_center(portal_img, confidence=confidence,retry_with_mouse_clear=False)
    # if coords is None:
    #     print("Could not find portal to enter.")
    #     return False

    # click(coords)
    # while not locate_center(ZANA, confidence=confidence, grayscale=grayscale,retry_with_mouse_clear=False):
    #     time.sleep(0.5)

    # #inch closer to first portal
    # click(coords=(50,550))
    # time.sleep(2)
    # # # enter first portal
    
    # portal_coords = locate_center(GEN_PORTAL, confidence=confidence, grayscale=grayscale,retry_with_mouse_clear=False)
    # portal_coords = (portal_coords[0], portal_coords[1]+50) if portal_coords else None
    # print(portal_coords)
    # pyautogui.moveTo(portal_coords, duration=1) if portal_coords else None
    # exit()
    # click(portal_coords)

    # step twice to second portal
    click((705, 115))
    time.sleep(2)
    click((705, 115))

    # wait for cutscene
    while not locate_center(GEN_PORTAL, confidence=0.8, grayscale=True,retry_with_mouse_clear=False):
        time.sleep(0.5)

    # enter second portal
    click_image(GEN_PORTAL, confidence=0.8, grayscale=True)
    time.sleep(1)
    press("e")
    time.sleep(0.1)
    press("w")
    # go to arena center
    click((500, 140))
    time.sleep(2)
    #activate lazer and rf
    
    return True

enter_arena()



