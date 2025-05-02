import win32gui
import win32con
import win32api
import ctypes
import ctypes.wintypes
import threading
import time
import logging
import sys
from window_manager_soft import WindowPositioner

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("WindowHookManager")

# Windows API constants for hooks
EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_SYSTEM_MOVESIZESTART = 0x000A
EVENT_SYSTEM_MOVESIZEEND = 0x000B
EVENT_SYSTEM_MINIMIZESTART = 0x0016
EVENT_SYSTEM_MINIMIZEEND = 0x0017
EVENT_OBJECT_CREATE = 0x8000
EVENT_OBJECT_DESTROY = 0x8001
EVENT_OBJECT_SHOW = 0x8002
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNTHREAD = 0x0001
WINEVENT_SKIPOWNPROCESS = 0x0002

# Function type for WinEventProc callback
WINEVENTPROC = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)

# Get required functions from user32.dll
user32 = ctypes.windll.user32
SetWinEventHook = user32.SetWinEventHook
UnhookWinEvent = user32.UnhookWinEvent


class WindowHookManager:
    """
    Manages window event hooks and uses WindowPositioner to position windows
    when appropriate events occur.

    This module is responsible for detecting window events (creation, showing, resizing)
    and calling the WindowPositioner to apply positioning when needed.
    """

    def __init__(self, positioner=None):
        # Store the window positioner
        self.positioner = positioner or WindowPositioner()

        # Set up event tracking
        self.running = True
        self.event_hooks = []  # Store event hook handles
        self.pending_windows = {}  # Store windows that need positioning with timestamps

        # Create function refs to prevent garbage collection
        self._event_proc_refs = []

        # Tracking for duplicate events
        self.last_positioned = {}  # Track when windows were last positioned
        self.position_cooldown = (
            0.5  # Seconds to wait before repositioning the same window
        )

        logger.info("Window hook manager initialized")

    def win_event_callback(
        self,
        hWinEventHook,
        event,
        hwnd,
        idObject,
        idChild,
        dwEventThread,
        dwmsEventTime,
    ):
        """Callback for window events"""
        if not hwnd or not self.running:
            return

        # Only process main window objects, not child controls
        if idObject != 0 or idChild != 0:
            return

        try:
            # Skip invisible windows and windows with no title
            if not win32gui.IsWindowVisible(hwnd) or not win32gui.GetWindowText(hwnd):
                return

            # Check if we recently positioned this window (avoid duplicate work)
            current_time = time.time()
            if hwnd in self.last_positioned:
                elapsed = current_time - self.last_positioned[hwnd]
                if elapsed < self.position_cooldown:
                    return

            # Get a readable event name for logging
            event_name = self._get_event_name(event)
            window_title = win32gui.GetWindowText(hwnd)
            logger.debug(f"Event: {event_name} for '{window_title}'")

            # Handle different event types
            if event == EVENT_OBJECT_CREATE:
                # New window created - add to pending with delayed positioning
                logger.info(f"Window created: '{window_title}'")
                self._add_pending_window(hwnd)

            elif event == EVENT_OBJECT_SHOW:
                # Window shown - try to position immediately
                logger.info(f"Window shown: '{window_title}'")
                threading.Thread(
                    target=self._delayed_position,
                    args=(hwnd, 0.1),  # Small delay for window to stabilize
                ).start()

            elif event == EVENT_SYSTEM_FOREGROUND:
                # Window focused - only position if it's in the managed list
                info = self.positioner.get_window_info(hwnd)
                if info and self.positioner.should_manage_window(
                    info["process_name"], info["window_class"]
                ):
                    logger.info(f"Window focused: '{window_title}'")
                    threading.Thread(
                        target=self._delayed_position,
                        args=(hwnd, 0.05),  # Minimal delay for focus events
                    ).start()

            elif event == EVENT_SYSTEM_MOVESIZEEND:
                # Window resize/move ended - reapply positioning
                logger.info(f"Window resize/move ended: '{window_title}'")
                threading.Thread(
                    target=self._delayed_position,
                    args=(hwnd, 0.2),  # Slightly longer delay after resize
                ).start()

        except Exception as e:
            logger.error(f"Error in win_event_callback: {e}")

    def _get_event_name(self, event):
        """Convert event code to readable name for logging"""
        event_names = {
            EVENT_SYSTEM_FOREGROUND: "FOREGROUND",
            EVENT_SYSTEM_MOVESIZESTART: "MOVESIZE_START",
            EVENT_SYSTEM_MOVESIZEEND: "MOVESIZE_END",
            EVENT_SYSTEM_MINIMIZESTART: "MINIMIZE_START",
            EVENT_SYSTEM_MINIMIZEEND: "MINIMIZE_END",
            EVENT_OBJECT_CREATE: "CREATE",
            EVENT_OBJECT_DESTROY: "DESTROY",
            EVENT_OBJECT_SHOW: "SHOW",
        }
        return event_names.get(event, f"UNKNOWN_{event}")

    def _add_pending_window(self, hwnd):
        """Add window to pending list for delayed positioning"""
        self.pending_windows[hwnd] = {
            "timestamp": time.time(),
            "attempts": 0,
        }

    def _process_pending_windows(self):
        """Process windows that are waiting for positioning"""
        current_time = time.time()
        to_remove = []

        for hwnd, info in list(self.pending_windows.items()):
            # Skip non-existing windows
            if not win32gui.IsWindow(hwnd):
                to_remove.append(hwnd)
                continue

            # Calculate delay based on attempts (exponential backoff)
            attempts = info["attempts"]
            delay = min(0.5 * (2**attempts), 5.0)  # Max 5 seconds delay

            # Check if it's time to try this window
            if current_time - info["timestamp"] >= delay:
                # Try to position the window
                try:
                    success = self.positioner.position_window_by_handle(hwnd)

                    if success:
                        self.last_positioned[hwnd] = current_time
                        to_remove.append(hwnd)
                    else:
                        # Update for next attempt
                        info["attempts"] += 1
                        info["timestamp"] = current_time

                        # Give up after 5 attempts
                        if info["attempts"] >= 5:
                            logger.warning(
                                f"Giving up on window {hwnd} after 5 attempts"
                            )
                            to_remove.append(hwnd)
                except Exception as e:
                    logger.error(f"Error positioning pending window: {e}")
                    to_remove.append(hwnd)

        # Remove processed or failed windows
        for hwnd in to_remove:
            if hwnd in self.pending_windows:
                del self.pending_windows[hwnd]

    def _delayed_position(self, hwnd, delay=0.1):
        """Position a window after a short delay"""
        time.sleep(delay)
        try:
            # Check if window still exists and is not minimized
            if win32gui.IsWindow(hwnd) and not win32gui.IsIconic(hwnd):
                success = self.positioner.position_window_by_handle(hwnd)
                if success:
                    self.last_positioned[hwnd] = time.time()
        except Exception as e:
            logger.error(f"Error in delayed positioning: {e}")

    def install_hooks(self):
        """Install Windows event hooks"""
        try:
            # Create WinEventProc callback functions - each event type needs its own callback
            window_create_proc = WINEVENTPROC(self.win_event_callback)
            window_show_proc = WINEVENTPROC(self.win_event_callback)
            foreground_proc = WINEVENTPROC(self.win_event_callback)
            movesize_end_proc = WINEVENTPROC(self.win_event_callback)

            # Store references to prevent garbage collection
            self._event_proc_refs.append(window_create_proc)
            self._event_proc_refs.append(window_show_proc)
            self._event_proc_refs.append(foreground_proc)
            self._event_proc_refs.append(movesize_end_proc)

            # Install hooks
            hook1 = SetWinEventHook(
                EVENT_OBJECT_CREATE,
                EVENT_OBJECT_CREATE,
                0,
                window_create_proc,
                0,
                0,
                WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
            )

            hook2 = SetWinEventHook(
                EVENT_OBJECT_SHOW,
                EVENT_OBJECT_SHOW,
                0,
                window_show_proc,
                0,
                0,
                WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
            )

            hook3 = SetWinEventHook(
                EVENT_SYSTEM_FOREGROUND,
                EVENT_SYSTEM_FOREGROUND,
                0,
                foreground_proc,
                0,
                0,
                WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
            )

            hook4 = SetWinEventHook(
                EVENT_SYSTEM_MOVESIZEEND,
                EVENT_SYSTEM_MOVESIZEEND,
                0,
                movesize_end_proc,
                0,
                0,
                WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
            )

            # Store hook handles
            self.event_hooks = []
            if hook1:
                self.event_hooks.append(hook1)
            if hook2:
                self.event_hooks.append(hook2)
            if hook3:
                self.event_hooks.append(hook3)
            if hook4:
                self.event_hooks.append(hook4)

            logger.info(f"Installed {len(self.event_hooks)} window event hooks")
            return len(self.event_hooks) > 0
        except Exception as e:
            logger.error(f"Failed to install event hooks: {e}")
            return False

    def uninstall_hooks(self):
        """Remove event hooks"""
        for hook in self.event_hooks:
            try:
                UnhookWinEvent(hook)
            except Exception as e:
                logger.error(f"Error removing hook {hook}: {e}")

        self.event_hooks = []
        logger.info("Uninstalled window event hooks")

    def monitor_message_loop(self):
        """Run a message loop to process window events"""
        msg = ctypes.wintypes.MSG()
        last_pending_check = time.time()

        while self.running:
            # Process Windows messages - this makes the event hooks work
            if user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            # Process pending windows periodically
            current_time = time.time()
            if current_time - last_pending_check > 0.5:  # Check every 500ms
                if self.pending_windows:
                    self._process_pending_windows()
                last_pending_check = current_time

            time.sleep(0.01)  # Small sleep to prevent high CPU usage

    def start(self):
        """Start the window hook manager"""
        # Initial positioning of all windows
        try:
            count = self.positioner.position_all_manageable_windows()
            logger.info(f"Initially positioned {count} windows")

            # Install hooks
            hook_success = self.install_hooks()
            if not hook_success:
                logger.error("Failed to install window hooks")
                return False

            # Start message loop thread for event processing
            self.message_thread = threading.Thread(target=self.monitor_message_loop)
            self.message_thread.daemon = True
            self.message_thread.start()

            logger.info("Window hook manager started")
            return True
        except Exception as e:
            logger.error(f"Error starting hook manager: {e}")
            return False

    def stop(self):
        """Stop the window hook manager"""
        try:
            self.running = False
            self.uninstall_hooks()
            logger.info("Window hook manager stopped")
        except Exception as e:
            logger.error(f"Error stopping hook manager: {e}")


def main():
    """Test the WindowHookManager functionality"""
    print("Window Hook Manager - Continuous window management")
    print("-" * 50)
    print("This module manages window positions automatically in response to events")
    print("Press Ctrl+C to exit\n")

    try:
        # Create window positioner and hook manager
        positioner = WindowPositioner()
        hook_manager = WindowHookManager(positioner)

        # Start the hook manager
        if hook_manager.start():
            print("Window hook manager started successfully")
            print("Windows will be automatically positioned when created or moved\n")

            # Keep the program running
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    finally:
        if "hook_manager" in locals():
            hook_manager.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
