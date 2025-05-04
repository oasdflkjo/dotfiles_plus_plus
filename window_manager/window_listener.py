import win32gui
import win32api
import win32con
import win32process
import ctypes
from ctypes import wintypes, byref, WINFUNCTYPE, windll, Structure, POINTER, c_int
import time
import json
import os
import threading
import sys

# Import from our modules
from window_identification import identify_window
from simple_window_manager import (
    Zone,
    load_zones,
    find_window_offsets,
    move_window_to_zone as original_move_window_to_zone,
)

# Configuration file
ZONES_FILE = "zones.json"
OFFSETS_FILE = "window_offsets.json"

# Global variables
running = False
listener_thread = None
zones = []
offsets_data = {}
already_processed_windows = set()
hook_ids = []
cbt_hook = None

# Debug mode
DEBUG = True

# WinEvent constants
EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_SYSTEM_MOVESIZEEND = 0x000B
EVENT_OBJECT_CREATE = 0x8000
EVENT_OBJECT_DESTROY = 0x8001
EVENT_OBJECT_SHOW = 0x8002
EVENT_OBJECT_NAMECHANGE = 0x800C

# CBT Hook constants
HCBT_MOVESIZE = 0
HCBT_MINMAX = 1
HCBT_CREATEWND = 3
HCBT_ACTIVATE = 5
WH_CBT = 5

# WinEvent callback function prototype
WINEVENTPROC = WINFUNCTYPE(
    None,
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.HWND,
    wintypes.LONG,
    wintypes.LONG,
    wintypes.DWORD,
    wintypes.DWORD,
)

# CBT Hook callback function prototype
CBTPROC = WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


# Add these structures for direct window manipulation
class WINDOWPLACEMENT(Structure):
    _fields_ = [
        ("length", wintypes.UINT),
        ("flags", wintypes.UINT),
        ("showCmd", wintypes.UINT),
        ("ptMinPosition", wintypes.POINT),
        ("ptMaxPosition", wintypes.POINT),
        ("rcNormalPosition", wintypes.RECT),
    ]


class MONITORINFO(Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


# Direct API constants for advanced manipulation
SWP_ASYNCWINDOWPOS = 0x4000
SWP_DEFERERASE = 0x2000
SWP_HIDEWINDOW = 0x0080
SWP_NOACTIVATE = 0x0010
SWP_NOCOPYBITS = 0x0100
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOREDRAW = 0x0008
MONITOR_DEFAULTTOPRIMARY = 0x00000001


def get_event_name(event_id):
    """Convert event ID to readable name"""
    events = {
        EVENT_SYSTEM_FOREGROUND: "FOREGROUND",
        EVENT_SYSTEM_MOVESIZEEND: "MOVESIZEEND",
        EVENT_OBJECT_CREATE: "CREATE",
        EVENT_OBJECT_DESTROY: "DESTROY",
        EVENT_OBJECT_SHOW: "SHOW",
        EVENT_OBJECT_NAMECHANGE: "NAMECHANGE",
    }
    return events.get(event_id, f"UNKNOWN({event_id})")


def debug_print(*args, **kwargs):
    """Print debug messages if debug mode is on"""
    if DEBUG:
        print("[DEBUG]", *args, **kwargs)
        sys.stdout.flush()  # Ensure output is visible immediately


def print_window_info(hwnd, event_type):
    """Print detailed information about any window"""
    try:
        window_title = win32gui.GetWindowText(hwnd) if hwnd else ""
        class_name = win32gui.GetClassName(hwnd) if hwnd else ""
        process_name = get_process_name(hwnd)
        window_id = identify_window(hwnd)
        is_visible = win32gui.IsWindowVisible(hwnd) if hwnd else False
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE) if hwnd else 0

        print(f"===== Window {event_type} Event =====")
        print(f"HWND: {hwnd}")
        print(f"Title: '{window_title}'")
        print(f"Class: '{class_name}'")
        print(f"Process: '{process_name}'")
        print(f"Window ID: '{window_id}'")
        print(f"Visible: {is_visible}")
        print(f"Style: 0x{style:08x}")
        print("=============================")
        sys.stdout.flush()
    except Exception as e:
        print(f"Error getting window info: {e}")


