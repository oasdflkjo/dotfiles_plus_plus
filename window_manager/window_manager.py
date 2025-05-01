import time
import win32gui
import win32con
import win32process
import win32api
import sys
import threading
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("WindowManager")

# Dictionary to track processed windows
processed_windows = set()


# Get screen dimensions to properly center windows
def get_screen_dimensions():
    try:
        # For logging purposes, get what Windows reports
        reported_width = win32api.GetSystemMetrics(0)
        reported_height = win32api.GetSystemMetrics(1)

        logger.info(f"Reported screen dimensions: {reported_width}x{reported_height}")

        return reported_width, reported_height
    except Exception as e:
        logger.error(f"Error getting screen dimensions: {e}")
        return 3440, 1440  # Default fallback


# Get screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = get_screen_dimensions()


# Calculate centered positions
def center_position(width, height, app_name=None):
    # Using a fixed reference screen size of 3440x1440
    reference_width = 3440
    reference_height = 1440

    # Calculate position to center on the reference screen - explicit division and casting
    x = int((reference_width - width) / 2)
    y = int((reference_height - height) / 2)

    logger.info(
        f"Calculated position for {app_name}: ({x},{y}) with size {width}x{height}"
    )

    return x, y


DEFAULT_WINDOW_X = (int)(787 / 1.25)
DEFAULT_WINDOW_Y = (int)(25 / 1.25)
DEFAULT_WINDOW_WIDTH = (int)(1850 / 1.25)
DEFAULT_WINDOW_HEIGHT = (int)(1395 / 1.25)


# Target window dimensions for applications (no calculations, fixed values)
WINDOW_SETTINGS = {
    "Chrome": {
        "x": DEFAULT_WINDOW_X,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH,
        "height": DEFAULT_WINDOW_HEIGHT,
    },
    "Discord": {
        "x": DEFAULT_WINDOW_X + 6,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH - 14,
        "height": DEFAULT_WINDOW_HEIGHT - 7,
    },
    "Cursor": {
        "x": DEFAULT_WINDOW_X + 6,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH - 14,
        "height": DEFAULT_WINDOW_HEIGHT - 7,
    },
    "WezTerm": {
        "x": DEFAULT_WINDOW_X,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH,
        "height": DEFAULT_WINDOW_HEIGHT,
    },
    "Notepad": {
        "x": DEFAULT_WINDOW_X,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH,
        "height": DEFAULT_WINDOW_HEIGHT,
    },
    "Steam": {
        "x": DEFAULT_WINDOW_X + 6,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH - 14,
        "height": DEFAULT_WINDOW_HEIGHT - 7,
    },
    "Explorer": {
        "x": DEFAULT_WINDOW_X,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH,
        "height": DEFAULT_WINDOW_HEIGHT,
    },
    "Zen": {
        "x": DEFAULT_WINDOW_X,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH,
        "height": DEFAULT_WINDOW_HEIGHT,
    },
    "VSCode": {
        "x": DEFAULT_WINDOW_X + 6,
        "y": DEFAULT_WINDOW_Y,
        "width": DEFAULT_WINDOW_WIDTH,
        "height": DEFAULT_WINDOW_HEIGHT,
    },
}

# List of exact application class names for matching
SAFE_APP_CLASSES = {
    "Chrome_WidgetWin_1": "Chrome",
    "Notepad": "Notepad",
    "ApplicationFrameWindow": "Notepad",  # For Notepad on newer Windows
    "Notepad++": "Notepad",  # Notepad++ (just in case)
    "NotepadWindowClass": "Notepad",  # Alternative Notepad class
    "Discord": "Discord",
    "SDL_app": "Steam",  # Steam window class
    "CabinetWClass": "Explorer",  # Windows File Explorer
    "org.wezfurlong.wezterm": "WezTerm",  # Actual WezTerm window class
    "Chrome_WidgetWin_0": "VSCode",  # VS Code main window class
}

# Dictionary mapping alternative titles to our application names
TITLE_MAPPINGS = {
    "google chrome": "Chrome",
    "chrome": "Chrome",
    "wezterm": "WezTerm",
    "notepad": "Notepad",
    "zen": "Zen",
    "discord": "Discord",
    "cursor": "Cursor",
    "window_manager": "Cursor",  # Match Cursor with project path in title
    "visual studio code": "VSCode",
    "vs code": "VSCode",
    "vscode": "VSCode",
    "steam": "Steam",  # Match Steam in window title
    "explorer": "Explorer",  # Match Explorer in window title
    "file explorer": "Explorer",  # Alternative Explorer name
    "this pc": "Explorer",  # Common Explorer window title
}

