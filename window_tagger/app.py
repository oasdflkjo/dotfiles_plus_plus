import json
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import win32gui
import win32process
import win32api
import win32con

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'tag_definitions.json')
ZONES_PATH = os.path.join(os.path.dirname(__file__), 'zones.json')
OFFSETS_PATH = os.path.join(os.path.dirname(__file__), 'tag_offsets.json')

def load_definitions():
    if not os.path.exists(CONFIG_PATH):
        return []
        
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure the data is a list
            if isinstance(data, list):
                return data
            else:
                print(f"Warning: {CONFIG_PATH} does not contain a valid list. Using empty list.")
                return []
    except json.JSONDecodeError:
        print(f"Warning: {CONFIG_PATH} contains invalid JSON. Using empty list.")
        return []
    except Exception as e:
        print(f"Error loading definitions: {e}")
        return []

def save_definitions(definitions):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(definitions, f, indent=2)

def load_zones():
    if not os.path.exists(ZONES_PATH):
        # Create default centered zone
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
        os.makedirs(os.path.dirname(ZONES_PATH), exist_ok=True)
        with open(ZONES_PATH, 'w', encoding='utf-8') as f:
            json.dump(zones, f, indent=2)
            
        return zones
    
    with open(ZONES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_offsets():
    if not os.path.exists(OFFSETS_PATH):
        return {}
    
    try:
        with open(OFFSETS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure the data is a dictionary
            if isinstance(data, dict):
                return data
            else:
                print(f"Warning: {OFFSETS_PATH} does not contain a valid dictionary. Using empty dict.")
                return {}
    except json.JSONDecodeError:
        print(f"Warning: {OFFSETS_PATH} contains invalid JSON. Using empty dict.")
        return {}
    except Exception as e:
        print(f"Error loading offsets: {e}")
        return {}

def save_offset(tag_name, x_offset, y_offset, width_offset, height_offset):
    offsets = load_offsets()
    
    # Add or update the offset for this tag
    offsets[tag_name] = {
        "x_offset": x_offset,
        "y_offset": y_offset,
        "width_offset": width_offset,
        "height_offset": height_offset
    }
    
    # Save the offsets
    os.makedirs(os.path.dirname(OFFSETS_PATH), exist_ok=True)
    with open(OFFSETS_PATH, 'w', encoding='utf-8') as f:
        json.dump(offsets, f, indent=2)

def get_process_name(hwnd):
    try:
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        h_process = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
            False,
            pid
        )
        if h_process:
            try:
                process_path = win32process.GetModuleFileNameEx(h_process, 0)
                return os.path.basename(process_path).lower()
            finally:
                win32api.CloseHandle(h_process)
    except:
        pass
    return ""

def get_active_window_info():
    hwnd = win32gui.GetForegroundWindow()
    window_title = win32gui.GetWindowText(hwnd)
    class_name = win32gui.GetClassName(hwnd)
    process_name = get_process_name(hwnd)
    
    # Get window dimensions
    rect = win32gui.GetWindowRect(hwnd)
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    
    return {
        "hwnd": hwnd,
        "window_title": window_title,
        "class_name": class_name,
        "process_name": process_name,
        "width": width,
        "height": height,
        "x": rect[0],
        "y": rect[1]
    }

def position_window_with_offsets(hwnd, base_x, base_y, base_width, base_height, x_offset, y_offset, width_offset, height_offset):
    """Position window with the given base values and offsets"""
    # Apply offsets to base values
    x = base_x + x_offset
    y = base_y + y_offset
    width = base_width + width_offset
    height = base_height + height_offset
    
    # Ensure minimum dimensions
    width = max(100, width)
    height = max(100, height)
    
    # Set window position and size
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        x, y,
        width, height,
        win32con.SWP_SHOWWINDOW
    )
    
    return x, y, width, height

def find_matching_tag(window_info):
    """Find a tag that matches the given window information"""
    definitions = load_definitions()
    
    # Get window properties
    process_name = window_info.get("process_name", "")
    class_name = window_info.get("class_name", "")
    window_title = window_info.get("window_title", "")
    
    # Try to find a matching tag
    for tag in definitions:
        # Check process name if specified
        if tag.get("process_name") and tag.get("process_name") != process_name:
            continue
            
        # Check class name if specified
        if tag.get("class_name") and tag.get("class_name") != class_name:
            continue
            
        # Check window title if specified (partial match)
        if tag.get("window_title") and tag.get("window_title") not in window_title:
            continue
            
        # If we get here, all specified criteria match
        return tag
    
    # No match found
    return None

