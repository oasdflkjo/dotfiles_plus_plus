import win32gui
import win32api
import win32con
import win32process
import ctypes
from ctypes import wintypes
import json
import os
import time
import sys

# Import window identification module
from window_identification import identify_window

print("→ sys.executable:", sys.executable)
print("→ script __file__:", os.path.abspath(__file__))
print("→ cwd:", os.getcwd())

# Configuration files
ZONES_FILE = "zones.json"
OFFSETS_FILE = "window_offsets.json"

# Hotkey constants
MOD_WIN = 0x0008
VK_C = 0x43
HOTKEY_ID_CENTER = 1

# Global variables
zones = []  # Making zones global so it can be accessed by hotkey handlers


class Zone:
    def __init__(self, name, x, y, width, height, description=""):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.description = description

    def contains_point(self, x, y):
        """Check if point is inside this zone."""
        return (
            self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height
        )


def get_file_mod_time(file_path):
    """Get the last modification time of a file"""
    try:
        if os.path.exists(file_path):
            return os.path.getmtime(file_path)
        return 0
    except Exception as e:
        print(f"Error getting file mod time: {e}")
        return 0


def load_zones(file_path=ZONES_FILE):
    """Load zones from JSON file"""
    try:
        # Get screen dimensions
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)

            zones = []
            for key, zone_data in data.items():
                zones.append(
                    Zone(
                        zone_data.get("name", key),
                        zone_data.get("x", 0),
                        zone_data.get("y", 0),
                        zone_data.get("width", screen_width // 2),
                        zone_data.get("height", screen_height // 2),
                        zone_data.get("description", ""),
                    )
                )

            if zones:
                print(f"Loaded {len(zones)} zones from {file_path}")
                return zones
    except Exception as e:
        print(f"Error loading zones: {e}")

    # Create default zones if loading fails
    print("Creating default zones")
    return [
        Zone(
            "Left Half", 0, 0, screen_width // 2, screen_height, "Left half of screen"
        ),
        Zone(
            "Right Half",
            screen_width // 2,
            0,
            screen_width // 2,
            screen_height,
            "Right half of screen",
        ),
        Zone(
            "Centered",
            screen_width // 6,
            screen_height // 12,
            2 * screen_width // 3,
            5 * screen_height // 6,
            "Centered window with margins",
        ),
    ]


def load_window_offsets(file_path=OFFSETS_FILE):
    """Load window offsets from JSON file"""
    # Default structure with empty applications list
    default_data = {"applications": []}

    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)

            # Ensure applications exists in the data
            if "applications" not in data:
                data["applications"] = []

            # Minimal migration for legacy entries
            for app in data["applications"]:
                # Convert older entries to the new format
                if "id" not in app and "pattern" in app:
                    app["id"] = app["pattern"]

            return data
    except Exception as e:
        print(f"Error loading window offsets: {e}")

    # Return default structure if file doesn't exist or has errors
    return default_data


def find_window_offsets(window_id, offsets_data):
    """Find offsets for a specific window ID"""
    # Hardcoded defaults
    default_offsets = {
        "x_offset": 0,
        "y_offset": 0,
        "width_offset": 0,
        "height_offset": 0,
    }

    if not window_id:
        return default_offsets

    # Look for matching entry
    for app in offsets_data.get("applications", []):
        if window_id == app.get("id", app.get("pattern", "")):
            return app

    # Return defaults if no match found
    return default_offsets


def create_overlay(zone):
    """Create a simple overlay showing the zone"""
    # Register window class
    class_name = "ZoneOverlayClass"
    wc = win32gui.WNDCLASS()
    wc.lpszClassName = class_name
    wc.hInstance = win32api.GetModuleHandle(None)
    wc.hbrBackground = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0))
    wc.lpfnWndProc = win32gui.DefWindowProc
    wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW

    try:
        win32gui.RegisterClass(wc)
    except:
        pass

    # Create window
    style = win32con.WS_POPUP
    ex_style = (
        win32con.WS_EX_LAYERED
        | win32con.WS_EX_TRANSPARENT
        | win32con.WS_EX_TOPMOST
        | win32con.WS_EX_TOOLWINDOW
    )

    try:
        hwnd = win32gui.CreateWindowEx(
            ex_style,
            class_name,
            "Zone Overlay",
            style,
            zone.x,
            zone.y,
            zone.width,
            zone.height,
            0,
            0,
            wc.hInstance,
            None,
        )

        # Paint the border
        hdc = win32gui.GetDC(hwnd)
        pen = win32gui.CreatePen(win32con.PS_SOLID, 2, win32api.RGB(120, 170, 240))
        old_pen = win32gui.SelectObject(hdc, pen)
        win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
        null_brush = win32gui.GetStockObject(win32con.NULL_BRUSH)
        old_brush = win32gui.SelectObject(hdc, null_brush)

        # Draw border
        win32gui.Rectangle(hdc, 0, 0, zone.width, zone.height)

        # Cleanup
        win32gui.SelectObject(hdc, old_pen)
        win32gui.SelectObject(hdc, old_brush)
        win32gui.DeleteObject(pen)
        win32gui.ReleaseDC(hwnd, hdc)

        # Set transparency
        color_key = win32api.RGB(0, 0, 0)
        win32gui.SetLayeredWindowAttributes(
            hwnd, color_key, 50, win32con.LWA_COLORKEY | win32con.LWA_ALPHA
        )

        # Show window
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.UpdateWindow(hwnd)

        return hwnd
    except Exception as e:
        print(f"Error creating overlay: {e}")
        return None


