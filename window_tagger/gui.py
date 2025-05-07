import tkinter as tk
from tkinter import ttk
from tagger_interface import TaggerInterface

class TaggerGUI:
    def __init__(self, root: tk.Tk, tagger: TaggerInterface):
        self.root = root
        self.tagger = tagger
        
        self.root.title("Window Tagger")
        self.root.geometry("400x500")
        
        # Get active window info
        self.window_info = self.tagger.get_active_window_info()
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Window info section
        ttk.Label(main_frame, text="Active Window Info", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        info_frame = ttk.LabelFrame(main_frame, text="Window Details", padding="5")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Process name
        ttk.Label(info_frame, text="Process:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=self.window_info["process_name"]).grid(row=0, column=1, sticky=tk.W)
        
        # Window title
        ttk.Label(info_frame, text="Title:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=self.window_info["window_title"]).grid(row=1, column=1, sticky=tk.W)
        
        # Class name
        ttk.Label(info_frame, text="Class:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=self.window_info["class_name"]).grid(row=2, column=1, sticky=tk.W)
        
        # Tag definition section
        tag_frame = ttk.LabelFrame(main_frame, text="Tag Definition", padding="5")
        tag_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Tag name
        ttk.Label(tag_frame, text="Tag Name:").grid(row=0, column=0, sticky=tk.W)
        self.tag_name_var = tk.StringVar()
        self.tag_name_entry = ttk.Entry(tag_frame, textvariable=self.tag_name_var)
        self.tag_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Checkboxes for matching criteria
        self.use_process_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tag_frame, text="Match Process Name", variable=self.use_process_var).grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        self.use_class_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tag_frame, text="Match Class Name", variable=self.use_class_var).grid(row=2, column=0, columnspan=2, sticky=tk.W)
        
        self.use_title_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tag_frame, text="Match Window Title", variable=self.use_title_var).grid(row=3, column=0, columnspan=2, sticky=tk.W)
        
        # Offset section
        offset_frame = ttk.LabelFrame(main_frame, text="Window Offsets", padding="5")
        offset_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # X offset
        ttk.Label(offset_frame, text="X Offset:").grid(row=0, column=0, sticky=tk.W)
        self.x_offset_var = tk.StringVar(value="0")
        ttk.Entry(offset_frame, textvariable=self.x_offset_var, width=10).grid(row=0, column=1, sticky=tk.W)
        
        # Y offset
        ttk.Label(offset_frame, text="Y Offset:").grid(row=1, column=0, sticky=tk.W)
        self.y_offset_var = tk.StringVar(value="0")
        ttk.Entry(offset_frame, textvariable=self.y_offset_var, width=10).grid(row=1, column=1, sticky=tk.W)
        
        # Width offset
        ttk.Label(offset_frame, text="Width Offset:").grid(row=2, column=0, sticky=tk.W)
        self.width_offset_var = tk.StringVar(value="0")
        ttk.Entry(offset_frame, textvariable=self.width_offset_var, width=10).grid(row=2, column=1, sticky=tk.W)
        
        # Height offset
        ttk.Label(offset_frame, text="Height Offset:").grid(row=3, column=0, sticky=tk.W)
        self.height_offset_var = tk.StringVar(value="0")
        ttk.Entry(offset_frame, textvariable=self.height_offset_var, width=10).grid(row=3, column=1, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Save Tag", command=self.save_tag).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Close", command=self.root.destroy).grid(row=0, column=1, padx=5)
        
        # Load existing tag info if available
        self.load_existing_tag_info()
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        tag_frame.columnconfigure(1, weight=1)
        offset_frame.columnconfigure(1, weight=1)
        
    def load_existing_tag_info(self):
        """Load existing tag information if available"""
        tag_info = self.tagger.get_existing_tag_info(self.window_info)
        if tag_info:
            tag_name, offsets = tag_info
            self.tag_name_var.set(tag_name)
            self.x_offset_var.set(str(offsets.get("x_offset", 0)))
            self.y_offset_var.set(str(offsets.get("y_offset", 0)))
            self.width_offset_var.set(str(offsets.get("width_offset", 0)))
            self.height_offset_var.set(str(offsets.get("height_offset", 0)))
    
    def save_tag(self):
        """Save the tag definition and offsets"""
        tag_name = self.tag_name_var.get().strip()
        if not tag_name:
            print("Please enter a tag name")
            return
        
        # Create tag definition
        tag_definition = {
            "name": tag_name,
            "process_name": self.window_info["process_name"] if self.use_process_var.get() else None,
            "class_name": self.window_info["class_name"] if self.use_class_var.get() else None,
            "window_title": self.window_info["window_title"] if self.use_title_var.get() else None
        }
        
        # Save tag definition
        self.tagger.save_tag_definition(tag_definition)
        
        # Save offsets
        try:
            x_offset = int(self.x_offset_var.get())
            y_offset = int(self.y_offset_var.get())
            width_offset = int(self.width_offset_var.get())
            height_offset = int(self.height_offset_var.get())
            
            self.tagger.save_offset(tag_name, x_offset, y_offset, width_offset, height_offset)
            
            print(f"Tag '{tag_name}' saved successfully")
            self.root.destroy()
            
        except ValueError:
            print("Please enter valid numbers for offsets") 