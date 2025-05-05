#!/usr/bin/env python
import os
import json
import time
from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFontDatabase, QFont

# Import Windows-specific modules if on Windows
if os.name == 'nt':
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
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        self.__class__.__module__.split('.')[-2], 
                                        config_file_name)
        
        # Create default config if it doesn't exist
        if not os.path.exists(self.config_file):
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"Created default configuration file: {self.config_file}")
        
        # Load configuration
        self.load_config()
        
        # Set window properties for transparency and always on desktop
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        
        # Make sure it stays on the desktop even during Win+D
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)
        
        # Throttling timers for various operations
        self.last_window_fix_time = 0
        self.last_visibility_check = 0
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
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
        if os.name == 'nt':
            fonts_dir = os.path.join(os.environ["WINDIR"], "Fonts")
            font_patterns = [
                "JetBrainsMonoNerdFont-Regular.ttf", 
                "JetBrainsMonoNF-Regular.ttf", 
                "JetBrainsMono-Regular.ttf"
            ]
            
            for pattern in font_patterns:
                font_path = os.path.join(fonts_dir, pattern)
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        print(f"Loaded font file: {font_path}")
                        font_loaded = True
                        self.font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
                        break
        
        # If JetBrainsMono not found, fall back to system default or Segoe UI
        if not font_loaded:
            if os.name == 'nt' and os.path.exists("C:/Windows/Fonts/segoeui.ttf"):
                font_id = QFontDatabase.addApplicationFont("C:/Windows/Fonts/segoeui.ttf")
                if font_id != -1:
                    self.font_name = "Segoe UI"
                    print(f"Using fallback font: Segoe UI")
                else:
                    print(f"Using system default font")
                    self.font_name = QFont().family()
            else:
                print(f"Using system default font")
                self.font_name = QFont().family()
    
    def _ensure_visibility(self):
        """Ensure the widget stays visible when Windows tries to hide it"""
        # Throttle visibility checks to prevent excessive window operations
        current_time = time.time()
        if current_time - self.last_visibility_check < 0.5:  # Only check every 500ms
            return
            
        self.last_visibility_check = current_time
        
        if not self.isVisible():
            self.show()
            self.raise_()
    
    def _fix_window_behavior(self):
        """Fix window behavior (throttled to prevent too many calls)"""
        # Throttle window fixes to prevent excessive API calls
        current_time = time.time()
        if current_time - self.last_window_fix_time < 1.0:  # Only fix once per second at most
            return
            
        self.last_window_fix_time = current_time
        
        if HAS_WIN32_MODULES and os.name == 'nt':
            try:
                hwnd = int(self.winId())
                
                # Just set window style, avoid parenting/positioning which can cause errors
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                ex_style |= win32con.WS_EX_TOOLWINDOW
                ex_style &= ~win32con.WS_EX_APPWINDOW
                ex_style |= win32con.WS_EX_NOACTIVATE
                
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
            except Exception:
                pass
    
    def eventFilter(self, obj, event):
        """Handle window events to prevent minimizing"""
        if obj == self and event.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # Prevent minimization
                self.setWindowState(Qt.WindowNoState)
                # Fix window behavior after state change
                self._fix_window_behavior()
                return True
        elif obj == self and event.type() == QEvent.Hide:
            # Handle hide events
            self._ensure_visibility()
            # Fix window behavior after visibility change
            self._fix_window_behavior()
            return True
        elif obj == self and event.type() == QEvent.Show:
            # Fix window behavior after the widget is shown
            self._fix_window_behavior()
        
        return super().eventFilter(obj, event)
    
    def nativeEvent(self, eventType, message):
        """Handle native Windows events to prevent hiding"""
        # We'll avoid trying to modify the window during event handling,
        # as this can cause QT to crash or get into a bad state.
        # Instead, we'll just focus on detecting hide/minimize events.
        
        # Let Qt handle all events normally
        return False, 0 