# System window classes to ignore
IGNORED_CLASSES = [
    "Shell_TrayWnd",  # Taskbar
    "DV2ControlHost",  # Windows UI elements
    "Progman",  # Desktop
    "WorkerW",  # Desktop components
    "Button",  # Buttons
    "Static",  # Static controls
    "SysListView32",  # List views
    "ToolbarWindow32",  # Toolbars
    "ComboBox",  # Combo boxes
    "Edit",  # Edit controls
    "Start",  # Start menu
    "SearchApp",  # Search
    "InputIndicator",  # Input indicators
    "Windows.UI.Core.CoreWindow",  # Windows Search and other modern UI elements
]

# Flag to control the service
running = True


# Force resize all target windows
def force_resize_all_windows():
    logger.info("Forcing resize of all target windows")

    # Clear processed windows to allow re-processing
    processed_windows.clear()

    # Get the current foreground window to prioritize it
    foreground_hwnd = win32gui.GetForegroundWindow()
    foreground_title = win32gui.GetWindowText(foreground_hwnd)
    foreground_class = get_window_class(foreground_hwnd)

    # Process the foreground window first if it's a target app
    if foreground_hwnd and foreground_title:
        target_app = get_target_app(foreground_title, foreground_class)
        if target_app and target_app in WINDOW_SETTINGS:
            logger.info(
                f"Force resizing foreground window: '{foreground_title}' ({target_app})"
            )

            # Log current window settings before resize for tuning purposes
            rect = win32gui.GetWindowRect(foreground_hwnd)
            current_x, current_y, current_right, current_bottom = rect
            current_width = current_right - current_x
            current_height = current_bottom - current_y

            logger.info(
                f"Current position: ({current_x},{current_y}) size: {current_width}x{current_height}"
            )
            logger.info(
                f"Target position: ({WINDOW_SETTINGS[target_app]['x']},{WINDOW_SETTINGS[target_app]['y']}) size: {WINDOW_SETTINGS[target_app]['width']}x{WINDOW_SETTINGS[target_app]['height']}"
            )

            # Print in a format that can be directly copied to the WINDOW_SETTINGS dict
            logger.info(f"Copy-paste format for {target_app}:")
            logger.info(f'"{target_app}": {{')
            logger.info(f'    "x": {current_x},')
            logger.info(f'    "y": {current_y},')
            logger.info(f'    "width": {current_width},')
            logger.info(f'    "height": {current_height},')
            logger.info(f"}},")

            position_window(foreground_hwnd, foreground_title, foreground_class)

    def enum_callback(hwnd, _):
        # Skip the foreground window as we've already processed it
        if hwnd == foreground_hwnd:
            return True

        if not win32gui.IsWindowVisible(hwnd):
            return True

        window_title = win32gui.GetWindowText(hwnd)
        window_class = get_window_class(hwnd)

        if not window_title or is_system_window(hwnd, window_class):
            return True

        target_app = get_target_app(window_title, window_class)
        if target_app and target_app in WINDOW_SETTINGS:
            logger.info(f"Force resizing {target_app} window: '{window_title}'")
            position_window(hwnd, window_title, window_class)

        return True

    try:
        win32gui.EnumWindows(enum_callback, None)
        logger.info("Completed force resize of all windows")
    except Exception as e:
        logger.error(f"Error during force resize: {e}")


def get_window_class(hwnd):
    """Get window class name."""
    try:
        class_name = win32gui.GetClassName(hwnd)
        return class_name
    except Exception:
        return ""


def is_system_window(hwnd, window_class):
    """Check if this is a system window that should never be resized."""
    # Skip windows with class names in our ignore list
    if window_class in IGNORED_CLASSES:
        return True

    # Skip windows with specific styles that indicate system components
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    # Skip tool windows
    if ex_style & win32con.WS_EX_TOOLWINDOW:
        return True

    # Skip child windows
    if style & win32con.WS_CHILD:
        return True

    return False


