"""
Print screen coordinates to the console on each right click.
Stop with Ctrl+C.
"""

from pynput import mouse
from focus_window import focus_window

focus_window()

def on_click(x, y, button, pressed):
    if button == mouse.Button.right and pressed:
        print(f"({x}, {y})", flush=True)


def main():
    print("Listening for right clicks — coordinates print below. Ctrl+C to quit.", flush=True)
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()


if __name__ == "__main__":
    main()