def win_event_callback(
    hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime
):
    """Callback for window events"""
    # Only process top-level windows (idObject == 0 means OBJID_WINDOW)
    if idObject != 0 or not hwnd or not win32gui.IsWindow(hwnd):
        return

    # Get readable event name
    event_name = get_event_name(event)

    # Handle different event types
    if event == EVENT_OBJECT_CREATE:
        # Window created
        print_window_info(hwnd, event_name)
        handle_new_window(hwnd, event_name.lower())
    elif event == EVENT_OBJECT_SHOW:
        # Window shown or possibly title changed
        print_window_info(hwnd, event_name)

        # Special handling for WezTerm windows that might have changed title
        process_name = get_process_name(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        window_title = win32gui.GetWindowText(hwnd)

        # If it's a WezTerm process and the window is visible with a terminal title
        if "wezterm-gui.exe" in process_name and win32gui.IsWindowVisible(hwnd):
            if (
                "pwsh.exe" in window_title
                or "cmd.exe" in window_title
                or "bash" in window_title
            ):
                # This is likely a WezTerm window that has been initialized with a shell
                handle_new_window(hwnd, event_name.lower())
            elif window_title == "wezterm":
                # This is the initial WezTerm window, we should ignore it and wait for shell title
                debug_print("WezTerm initializing, waiting for shell title...")
    elif event == EVENT_SYSTEM_FOREGROUND:
        # Window got focus
        # Optionally handle focus events if needed
        pass


def cbt_hook_callback(nCode, wParam, lParam):
    """Callback for CBT hooks - intercepts window creation before it's shown"""
    try:
        if nCode == HCBT_CREATEWND:
            # This is called when a window is being created, before it's visible
            hwnd = wParam

            # Get the window information right away
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            process_name = get_process_name(hwnd)
            window_id = identify_window(hwnd)

            # Print debug info
            print_window_info(hwnd, "CBT_CREATEWND")

            # Only process windows we're sure are the main WezTerm windows
            # Many helper windows have wezterm-gui.exe as the process but shouldn't be positioned
            if process_name == "wezterm-gui.exe":
                if class_name == "org.wezfurlong.wezterm":
                    # This is potentially a valid main WezTerm window
                    debug_print("Main WezTerm window class detected")

                    # Check window size - if it's too small, it's not the main window
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]

                        if width < 100 or height < 100:
                            debug_print(
                                f"Window too small ({width}x{height}), skipping"
                            )
                            return windll.user32.CallNextHookEx(
                                0, nCode, wParam, lParam
                            )
                    except:
                        pass

                    # If it has a generic "wezterm" title, it's not initialized yet
                    if window_title == "wezterm":
                        debug_print(
                            "Main WezTerm window detected at creation, but title not initialized yet"
                        )

                        # We'll let the SHOW event handler take care of it when title changes to shell name
                        return windll.user32.CallNextHookEx(0, nCode, wParam, lParam)

                    # Get zone and offsets if it's an initialized window
                    selected_zone = find_zone_for_window(window_id)
                    if selected_zone:
                        debug_print("Setting up positioning for WezTerm window")
                        offsets = find_window_offsets(window_id, offsets_data)

                        # Prepare a positioning thread - don't try to position immediately
                        timer_thread = threading.Thread(
                            target=position_after_creation,
                            args=(hwnd, selected_zone, offsets, window_id),
                        )
                        timer_thread.daemon = True
                        timer_thread.start()
                else:
                    # Not the main window class, skip positioning
                    debug_print(f"Skipping WezTerm helper window: {class_name}")

        # Always call the next hook in the chain
        return windll.user32.CallNextHookEx(0, nCode, wParam, lParam)
    except Exception as e:
        debug_print(f"Error in CBT hook: {e}")
        return windll.user32.CallNextHookEx(0, nCode, wParam, lParam)


def position_after_creation(hwnd, zone, offsets, window_id):
    """Position window after creation - run in a separate thread"""
    try:
        if not hwnd or not win32gui.IsWindow(hwnd):
            return

        # Short delay to let the window initialize
        time.sleep(0.2)

        # Re-check if this is actually a terminal window
        window_title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        process_name = get_process_name(hwnd)
        is_visible = win32gui.IsWindowVisible(hwnd)

        # Check if it's a real terminal window
        if not is_visible:
            debug_print(f"Window is not visible, skipping positioning: {window_title}")
            return

        # Skip if it still has the generic 'wezterm' title or is a helper window
        if window_title == "wezterm" or "probing" in window_title.lower():
            debug_print(f"Skipping uninitialized WezTerm window: {window_title}")
            return

        # Check window size
        try:
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            if width < 100 or height < 100:
                debug_print(
                    f"Window too small ({width}x{height}), skipping positioning: {window_title}"
                )
                return
        except:
            pass

        # Validate this is a properly initialized terminal
        if (
            "pwsh.exe" in window_title
            or "cmd.exe" in window_title
            or "bash" in window_title
        ):
            print(f"Positioning window at creation time: {window_title}")
        else:
            debug_print(f"Not a terminal window or not initialized yet: {window_title}")
            return

        # Try the most aggressive method first
        if force_position_window(hwnd, zone, offsets):
            debug_print("Used forced positioning successfully")
            return

        # Fall back to previous strategies

        # STRATEGY 1: Hide window during positioning
        # Hide the window while we position it (SW_HIDE = 0)
        win32gui.ShowWindow(hwnd, 0)

        # STRATEGY 2: Move off-screen first
        # Move the window far off-screen
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            -10000,
            -10000,  # Way off screen
            100,
            100,  # Small size
            win32con.SWP_NOACTIVATE,
        )

        # STRATEGY 3: Modify window styles to prevent auto-show
        # Remove visible styles temporarily
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        new_style = style & ~win32con.WS_VISIBLE
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)

        # Apply the correct position and size
        original_move_window_to_zone(hwnd, zone, offsets)

        # Give it a moment to apply position
        time.sleep(0.05)

        # Now show the window in the correct position
        # Restore visible style
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style | win32con.WS_VISIBLE)

        # Show and activate window
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(hwnd)

    except Exception as e:
        debug_print(f"Error positioning window: {e}")