def get_target_app(window_title, window_class):
    """Determine which target application this window belongs to."""
    # First try by exact class match (most reliable)
    if window_class in SAFE_APP_CLASSES:
        app = SAFE_APP_CLASSES[window_class]

        # Special handling for Chrome_WidgetWin_1 - could be Chrome, Cursor, Discord, or VSCode
        if window_class == "Chrome_WidgetWin_1":
            title_lower = window_title.lower()
            if "discord" in title_lower:
                app = "Discord"
            elif "cursor" in title_lower or "window_manager" in title_lower:
                app = "Cursor"
            elif "visual studio code" in title_lower:
                app = "VSCode"

        # Special handling for SDL_app - confirm it's Steam
        if window_class == "SDL_app" and "steam" not in window_title.lower():
            # Only treat as Steam if process is steamwebhelper.exe or contains "steam" in title
            logger.info(
                f"SDL_app window found: '{window_title}', checking if it's Steam"
            )

        # No need for excessive logging here - just return the app for CabinetWClass
        if window_class == "CabinetWClass":
            return "Explorer"

        return app

    # Special handling for Notepad - match both by class and window title
    if window_class == "Notepad" or "Notepad" in window_class:
        logger.info(f"Notepad detected with class: {window_class}")
        return "Notepad"

    # Then try by title
    title_lower = window_title.lower()
    for key, app in TITLE_MAPPINGS.items():
        if key in title_lower:
            return app

    # No match
    return None


def get_window_process_name(hwnd):
    """Get the process name for this window."""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return f"PID: {pid}"
    except:
        return "Unknown"


def position_window(hwnd, window_title, window_class):
    """Position window according to settings."""
    # Skip if already processed
    if hwnd in processed_windows:
        return

    # Get the target application name
    target_app = get_target_app(window_title, window_class)

    # Log more details for debugging - especially for Discord and Notepad
    if "Discord" in window_title:
        logger.info(f"Discord window found - Title: '{window_title}'")
        logger.info(f"  Class: {window_class}")
        logger.info(f"  Resolved to app: {target_app}")

    if "Notepad" in window_title or window_class == "Notepad":
        logger.info(f"Notepad window found - Title: '{window_title}'")
        logger.info(f"  Class: {window_class}")
        logger.info(f"  Resolved to app: {target_app}")

    # Log Steam window detection
    if "Steam" in window_title or window_class == "SDL_app":
        logger.info(f"Steam window found - Title: '{window_title}'")
        logger.info(f"  Class: {window_class}")
        logger.info(f"  Process: {get_window_process_name(hwnd)}")
        logger.info(f"  Resolved to app: {target_app}")

    # Log Explorer window detection - only once when first detected
    if window_class == "CabinetWClass" and hwnd not in processed_windows:
        logger.info(f"New Explorer window found - Title: '{window_title}'")
        # Only log process info once to reduce spam
        logger.info(f"  Process: {get_window_process_name(hwnd)}")

    if not target_app or target_app not in WINDOW_SETTINGS:
        return

    # Skip tiny Windows that are probably background players or minimized windows
    rect = win32gui.GetWindowRect(hwnd)
    current_x, current_y, current_right, current_bottom = rect
    current_width = current_right - current_x
    current_height = current_bottom - current_y

    # Skip special windows that are very small or positioned far off-screen
    if (
        (current_width < 200 and current_height < 50)
        or current_x < -1000
        or current_y < -1000
    ):
        logger.info(
            f"Skipping special window at ({current_x},{current_y}) size {current_width}x{current_height}"
        )
        return

    # Mark as processed
    processed_windows.add(hwnd)

    try:
        # Get the process name for debugging
        process_info = get_window_process_name(hwnd)

        # Log detailed window info for debugging - skip for Explorer to reduce spam
        if target_app != "Explorer":
            logger.info(f"Window info before resize:")
            logger.info(f"  Title: {window_title}")
            logger.info(f"  Class: {window_class}")
            logger.info(f"  Process: {process_info}")
            logger.info(f"  Position: X={current_x}, Y={current_y}")
            logger.info(f"  Size: Width={current_width}, Height={current_height}")

        # Get the settings for this app
        settings = WINDOW_SETTINGS[target_app]
        x, y = settings["x"], settings["y"]
        width, height = settings["width"], settings["height"]

        # Always reposition for pixel-perfect accuracy
        # Check if window is in a special state that affects resizing
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

        # If window is maximized, restore it first
        if style & win32con.WS_MAXIMIZE:
            logger.info("Window is maximized, restoring first")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.1)  # Give it time to restore

        # Special handling for Cursor to ensure correct sizing
        if target_app == "Cursor":
            # Ensure window has the right style bits for resizing
            current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            if not (current_style & win32con.WS_THICKFRAME):
                logger.info("Adding WS_THICKFRAME style to Cursor window")
                win32gui.SetWindowLong(
                    hwnd, win32con.GWL_STYLE, current_style | win32con.WS_THICKFRAME
                )

        # Set the position
        logger.info(f"Moving window to ({x},{y}) with size {width}x{height}")
        win32gui.MoveWindow(hwnd, x, y, width, height, True)

        # Get the new window rect to verify it worked
        new_rect = win32gui.GetWindowRect(hwnd)
        new_x, new_y, new_right, new_bottom = new_rect
        new_width = new_right - new_x
        new_height = new_bottom - new_y

        logger.info(f"Positioned {target_app} window '{window_title}'")
        logger.info(f"  Requested: Position ({x},{y}) Size {width}x{height}")
        logger.info(
            f"  Actual: Position ({new_x},{new_y}) Size {new_width}x{new_height}"
        )

        # If there's still a significant difference, log a warning
        if abs(new_width - width) > 10 or abs(new_height - height) > 10:
            logger.warning(f"Window size mismatch after positioning! App: {target_app}")
            logger.warning(
                f"  Difference: Width {new_width-width}, Height {new_height-height}"
            )
    except Exception as e:
        logger.error(f"Error positioning window: {e}")


