"""
Print screen coordinates to the console on each right click
and show a small overlay near the cursor with the current
mouse position.

Stop with Ctrl+C.
"""

import threading
import tkinter as tk

from pynput import mouse
from focus_window import focus_window

focus_window("Path of Exile")


# -----------------------------
# Overlay UI
# -----------------------------
class CursorOverlay:
    def __init__(self):
        self.root = tk.Tk()

        # Remove window borders
        self.root.overrideredirect(True)

        # Keep on top
        self.root.attributes("-topmost", True)

        # Transparent background support
        self.root.attributes("-alpha", 0.85)

        # Small label
        self.label = tk.Label(
            self.root,
            text="(0, 0)",
            font=("Consolas", 10),
            bg="black",
            fg="lime",
            padx=6,
            pady=2,
        )
        self.label.pack()

        # Prevent taskbar icon
        self.root.withdraw()
        self.root.deiconify()

    def update_position(self, x, y):
        self.label.config(text=f"{x}, {y}")

        # Slightly right and above cursor
        offset_x = 12
        offset_y = -40

        self.root.geometry(f"+{x + offset_x}+{y + offset_y}")

    def run(self):
        self.root.mainloop()


overlay = CursorOverlay()


# -----------------------------
# Mouse callbacks
# -----------------------------
def on_move(x, y):
    overlay.root.after(0, overlay.update_position, x, y)


def on_click(x, y, button, pressed):
    if button == mouse.Button.right and pressed:
        print(f"({x}, {y})", flush=True)


# -----------------------------
# Main
# -----------------------------
def main():
    print(
        "Listening for right clicks — coordinates print below. Ctrl+C to quit.",
        flush=True,
    )

    listener = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
    )

    listener.start()

    overlay.run()

    listener.join()


if __name__ == "__main__":
    main()