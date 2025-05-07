import tkinter as tk
from tkinter import ttk, messagebox
import win32gui
import win32api
import win32con

class TaggerGUI:
    def __init__(self, root, app_interface):
        self.root = root
        self.app_interface = app_interface
        self.root.title("Window Tagger")
        self.root.geometry("500x600")
        
        # Get current window info from app interface
        self.current_window = app_interface.get_active_window_info()
        
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
        centered = self.app_interface.get_centered_zone()
        
        # Apply current offsets (will be 0 if reset or first time)
        new_x, new_y, new_width, new_height = self.app_interface.position_window_with_offsets(
            self.current_window["hwnd"],
            centered.get("x", 0),
            centered.get("y", 0),
            centered.get("width", 0),
            centered.get("height", 0),
            self.x_offset,
            self.y_offset,
            self.width_offset,
            self.height_offset
        )
        
        # Flash the window to indicate success
        win32gui.FlashWindow(self.current_window["hwnd"], True)
        
        # Update the current window info
        self.current_window = self.app_interface.get_active_window_info()
        
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
            # Save window offsets
            self.app_interface.save_offset(
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
        
        # Save window offsets
        self.app_interface.save_offset(
            tag_name,
            self.x_offset,
            self.y_offset,
            self.width_offset,
            self.height_offset
        )
        
        # Save tag definition
        self.app_interface.save_tag_definition(tag_definition)
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
            
        # Get existing tag and offsets from app interface
        tag_info = self.app_interface.get_existing_tag_info(self.current_window)
        
        if tag_info:
            tag_name, offsets = tag_info
            # Set the tag name
            self.app_name = tag_name
            
            # Load offsets
            self.x_offset = offsets.get("x_offset", 0)
            self.y_offset = offsets.get("y_offset", 0)
            self.width_offset = offsets.get("width_offset", 0)
            self.height_offset = offsets.get("height_offset", 0) 