def monitor_windows():
    """Monitor for new windows of our target applications."""
    logger.info("Starting window monitor for target applications")

    # Track known windows
    known_windows = {}

    # Track last log time for Explorer windows to reduce spam
    last_explorer_log_time = 0

    while running:
        try:
            # Rate limit Explorer logging - no more than once every 5 seconds
            current_time = time.time()
            should_log_explorer = (current_time - last_explorer_log_time) > 5

            def enum_callback(hwnd, new_windows):
                # Skip invisible windows
                if not win32gui.IsWindowVisible(hwnd):
                    return True

                # Get window info
                window_title = win32gui.GetWindowText(hwnd)
                window_class = get_window_class(hwnd)

                # Skip empty titles and system windows
                if not window_title or is_system_window(hwnd, window_class):
                    return True

                # Check if this is one of our target applications
                target_app = get_target_app(window_title, window_class)

                # Add to new_windows if it's a target app
                if target_app and target_app in WINDOW_SETTINGS:
                    # For Explorer windows, only include if we should log them
                    if (
                        target_app != "Explorer"
                        or should_log_explorer
                        or hwnd not in known_windows
                    ):
                        new_windows.append(
                            (hwnd, window_title, window_class, target_app)
                        )

                return True

            new_windows = []
            win32gui.EnumWindows(enum_callback, new_windows)

            # Process any new windows
            explorer_processed = False

            for hwnd, title, class_name, app_name in new_windows:
                # Skip Explorer windows after processing one to avoid spam
                if app_name == "Explorer":
                    if explorer_processed:
                        continue
                    explorer_processed = True
                    last_explorer_log_time = current_time

                if hwnd not in known_windows:
                    logger.info(
                        f"New {app_name} window detected: '{title}' (Class: {class_name})"
                    )
                    position_window(hwnd, title, class_name)

                # Update known windows
                known_windows[hwnd] = (title, class_name)

            # Clean up closed windows
            closed_windows = [
                hwnd for hwnd in known_windows if not win32gui.IsWindow(hwnd)
            ]
            for hwnd in closed_windows:
                known_windows.pop(hwnd)
                if hwnd in processed_windows:
                    processed_windows.remove(hwnd)

            time.sleep(0.2)  # Poll interval
        except Exception as e:
            logger.error(f"Error in window monitor: {e}")
            time.sleep(1)


def main():
    """Main function to run the window manager."""
    global running
    try:
        logger.info("Window Manager starting...")

        # Log the fixed window settings
        logger.info("Using fixed window settings:")
        for app, settings in WINDOW_SETTINGS.items():
            logger.info(
                f"  {app}: Position ({settings['x']},{settings['y']}) Size {settings['width']}x{settings['height']}"
            )

        # Run an initial resize of all windows
        force_resize_all_windows()

        # Start the monitoring thread
        monitor_thread = threading.Thread(target=monitor_windows, daemon=True)
        monitor_thread.start()

        logger.info("Window Manager is running. Press Ctrl+C to exit.")

        # Keep the main thread alive but not consuming too much CPU
        while running:
            time.sleep(0.1)

    except KeyboardInterrupt:
        running = False
        logger.info("Window Manager stopping...")
        time.sleep(0.5)
        logger.info("Window Manager stopped.")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()