def is_wezterm_window(hwnd, window_id, class_name, process_name):
    """More robust check for WezTerm windows"""
    # Get window title and check if it's visible
    window_title = win32gui.GetWindowText(hwnd) if hwnd else ""
    is_visible = win32gui.IsWindowVisible(hwnd) if hwnd else False

    # Skip probing windows
    if "probing window" in window_title.lower():
        debug_print(f"Ignoring WezTerm probing window: '{window_title}'")
        return False

    # Skip invisible windows
    if not is_visible:
        debug_print(f"Ignoring invisible window: '{window_title}'")
        return False

    # Check window size - probing windows are often tiny
    try:
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        # If it's a very small window, likely not a real terminal
        if width < 100 or height < 100:
            debug_print(f"Ignoring small window ({width}x{height}): '{window_title}'")
            return False
    except:
        pass

    # Early detection - if it's a WezTerm process, consider it a candidate
    if process_name and ("wezterm" in process_name.lower()):
        debug_print(f"WezTerm process detected: {process_name}")

        # Only consider the window a valid WezTerm window if:
        # 1. It's visible
        # 2. It has a title that indicates a terminal (like "pwsh.exe")
        # 3. It's not a probing window
        if (
            is_visible
            and window_title
            and "wezterm" != window_title.lower()
            and not "probing" in window_title.lower()
        ):
            return True

        # If the title is just "wezterm", it's likely not initialized yet
        if window_title.lower() == "wezterm":
            debug_print("Ignoring uninitalized WezTerm window with generic title")
            return False

    # Check class name
    if "wezterm" in class_name.lower() or class_name == "org.wezfurlong.wezterm":
        # Main application window usually has a proper title with shell name
        # Don't accept generic "wezterm" title, wait for actual shell title
        if (
            is_visible
            and len(window_title) > 5
            and window_title.lower() != "wezterm"
            and "probing" not in window_title.lower()
        ):
            return True

    return False


def get_process_name(hwnd):
    """Get process name for a window"""
    try:
        if not hwnd:
            return ""

        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        hProcess = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
        )
        if hProcess:
            try:
                process_path = win32process.GetModuleFileNameEx(hProcess, 0)
                return os.path.basename(process_path).lower()
            finally:
                win32api.CloseHandle(hProcess)
    except Exception as e:
        debug_print(f"Error getting process name: {e}")

    return ""


def handle_new_window(hwnd, event_type):
    """Handle new window creation or activation"""
    # Make sure it's a valid window
    if not hwnd or not win32gui.IsWindow(hwnd):
        return

    # Get window info
    window_id = identify_window(hwnd)
    window_title = win32gui.GetWindowText(hwnd)
    class_name = win32gui.GetClassName(hwnd)
    process_name = get_process_name(hwnd)

    # Skip if already processed (except for SHOW events that might be title updates)
    if hwnd in already_processed_windows and event_type != "show":
        debug_print(f"Skipping already processed window: {hwnd}")
        return

    # More robust WezTerm check
    if is_wezterm_window(hwnd, window_id, class_name, process_name):
        debug_print("WezTerm window detected!")

        # Find appropriate zone and offsets
        selected_zone = find_zone_for_window(window_id)
        if selected_zone:
            # Short delay to let the window initialize
            time.sleep(0.1)

            # Get offsets for this window type
            offsets = find_window_offsets(window_id, offsets_data)

            # Move window to zone
            print(f"Auto-positioning WezTerm window to zone: {selected_zone.name}")
            if process_name == "wezterm-gui.exe" and "pwsh.exe" in window_title:
                print(f"Moving {window_title} to zone: {selected_zone.name}")
            else:
                print(f"Auto-positioning WezTerm window to zone: {selected_zone.name}")

            original_move_window_to_zone(hwnd, selected_zone, offsets)

            # Mark as processed
            already_processed_windows.add(hwnd)

            # Activate the window to bring it to front
            try:
                win32gui.SetForegroundWindow(hwnd)
            except:
                pass


