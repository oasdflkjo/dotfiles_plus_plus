#!/usr/bin/env python
import os
import json
import time
from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QFontDatabase, QFont

# Import Windows-specific modules if on Windows
if os.name == "nt":
    try:
        import win32con
        import win32gui
        import win32api
        import ctypes
        from ctypes import wintypes

        HAS_WIN32_MODULES = True
    except ImportError:
        HAS_WIN32_MODULES = False
else:
    HAS_WIN32_MODULES = False


class BaseWidget(QMainWindow):
    """Base class for desktop widgets providing common functionality"""

    def __init__(self, config_file_name, default_config, parent=None):
        super().__init__(parent)

        # Store the config file name and default config
        self.config_file_name = config_file_name
        self.config = default_config.copy()

        # Config file path
        self.config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            self.__class__.__module__.split(".")[-2],
            config_file_name,
        )

        # Create default config if it doesn't exist
        if not os.path.exists(self.config_file):
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
            print(f"Created default configuration file: {self.config_file}")

        # Load configuration
        self.load_config()

        # Set window properties
        self._configure_window()

        # Throttling timers for various operations
        self.last_window_fix_time = 0
        self.last_visibility_check = 0

        # Set up visibility timer
        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self._monitor_visibility)
        self.visibility_timer.start(200)  # Check every 200ms

    def _configure_window(self):
        """Configure window properties for desktop functionality"""
        # Frameless, tool window that doesn't take focus
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.NoDropShadowWindowHint  # Added to prevent shadow artifacts
        )

        # Set attributes for transparency and behavior
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)

        # Critical for Win+D handling: ensure our widget stays on the desktop
        if HAS_WIN32_MODULES:
            self._setup_desktop_window()

    def _setup_desktop_window(self):
        """Set up window specifically to stay behind other windows (bottommost)"""
        if not HAS_WIN32_MODULES or not os.name == "nt":
            return

        try:
            # Get window handle
            hwnd = int(self.winId())

            # Set window styles for a desktop widget
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style |= win32con.WS_EX_TOOLWINDOW  # Tool window (no taskbar icon)
            ex_style |= win32con.WS_EX_NOACTIVATE  # Don't activate when clicked
            ex_style &= ~win32con.WS_EX_APPWINDOW  # Not an app window
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

            # Set style for visibility
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style |= win32con.WS_VISIBLE  # Make sure it's visible
            style &= ~win32con.WS_POPUP  # Not a popup window
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

            # Make sure it's visible
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNA)

            # Set the window as bottommost (behind all other windows)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_BOTTOM,  # BOTTOM instead of TOPMOST
                0,
                0,
                0,
                0,  # we don't change the position or size
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
            )
        except Exception as e:
            print(f"Error setting up desktop window: {e}")

    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values, preserving defaults for missing keys
                    for key, value in loaded_config.items():
                        self.config[key] = value
                print(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            print(f"Error loading configuration: {e}")

    def get_config_file_path(self):
        """Get the path to the config file"""
        return self.config_file

    def load_font(self, font_name="JetBrainsMono Nerd Font"):
        """Load and set up the font"""
        # Set default font name to try
        self.font_name = font_name
        font_loaded = False

        # Try to find JetBrainsMono Nerd Font in Windows fonts directory
        if os.name == "nt":
            fonts_dir = os.path.join(os.environ["WINDIR"], "Fonts")
            font_patterns = [
                "JetBrainsMonoNerdFont-Regular.ttf",
                "JetBrainsMonoNF-Regular.ttf",
                "JetBrainsMono-Regular.ttf",
            ]

            for pattern in font_patterns:
                font_path = os.path.join(fonts_dir, pattern)
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        print(f"Loaded font file: {font_path}")
                        font_loaded = True
                        self.font_name = QFontDatabase.applicationFontFamilies(font_id)[
                            0
                        ]
                        break

        # If JetBrainsMono not found, fall back to system default or Segoe UI
        if not font_loaded:
            if os.name == "nt" and os.path.exists("C:/Windows/Fonts/segoeui.ttf"):
                font_id = QFontDatabase.addApplicationFont(
                    "C:/Windows/Fonts/segoeui.ttf"
                )
                if font_id != -1:
                    self.font_name = "Segoe UI"
                    print(f"Using fallback font: Segoe UI")
                else:
                    print(f"Using system default font")
                    self.font_name = QFont().family()
            else:
                print(f"Using system default font")
                self.font_name = QFont().family()

    def _monitor_visibility(self):
        """Monitor and restore visibility regularly, important for Win+D recovery"""
        # Check if our window is visible, restore if hidden
        if not self.isVisible() or self.windowState() & Qt.WindowMinimized:
            self._restore_visibility()

    def _restore_visibility(self):
        """Restore window visibility after Win+D or other events"""
        # Unminimize if minimized
        if self.windowState() & Qt.WindowMinimized:
            self.setWindowState(Qt.WindowNoState)

        # Show if hidden
        if not self.isVisible():
            self.show()

        # Use Win32 APIs to enforce visibility
        if HAS_WIN32_MODULES and os.name == "nt":
            try:
                hwnd = int(self.winId())
                # Just use the simple ShowWindow command
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWNA)

                # Make sure it stays bottommost
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_BOTTOM,  # BOTTOM instead of TOPMOST
                    0,
                    0,
                    0,
                    0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                )
            except Exception:
                pass

    def eventFilter(self, obj, event):
        """Handle window events to prevent minimizing"""
        if obj == self:
            if event.type() == QEvent.WindowStateChange:
                if self.windowState() & Qt.WindowMinimized:
                    # Prevent minimization
                    self.setWindowState(Qt.WindowNoState)
                    return True
            elif event.type() == QEvent.Hide:
                # Handle hide events
                self._restore_visibility()
                return True
            elif event.type() == QEvent.Show:
                # Ensure proper window setup when shown
                self._setup_desktop_window()

        return super().eventFilter(obj, event)

    def showEvent(self, event):
        """Ensure proper window behavior when shown"""
        super().showEvent(event)
        # Make sure window is properly set up when shown
        self._setup_desktop_window()

    def closeEvent(self, event):
        """Clean up resources when closing"""
        # Stop timers
        self.visibility_timer.stop()
        super().closeEvent(event)

    def nativeEvent(self, eventType, message):
        """Handle native Windows events to prevent hiding"""
        # We'll avoid trying to modify the window during event handling,
        # as this can cause QT to crash or get into a bad state.
        # Instead, we'll just focus on detecting hide/minimize events.

        # Let Qt handle all events normally
        return False, 0