def center_active_window_with_tag():
    """Center the active window using its tag definition if found"""
    # Get active window info
    window_info = get_active_window_info()
    
    # Try to find a matching tag
    tag = find_matching_tag(window_info)
    
    if not tag:
        print("No matching tag found for the active window.")
        # Flash the window to indicate error
        win32gui.FlashWindow(window_info["hwnd"], True)
        return False
    
    # Get the tag name
    tag_name = tag.get("name")
    
    # Load zones and offsets
    zones = load_zones()
    offsets = load_offsets()
    
    # Get the centered zone
    centered = zones.get("centered", {})
    
    # Get offsets for this tag
    tag_offsets = offsets.get(tag_name, {})
    x_offset = tag_offsets.get("x_offset", 0)
    y_offset = tag_offsets.get("y_offset", 0)
    width_offset = tag_offsets.get("width_offset", 0)
    height_offset = tag_offsets.get("height_offset", 0)
    
    # Apply centering with offsets
    position_window_with_offsets(
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

def on_win_c_hotkey():
    """Handler for Win+C hotkey"""
    try:
        center_active_window_with_tag()
    except Exception as e:
        print(f"Error in Win+C handler: {e}")

class TaggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Tagger")
        self.root.geometry("500x600")  # Made taller for additional controls
        self.definitions = load_definitions()
        
        # Store the base dimensions and position (from centered zone)
        self.zones = load_zones()
        centered = self.zones.get("centered", {})
        self.base_x = centered.get("x", 0)
        self.base_y = centered.get("y", 0)
        self.base_width = centered.get("width", 0)
        self.base_height = centered.get("height", 0)
        
        # Get current window info
        self.current_window = get_active_window_info()
        
        # Get application name for auto-filling tag field
        self.app_name = self.get_app_name_from_process()
        
        # Initialize offsets
        self.x_offset = 0
        self.y_offset = 0
        self.width_offset = 0
        self.height_offset = 0
        
        # Try to load existing tag information
        self.load_existing_tag()
        
        # Setup GUI
        self.setup_gui()
        
    def get_app_name_from_process(self):
        """Extract a reasonable app name from the process name"""
        process = self.current_window["process_name"].lower()
        if not process:
            return ""
            
        # Remove .exe extension if present
        if process.endswith(".exe"):
            process = process[:-4]
            
        return process
        
    def setup_gui(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Current window info section
        ttk.Label(frame, text="Current Window:", font=("", 12, "bold")).grid(column=0, row=0, sticky=tk.W, pady=(0, 10))
        
        info_frame = ttk.LabelFrame(frame, text="Window Information")
        info_frame.grid(column=0, row=1, sticky=(tk.W, tk.E), padx=5, pady=5, columnspan=2)
        
        # Process name
        ttk.Label(info_frame, text="Process Name:").grid(column=0, row=0, sticky=tk.W, padx=5, pady=2)
        self.process_label = ttk.Label(info_frame, text=self.current_window["process_name"])
        self.process_label.grid(column=1, row=0, sticky=tk.W, padx=5, pady=2)
        self.process_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(info_frame, text="Use for matching", variable=self.process_var).grid(column=2, row=0, padx=5)
        
        # Class name
        ttk.Label(info_frame, text="Class Name:").grid(column=0, row=1, sticky=tk.W, padx=5, pady=2)
        self.class_label = ttk.Label(info_frame, text=self.current_window["class_name"])
        self.class_label.grid(column=1, row=1, sticky=tk.W, padx=5, pady=2)
        self.class_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(info_frame, text="Use for matching", variable=self.class_var).grid(column=2, row=1, padx=5)
        
        # Window title
        ttk.Label(info_frame, text="Window Title:").grid(column=0, row=2, sticky=tk.W, padx=5, pady=2)
        self.title_label = ttk.Label(info_frame, text=self.current_window["window_title"])
        self.title_label.grid(column=1, row=2, sticky=tk.W, padx=5, pady=2)
        self.title_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(info_frame, text="Use for matching", variable=self.title_var).grid(column=2, row=2, padx=5)
        
        # Current offsets
        ttk.Label(info_frame, text="Offsets:").grid(column=0, row=3, sticky=tk.W, padx=5, pady=2)
        self.offsets_label = ttk.Label(info_frame, text="X: 0, Y: 0, Width: 0, Height: 0")
        self.offsets_label.grid(column=1, row=3, sticky=tk.W, padx=5, pady=2)
        
        # Tag name section
        tag_frame = ttk.Frame(frame)
        tag_frame.grid(column=0, row=2, sticky=(tk.W, tk.E), padx=5, pady=15, columnspan=2)
        
        ttk.Label(tag_frame, text="Tag Name:").grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        self.tag_name = tk.StringVar(value=self.app_name)  # Pre-fill with app name
        self.tag_entry = ttk.Entry(tag_frame, textvariable=self.tag_name, width=25)
        self.tag_entry.grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Window positioning and sizing buttons
        position_frame = ttk.LabelFrame(frame, text="Window Adjustments")
        position_frame.grid(column=0, row=3, sticky=(tk.W, tk.E), padx=5, pady=5, columnspan=2)
        
        # Center window button
        ttk.Button(
            position_frame, 
            text="Center Window", 
            command=self.center_current_window
        ).grid(column=0, row=0, padx=5, pady=5, columnspan=2)
        
        # X position adjustments
        x_frame = ttk.Frame(position_frame)
        x_frame.grid(column=0, row=1, padx=5, pady=5, columnspan=2)
        
        ttk.Label(x_frame, text="X Position:").grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(x_frame, text="-1", command=lambda: self.adjust_offset("x", -1)).grid(column=1, row=0, padx=5)
        ttk.Button(x_frame, text="+1", command=lambda: self.adjust_offset("x", 1)).grid(column=2, row=0, padx=5)
        
        # Y position adjustments
        y_frame = ttk.Frame(position_frame)
        y_frame.grid(column=0, row=2, padx=5, pady=5, columnspan=2)
        
        ttk.Label(y_frame, text="Y Position:").grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(y_frame, text="-1", command=lambda: self.adjust_offset("y", -1)).grid(column=1, row=0, padx=5)
        ttk.Button(y_frame, text="+1", command=lambda: self.adjust_offset("y", 1)).grid(column=2, row=0, padx=5)
        
        # Width adjustments
        width_frame = ttk.Frame(position_frame)
        width_frame.grid(column=0, row=3, padx=5, pady=5, columnspan=2)
        
        ttk.Label(width_frame, text="Width:").grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(width_frame, text="-1", command=lambda: self.adjust_offset("width", -1)).grid(column=1, row=0, padx=5)
        ttk.Button(width_frame, text="+1", command=lambda: self.adjust_offset("width", 1)).grid(column=2, row=0, padx=5)
        
        # Height adjustments
        height_frame = ttk.Frame(position_frame)
        height_frame.grid(column=0, row=4, padx=5, pady=5, columnspan=2)
        
        ttk.Label(height_frame, text="Height:").grid(column=0, row=0, padx=5, pady=5)
        ttk.Button(height_frame, text="-1", command=lambda: self.adjust_offset("height", -1)).grid(column=1, row=0, padx=5)
        ttk.Button(height_frame, text="+1", command=lambda: self.adjust_offset("height", 1)).grid(column=2, row=0, padx=5)
        
        # Reset button
        ttk.Button(
            position_frame,
            text="Reset Offsets",
            command=self.reset_offsets
        ).grid(column=0, row=5, padx=5, pady=5, columnspan=2)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(column=0, row=4, sticky=(tk.E), padx=5, pady=5, columnspan=2)
        
        ttk.Button(button_frame, text="Save Tag", command=self.save_tag).grid(column=0, row=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.root.destroy).grid(column=1, row=0, padx=5)
    
    def center_current_window(self):
        """Center the window using base values and current offsets"""
        # Get the centered zone
        centered = self.zones.get("centered", {})
        
        # Apply current offsets (will be 0 if reset or first time)
        new_x, new_y, new_width, new_height = position_window_with_offsets(
            self.current_window["hwnd"],
            self.base_x,
            self.base_y,
            self.base_width,
            self.base_height,
            self.x_offset,
            self.y_offset,
            self.width_offset,
            self.height_offset
        )
        
        # Flash the window to indicate success
        win32gui.FlashWindow(self.current_window["hwnd"], True)
        
        # Update the current window info
        self.current_window = get_active_window_info()
        
        # Save offsets for current application
        self.save_current_offsets()
    
    def adjust_offset(self, offset_type, delta):
        """Adjust a specific offset and recenter the window"""
        # Update the appropriate offset
        if offset_type == "x":
            self.x_offset += delta
        elif offset_type == "y":
            self.y_offset += delta
        elif offset_type == "width":
            self.width_offset += delta
        elif offset_type == "height":
            self.height_offset += delta
        
        # Update the offsets label
        self.update_offsets_label()
        
        # Recenter window with new offsets
        self.center_current_window()
    
    def reset_offsets(self):
        """Reset offsets to zero and recenter window"""
        # Reset all offsets
        self.x_offset = 0
        self.y_offset = 0
        self.width_offset = 0
        self.height_offset = 0
        
        # Update the offsets label
        self.update_offsets_label()
        
        # Recenter window with reset offsets
        self.center_current_window()
    
    def update_offsets_label(self):
        """Update the offsets label"""
        self.offsets_label.config(
            text=f"X: {self.x_offset}, Y: {self.y_offset}, Width: {self.width_offset}, Height: {self.height_offset}"
        )
    
    def save_current_offsets(self):
        """Save current offsets for the app"""
        tag_name = self.tag_name.get()
        
        if not tag_name:
            # Use process name if no tag name is provided
            tag_name = self.app_name
            
        if tag_name:
            # Save window offsets to tag_offsets.json
            save_offset(
                tag_name,
                self.x_offset,
                self.y_offset,
                self.width_offset,
                self.height_offset
            )
    
    def save_tag(self):
        tag_name = self.tag_name.get()
        
        if not tag_name:
            # Show error if no tag name
            self.show_error("Tag name is required")
            return
            
        tag_definition = {
            "name": tag_name
        }
        
        if self.process_var.get():
            tag_definition["process_name"] = self.current_window["process_name"]
        
        if self.class_var.get():
            tag_definition["class_name"] = self.current_window["class_name"]
        
        if self.title_var.get():
            tag_definition["window_title"] = self.current_window["window_title"]
        
        # Save window offsets to tag_offsets.json
        save_offset(
            tag_name,
            self.x_offset,
            self.y_offset,
            self.width_offset,
            self.height_offset
        )
        
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
        
        # Save definitions
        save_definitions(self.definitions)
        self.root.destroy()
    
    def show_error(self, message):
        """Show an error message"""
        messagebox.showerror("Error", message)
    
    def load_existing_tag(self):
        """Try to find and load existing tag information for this window"""
        # First try to match based on process name
        process_name = self.current_window.get("process_name", "")
        if not process_name:
            return
            
        # Check if any existing tag matches this process
        potential_tag = None
        for tag in self.definitions:
            if tag.get("process_name") == process_name:
                # Found a process match, check if class and title also match if specified
                class_match = True
                if tag.get("class_name") and tag.get("class_name") != self.current_window.get("class_name", ""):
                    class_match = False
                
                title_match = True
                if tag.get("window_title") and tag.get("window_title") not in self.current_window.get("window_title", ""):
                    title_match = False
                
                if class_match and title_match:
                    potential_tag = tag
                    break
        
        # If we found a matching tag, load its information
        if potential_tag:
            tag_name = potential_tag.get("name", "")
            if tag_name:
                # Set the tag name
                self.app_name = tag_name
                
                # Load offsets if they exist
                offsets = load_offsets().get(tag_name, {})
                self.x_offset = offsets.get("x_offset", 0)
                self.y_offset = offsets.get("y_offset", 0)
                self.width_offset = offsets.get("width_offset", 0)
                self.height_offset = offsets.get("height_offset", 0)

def on_hotkey():
    # Create a new tkinter window when hotkey is pressed
    root = tk.Tk()
    app = TaggerApp(root)
    root.mainloop()

def register_hotkeys():
    """Register all application hotkeys"""
    # Register Ctrl+Alt+T for tagging window
    keyboard.add_hotkey('ctrl+alt+t', on_hotkey)
    
    # Register Win+C for centering active window
    keyboard.add_hotkey('win+c', on_win_c_hotkey)
    
    print("Hotkeys registered:")
    print("  Ctrl+Alt+T: Open tagging interface")
    print("  Win+C: Center active window (if it has a tag definition)")

def main():
    # Register hotkeys
    register_hotkeys()
    
    print("Window Tagger running in background.")
    print("Press Ctrl+C to exit.")
    
    # Keep the script running
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main() 