def enum_windows_callback(hwnd, _):
    """Callback for EnumWindows to find existing WezTerm windows"""
    if win32gui.IsWindowVisible(hwnd):
        window_id = identify_window(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        process_name = get_process_name(hwnd)

        # Print all visible windows for debugging
        print_window_info(hwnd, "EXISTING")

        if is_wezterm_window(hwnd, window_id, class_name, process_name):
            handle_new_window(hwnd, "existing")
    return True


def find_existing_wezterm_windows():
    """Find and process existing WezTerm windows"""
    debug_print("Looking for existing WezTerm windows...")
    win32gui.EnumWindows(enum_windows_callback, None)


def find_zone_for_window(window_id):
    """Find the appropriate zone for the given window type"""
    global zones

    # You can implement your zone selection logic here
    # For now, we'll just use the first zone (often "Centered")
    if zones and len(zones) > 0:
        # Choose the default zone (Centered if available, otherwise first)
        for zone in zones:
            if zone.name == "Centered":
                return zone
        return zones[0]

    return None


def register_event_hooks():
    """Register WinEvent hooks to receive window events"""
    global hook_ids

    # Store callback reference to prevent garbage collection
    callback = WINEVENTPROC(win_event_callback)

    # Set WinEvent hooks
    hooks = [
        (EVENT_OBJECT_CREATE, "window creation"),
        (EVENT_OBJECT_SHOW, "window show"),
        (EVENT_SYSTEM_FOREGROUND, "window focus"),
    ]

    for event, desc in hooks:
        # Create hook: WINEVENT_OUTOFCONTEXT for asynchronous operation
        hook_id = windll.user32.SetWinEventHook(
            event,
            event,  # Range of events (same = single event)
            0,  # Handle to DLL (0 = current process)
            callback,  # Callback function
            0,
            0,  # Process and thread IDs (0 = all)
            0x0000,  # WINEVENT_OUTOFCONTEXT = asynchronous
        )

        if hook_id:
            hook_ids.append((hook_id, callback))  # Keep reference to callback
            print(f"Registered {desc} hook: {hook_id}")
        else:
            print(f"Failed to register {desc} hook")

    return len(hook_ids) > 0


def register_cbt_hook():
    """Register CBT hook to intercept window creation before it's shown"""
    global cbt_hook

    # Create callback function
    cbt_callback = CBTPROC(cbt_hook_callback)

    # Register CBT hook - this catches window creation before it's shown
    hook_id = windll.user32.SetWindowsHookExW(
        WH_CBT,  # Hook type
        cbt_callback,  # Callback function
        0,  # Handle to DLL (0 = current process)
        0,  # Thread ID (0 = all threads)
    )

    if hook_id:
        print(f"Registered CBT hook for early window interception: {hook_id}")
        cbt_hook = (hook_id, cbt_callback)  # Keep reference to callback
        return True
    else:
        print("Failed to register CBT hook")
        return False


def unregister_cbt_hook():
    """Unregister CBT hook"""
    global cbt_hook

    if cbt_hook:
        hook_id, callback = cbt_hook
        result = windll.user32.UnhookWindowsHookEx(hook_id)
        if result:
            print(f"Unregistered CBT hook: {hook_id}")
        else:
            print(f"Failed to unregister CBT hook: {hook_id}")
        cbt_hook = None


def unregister_event_hooks():
    """Unregister WinEvent hooks"""
    global hook_ids

    for hook_id, callback in hook_ids:
        windll.user32.UnhookWinEvent(hook_id)
        print(f"Unregistered hook: {hook_id}")

    hook_ids = []


def message_loop():
    """Process Windows messages for event hooks"""
    msg = wintypes.MSG()

    while running:
        # GetMessage blocks until a message arrives, PeekMessage doesn't block
        if windll.user32.PeekMessageW(byref(msg), 0, 0, 0, 1):
            windll.user32.TranslateMessage(byref(msg))
            windll.user32.DispatchMessageW(byref(msg))
        else:
            # Sleep to reduce CPU usage
            time.sleep(0.1)


def listener_loop():
    """Main listener loop"""
    global running, zones, offsets_data

    # Register WinEvent hooks
    if not register_event_hooks():
        print("Failed to create event hooks")
        return

    # Register CBT hook for early window interception
    register_cbt_hook()

    # Find existing WezTerm windows on startup
    find_existing_wezterm_windows()

    print("Window event listener started")
    print("Waiting for new windows...")

    # Run message loop
    message_loop()

    # Cleanup
    unregister_event_hooks()
    unregister_cbt_hook()

    print("Window listener stopped")


def start_listener():
    """Start the window listener"""
    global running, listener_thread, zones, offsets_data

    if running:
        print("Listener already running")
        return False

    # Load configuration
    zones = load_zones(ZONES_FILE)
    try:
        with open(OFFSETS_FILE, "r") as f:
            offsets_data = json.load(f)
    except Exception as e:
        print(f"Error loading offsets file: {e}")
        offsets_data = {"applications": []}

    # Set flag and start thread
    running = True
    listener_thread = threading.Thread(target=listener_loop)
    listener_thread.daemon = True
    listener_thread.start()

    return True


def stop_listener():
    """Stop the window listener"""
    global running, listener_thread

    if not running:
        print("Listener not running")
        return False

    # Clear flag and wait for thread to end
    running = False
    if listener_thread:
        listener_thread.join(timeout=2.0)

    return True


def register_journal_hook():
    """Register a journal hook - the most aggressive form of input event interception"""
    # NOTE: This is an advanced technique that requires careful handling
    # Journal hooks can intercept mouse/keyboard events before they reach applications
    # We could use this to intercept the first interaction with a new window
    # but it's generally not needed for window positioning and can impact system performance
    # Leaving this as a placeholder for now
    pass


# Function to forcefully position a window bypassing normal display behavior
def force_position_window(hwnd, zone, offsets):
    """Aggressively position window with direct API calls to bypass normal window behavior"""
    if not hwnd or not win32gui.IsWindow(hwnd):
        return False

    try:
        # First, prevent the window from being visible during positioning
        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

        # Get monitor info to properly position window
        monitor = windll.user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTOPRIMARY)
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        windll.user32.GetMonitorInfoW(monitor, byref(info))

        # Calculate position from zone with offsets
        x = zone.x + int(offsets.get("x_offset", 0))
        y = zone.y + int(offsets.get("y_offset", 0))
        width = zone.width + int(offsets.get("width_offset", 0))
        height = zone.height + int(offsets.get("height_offset", 0))

        # Ensure dimensions are positive
        width = max(100, width)
        height = max(100, height)

        # Get window style and update it to add maximize or fullscreen if needed
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        # Remove border and caption for fullscreen-like behavior
        if zone.name.lower() == "fullscreen":
            new_style = style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)

            # Use monitor dimensions for fullscreen
            x, y = info.rcMonitor.left, info.rcMonitor.top
            width = info.rcMonitor.right - info.rcMonitor.left
            height = info.rcMonitor.bottom - info.rcMonitor.top

        # Force window placement directly
        placement = WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(WINDOWPLACEMENT)
        windll.user32.GetWindowPlacement(hwnd, byref(placement))

        # Update placement structure
        placement.rcNormalPosition.left = x
        placement.rcNormalPosition.top = y
        placement.rcNormalPosition.right = x + width
        placement.rcNormalPosition.bottom = y + height

        # For maximum aggressiveness, set all flags we can
        flags = (
            SWP_ASYNCWINDOWPOS
            | SWP_DEFERERASE
            | SWP_HIDEWINDOW
            | SWP_NOACTIVATE
            | SWP_NOCOPYBITS
            | SWP_NOREDRAW
        )

        # Direct window position move - most aggressive method
        windll.user32.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, width, height, flags)

        # Set placement to ensure window restore position is correct
        placement.showCmd = win32con.SW_HIDE  # Start hidden
        windll.user32.SetWindowPlacement(hwnd, byref(placement))

        # Create a fresh rect and use MoveWindow as backup method
        windll.user32.MoveWindow(hwnd, x, y, width, height, False)

        # Short delay to ensure positions take effect
        time.sleep(0.01)

        # Now make it visible and activate
        placement.showCmd = win32con.SW_SHOW
        windll.user32.SetWindowPlacement(hwnd, byref(placement))
        windll.user32.SetForegroundWindow(hwnd)

        return True
    except Exception as e:
        debug_print(f"Error in force_position_window: {e}")
        # Fall back to original method if this fails
        return False


# Run as standalone module
if __name__ == "__main__":
    try:
        start_listener()
        print("Press Ctrl+C to exit")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_listener()
