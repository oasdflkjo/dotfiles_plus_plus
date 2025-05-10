import json
import os
import time
import sys
import win32gui
import win32api
import win32con
import win32process
import psutil
from app_core import WindowTagger

# Global variables
zones_file = "zones.json"
tag_definitions_file = "tag_definitions.json"
tag_offsets_file = "tag_offsets.json"

zones = {}
tag_definitions = []
tag_offsets = {}
monitored_windows = set()


def load_configs():
    """Load all configuration files"""
    global zones, tag_definitions, tag_offsets

    # Load zones
    if os.path.exists(zones_file):
        try:
            with open(zones_file, "r") as f:
                zones = json.load(f)
            print(f"Loaded {len(zones)} zones")
        except Exception as e:
            print(f"Error loading zones: {e}")
            return False
    else:
        print(f"Zones file not found: {zones_file}")
        return False

    # Load tag definitions
    if os.path.exists(tag_definitions_file):
        try:
            with open(tag_definitions_file, "r") as f:
                tag_definitions = json.load(f)
            print(f"Loaded {len(tag_definitions)} tag definitions")
        except Exception as e:
            print(f"Error loading tag definitions: {e}")
            return False
    else:
        print(f"Tag definitions file not found: {tag_definitions_file}")
        return False

    # Load tag offsets
    if os.path.exists(tag_offsets_file):
        try:
            with open(tag_offsets_file, "r") as f:
                tag_offsets = json.load(f)
            print(f"Loaded {len(tag_offsets)} tag offsets")
        except Exception as e:
            print(f"Error loading tag offsets: {e}")
            return False
    else:
        print(f"Tag offsets file not found: {tag_offsets_file}")
        return False

    return True


def is_valid_window(hwnd):
    """Check if window is valid for processing"""
    if not win32gui.IsWindowVisible(hwnd):
        return False

    if not win32gui.IsWindow(hwnd):
        return False

    # Ignore windows with no title
    title = win32gui.GetWindowText(hwnd)
    if not title:
        return False

    # Ignore minimized windows
    if win32gui.IsIconic(hwnd):
        return False

    return True


def get_window_tag(hwnd):
    """Get tag for a window based on the tag definitions"""
    global tag_definitions

    try:
        # Get window info
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)

        # Get process name
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)

        # This requires psutil which you might need to install
        # For now, we'll just use a simpler approach
        process_name = None

        # Check each tag definition
        for tag_def in tag_definitions:
            match = True

            # Check class name if defined
            if "class_name" in tag_def and tag_def["class_name"] != class_name:
                match = False

            # Check process name if defined and available
            if (
                process_name
                and "process_name" in tag_def
                and tag_def["process_name"] != process_name
            ):
                match = False

            # Check title substring if defined
            if "title_substring" in tag_def and tag_def["title_substring"] not in title:
                match = False

            if match:
                return tag_def["name"]

    except Exception as e:
        print(f"Error getting window tag: {e}")

    return None


def get_window_geometry(hwnd):
    """Get window geometry"""
    rect = RECT()
    windll.user32.GetWindowRect(hwnd, byref(rect))

    return {
        "x": rect.left,
        "y": rect.top,
        "width": rect.right - rect.left,
        "height": rect.bottom - rect.top,
    }


def apply_zone_with_offsets(hwnd, tag_name):
    """Apply a zone to a window with tag-specific offsets"""
    global zones, tag_offsets

    # Default to "centered" zone
    zone_name = "centered"
    if zone_name not in zones:
        print(f"Zone '{zone_name}' not found")
        return False

    zone = zones[zone_name]

    try:
        # Get offsets for this tag
        offsets = tag_offsets.get(
            tag_name,
            {"x_offset": 0, "y_offset": 0, "width_offset": 0, "height_offset": 0},
        )

        # Get window geometry
        geo = get_window_geometry(hwnd)

        # Calculate screen center
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        # Calculate new position
        new_width = zone.get("width", screen_width * 0.8) + offsets["width_offset"]
        new_height = zone.get("height", screen_height * 0.8) + offsets["height_offset"]

        # Use zone position if available, otherwise center
        if "x" in zone and "y" in zone:
            new_x = zone["x"] + offsets["x_offset"]
            new_y = zone["y"] + offsets["y_offset"]
        else:
            new_x = (screen_width - new_width) // 2 + offsets["x_offset"]
            new_y = (screen_height - new_height) // 2 + offsets["y_offset"]

        # Print details
        title = win32gui.GetWindowText(hwnd)
        print(f"Applying zone to '{title}' with tag '{tag_name}'")
        print(f"  Position: ({new_x}, {new_y})")
        print(f"  Size: {new_width}x{new_height}")
        print(
            f"  Offsets: x:{offsets['x_offset']}, y:{offsets['y_offset']}, w:{offsets['width_offset']}, h:{offsets['height_offset']}"
        )

        # Set window position
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            int(new_x),
            int(new_y),
            int(new_width),
            int(new_height),
            win32con.SWP_SHOWWINDOW,
        )

        # Add to monitored windows
        monitored_windows.add(hwnd)
        return True
    except Exception as e:
        print(f"Error applying zone: {e}")
        return False


def enum_windows_callback(hwnd, tagger):
    """Process each window"""
    if hwnd not in monitored_windows and is_valid_window(hwnd):
        try:
            # Get window info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "unknown"

            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)

            # Get window position and size
            rect = win32gui.GetWindowRect(hwnd)
            x = rect[0]
            y = rect[1]
            width = rect[2] - x
            height = rect[3] - y

            window_info = {
                "hwnd": hwnd,
                "process_name": process_name,
                "window_title": window_title,
                "class_name": class_name,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }

            # Try to find a matching tag using the exact same function as in app_core.py
            tag_info = tagger.get_existing_tag_info(window_info)

            if tag_info:
                tag_name, offsets = tag_info

                # Get the centered zone
                centered = tagger.get_centered_zone()

                # Get offsets for this tag
                x_offset = offsets.get("x_offset", 0)
                y_offset = offsets.get("y_offset", 0)
                width_offset = offsets.get("width_offset", 0)
                height_offset = offsets.get("height_offset", 0)

                print(f"Tagged window: '{window_title}' (Class: {class_name})")
                print(f"  Tag: {tag_name}")
                print(
                    f"  Applying offsets: x:{x_offset}, y:{y_offset}, w:{width_offset}, h:{height_offset}"
                )

                # Apply centering with offsets using the exact same function from app_core.py
                tagger.position_window_with_offsets(
                    hwnd,
                    centered.get("x", 0),
                    centered.get("y", 0),
                    centered.get("width", 0),
                    centered.get("height", 0),
                    x_offset,
                    y_offset,
                    width_offset,
                    height_offset,
                )

                # Flash the window to indicate success
                win32gui.FlashWindow(hwnd, True)

            # Add to monitored windows regardless of whether we centered it
            monitored_windows.add(hwnd)

        except Exception as e:
            print(f"Error processing window: {e}")


def monitor_windows(tagger):
    """Monitor for windows and apply tags to new ones"""
    print("Monitoring for new windows...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            # Check for new windows
            win32gui.EnumWindows(
                lambda hwnd, param: enum_windows_callback(hwnd, tagger), None
            )

            # Sleep to reduce CPU usage
            time.sleep(1)
    except KeyboardInterrupt:
        print("Monitoring stopped")


def main():
    """Main function"""
    print("Auto Resize Monitor Starting...")

    # Initialize the WindowTagger (same as in the main app)
    tagger = WindowTagger()

    # Start monitoring
    monitor_windows(tagger)


if __name__ == "__main__":
    main()