def destroy_overlay(hwnd):
    """Destroy overlay window"""
    if hwnd:
        try:
            win32gui.DestroyWindow(hwnd)
        except:
            pass


def is_shift_pressed():
    """Check if shift key is pressed"""
    return (
        win32api.GetAsyncKeyState(win32con.VK_SHIFT) & 0x8000 != 0
        or win32api.GetAsyncKeyState(win32con.VK_LSHIFT) & 0x8000 != 0
        or win32api.GetAsyncKeyState(win32con.VK_RSHIFT) & 0x8000 != 0
    )


def is_mouse_button_pressed():
    """Check if left mouse button is pressed"""
    return win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000 != 0


def move_window_to_zone(hwnd, zone, offsets):
    """Move a window to a specific zone with offsets"""
    try:
        if not (hwnd and zone):
            return False

        # For fullscreen windows or minimized windows, we'll skip
        window_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if (
            not (window_style & win32con.WS_VISIBLE)
            or window_style & win32con.WS_MINIMIZE
        ):
            return False

        # Get current window rect
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except:
            return False

        # Apply offsets
        x = zone.x + offsets.get("x_offset", 0)
        y = zone.y + offsets.get("y_offset", 0)
        width = zone.width + offsets.get("width_offset", 0)
        height = zone.height + offsets.get("height_offset", 0)

        # Set window position
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            x,
            y,
            width,
            height,
            win32con.SWP_SHOWWINDOW,
        )
        return True
    except Exception as e:
        print(f"Error moving window to zone: {e}")
        return False


def save_window_offset(window_id, window_title, offsets_data, zone_used=None):
    """Save window offset for future use"""
    # Check if this window ID already exists
    for app in offsets_data.get("applications", []):
        # For backward compatibility, check both pattern and id fields
        if window_id == app.get("pattern", "") or window_id == app.get("id", ""):
            # Entry exists, we don't need to create a new one
            return

    # Create new entry - simplified structure with only the necessary fields
    new_entry = {
        "id": window_id,
        "x_offset": 0,
        "y_offset": 0,
        "width_offset": 0,
        "height_offset": 0,
    }

    offsets_data["applications"].append(new_entry)

    # Save to file
    try:
        with open(OFFSETS_FILE, "w") as f:
            json.dump(offsets_data, f, indent=2)
        print(f"Added entry for: {window_id}")
    except Exception as e:
        print(f"Error saving window offsets: {e}")


def check_config_files(
    zones_file, offsets_file, last_zones_mod_time, last_offsets_mod_time
):
    """Check if config files have changed and need to be reloaded"""
    zones_changed = False
    offsets_changed = False

    # Check zones file
    current_zones_time = get_file_mod_time(zones_file)
    if current_zones_time > last_zones_mod_time:
        print(f"🔄 Zones file changed, reloading...")
        zones_changed = True
        last_zones_mod_time = current_zones_time

    # Check offsets file
    current_offsets_time = get_file_mod_time(offsets_file)
    if current_offsets_time > last_offsets_mod_time:
        print(f"🔄 Window offsets file changed, reloading...")
        offsets_changed = True
        last_offsets_mod_time = current_offsets_time

    return zones_changed, offsets_changed, last_zones_mod_time, last_offsets_mod_time


def get_window_under_cursor():
    """Get window handle under cursor"""
    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    hwnd = ctypes.windll.user32.WindowFromPoint(point)

    if hwnd:
        # Get top-level window
        return win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
    return None


def register_hotkeys():
    """Register the Win+C hotkey for centering active window"""
    try:
        # Register Win+C for centering active window
        result = ctypes.windll.user32.RegisterHotKey(
            None, HOTKEY_ID_CENTER, MOD_WIN, VK_C
        )
        if not result:
            print("Failed to register Win+C hotkey")
        else:
            print("Registered Win+C hotkey for centering active window")
    except Exception as e:
        print(f"Error registering hotkeys: {e}")


def unregister_hotkeys():
    """Unregister all hotkeys"""
    try:
        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID_CENTER)
    except:
        pass


def get_active_window():
    """Get the currently active window handle"""
    return win32gui.GetForegroundWindow()


