import json
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk
import keyboard
import win32gui
import win32process
import win32api
import win32con

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'tag_definitions.json')

def load_definitions():
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_definitions(definitions):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(definitions, f, indent=2)

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
    
    return {
        "hwnd": hwnd,
        "window_title": window_title,
        "class_name": class_name,
        "process_name": process_name
    }

class TaggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Tagger")
        self.root.geometry("500x400")
        self.definitions = load_definitions()
        
        self.current_window = get_active_window_info()
        
        # Setup GUI
        self.setup_gui()
        
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
        
        # Tag name section
        tag_frame = ttk.Frame(frame)
        tag_frame.grid(column=0, row=2, sticky=(tk.W, tk.E), padx=5, pady=15, columnspan=2)
        
        ttk.Label(tag_frame, text="Tag Name:").grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        self.tag_name = tk.StringVar()
        self.tag_entry = ttk.Entry(tag_frame, textvariable=self.tag_name, width=25)
        self.tag_entry.grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(column=0, row=3, sticky=(tk.E), padx=5, pady=5, columnspan=2)
        
        ttk.Button(button_frame, text="Save Tag", command=self.save_tag).grid(column=0, row=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.root.destroy).grid(column=1, row=0, padx=5)
    
    def save_tag(self):
        tag_definition = {
            "name": self.tag_name.get()
        }
        
        if self.process_var.get():
            tag_definition["process_name"] = self.current_window["process_name"]
        
        if self.class_var.get():
            tag_definition["class_name"] = self.current_window["class_name"]
        
        if self.title_var.get():
            tag_definition["window_title"] = self.current_window["window_title"]
        
        # Add to definitions and save
        self.definitions.append(tag_definition)
        save_definitions(self.definitions)
        self.root.destroy()

def on_hotkey():
    # Create a new tkinter window when hotkey is pressed
    root = tk.Tk()
    app = TaggerApp(root)
    root.mainloop()

def main():
    # Register the hotkey
    keyboard.add_hotkey('ctrl+alt+t', on_hotkey)
    
    print("Window Tagger running in background. Press Ctrl+Alt+T to tag a window.")
    print("Press Ctrl+C to exit.")
    
    # Keep the script running
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main() 