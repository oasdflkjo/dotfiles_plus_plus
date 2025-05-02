import win32gui
import win32process
import win32con
import json
import psutil
import os
from datetime import datetime


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
    """Scan all windows and return their details."""
    windows = []

    def enum_callback(hwnd, _):
        if not is_window_visible_and_valid(hwnd):
            return True

        title = win32gui.GetWindowText(hwnd)
        window_class = get_window_class(hwnd)

        # Get window position and size
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Skip windows with zero dimensions
            if width <= 0 or height <= 0:
                return True

            # Get process information
            pid = get_window_pid(hwnd)
            process_name = get_process_name(pid) if pid else "Unknown"

            # Store window data
            windows.append(
                {
                    "hwnd": hwnd,
                    "title": title,
                    "class": window_class,
                    "pid": pid,
                    "process_name": process_name,
                    "position": {"x": left, "y": top, "width": width, "height": height},
                }
            )
        except Exception as e:
            print(f"Error processing window {title}: {e}")

        return True

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


if __name__ == "__main__":
    main()
