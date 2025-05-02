import tkinter as tk
from tkinter import ttk
import json
import os
import win32gui
import win32con
import threading
import time
from pathlib import Path

# Import our window scanner module
import window_scanner


class WindowResizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Resizer")
        self.root.geometry("650x550")
        self.root.resizable(True, True)

        # Make window stay on top
        self.root.attributes("-topmost", True)

        # Store current windows and configs
        self.windows = []
        self.window_configs = {}
        self.selected_window = None

        # Load or create config file
        self.config_path = Path("defined_window_positions.json")
        self.load_config()

        # Create the UI
        self.create_widgets()

        # Initial window scan
        self.scan_windows()

    def create_widgets(self):
        """Create all the GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Window selection section
        selection_frame = ttk.LabelFrame(
            main_frame, text="Window Selection", padding="10"
        )
        selection_frame.pack(fill=tk.X, pady=5)

        # Refresh button and window selector
        refresh_btn = ttk.Button(
            selection_frame, text="Refresh Windows", command=self.scan_windows
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        self.window_selector = ttk.Combobox(selection_frame, width=50)
        self.window_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.window_selector.bind("<<ComboboxSelected>>", self.on_window_selected)

        # Window information section
        info_frame = ttk.LabelFrame(main_frame, text="Window Information", padding="10")
        info_frame.pack(fill=tk.X, pady=10)

        # Display window details
        self.window_info = ttk.Label(info_frame, text="Select a window to view details")
        self.window_info.pack(fill=tk.X)

        # Position editing section
        position_frame = ttk.LabelFrame(
            main_frame, text="Position & Size", padding="10"
        )
        position_frame.pack(fill=tk.X, pady=10)

        # Create a grid for inputs with +/- buttons
        # Row 1: X position with +/- buttons
        ttk.Label(position_frame, text="X Position:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )

        x_frame = ttk.Frame(position_frame)
        x_frame.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(
            x_frame, text="-", width=2, command=lambda: self.adjust_position("x", -1)
        ).pack(side=tk.LEFT)
        self.x_position = ttk.Entry(x_frame, width=8)
        self.x_position.pack(side=tk.LEFT, padx=2)
        ttk.Button(
            x_frame, text="+", width=2, command=lambda: self.adjust_position("x", 1)
        ).pack(side=tk.LEFT)

        # Row 1 (cont): Y position with +/- buttons
        ttk.Label(position_frame, text="Y Position:").grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )

        y_frame = ttk.Frame(position_frame)
        y_frame.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(
            y_frame, text="-", width=2, command=lambda: self.adjust_position("y", -1)
        ).pack(side=tk.LEFT)
        self.y_position = ttk.Entry(y_frame, width=8)
        self.y_position.pack(side=tk.LEFT, padx=2)
        ttk.Button(
            y_frame, text="+", width=2, command=lambda: self.adjust_position("y", 1)
        ).pack(side=tk.LEFT)

        # Row 2: Width with +/- buttons
        ttk.Label(position_frame, text="Width:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )

        width_frame = ttk.Frame(position_frame)
        width_frame.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(
            width_frame,
            text="-",
            width=2,
            command=lambda: self.adjust_position("width", -1),
        ).pack(side=tk.LEFT)
        self.width = ttk.Entry(width_frame, width=8)
        self.width.pack(side=tk.LEFT, padx=2)
        ttk.Button(
            width_frame,
            text="+",
            width=2,
            command=lambda: self.adjust_position("width", 1),
        ).pack(side=tk.LEFT)

        # Row 2 (cont): Height with +/- buttons
        ttk.Label(position_frame, text="Height:").grid(
            row=1, column=2, sticky=tk.W, padx=5, pady=5
        )

        height_frame = ttk.Frame(position_frame)
        height_frame.grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(
            height_frame,
            text="-",
            width=2,
            command=lambda: self.adjust_position("height", -1),
        ).pack(side=tk.LEFT)
        self.height = ttk.Entry(height_frame, width=8)
        self.height.pack(side=tk.LEFT, padx=2)
        ttk.Button(
            height_frame,
            text="+",
            width=2,
            command=lambda: self.adjust_position("height", 1),
        ).pack(side=tk.LEFT)

        # Actions section
        actions_frame = ttk.Frame(main_frame, padding="10")
        actions_frame.pack(fill=tk.X, pady=10)

        # Action buttons
        ttk.Button(
            actions_frame, text="Apply to Window", command=self.apply_to_window
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            actions_frame, text="Save Position", command=self.save_window_position
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            actions_frame, text="Remove from Config", command=self.remove_window_config
        ).pack(side=tk.LEFT, padx=5)

        # Always on top toggle
        self.always_on_top_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            actions_frame,
            text="Always on Top",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
        ).pack(side=tk.RIGHT, padx=5)

        # Save all button at the bottom
        ttk.Button(
            main_frame, text="Save All Settings to JSON", command=self.save_config
        ).pack(pady=10)

        # Saved configurations list
        configs_frame = ttk.LabelFrame(
            main_frame, text="Saved Window Configurations", padding="10"
        )
        configs_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Scrollable list of saved configs
        scrollbar = ttk.Scrollbar(configs_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.configs_list = tk.Listbox(
            configs_frame, height=5, yscrollcommand=scrollbar.set
        )
        self.configs_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.configs_list.yview)

        # Select config when clicked
        self.configs_list.bind("<<ListboxSelect>>", self.on_config_selected)

    def toggle_always_on_top(self):
        """Toggle the always-on-top state of the window"""
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def refresh_with_preserved_selection(self, current_selection):
        """Refresh window list while preserving the current selection"""
        # Scan windows
        self.windows = window_scanner.scan_windows()

        # Update dropdown options
        options = []
        for window in self.windows:
            process_name = window.get("process_name", "")
            title = window.get("title", "")
            if title:
                display_text = f"{process_name}: {title}"
                if len(display_text) > 70:
                    display_text = display_text[:67] + "..."
                options.append(display_text)

        # Update the dropdown values
        self.window_selector["values"] = options

        # Restore the selection if possible
        if options and current_selection < len(options):
            self.window_selector.current(current_selection)
            self.on_window_selected(None)

        # Update saved configs list
        self.update_configs_list()

    def adjust_position(self, field, delta):
        """Adjust a position field by a delta and apply the change"""
        if not self.selected_window:
            return

        try:
            # Store current selection index
            current_selection = self.window_selector.current()

            # Get the current value
            if field == "x":
                entry = self.x_position
            elif field == "y":
                entry = self.y_position
            elif field == "width":
                entry = self.width
            elif field == "height":
                entry = self.height
            else:
                return

            current_value = int(entry.get())

            # Calculate the new value
            new_value = current_value + delta

            # Update the entry
            entry.delete(0, tk.END)
            entry.insert(0, str(new_value))

            # Get all values from input fields
            x = int(self.x_position.get())
            y = int(self.y_position.get())
            width = int(self.width.get())
            height = int(self.height.get())

            # Get window handle
            hwnd = self.selected_window.get("hwnd")

            if hwnd:
                # Set window position
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,  # Put window at top of z-order
                    x,
                    y,
                    width,
                    height,
                    win32con.SWP_SHOWWINDOW,
                )

                # Update the stored position
                if "position" in self.selected_window:
                    self.selected_window["position"]["x"] = x
                    self.selected_window["position"]["y"] = y
                    self.selected_window["position"]["width"] = width
                    self.selected_window["position"]["height"] = height

                # Refresh after a short delay with preserved selection
                threading.Timer(
                    0.5,
                    lambda: self.refresh_with_preserved_selection(current_selection),
                ).start()
        except Exception as e:
            print(f"Error adjusting {field}: {e}")

    def scan_windows(self):
        """Scan for active windows and update the dropdown"""
        self.windows = window_scanner.scan_windows()

        # Create dropdown options from window titles
        options = []
        for window in self.windows:
            process_name = window.get("process_name", "")
            title = window.get("title", "")
            if title:
                display_text = f"{process_name}: {title}"
                if len(display_text) > 70:
                    display_text = display_text[:67] + "..."
                options.append(display_text)

        # Update the dropdown
        self.window_selector["values"] = options
        if options:
            self.window_selector.current(0)
            self.on_window_selected(None)

        # Update saved configs list
        self.update_configs_list()

    def on_window_selected(self, event):
        """Handle window selection from dropdown"""
        selection = self.window_selector.current()
        if selection >= 0 and selection < len(self.windows):
            self.selected_window = self.windows[selection]

            # Update the information display
            window_class = self.selected_window.get("class", "Unknown")
            process_name = self.selected_window.get("process_name", "Unknown")
            pid = self.selected_window.get("pid", "Unknown")

            info_text = f"Process: {process_name}\nClass: {window_class}\nPID: {pid}"
            self.window_info.config(text=info_text)

            # Update position fields
            position = self.selected_window.get("position", {})
            self.x_position.delete(0, tk.END)
            self.x_position.insert(0, position.get("x", ""))

            self.y_position.delete(0, tk.END)
            self.y_position.insert(0, position.get("y", ""))

            self.width.delete(0, tk.END)
            self.width.insert(0, position.get("width", ""))

            self.height.delete(0, tk.END)
            self.height.insert(0, position.get("height", ""))

    def apply_to_window(self):
        """Apply the current position settings to the selected window"""
        if not self.selected_window:
            return

        try:
            # Store current selection index
            current_selection = self.window_selector.current()

            # Get values from input fields
            x = int(self.x_position.get())
            y = int(self.y_position.get())
            width = int(self.width.get())
            height = int(self.height.get())

            # Get window handle
            hwnd = self.selected_window.get("hwnd")

            if hwnd:
                # Set window position
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,  # Put window at top of z-order
                    x,
                    y,
                    width,
                    height,
                    win32con.SWP_SHOWWINDOW,
                )

                # Update the stored position
                if "position" in self.selected_window:
                    self.selected_window["position"]["x"] = x
                    self.selected_window["position"]["y"] = y
                    self.selected_window["position"]["width"] = width
                    self.selected_window["position"]["height"] = height

                # Refresh after a short delay with preserved selection
                threading.Timer(
                    0.5,
                    lambda: self.refresh_with_preserved_selection(current_selection),
                ).start()
        except Exception as e:
            print(f"Error applying window position: {e}")

    def save_window_position(self):
        """Save the current window position to the configuration"""
        if not self.selected_window:
            return

        try:
            process_name = self.selected_window.get("process_name", "")
            window_class = self.selected_window.get("class", "")

            if not process_name or not window_class:
                return

            # Create a unique identifier using both process name and window class
            # Remove .exe extension for cleaner naming
            process_name = process_name.replace(".exe", "")
            config_key = f"{process_name}|{window_class}"

            # Get values from input fields
            x = int(self.x_position.get())
            y = int(self.y_position.get())
            width = int(self.width.get())
            height = int(self.height.get())

            # Save to configuration with process and class information
            self.window_configs[config_key] = {
                "process": process_name,
                "class": window_class,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }

            # Update the config list
            self.update_configs_list()

            # Save to file
            self.save_config()
        except Exception as e:
            print(f"Error saving window position: {e}")

    def remove_window_config(self):
        """Remove the current window from saved configurations"""
        if not self.selected_window:
            return

        process_name = self.selected_window.get("process_name", "").replace(".exe", "")
        window_class = self.selected_window.get("class", "")
        config_key = f"{process_name}|{window_class}"

        if config_key in self.window_configs:
            del self.window_configs[config_key]
            self.update_configs_list()
            self.save_config()

    def load_config(self):
        """Load window positions from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.window_configs = json.load(f)
                print(f"Loaded configurations for {len(self.window_configs)} windows")
            else:
                # Create default config
                self.window_configs = {}
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.window_configs = {}

    def save_config(self):
        """Save window positions to JSON file"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.window_configs, f, indent=2, ensure_ascii=False)
            print(f"Saved configurations for {len(self.window_configs)} windows")
        except Exception as e:
            print(f"Error saving config: {e}")

    def update_configs_list(self):
        """Update the list of saved configurations"""
        self.configs_list.delete(0, tk.END)
        for config_key, config in self.window_configs.items():
            # Check if this is the new or old format
            if isinstance(config, dict) and "process" in config and "class" in config:
                # New format with process and class
                process = config.get("process", "")
                window_class = config.get("class", "")
                size_info = f"{config['width']}x{config['height']}"
                pos_info = f"({config['x']},{config['y']})"
                display = f"{process} ({window_class}): {size_info} at {pos_info}"
            else:
                # Old format or custom entry
                parts = config_key.split("|", 1)
                if len(parts) > 1:
                    process, window_class = parts
                    size_info = f"{config['width']}x{config['height']}"
                    pos_info = f"({config['x']},{config['y']})"
                    display = f"{process} ({window_class}): {size_info} at {pos_info}"
                else:
                    # Legacy format
                    app_name = config_key
                    size_info = f"{config['width']}x{config['height']}"
                    pos_info = f"({config['x']},{config['y']})"
                    display = f"{app_name}: {size_info} at {pos_info}"

            self.configs_list.insert(tk.END, display)

    def on_config_selected(self, event):
        """Handle selection of a saved configuration"""
        selection = self.configs_list.curselection()
        if not selection:
            return

        # Get the selected item index
        index = selection[0]

        # Get the config key at this index
        config_key = list(self.window_configs.keys())[index]
        config = self.window_configs[config_key]

        # Check if this is the new or old format
        if isinstance(config, dict) and "process" in config and "class" in config:
            # New format
            process_name = config.get("process", "")
            window_class = config.get("class", "")
        else:
            # Old format
            parts = config_key.split("|", 1)
            if len(parts) > 1:
                process_name, window_class = parts
            else:
                process_name = config_key
                window_class = None

        # Find if any current window matches this config
        found = False
        for i, window in enumerate(self.windows):
            current_process = window.get("process_name", "").replace(".exe", "")
            current_class = window.get("class", "")

            # Match based on both process name and window class if available
            if current_process == process_name:
                if window_class is None or current_class == window_class:
                    # Select this window in the dropdown
                    self.window_selector.current(i)
                    self.on_window_selected(None)

                    # Load the saved position
                    if config:
                        self.x_position.delete(0, tk.END)
                        self.x_position.insert(0, config.get("x", ""))

                        self.y_position.delete(0, tk.END)
                        self.y_position.insert(0, config.get("y", ""))

                        self.width.delete(0, tk.END)
                        self.width.insert(0, config.get("width", ""))

                        self.height.delete(0, tk.END)
                        self.height.insert(0, config.get("height", ""))

                        found = True
                        break

        # If we didn't find a matching window, just show the config values
        if not found and config:
            info_text = f"No matching window found\nProcess: {process_name}"
            if window_class:
                info_text += f"\nClass: {window_class}"
            self.window_info.config(text=info_text)

            self.x_position.delete(0, tk.END)
            self.x_position.insert(0, config.get("x", ""))

            self.y_position.delete(0, tk.END)
            self.y_position.insert(0, config.get("y", ""))

            self.width.delete(0, tk.END)
            self.width.insert(0, config.get("width", ""))

            self.height.delete(0, tk.END)
            self.height.insert(0, config.get("height", ""))


def main():
    root = tk.Tk()
    app = WindowResizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
