import win32gui
import win32process
import win32con
import json
import psutil
import os
from datetime import datetime

# List of window classes to ignore
IGNORED_WINDOW_CLASSES = [
    "Shell_TrayWnd",  # Taskbar
    "DV2ControlHost",  # Windows Desktop
    # Removed UWP classes from ignored list to properly detect them
]

# UWP classes to look for when identifying real app windows
UWP_CLASSES = [
    "Windows.UI.Core.CoreWindow",
    "ApplicationFrameWindow",
]


def get_window_class(hwnd):
    """Get the class name of a window."""
    try:
        return win32gui.GetClassName(hwnd)
    except Exception:
        return ""


def is_window_visible_and_valid(hwnd):
    """Check if window is visible and has a title."""
    if not win32gui.IsWindowVisible(hwnd):
        return False

    if not win32gui.GetWindowText(hwnd):
        return False

    return True


def get_window_pid(hwnd):
    """Get the PID of the process that created the window."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except Exception:
        return None


def get_process_name(pid):
    """Get the name of the process using psutil."""
    try:
        return psutil.Process(pid).name()
    except Exception:
        return "Unknown"


def scan_windows():
    """
    Scan all active windows and return a list of window information dictionaries
    """
    windows = []
    uwp_windows = {}  # Store UWP windows by PID for special handling

    def enum_callback(hwnd, _):
        # Skip invisible or minimized windows
        if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
            return True

        # Get window title
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True

        # Get window class
        window_class = win32gui.GetClassName(hwnd)

        # Skip certain system windows
        if window_class in IGNORED_WINDOW_CLASSES:
            return True

        # Get process information
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Skip if we couldn't get the process ID
        if not pid:
            return True

        try:
            process = psutil.Process(pid)
            process_name = process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Skip processes we can't access
            return True

        # Get window rect
        rect = win32gui.GetWindowRect(hwnd)

        # Special handling for UWP apps
        is_uwp = False
        for uwp_class in UWP_CLASSES:
            if uwp_class in window_class:
                is_uwp = True
                break

        # Process UWP windows
        if is_uwp:
            # For ApplicationFrameWindow, improve name detection
            if window_class == "ApplicationFrameWindow":
                # Try to use title to determine a better app name
                if "Calculator" in title:
                    process_name = "CalculatorApp"
                elif "Photos" in title:
                    process_name = "PhotosApp"
                elif "Settings" in title:
                    process_name = "SettingsApp"
                else:
                    # Extract app name from window title
                    app_name = title.split(" - ")[0] if " - " in title else title
                    app_name = app_name.replace(" ", "")
                    process_name = app_name + "App"

            # Add all UWP windows to the list - we'll handle filtering in the window manager
            window_info = {
                "hwnd": hwnd,
                "title": title,
                "class": window_class,
                "pid": pid,
                "process_name": process_name.replace(".exe", ""),
                "rect": rect,
                "is_uwp": True,
            }
            windows.append(window_info)
            return True

        # Create window info dictionary for regular windows
        window_info = {
            "hwnd": hwnd,
            "title": title,
            "class": window_class,
            "pid": pid,
            "process_name": process_name.replace(".exe", ""),
            "rect": rect,
            "is_uwp": is_uwp,
        }

        # Add to windows list
        windows.append(window_info)
        return True

    # Enumerate all windows
    win32gui.EnumWindows(enum_callback, None)

    return windows


def save_windows_to_json(windows, output_file="windows.json"):
    """Save windows data to JSON file."""
    # Add timestamp and metadata
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_windows": len(windows),
        "windows": windows,
    }

    # Convert hwnd to string since JSON doesn't support int keys
    for window in data["windows"]:
        window["hwnd"] = str(window["hwnd"])

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(windows)} windows to {os.path.abspath(output_file)}")
    return os.path.abspath(output_file)


def main():
    """Main function to scan windows and save to JSON."""
    print("Scanning windows...")
    windows = scan_windows()

    # Sort windows by process name for better readability
    windows.sort(key=lambda w: w.get("process_name", "").lower())

    # Save to JSON
    json_path = save_windows_to_json(windows)
    print(f"Window data saved to {json_path}")

    # Print out calculators specifically for debugging
    calculator_windows = [
        w
        for w in windows
        if "Calculator" in w.get("title", "")
        or "Calculator" in w.get("process_name", "")
    ]
    if calculator_windows:
        print("\nCalculator windows found:")
        for calc in calculator_windows:
            print(f"  - {calc['process_name']} | {calc['class']} - '{calc['title']}'")
            print(f"    Position: {calc['rect']}")
    else:
        print("\nNo Calculator windows found!")

    # Print manageable windows
    print("\nAll windows found:")
    for window in windows:
        print(f"  - {window['process_name']} | {window['class']} - '{window['title']}'")

    return windows


if __name__ == "__main__":
    main()
