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

if __name__ == "__main__":
    time.sleep(2)  # Gives you time to switch context if needed
    focus_window()