def center_active_window():
    """Center the active window using the center zone in the config"""
    active_hwnd = get_active_window()
    if not active_hwnd:
        print("No active window found")
        return

    # Get window identification for possible offsets
    window_id = identify_window(active_hwnd)

    # Skip unknown applications - don't process Win+C for unknown_app
    if window_id == "unknown_app":
        print("Window not recognized. Please first drop it in a zone manually.")
        return

    # Get window title for logging
    window_title = win32gui.GetWindowText(active_hwnd)

    # Find the center zone
    center_zone = None
    for zone in zones:
        if zone.name.lower() == "centered" or zone.name.lower() == "center":
            center_zone = zone
            break

    if not center_zone:
        print("No center zone defined in config")
        return

    # Load offsets
    offsets_data = load_window_offsets()
    offsets = find_window_offsets(window_id, offsets_data)

    print(f"Centering window: {window_title} ({window_id})")
    move_window_to_zone(active_hwnd, center_zone, offsets)


def handle_hotkey_message(msg):
    """Handle a hotkey message"""
    if msg.message == win32con.WM_HOTKEY:
        if msg.wParam == HOTKEY_ID_CENTER:
            # When Win+C is pressed
            print("Win+C pressed - centering active window")
            center_active_window()
            return True
    return False


def main():
    """Main application loop"""
    global zones

    # Load configuration
    zones = load_zones()
    offsets_data = load_window_offsets()

    # Store file modification times for auto-reload
    last_zones_mod_time = get_file_mod_time(ZONES_FILE)
    last_offsets_mod_time = get_file_mod_time(OFFSETS_FILE)

    # File check interval (seconds)
    file_check_interval = 1.0
    last_check_time = time.time()

    # Register hotkeys
    register_hotkeys()

    print("Window Manager started")
    print("Use Shift+drag to move windows to zones")
    print("Press Win+C to center active window")
    print("Configuration files will be auto-reloaded when changed")
    print("Press Ctrl+C to exit")

    # State variables
    dragging = False
    dragging_window = None
    active_zone = None
    overlay_hwnd = None

    try:
        while True:
            # Check for Windows messages (for hotkeys)
            msg = wintypes.MSG()
            if ctypes.windll.user32.PeekMessageA(
                ctypes.byref(msg), None, 0, 0, 1
            ):  # PM_REMOVE = 1
                # If it's a hotkey message, handle it
                if handle_hotkey_message(msg):
                    continue  # Message was handled

                # Otherwise, process normal Windows messages
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))

            # Check for config file changes periodically
            current_time = time.time()
            if current_time - last_check_time > file_check_interval:
                (
                    zones_changed,
                    offsets_changed,
                    last_zones_mod_time,
                    last_offsets_mod_time,
                ) = check_config_files(
                    ZONES_FILE, OFFSETS_FILE, last_zones_mod_time, last_offsets_mod_time
                )

                if zones_changed:
                    zones = load_zones()

                if offsets_changed:
                    offsets_data = load_window_offsets()

                last_check_time = current_time

            # Get current state
            shift_pressed = is_shift_pressed()
            mouse_pressed = is_mouse_button_pressed()
            mouse_x, mouse_y = win32api.GetCursorPos()

            # Detect start of shift+drag operation
            if shift_pressed and mouse_pressed and not dragging:
                # Small delay to ensure it's a real drag, not just a click
                time.sleep(0.1)
                if not is_mouse_button_pressed():
                    continue  # Button released too quickly

                dragging = True
                dragging_window = get_window_under_cursor()

                if dragging_window:
                    title = win32gui.GetWindowText(dragging_window)
                    print(f"Dragging window: {title}")
                else:
                    dragging = False

            # During shift+drag, check which zone we're over
            if dragging and dragging_window:
                # Find active zone
                current_zone = None
                for zone in zones:
                    if zone.contains_point(mouse_x, mouse_y):
                        current_zone = zone
                        break

                # Zone changed, update overlay
                if current_zone != active_zone:
                    destroy_overlay(overlay_hwnd)
                    active_zone = current_zone

                    if active_zone:
                        print(f"Over zone: {active_zone.name}")
                        overlay_hwnd = create_overlay(active_zone)

            # Detect end of drag operation
            if dragging and (not shift_pressed or not mouse_pressed):
                print("Drag operation ended")

                # If we were over a zone when released, resize the window
                if active_zone and dragging_window:
                    # Identify the window
                    window_id = identify_window(dragging_window)
                    window_title = win32gui.GetWindowText(dragging_window)

                    # Find appropriate offsets
                    offsets = find_window_offsets(window_id, offsets_data)

                    # Move window to zone
                    move_window_to_zone(dragging_window, active_zone, offsets)

                    # Save window info if new
                    save_window_offset(
                        window_id, window_title, offsets_data, active_zone
                    )

                # Reset state
                dragging = False
                dragging_window = None
                active_zone = None
                destroy_overlay(overlay_hwnd)
                overlay_hwnd = None

            # Sleep to prevent high CPU usage
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        destroy_overlay(overlay_hwnd)
        unregister_hotkeys()


if __name__ == "__main__":
    main()
