import win32gui
import win32con
import win32process
import psutil
import threading
import logging
import json
from pathlib import Path
import re

# Import window zones module
from window_zones import WindowZones

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("WindowPositioner")

# List of known UWP app patterns
UWP_CLASSES = [
    "Windows.UI.Core.CoreWindow",  # The actual UWP app window
    "ApplicationFrameWindow",  # The UWP container window
]

# UWP Apps we want to prioritize by their specific core window
UWP_APP_PREFERENCES = {
    "Calculator": "CalculatorApp|ApplicationFrameWindow",  # Only use ApplicationFrameWindow for Calculator
    "Photos": "PhotosApp|Windows.UI.Core.CoreWindow",
    "Settings": "SettingsApp|Windows.UI.Core.CoreWindow",
    # Add more specific UWP apps here
}


class WindowPositioner:
    """
    A lightweight window positioning system that applies configuration-based
    positioning to windows.

    This module ONLY handles the positioning logic and provides an API for other
    modules to trigger positioning operations. It does not handle window event
    detection or monitoring - that should be handled by separate modules.
    """

    def __init__(
        self,
        zones_config_path="window_zones.json",
        legacy_config_path="defined_window_positions.json",
    ):
        # Set up configuration
        self.zones_config_path = Path(zones_config_path)
        self.legacy_config_path = Path(legacy_config_path)
        self.resize_lock = threading.Lock()
        self.resize_in_progress = {}  # Track windows being resized

        # Initialize WindowZones
        self.window_zones = WindowZones(zones_config_path)

        # Legacy window configs (for backward compatibility)
        self.legacy_window_configs = {}
        if self.legacy_config_path.exists():
            self.load_legacy_config()

        # Store UWP app tracking
        self.uwp_window_map = (
            {}
        )  # Map of UWP container windows to their specific windows

        logger.info("Window positioner initialized")

    def load_legacy_config(self):
        """Load legacy window positions from JSON file"""
        try:
            if self.legacy_config_path.exists():
                with open(self.legacy_config_path, "r", encoding="utf-8") as f:
                    self.legacy_window_configs = json.load(f)
                logger.info(
                    f"Loaded legacy configurations for {len(self.legacy_window_configs)} windows"
                )
        except Exception as e:
            logger.error(f"Error loading legacy config: {e}")
            self.legacy_window_configs = {}

    def reload_config(self):
        """Reload the configuration file"""
        # Reinitialize WindowZones to reload config
        self.window_zones = WindowZones(self.zones_config_path)

        # Reload legacy config if it exists
        if self.legacy_config_path.exists():
            self.load_legacy_config()

        # Clear UWP window map
        self.uwp_window_map = {}

        logger.info("Configuration reloaded")
        return True

    def get_window_info(self, hwnd):
        """
        Get window information for a given window handle

        Args:
            hwnd: Window handle

        Returns:
            Dictionary with window info (process_name, window_class, title, rect) or None if failed
        """
        try:
            # Get window class
            window_class = win32gui.GetClassName(hwnd)

            # Get window title
            window_title = win32gui.GetWindowText(hwnd)

            # Get process information
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # Special handling for UWP apps
            process_name = ""
            is_uwp = False

            # Check if this is a UWP app
            if any(uwp_class in window_class for uwp_class in UWP_CLASSES):
                is_uwp = True

                # Skip ApplicationFrameWindow for apps we know better windows for
                if window_class == "ApplicationFrameWindow":
                    # Check if this is a known app from the title
                    for app_name, preferred_key in UWP_APP_PREFERENCES.items():
                        if app_name in window_title:
                            # Skip this container window and prefer the CoreWindow
                            return {
                                "process_name": app_name.replace(" ", "") + "App",
                                "window_class": window_class,
                                "title": window_title,
                                "rect": win32gui.GetWindowRect(hwnd),
                                "hwnd": hwnd,
                                "is_uwp": is_uwp,
                                "skip_positioning": True,  # Flag to skip this window
                            }

                # For UWP apps, try to extract the app name from the title
                if "Calculator" in window_title:
                    process_name = "CalculatorApp"
                elif "Photos" in window_title:
                    process_name = "PhotosApp"
                elif "Settings" in window_title:
                    process_name = "SettingsApp"
                else:
                    # Try to get the actual process name
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name().replace(".exe", "")

                        # If it's ApplicationFrameHost, try to get the real app name from window title
                        if process_name == "ApplicationFrameHost":
                            # Extract app name from window title (e.g., "Calculator")
                            app_name = re.match(r"^([^\-\–]+)", window_title)
                            if app_name:
                                process_name = (
                                    app_name.group(1).strip().replace(" ", "") + "App"
                                )
                            else:
                                process_name = "UnknownUWPApp"
                    except:
                        # Fallback to a generic name based on title
                        process_name = window_title.split()[0].replace(" ", "") + "App"
            else:
                # Standard Win32 app
                try:
                    process = psutil.Process(pid)
                    process_name = process.name().replace(".exe", "")
                except Exception as e:
                    logger.error(f"Failed to get process name for pid {pid}: {e}")
                    return None

            # Get window rect
            rect = win32gui.GetWindowRect(hwnd)

            return {
                "process_name": process_name,
                "window_class": window_class,
                "title": window_title,
                "rect": rect,
                "hwnd": hwnd,
                "is_uwp": is_uwp,
            }
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return None

    def should_manage_window(self, process_name, window_class):
        """
        Determine if a window should be managed based on process name and class

        Args:
            process_name: Process name without .exe
            window_class: Window class name

        Returns:
            Boolean indicating whether this window should be managed
        """
        if not process_name or not window_class:
            return False

        # Special handling for Calculator - only manage ApplicationFrameWindow
        if process_name == "CalculatorApp":
            if window_class == "ApplicationFrameWindow":
                logger.info(
                    f"Explicitly managing Calculator window ({process_name}|{window_class})"
                )
                return True
            else:
                # Skip any other Calculator windows
                return False

        # Skip ApplicationFrameWindow when a specific UWP app is configured
        if window_class == "ApplicationFrameWindow":
            for _, preferred_key in UWP_APP_PREFERENCES.items():
                if (
                    preferred_key in self.window_zones.window_layouts
                    or preferred_key in self.window_zones.adjustments
                ):
                    # Skip container if we have config for the specific app
                    if process_name + "|" + window_class in preferred_key:
                        return False

        # Create window key in format used by window_zones
        window_key = f"{process_name}|{window_class}"

        # Check if this window has adjustments for any zone
        if window_key in self.window_zones.adjustments:
            return True

        # Check if this window has a layout selected
        if window_key in self.window_zones.window_layouts:
            return True

        # Legacy support
        # Check for exact process+class match
        if window_key in self.legacy_window_configs:
            return True

        # Check for new format entries in legacy config
        for key, config in self.legacy_window_configs.items():
            if isinstance(config, dict) and "process" in config and "class" in config:
                if (
                    config["process"] == process_name
                    and config["class"] == window_class
                ):
                    return True

        # Legacy support for old format configs (just process name)
        if process_name in self.legacy_window_configs:
            return True

        return False

    def position_uwp_window(self, hwnd, x, y, width, height):
        """
        Use special flags and techniques for UWP windows

        Returns:
            Boolean indicating success
        """
        try:
            # Set specific flags for UWP positioning
            flags = win32con.SWP_SHOWWINDOW | win32con.SWP_ASYNCWINDOWPOS

            # Position the window
            result = win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOP,  # Put window at the top of the Z order
                x,
                y,
                width,
                height,
                flags,
            )

            # Force window to update and redraw
            win32gui.UpdateWindow(hwnd)
            win32gui.RedrawWindow(
                hwnd,
                None,
                None,
                win32con.RDW_INVALIDATE
                | win32con.RDW_ERASE
                | win32con.RDW_FRAME
                | win32con.RDW_ALLCHILDREN,
            )

            # Try to activate the window to ensure it takes the new position
            win32gui.SetForegroundWindow(hwnd)

            return result is not None
        except Exception as e:
            logger.error(f"Error in position_uwp_window: {e}")
            return False

    def position_window(self, hwnd, process_name, window_class, force=False):
        """
        Position a window according to its configuration

        Args:
            hwnd: Window handle
            process_name: Process name without .exe
            window_class: Window class name
            force: Force positioning even if already in correct position

        Returns:
            Boolean indicating success
        """
        if not hwnd or not process_name or not window_class:
            return False

        # Skip if this is a resize we're already handling
        if hwnd in self.resize_in_progress and self.resize_in_progress[hwnd]:
            return False

        # Special handling for Calculator - always force positioning
        if process_name == "CalculatorApp" and window_class == "ApplicationFrameWindow":
            force = True
            logger.info(f"Forcing position update for Calculator window")

        # Create window identifier key
        window_key = f"{process_name}|{window_class}"

        # Special handling for UWP container windows - skip if there's a better target
        if window_class == "ApplicationFrameWindow" and process_name != "CalculatorApp":
            for app_name, preferred_key in UWP_APP_PREFERENCES.items():
                if (
                    preferred_key in self.window_zones.window_layouts
                    or preferred_key in self.window_zones.adjustments
                ):
                    # Skip this container window and use the specific app window instead
                    logger.info(
                        f"Skipping UWP container {window_key} in favor of {preferred_key}"
                    )
                    return False

        # Check if this is a UWP app
        is_uwp = any(uwp_class in window_class for uwp_class in UWP_CLASSES)

        try:
            # Acquire resize lock to prevent recursive resizing
            with self.resize_lock:
                self.resize_in_progress[hwnd] = True

                # Get current window position for logging
                try:
                    current_rect = win32gui.GetWindowRect(hwnd)
                    current_x, current_y, current_right, current_bottom = current_rect
                    current_width = current_right - current_x
                    current_height = current_bottom - current_y
                except Exception:
                    logger.warning(
                        f"Failed to get window rect for {window_key}, window may be closing"
                    )
                    self.resize_in_progress[hwnd] = False
                    return False

                # Try to position based on window zone configuration
                # Get the specific layout selected for this window (or default if none)
                zone_key = self.window_zones.get_window_layout(window_key)
                zone = None

                # If this window has adjustments, use them
                if (
                    window_key in self.window_zones.adjustments
                    and zone_key in self.window_zones.adjustments[window_key]
                ):
                    zone = self.window_zones.get_adjusted_zone(zone_key, window_key)
                    logger.info(
                        f"Using zone '{zone_key}' with adjustments for {window_key}"
                    )
                else:
                    # Just use the default zone with no adjustments
                    zone = self.window_zones.get_zone_details(zone_key)
                    logger.info(f"Using default zone '{zone_key}' for {window_key}")

                if zone:
                    # Check if this is a custom zone (direct values)
                    is_custom = zone.get("is_custom", False)

                    # Get coordinates from zone
                    x = zone.get("x", current_x)
                    y = zone.get("y", current_y)
                    width = zone.get("width", current_width)
                    height = zone.get("height", current_height)

                    # Log the position change
                    logger.info(
                        f"Positioning {process_name} window (class: {window_class})"
                    )
                    logger.info(
                        f"  From: ({current_x},{current_y}) {current_width}x{current_height}"
                    )
                    logger.info(f"  To:   ({x},{y}) {width}x{height}")

                    if is_uwp:
                        logger.info(f"  Special handling for UWP window")

                    # Skip if position is already correct (with small tolerance) and not forced
                    if (
                        not force
                        and abs(current_x - x) <= 5
                        and abs(current_y - y) <= 5
                        and abs(current_width - width) <= 5
                        and abs(current_height - height) <= 5
                    ):
                        logger.info(
                            "Window already in correct position (within tolerance), skipping"
                        )
                        self.resize_in_progress[hwnd] = False
                        return True

                    # Apply the position
                    try:
                        # Set special flags for UWP apps
                        if is_uwp:
                            # Use our special UWP positioning function
                            self.position_uwp_window(hwnd, x, y, width, height)
                        else:
                            # Standard Win32 window positioning
                            flags = win32con.SWP_SHOWWINDOW
                            result = win32gui.SetWindowPos(
                                hwnd,
                                win32con.HWND_TOP,  # Put window at the top of the Z order
                                x,
                                y,
                                width,
                                height,
                                flags,
                            )
                            logger.debug(f"SetWindowPos result: {result}")
                    except Exception as e:
                        logger.error(f"Failed to position window: {e}")
                        self.resize_in_progress[hwnd] = False
                        return False

                    self.resize_in_progress[hwnd] = False
                    return True

                # Fallback to legacy configuration if no zone was found
                config = None

                # Check new composite key format in legacy config
                if window_key in self.legacy_window_configs:
                    config = self.legacy_window_configs[window_key]
                else:
                    # Check new dictionary format in legacy config
                    for key, entry in self.legacy_window_configs.items():
                        if (
                            isinstance(entry, dict)
                            and "process" in entry
                            and "class" in entry
                        ):
                            if (
                                entry["process"] == process_name
                                and entry["class"] == window_class
                            ):
                                config = entry
                                break

                    # If still not found, try legacy format (just process name)
                    if config is None and process_name in self.legacy_window_configs:
                        config = self.legacy_window_configs[process_name]

                if config:
                    # Get new position from legacy config
                    x = config.get("x", current_x)
                    y = config.get("y", current_y)
                    width = config.get("width", current_width)
                    height = config.get("height", current_height)

                    # Log the position change
                    logger.info(
                        f"Positioning {process_name} window using legacy config (class: {window_class})"
                    )
                    logger.info(
                        f"  From: ({current_x},{current_y}) {current_width}x{current_height}"
                    )
                    logger.info(f"  To:   ({x},{y}) {width}x{height}")

                    # Apply the position
                    try:
                        if is_uwp:
                            # Use our special UWP positioning function
                            self.position_uwp_window(hwnd, x, y, width, height)
                        else:
                            # Standard Win32 window positioning
                            flags = win32con.SWP_SHOWWINDOW
                            win32gui.SetWindowPos(
                                hwnd,
                                win32con.HWND_TOP,
                                x,
                                y,
                                width,
                                height,
                                flags,
                            )
                    except Exception as e:
                        logger.error(f"Failed to position window: {e}")
                        self.resize_in_progress[hwnd] = False
                        return False

                    self.resize_in_progress[hwnd] = False
                    return True

                self.resize_in_progress[hwnd] = False
                return False
        except Exception as e:
            logger.error(f"Error positioning window: {e}")
            if hwnd in self.resize_in_progress:
                self.resize_in_progress[hwnd] = False
            return False

    def position_window_by_handle(self, hwnd):
        """
        Position a window by its handle - easy API for external callers

        Args:
            hwnd: Window handle

        Returns:
            Boolean indicating success
        """
        try:
            # Skip minimized windows
            if win32gui.IsIconic(hwnd):
                return False

            # Skip invisible windows
            if not win32gui.IsWindowVisible(hwnd):
                return False

            # Skip empty titled windows
            if not win32gui.GetWindowText(hwnd):
                return False

            # Get window info
            info = self.get_window_info(hwnd)
            if not info:
                return False

            # Skip if explicitly flagged to skip (replacement UWP window)
            if info.get("skip_positioning", False):
                return False

            # Check if we should manage this window
            process_name = info["process_name"]
            window_class = info["window_class"]

            if self.should_manage_window(process_name, window_class):
                return self.position_window(hwnd, process_name, window_class)

            return False
        except Exception as e:
            logger.error(f"Error in position_window_by_handle: {e}")
            return False

    def position_all_manageable_windows(self):
        """
        Position all windows that are configured for management

        Returns:
            Number of windows positioned
        """
        positioned_count = 0

        def enum_callback(hwnd, _):
            nonlocal positioned_count

            # Skip invisible or minimized windows
            if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                return True

            # Skip windows with no title
            if not win32gui.GetWindowText(hwnd):
                return True

            try:
                info = self.get_window_info(hwnd)
                if not info:
                    return True

                # Always try to position Calculator windows with ApplicationFrameWindow class
                if (
                    info["process_name"] == "CalculatorApp"
                    and info["window_class"] == "ApplicationFrameWindow"
                ):
                    logger.info(f"Found Calculator window - attempting to position it")
                    if self.position_window(
                        hwnd, info["process_name"], info["window_class"], force=True
                    ):
                        positioned_count += 1
                    return True

                # Skip non-relevant CoreWindow for Calculator
                if (
                    info["process_name"] == "CalculatorApp"
                    and info["window_class"] == "Windows.UI.Core.CoreWindow"
                ):
                    logger.info(
                        f"Skipping Calculator CoreWindow - not needed for positioning"
                    )
                    return True

                # For other windows, use normal logic
                if not info.get(
                    "skip_positioning", False
                ) and self.should_manage_window(
                    info["process_name"], info["window_class"]
                ):
                    if self.position_window_by_handle(hwnd):
                        positioned_count += 1
            except Exception as e:
                logger.error(f"Error in enum_callback: {e}")

            return True  # Continue enumeration

        try:
            win32gui.EnumWindows(enum_callback, None)
        except Exception as e:
            logger.error(f"Error in EnumWindows: {e}")

        logger.info(f"Positioned {positioned_count} windows")
        return positioned_count

    def get_managed_windows(self):
        """
        Get list of all windows that match management criteria

        Returns:
            List of window info dictionaries for manageable windows
        """
        managed_windows = []
        all_windows = []

        def enum_callback(hwnd, _):
            # Skip invisible or minimized windows
            if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                return True

            # Skip windows with no title
            if not win32gui.GetWindowText(hwnd):
                return True

            try:
                info = self.get_window_info(hwnd)
                if not info:
                    return True

                # Save all windows for debugging
                all_windows.append(info)

                # Skip if explicitly flagged to skip
                if info.get("skip_positioning", False):
                    return True

                # Check if this should be managed
                if self.should_manage_window(
                    info["process_name"], info["window_class"]
                ):
                    managed_windows.append(info)
            except Exception as e:
                logger.error(f"Error getting managed window info: {e}")

            return True  # Continue enumeration

        try:
            win32gui.EnumWindows(enum_callback, None)
        except Exception as e:
            logger.error(f"Error in EnumWindows: {e}")

        # Debug output for Calculator windows
        calculator_windows = [
            w
            for w in all_windows
            if "Calculator" in w.get("title", "")
            or "Calculator" in w.get("process_name", "")
        ]
        if calculator_windows:
            logger.info(f"Found {len(calculator_windows)} Calculator windows:")
            for calc in calculator_windows:
                is_managed = any(m["hwnd"] == calc["hwnd"] for m in managed_windows)
                managed_str = "MANAGED" if is_managed else "NOT MANAGED"
                logger.info(
                    f"  - {calc['process_name']} | {calc['window_class']} - '{calc['title']}' ({managed_str})"
                )

                # Check why it's not managed
                if not is_managed:
                    window_key = f"{calc['process_name']}|{calc['window_class']}"
                    logger.info(f"    Key: {window_key}")
                    logger.info(
                        f"    In adjustments? {window_key in self.window_zones.adjustments}"
                    )
                    logger.info(
                        f"    In window_layouts? {window_key in self.window_zones.window_layouts}"
                    )

                    # Try to manage it if it has a layout
                    if (
                        calc["process_name"] == "CalculatorApp"
                        and calc["window_class"] == "ApplicationFrameWindow"
                    ):
                        logger.info(f"    Forcing management of Calculator window")
                        managed_windows.append(calc)

        return managed_windows


# Simple test function
def main():
    """Test the WindowPositioner functionality by doing a one-time positioning of all windows"""
    print("Window Manager - One-time positioning operation")
    print("-" * 50)
    positioner = WindowPositioner()

    print("\nPositioning all manageable windows...")
    count = positioner.position_all_manageable_windows()
    print(f"Positioned {count} windows")

    print("\nManageable windows found:")
    managed = positioner.get_managed_windows()
    if managed:
        for window in managed:
            print(
                f"  - {window['process_name']} | {window['window_class']} - '{window['title']}'"
            )
    else:
        print("  No manageable windows found")

    print("\nDone. For continuous window management, use hotkey_manager.py")


if __name__ == "__main__":
    main()
