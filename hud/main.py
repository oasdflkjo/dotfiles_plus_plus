#!/usr/bin/env python
import sys
import os
import json
import importlib
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QShortcut
from PyQt5.QtGui import QFont, QFontDatabase, QColor, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QFileSystemWatcher, QEvent, QPoint, QObject

# Import our widgets
from widgets.clock.clock import ClockWidget, HAS_WIN32_MODULES
from widgets.gmail.gmail import EmailWidget

# Import Windows-specific modules if needed
if HAS_WIN32_MODULES:
    import win32con
    import win32gui

class WidgetManager(QObject):
    """
    Simple manager for desktop widgets with:
    - Hot-reload of widget code
    - Position persistence
    - Movement/dragging support
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize QApplication
        self.app = QApplication.instance() or QApplication(sys.argv)
        
        # Create a dummy main window just for keyboard shortcuts
        self.dummy_window = QMainWindow()
        self.dummy_window.setGeometry(0, 0, 1, 1)
        self.dummy_window.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        
        # Set up keyboard shortcuts
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self.dummy_window)
        self.quit_shortcut.activated.connect(self.quit)
        self.dummy_window.show()
        
        # Active widgets
        self.widgets = {}
        
        # Config storage
        self.config_files = {}  # Maps widget names to config file paths
        self.positions = {}  # Stores widget positions
        
        # Dragging state
        self.dragging = {}  # Tracks dragging state for each widget
        self.drag_positions = {}  # Stores drag positions
        
        # File watchers
        self.code_watcher = QFileSystemWatcher()  # For widget code files
        self.config_watcher = QFileSystemWatcher()  # For config files
        
        # Track last modified times
        self.last_modified = {}
        
        # Setup file watchers
        self._setup_file_watchers()
        
        # Create widgets
        self._create_widgets()
        
        # Install event filter for all widgets
        for name, widget in self.widgets.items():
            widget.installEventFilter(self)
            
        # Load positions
        self._restore_positions()
    
    def _setup_file_watchers(self):
        """Setup file watchers for hot reloading and config changes"""
        # Watch widget module files for code changes
        self._watch_code_file("widgets/clock/clock.py")
        self._watch_code_file("widgets/gmail/gmail.py")
        
        # Connect signals
        self.code_watcher.fileChanged.connect(self._on_code_changed)
        self.config_watcher.fileChanged.connect(self._on_config_changed)
    
    def _watch_code_file(self, filename):
        """Add a code file to watch for changes"""
        path = os.path.abspath(filename)
        if os.path.exists(path):
            self.code_watcher.addPath(path)
            self.last_modified[path] = os.path.getmtime(path)
            print(f"Watching code file: {path}")
    
    def _watch_config_file(self, widget_name, config_path):
        """Add a config file to watch for changes"""
        if os.path.exists(config_path):
            self.config_files[widget_name] = config_path
            self.config_watcher.addPath(config_path)
            print(f"Watching config file: {config_path}")
    
    def _create_widgets(self):
        """Create and show all widgets"""
        # Create clock widget
        self.widgets["clock"] = ClockWidget()
        
        # Watch its config file
        config_path = self.widgets["clock"].get_config_file_path()
        self._watch_config_file("clock", config_path)
        
        # Create email widget
        self.widgets["email"] = EmailWidget()
        
        # Watch its config file
        email_config_path = self.widgets["email"].get_config_file_path()
        self._watch_config_file("email", email_config_path)
        
        # Show widgets and make them stay on desktop
        for name, widget in self.widgets.items():
            widget.show()
            print(f"{name.capitalize()} widget started")
            
        # Set desktop window behavior for Windows
        if HAS_WIN32_MODULES:
            self._set_desktop_behavior()
    
    def _set_desktop_behavior(self):
        """Set desktop window behavior for all widgets"""
        print("Setting desktop window behavior for all widgets")
        for name, widget in self.widgets.items():
            try:
                # Only make window behavior modifications during initialization,
                # not during event handling which can cause errors
                hwnd = int(widget.winId())
                
                # Set window as tool window that doesn't show in taskbar
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                ex_style |= win32con.WS_EX_TOOLWINDOW  # Tool window style
                ex_style &= ~win32con.WS_EX_APPWINDOW  # Not an app window
                ex_style |= win32con.WS_EX_NOACTIVATE  # Don't activate when clicked
                
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
                
                # Make widget stay on desktop by setting proper window style
                # Avoid excessive window operations that can cause errors
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                style |= win32con.WS_VISIBLE
                win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
                
                # Just make sure the window is visible - avoid complex operations
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                
                print(f"Desktop window behavior set for {name}")
            except Exception as e:
                print(f"Error setting window behavior for {name}: {e}")
    
    def _on_code_changed(self, path):
        """Handle code file changes by scheduling a reload after a short delay"""
        # Use a timer to ensure the file write is complete
        QTimer.singleShot(100, lambda: self._reload_module(path))
    
    def _on_config_changed(self, path):
        """Handle config file changes"""
        # Apply config changes to the appropriate widget
        for name, config_path in self.config_files.items():
            if config_path == path and name in self.widgets:
                # Load the config and apply
                try:
                    # Just reload the widget's config from its file
                    self.widgets[name].load_config()
                    self.widgets[name].apply_config()
                    print(f"Applied updated configuration for {name} widget")
                except Exception as e:
                    print(f"Error updating {name} widget configuration: {e}")
    
    def _reload_module(self, path):
        """Reload the module and recreate affected widgets"""
        try:
            # Check if the file has actually changed
            current_mtime = os.path.getmtime(path)
            if current_mtime <= self.last_modified.get(path, 0):
                return
            
            self.last_modified[path] = current_mtime
            
            # Determine which module was changed
            path_parts = path.replace('\\', '/').split('/')
            if len(path_parts) >= 3 and path_parts[0] == 'widgets':
                widget_type = path_parts[1]  # e.g., "clock" or "gmail"
                module_name = path_parts[2].split('.')[0]  # Remove file extension
                full_module = f"widgets.{widget_type}.{module_name}"
            else:
                full_module = os.path.basename(path)[:-3]  # Fallback to just the filename
                
            print(f"Hot-reloading module: {full_module}")
            
            # Reload the module
            if full_module in sys.modules:
                # Store widget positions before reloading
                self._save_positions()
                
                # Reload the module
                importlib.reload(sys.modules[full_module])
                
                # Recreate widgets based on which module changed
                if widget_type == "clock":
                    self._recreate_widget("clock", ClockWidget)
                elif widget_type == "gmail":
                    self._recreate_widget("email", EmailWidget)
        
        except Exception as e:
            print(f"Error during hot reload: {e}")
    
    def _recreate_widget(self, name, widget_class):
        """Recreate a widget while preserving its position"""
        if name in self.widgets:
            # Close the old widget
            old_widget = self.widgets[name]
            old_widget.close()
            old_widget.deleteLater()
            
            # Create a new widget
            self.widgets[name] = widget_class()
            
            # Install event filter
            self.widgets[name].installEventFilter(self)
            
            # Restore position if available
            if name in self.positions:
                self.widgets[name].move(self.positions[name])
            
            # Watch its config file
            config_path = self.widgets[name].get_config_file_path()
            self._watch_config_file(name, config_path)
            
            # Show the new widget
            self.widgets[name].show()
            print(f"{name.capitalize()} widget reloaded")
            
            # Apply desktop behavior
            if HAS_WIN32_MODULES:
                self._set_desktop_behavior()
    
    def _save_positions(self):
        """Save positions of all widgets"""
        for name, widget in self.widgets.items():
            self.positions[name] = QPoint(widget.x(), widget.y())
            
            # Also save to config file if we know the widget's config
            self._save_position_to_config(name)
    
    def _save_position_to_config(self, widget_name):
        """Save a widget's position to its config file"""
        if widget_name not in self.widgets or widget_name not in self.config_files:
            return
            
        widget = self.widgets[widget_name]
        config_path = self.config_files[widget_name]
        
        try:
            # Load current config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update position
            if "window_position" not in config:
                config["window_position"] = {}
                
            config["window_position"]["x"] = widget.x()
            config["window_position"]["y"] = widget.y()
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            print(f"Saved position for {widget_name}: X={widget.x()}, Y={widget.y()}")
            
        except Exception as e:
            print(f"Error saving position for {widget_name}: {e}")
    
    def _restore_positions(self):
        """Restore positions of all widgets from their config files"""
        for name, config_path in self.config_files.items():
            if name in self.widgets:
                self._restore_widget_position(name, config_path)
    
    def _restore_widget_position(self, widget_name, config_path):
        """Restore a widget's position from its config file"""
        try:
            # Load config
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                if "window_position" in config:
                    pos = config["window_position"]
                    x, y = pos.get("x", -1), pos.get("y", -1)
                    
                    if x >= 0 and y >= 0:
                        self.widgets[widget_name].move(x, y)
                        self.positions[widget_name] = QPoint(x, y)
                        print(f"Restored position for {widget_name}: X={x}, Y={y}")
                    else:
                        # Center on screen
                        self._center_widget(widget_name)
                else:
                    # Center on screen
                    self._center_widget(widget_name)
                    
        except Exception as e:
            print(f"Error restoring position for {widget_name}: {e}")
            # Center on screen
            self._center_widget(widget_name)
    
    def _center_widget(self, widget_name):
        """Center a widget on the screen"""
        if widget_name in self.widgets:
            widget = self.widgets[widget_name]
            screen = self.app.primaryScreen().geometry()
            widget.move(
                (screen.width() - widget.width()) // 2,
                (screen.height() - widget.height()) // 2
            )
            print(f"Centered {widget_name} widget on screen")
    
    def eventFilter(self, obj, event):
        """Event filter to handle dragging for all widgets"""
        # Handle window state change event (minimizing)
        if event.type() == QEvent.WindowStateChange and obj in self.widgets.values():
            if obj.windowState() & Qt.WindowMinimized:
                # Restore window state
                obj.setWindowState(Qt.WindowNoState)
                return True
        
        # Process mouse events for dragging
        if obj in self.widgets.values():
            widget_name = next(name for name, widget in self.widgets.items() if widget == obj)
            
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.dragging[widget_name] = True
                try:
                    self.drag_positions[widget_name] = event.globalPosition().toPoint() - obj.frameGeometry().topLeft()
                except AttributeError:
                    self.drag_positions[widget_name] = event.globalPos() - obj.frameGeometry().topLeft()
                return True
                
            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                self.dragging[widget_name] = False
                self._save_position_to_config(widget_name)
                return True
                
            elif event.type() == QEvent.MouseMove and self.dragging.get(widget_name, False):
                if widget_name in self.drag_positions:
                    try:
                        obj.move(event.globalPosition().toPoint() - self.drag_positions[widget_name])
                    except AttributeError:
                        obj.move(event.globalPos() - self.drag_positions[widget_name])
                    return True
        
        return super().eventFilter(obj, event)
    
    def quit(self):
        """Clean shutdown of the application"""
        print("Shutting down desktop widgets...")
        
        # Save widget positions before closing
        self._save_positions()
        
        # Close all widgets
        for name, widget in self.widgets.items():
            try:
                widget.close()
            except Exception as e:
                print(f"Error closing {name} widget: {e}")
                
        # Quit the application
        self.app.quit()
    
    def run(self):
        """Run the application main loop"""
        print("\nDesktop Widget System started with hot-reload")
        print("Edit widget modules to change functionality - changes apply automatically")
        print("Drag widgets to reposition them - positions are saved automatically")
        print("Press Ctrl+Q to quit")
        
        try:
            return self.app.exec_()
        except KeyboardInterrupt:
            self.quit()
            return 0

def main():
    """Main application entry point"""
    manager = WidgetManager()
    return manager.run()

if __name__ == "__main__":
    sys.exit(main())
