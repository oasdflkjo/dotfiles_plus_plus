import json
import os
import win32gui
import win32process
import win32api
import win32con
import psutil
import keyboard
from tagger_interface import TaggerInterface

class WindowTagger(TaggerInterface):
    def __init__(self):
        self.definitions_file = "tag_definitions.json"
        self.offsets_file = "tag_offsets.json"
        self.zones_file = "zones.json"
        self.definitions = self.load_definitions()
        self.offsets = self.load_offsets()
        self.zones = self.load_zones()
        
        # Taskbar state
        self.taskbar_hidden = False
        self.taskbar_window = None
        
        # Register hotkeys
        keyboard.add_hotkey("ctrl+alt+t", self.show_tag_dialog)
        keyboard.add_hotkey("win+c", self.center_active_window_with_tag)
        keyboard.add_hotkey("win+f12", self.toggle_taskbar)
        
        print("Hotkeys registered:")
        print("  Ctrl+Alt+T: Open tagging interface")
        print("  Win+C: Center active window (if it has a tag definition)")
        print("  Win+F12: Toggle taskbar visibility")
        
        # Hide taskbar on startup
        self.hide_taskbar_on_startup()
        
    def load_definitions(self):
        """Load window definitions from JSON file"""
        if os.path.exists(self.definitions_file):
            try:
                with open(self.definitions_file, "r") as f:
                    data = json.load(f)
                    # Ensure the data is a list
                    if isinstance(data, list):
                        return data
                    else:
                        print(f"Warning: {self.definitions_file} does not contain a valid list. Using empty list.")
                        return []
            except json.JSONDecodeError:
                print(f"Warning: {self.definitions_file} contains invalid JSON. Using empty list.")
                return []
            except Exception as e:
                print(f"Error loading definitions: {e}")
                return []
        return []
    
    def load_offsets(self):
        """Load window offsets from JSON file"""
        if os.path.exists(self.offsets_file):
            try:
                with open(self.offsets_file, "r") as f:
                    data = json.load(f)
                    # Ensure the data is a dictionary
                    if isinstance(data, dict):
                        return data
                    else:
                        print(f"Warning: {self.offsets_file} does not contain a valid dictionary. Using empty dict.")
                        return {}
            except json.JSONDecodeError:
                print(f"Warning: {self.offsets_file} contains invalid JSON. Using empty dict.")
                return {}
            except Exception as e:
                print(f"Error loading offsets: {e}")
                return {}
        return {}
    
    def load_zones(self):
        """Load window zones from JSON file"""
        if os.path.exists(self.zones_file):
            try:
                with open(self.zones_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {self.zones_file} contains invalid JSON. Creating default zone.")
                return self.create_default_zone()
            except Exception as e:
                print(f"Error loading zones: {e}")
                return self.create_default_zone()
        else:
            return self.create_default_zone()
    
    def create_default_zone(self):
        """Create default centered zone"""
        # Get screen dimensions
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        
        # Default centered zone with margins
        centered_zone = {
            "name": "Centered",
            "x": screen_width // 6,
            "y": screen_height // 12,
            "width": 2 * screen_width // 3,
            "height": 5 * screen_height // 6,
            "description": "Centered window with margins"
        }
        
        zones = {"centered": centered_zone}
        
        # Save the default zone
        os.makedirs(os.path.dirname(self.zones_file), exist_ok=True)
        with open(self.zones_file, "w") as f:
            json.dump(zones, f, indent=2)
            
        return zones
    
    def save_definitions(self):
        """Save window definitions to JSON file"""
        # Only create directory if the file path contains a directory
        dirname = os.path.dirname(self.definitions_file)
        if dirname:  # Only create directory if there is a path component
            os.makedirs(dirname, exist_ok=True)
        with open(self.definitions_file, "w") as f:
            json.dump(self.definitions, f, indent=2)
    
    def save_offsets(self):
        """Save window offsets to JSON file"""
        # Only create directory if the file path contains a directory
        dirname = os.path.dirname(self.offsets_file)
        if dirname:  # Only create directory if there is a path component
            os.makedirs(dirname, exist_ok=True)
        with open(self.offsets_file, "w") as f:
            json.dump(self.offsets, f, indent=2)
    
    def get_active_window_info(self):
        """Get information about the currently active window"""
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            print(f"Debug - Active window process name: {process_name}")  # Debug print
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = "unknown"
            print("Debug - Could not get process name")  # Debug print
        
        window_title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        print(f"Debug - Window class name: {class_name}")  # Debug print
        
        # Get window position and size
        rect = win32gui.GetWindowRect(hwnd)
        x = rect[0]
        y = rect[1]
        width = rect[2] - x
        height = rect[3] - y
        
        return {
            "hwnd": hwnd,
            "process_name": process_name,
            "window_title": window_title,
            "class_name": class_name,
            "x": x,
            "y": y,
            "width": width,
            "height": height
        }
    
    def get_centered_zone(self):
        """Get the centered zone dimensions"""
        # Get the centered zone from zones.json
        centered = self.zones.get("centered", {})
        if not centered:
            # Fallback to default centered zone if not found
            return self.create_default_zone()["centered"]
        return centered
    
    def position_window_with_offsets(self, hwnd, base_x, base_y, base_width, base_height, x_offset, y_offset, width_offset, height_offset):
        """Position window with base values and offsets"""
        # Calculate final position and size
        final_x = base_x + x_offset
        final_y = base_y + y_offset
        final_width = base_width + width_offset
        final_height = base_height + height_offset
        
        # Move and resize window
        win32gui.MoveWindow(hwnd, final_x, final_y, final_width, final_height, True)
        
        return final_x, final_y, final_width, final_height
    
    def save_tag_definition(self, tag_definition):
        """Save a new tag definition"""
        tag_name = tag_definition["name"]
        
        # Check if tag with this name already exists
        tag_exists = False
        for i, existing_tag in enumerate(self.definitions):
            if existing_tag.get("name") == tag_name:
                # Update existing tag instead of adding a new one
                self.definitions[i] = tag_definition
                tag_exists = True
                break
        
        # Only add if tag doesn't already exist
        if not tag_exists:
            self.definitions.append(tag_definition)
            
        self.save_definitions()
    
    def save_offset(self, tag_name, x_offset, y_offset, width_offset, height_offset):
        """Save window offsets for a tag"""
        self.offsets[tag_name] = {
            "x_offset": x_offset,
            "y_offset": y_offset,
            "width_offset": width_offset,
            "height_offset": height_offset
        }
        self.save_offsets()
    
    def get_existing_tag_info(self, window_info):
        """Get existing tag information for a window"""
        # First try to match based on process name
        process_name = window_info.get("process_name", "")
        if not process_name:
            return None
            
        print(f"Debug - Looking for tag matching process: {process_name}")  # Debug print
        print(f"Debug - Available tags: {self.definitions}")  # Debug print
            
        # Look for matching tag
        for tag in self.definitions:
            # Check process name if specified
            if tag.get("process_name"):
                print(f"Debug - Comparing with tag process: {tag.get('process_name')}")  # Debug print
                if tag.get("process_name").lower() != process_name.lower():  # Case-insensitive comparison
                    continue
                
            # Check class name if specified
            if tag.get("class_name"):
                print(f"Debug - Comparing with tag class: {tag.get('class_name')}")  # Debug print
                if tag.get("class_name") != window_info.get("class_name", ""):
                    continue
                
            # Check title substring if specified
            if tag.get("title_substring"):
                print(f"Debug - Comparing with tag title substring: {tag.get('title_substring')}")  # Debug print
                window_title = window_info.get("window_title", "").lower()
                title_substring = tag.get("title_substring").lower()
                if title_substring not in window_title:
                    continue
                
            # If we get here, all specified criteria match
            print(f"Debug - Found matching tag: {tag.get('name')}")  # Debug print
            return tag.get("name"), self.offsets.get(tag.get("name"), {})
                
        return None
    
    def center_active_window_with_tag(self):
        """Center the active window using its tag definition if found"""
        # Get active window info
        window_info = self.get_active_window_info()
        
        # Try to find a matching tag
        tag_info = self.get_existing_tag_info(window_info)
        
        if not tag_info:
            print("No matching tag found for the active window.")
            # Flash the window to indicate error
            win32gui.FlashWindow(window_info["hwnd"], True)
            return False
        
        tag_name, offsets = tag_info
        
        # Get the centered zone
        centered = self.get_centered_zone()
        
        # Get offsets for this tag
        x_offset = offsets.get("x_offset", 0)
        y_offset = offsets.get("y_offset", 0)
        width_offset = offsets.get("width_offset", 0)
        height_offset = offsets.get("height_offset", 0)
        
        # Apply centering with offsets
        self.position_window_with_offsets(
            window_info["hwnd"],
            centered.get("x", 0),
            centered.get("y", 0),
            centered.get("width", 0),
            centered.get("height", 0),
            x_offset,
            y_offset,
            width_offset,
            height_offset
        )
        
        # Flash the window to indicate success
        win32gui.FlashWindow(window_info["hwnd"], True)
        
        print(f"Centered window using tag '{tag_name}'")
        return True
    
    def show_tag_dialog(self):
        """Show the tag dialog"""
        # This method is not part of the interface as it's GUI-specific
        from gui import TaggerGUI
        import tkinter as tk
        root = tk.Tk()
        app = TaggerGUI(root, self)
        root.mainloop()
    
    def toggle_taskbar(self):
        """Toggle the visibility of the Windows taskbar"""
        # Find taskbar window if not already found
        if not self.taskbar_window:
            self.taskbar_window = win32gui.FindWindow("Shell_TrayWnd", None)
            if not self.taskbar_window:
                print("Taskbar window not found")
                return

        # Toggle visibility
        if self.taskbar_hidden:
            win32gui.ShowWindow(self.taskbar_window, win32con.SW_SHOW)
            self.taskbar_hidden = False
            print("Taskbar shown")
        else:
            win32gui.ShowWindow(self.taskbar_window, win32con.SW_HIDE)
            self.taskbar_hidden = True
            print("Taskbar hidden")
    
    def hide_taskbar_on_startup(self):
        """Hide the taskbar when the application starts"""
        self.taskbar_window = win32gui.FindWindow("Shell_TrayWnd", None)
        if self.taskbar_window:
            win32gui.ShowWindow(self.taskbar_window, win32con.SW_HIDE)
            self.taskbar_hidden = True
            print("Taskbar hidden on startup")
    
    def run(self):
        """Run the application"""
        print("Window Tagger running in background.")
        print("Press Ctrl+C to exit.")
        
        # Keep the script running
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("Exiting...")
            # Show taskbar before exiting
            if self.taskbar_hidden and self.taskbar_window:
                win32gui.ShowWindow(self.taskbar_window, win32con.SW_SHOW) 