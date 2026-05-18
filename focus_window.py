import win32gui
import win32con
import time

#should return true if window is focused, false otherwise - and only try to focus if not already focused

def focus_window(window_title="Path of Exile"):
    # Get the handle of the window with the specified title
    hwnd = win32gui.FindWindow(None, window_title)

    if hwnd == 0:
        print(f"Window '{window_title}' not found.")
        return False

    # Check if the window is already in the foreground
    if win32gui.GetForegroundWindow() == hwnd:
        print(f"Window '{window_title}' is already focused.")
        return True

    # Bring the window to the foreground
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # Restore if minimized
    win32gui.SetForegroundWindow(hwnd)
    print(f"Window '{window_title}' has been focused.")
    return True 

import time
import win32gui
import win32con


def focus_window_partial(partial_title):
    target_hwnd = None

    def enum_handler(hwnd, _):
        nonlocal target_hwnd

        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)

            if partial_title.lower() in title.lower():
                target_hwnd = hwnd

    # Enumerate all windows
    win32gui.EnumWindows(enum_handler, None)

    if not target_hwnd:
        print(f"No window containing '{partial_title}' found.")
        return False

    # Already focused
    if win32gui.GetForegroundWindow() == target_hwnd:
        print(f"Window already focused.")
        return True

    # Restore if minimized
    win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)

    # Focus window
    win32gui.SetForegroundWindow(target_hwnd)

    print(f"Focused window: {win32gui.GetWindowText(target_hwnd)}")
    return True




if __name__ == "__main__":
    time.sleep(2)  # Gives you time to switch context if needed
    focus_window()