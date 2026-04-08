import win32gui
import win32con
import time

def focus_window(window_name):
    def enum_windows_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if window_name.lower() in title.lower():
                windows.append(hwnd)

    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)

    if not windows:
        print(f"No window found with name: {window_name}")
        return

    hwnd = windows[0]

    # Restore if minimized
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    # Bring to foreground
    win32gui.SetForegroundWindow(hwnd)
    print(f"Focused window: {win32gui.GetWindowText(hwnd)}")

if __name__ == "__main__":
    time.sleep(2)  # Gives you time to switch context if needed
    focus_window("Path of Exile")