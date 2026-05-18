import time
import tkinter as tk

from macros.rpa_macros import *
from images.image_utils import locate_center
from images.img_paths import *


class DetectionOverlay:
    def __init__(self):
        self.root = tk.Tk()

        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.attributes("-transparentcolor", "black")

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        self.root.geometry(f"{screen_w}x{screen_h}+0+0")

        self.canvas = tk.Canvas(
            self.root,
            bg="black",
            highlightthickness=0
        )

        self.canvas.pack(fill="both", expand=True)

        self.box_size = 80

    def draw_box(self, x, y, color):
        size = self.box_size

        self.canvas.create_rectangle(
            x - size // 2,
            y - size // 2,
            x + size // 2,
            y + size // 2,
            outline=color,
            width=5
        )

    def clear(self):
        self.canvas.delete("all")

    def update(self):
        self.root.update()


def watch_for_images(
    good_images,
    bad_images,
    confidence=0.8,
    scan_interval=0.1,
    grayscale=True
):
    overlay = DetectionOverlay()

    while True:
        try:
            overlay.clear()

            bad_found = False

            # BAD IMAGES FIRST
            for image_path in bad_images:
                coords = locate_center(
                    image_path,
                    confidence=confidence,
                    retry_with_mouse_clear=False,
                    grayscale=grayscale
                )

                if coords:
                    x, y = coords
                    overlay.draw_box(x, y, "#FF0000")
                    bad_found = True

            # ONLY CHECK GOOD IF NO BAD WAS FOUND
            if not bad_found:
                for image_path in good_images:
                    coords = locate_center(
                        image_path,
                        confidence=confidence,
                        retry_with_mouse_clear=False,
                        grayscale=grayscale
                    )

                    if coords:
                        x, y = coords
                        overlay.draw_box(x, y, "#00FF00")

            overlay.update()
            time.sleep(scan_interval)

        except KeyboardInterrupt:
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(0.5)


# Example
watch_for_images(
    good_images=[
        DUPE_WARNING,
        QUANT_RARITY_WARNING,
        GRAND_WARNING,
        GCP_WARNING,
        
    ],

    bad_images=[
        FLASK_WARNING,
        RES_WARNING,
    ],

    confidence=0.88,
    scan_interval=0.05,
    grayscale=True
)