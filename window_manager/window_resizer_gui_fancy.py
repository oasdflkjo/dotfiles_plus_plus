import tkinter as tk
from tkinter import ttk
import win32gui
import win32con
import win32process
import threading
import time
from pathlib import Path
import json

# Import our modules
import window_scanner
from window_zones import WindowZones


class FancyWindowResizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Fancy Window Resizer")
        self.root.geometry(
            "700x750"
        )  # Make the window a bit taller to accommodate new controls
        self.root.resizable(True, True)

        # Make window stay on top
        self.root.attributes("-topmost", True)

        # Initialize window data
        self.windows = []
        self.selected_window = None
        self.selected_zone = None

        # Initialize zones
        self.zones = WindowZones()

        # Create the UI
        self.create_widgets()

        # Initial window scan
        self.scan_windows()

    def create_widgets(self):
        """Create the GUI components"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Window selection section
        window_frame = ttk.LabelFrame(main_frame, text="Window Selection", padding="10")
        window_frame.pack(fill=tk.X, pady=5)

        # Refresh button and window selector
        refresh_btn = ttk.Button(
            window_frame, text="Refresh Windows", command=self.scan_windows
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        self.window_selector = ttk.Combobox(window_frame, width=50)
        self.window_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.window_selector.bind("<<ComboboxSelected>>", self.on_window_selected)

        # Window information section
        info_frame = ttk.LabelFrame(main_frame, text="Window Information", padding="10")
        info_frame.pack(fill=tk.X, pady=10)

        # Display window details
        self.window_info = ttk.Label(info_frame, text="Select a window to view details")
        self.window_info.pack(fill=tk.X)

        # Zone selection section
        zone_frame = ttk.LabelFrame(main_frame, text="Zone Selection", padding="10")
        zone_frame.pack(fill=tk.X, pady=10)

        # Get all zones
        zones = self.zones.get_all_zones()
        zone_names = []
        self.zone_keys = []

        # Create zone buttons
        btn_frame = ttk.Frame(zone_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        # Create a button for each zone
        for zone_key, zone_data in zones.items():
            zone_name = zone_data.get("name", zone_key)
            self.zone_keys.append(zone_key)

            # Create a button for this zone
            btn = ttk.Button(
                btn_frame,
                text=zone_name,
                command=lambda zk=zone_key: self.apply_zone(zk),
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Default Zone Settings section (NEW)
        zone_settings_frame = ttk.LabelFrame(
            main_frame, text="Default Zone Settings", padding="10"
        )
        zone_settings_frame.pack(fill=tk.X, pady=10)

        # Dropdown to select which zone to edit
        zone_select_frame = ttk.Frame(zone_settings_frame)
        zone_select_frame.pack(fill=tk.X, pady=5)

        ttk.Label(zone_select_frame, text="Select Zone:").pack(side=tk.LEFT, padx=5)
        self.zone_settings_selector = ttk.Combobox(zone_select_frame, width=20)
        self.zone_settings_selector.pack(side=tk.LEFT, padx=5)

        # Populate with zone names
        zone_options = []
        for zone_key, zone_data in zones.items():
            zone_options.append(zone_data.get("name", zone_key))
        self.zone_settings_selector["values"] = zone_options
        if zone_options:
            self.zone_settings_selector.current(0)

        self.zone_settings_selector.bind(
            "<<ComboboxSelected>>", self.load_zone_settings
        )

        # Zone parameter entries
        settings_fields_frame = ttk.Frame(zone_settings_frame)
        settings_fields_frame.pack(fill=tk.X, pady=5)

        # X Position
        ttk.Label(settings_fields_frame, text="X:").grid(
            row=0, column=0, padx=5, pady=2
        )
        self.zone_x = ttk.Entry(settings_fields_frame, width=6)
        self.zone_x.grid(row=0, column=1, padx=5, pady=2)

        # Y Position
        ttk.Label(settings_fields_frame, text="Y:").grid(
            row=0, column=2, padx=5, pady=2
        )
        self.zone_y = ttk.Entry(settings_fields_frame, width=6)
        self.zone_y.grid(row=0, column=3, padx=5, pady=2)

        # Width
        ttk.Label(settings_fields_frame, text="Width:").grid(
            row=1, column=0, padx=5, pady=2
        )
        self.zone_width = ttk.Entry(settings_fields_frame, width=6)
        self.zone_width.grid(row=1, column=1, padx=5, pady=2)

        # Height
        ttk.Label(settings_fields_frame, text="Height:").grid(
            row=1, column=2, padx=5, pady=2
        )
        self.zone_height = ttk.Entry(settings_fields_frame, width=6)
        self.zone_height.grid(row=1, column=3, padx=5, pady=2)

        # Action buttons for zone settings
        zone_settings_actions = ttk.Frame(zone_settings_frame)
        zone_settings_actions.pack(fill=tk.X, pady=5)

        ttk.Button(
            zone_settings_actions,
            text="Save Zone Settings",
            command=self.save_zone_settings,
        ).pack(side=tk.LEFT, padx=5)

        # Load the initial zone settings
        self.load_zone_settings(None)

        # Zone adjustment section
        adjust_frame = ttk.LabelFrame(main_frame, text="Fine Adjustments", padding="10")
        adjust_frame.pack(fill=tk.X, pady=10)

        # Position adjustments with +/- buttons
        # X Position
        x_frame = ttk.Frame(adjust_frame)
        x_frame.pack(fill=tk.X, pady=5)

        ttk.Label(x_frame, text="X Position:").pack(side=tk.LEFT, padx=5)
        ttk.Button(
            x_frame,
            text="-10",
            width=3,
            command=lambda: self.adjust_offset("x_offset", -10),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            x_frame,
            text="-1",
            width=2,
            command=lambda: self.adjust_offset("x_offset", -1),
        ).pack(side=tk.LEFT, padx=2)

        self.x_offset = ttk.Entry(x_frame, width=6)
        self.x_offset.pack(side=tk.LEFT, padx=5)
        self.x_offset.insert(0, "0")

        ttk.Button(
            x_frame,
            text="+1",
            width=2,
            command=lambda: self.adjust_offset("x_offset", 1),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            x_frame,
            text="+10",
            width=3,
            command=lambda: self.adjust_offset("x_offset", 10),
        ).pack(side=tk.LEFT, padx=2)

        # Y Position
        y_frame = ttk.Frame(adjust_frame)
        y_frame.pack(fill=tk.X, pady=5)

        ttk.Label(y_frame, text="Y Position:").pack(side=tk.LEFT, padx=5)
        ttk.Button(
            y_frame,
            text="-10",
            width=3,
            command=lambda: self.adjust_offset("y_offset", -10),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            y_frame,
            text="-1",
            width=2,
            command=lambda: self.adjust_offset("y_offset", -1),
        ).pack(side=tk.LEFT, padx=2)

        self.y_offset = ttk.Entry(y_frame, width=6)
        self.y_offset.pack(side=tk.LEFT, padx=5)
        self.y_offset.insert(0, "0")

        ttk.Button(
            y_frame,
            text="+1",
            width=2,
            command=lambda: self.adjust_offset("y_offset", 1),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            y_frame,
            text="+10",
            width=3,
            command=lambda: self.adjust_offset("y_offset", 10),
        ).pack(side=tk.LEFT, padx=2)

        # Width
        width_frame = ttk.Frame(adjust_frame)
        width_frame.pack(fill=tk.X, pady=5)

        ttk.Label(width_frame, text="Width:").pack(side=tk.LEFT, padx=5)
        ttk.Button(
            width_frame,
            text="-10",
            width=3,
            command=lambda: self.adjust_offset("width_offset", -10),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            width_frame,
            text="-1",
            width=2,
            command=lambda: self.adjust_offset("width_offset", -1),
        ).pack(side=tk.LEFT, padx=2)

        self.width_offset = ttk.Entry(width_frame, width=6)
        self.width_offset.pack(side=tk.LEFT, padx=5)
        self.width_offset.insert(0, "0")

        ttk.Button(
            width_frame,
            text="+1",
            width=2,
            command=lambda: self.adjust_offset("width_offset", 1),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            width_frame,
            text="+10",
            width=3,
            command=lambda: self.adjust_offset("width_offset", 10),
        ).pack(side=tk.LEFT, padx=2)

        # Height
        height_frame = ttk.Frame(adjust_frame)
        height_frame.pack(fill=tk.X, pady=5)

        ttk.Label(height_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        ttk.Button(
            height_frame,
            text="-10",
            width=3,
            command=lambda: self.adjust_offset("height_offset", -10),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            height_frame,
            text="-1",
            width=2,
            command=lambda: self.adjust_offset("height_offset", -1),
        ).pack(side=tk.LEFT, padx=2)

        self.height_offset = ttk.Entry(height_frame, width=6)
        self.height_offset.pack(side=tk.LEFT, padx=5)
        self.height_offset.insert(0, "0")

        ttk.Button(
            height_frame,
            text="+1",
            width=2,
            command=lambda: self.adjust_offset("height_offset", 1),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            height_frame,
            text="+10",
            width=3,
            command=lambda: self.adjust_offset("height_offset", 10),
        ).pack(side=tk.LEFT, padx=2)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            action_frame, text="Apply Adjustments", command=self.apply_adjustments
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame, text="Save Adjustments", command=self.save_adjustments
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame, text="Reset Adjustments", command=self.reset_adjustments
        ).pack(side=tk.LEFT, padx=5)

        # Always on top toggle
        self.always_on_top_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            action_frame,
            text="Always on Top",
            variable=self.always_on_top_var,
            command=self.toggle_always_on_top,
        ).pack(side=tk.RIGHT, padx=5)

        # Current adjustments display
        adjustments_frame = ttk.LabelFrame(
            main_frame, text="Saved Adjustments", padding="10"
        )
        adjustments_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create a scrollable text area
        scrollbar = ttk.Scrollbar(adjustments_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.adjustments_text = tk.Text(
            adjustments_frame, height=10, yscrollcommand=scrollbar.set
        )
        self.adjustments_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.adjustments_text.yview)

        # Update adjustments text
        self.update_adjustments_display()

    def load_zone_settings(self, event):
        """Load the settings for the selected zone"""
        try:
            # Get selected zone from dropdown
            selected_index = self.zone_settings_selector.current()
            if selected_index < 0 or selected_index >= len(self.zone_keys):
                return

            zone_key = self.zone_keys[selected_index]
            zone = self.zones.get_zone_details(zone_key)

            if not zone:
                return

            # Update entry fields
            self.zone_x.delete(0, tk.END)
            self.zone_x.insert(0, str(zone.get("x", 0)))

            self.zone_y.delete(0, tk.END)
            self.zone_y.insert(0, str(zone.get("y", 0)))

            self.zone_width.delete(0, tk.END)
            self.zone_width.insert(0, str(zone.get("width", 800)))

            self.zone_height.delete(0, tk.END)
            self.zone_height.insert(0, str(zone.get("height", 600)))
        except Exception as e:
            print(f"Error loading zone settings: {e}")

    def save_zone_settings(self):
        """Save the modified settings for a zone"""
        try:
            # Get selected zone
            selected_index = self.zone_settings_selector.current()
            if selected_index < 0 or selected_index >= len(self.zone_keys):
                return

            zone_key = self.zone_keys[selected_index]

            # Get values from entry fields
            x = int(self.zone_x.get())
            y = int(self.zone_y.get())
            width = int(self.zone_width.get())
            height = int(self.zone_height.get())

            # Update zone defaults
            zone = self.zones.get_zone_details(zone_key)
            zone["x"] = x
            zone["y"] = y
            zone["width"] = width
            zone["height"] = height

            # Update in the zones object
            self.zones.default_zones[zone_key] = zone

            # Save to config file
            self.zones.save_config()

            # Show confirmation
            print(f"Updated default settings for {zone_key} zone")
        except Exception as e:
            print(f"Error saving zone settings: {e}")
            import traceback

            traceback.print_exc()

    def toggle_always_on_top(self):
        """Toggle the always-on-top state of the window"""
        self.root.attributes("-topmost", self.always_on_top_var.get())

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

    def on_window_selected(self, event):
        """Handle window selection from dropdown"""
        selection = self.window_selector.current()
        if selection >= 0 and selection < len(self.windows):
            # Store selected window
            self.selected_window = self.windows[selection]

            # Update the information display
            window_class = self.selected_window.get("class", "Unknown")
            process_name = self.selected_window.get("process_name", "Unknown")
            pid = self.selected_window.get("pid", "Unknown")

            info_text = f"Process: {process_name}\nClass: {window_class}\nPID: {pid}"
            self.window_info.config(text=info_text)

            # Reset zone selection
            self.selected_zone = None

            # Reset adjustments
            self.reset_adjustments()

    def apply_zone(self, zone_key):
        """Apply a zone to the selected window"""
        if not self.selected_window:
            return

        # Store the selected zone
        self.selected_zone = zone_key
        print(f"Selected zone: {zone_key}")

        try:
            process_name = self.selected_window.get("process_name", "").replace(
                ".exe", ""
            )
            window_class = self.selected_window.get("class", "")
            window_key = f"{process_name}|{window_class}"
            print(f"Window key: {window_key}")

            # Update the selected layout for this specific window in configuration
            self.zones.set_window_layout(window_key, zone_key)
            print(f"Saved '{zone_key}' as the selected layout for {window_key}")

            # Special handling for custom zone
            if zone_key == "custom":
                # Get current window position for custom zone's initial values
                hwnd = self.selected_window.get("hwnd")
                if hwnd:
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, right, bottom = rect
                    width = right - x
                    height = bottom - y

                    # Save as a custom position (direct values, not offsets)
                    self.zones.save_custom_position(window_key, x, y, width, height)
                    print(f"Saved current position as custom position for {window_key}")

                    # Update interface with these values
                    self.x_offset.delete(0, tk.END)
                    self.x_offset.insert(0, str(x))

                    self.y_offset.delete(0, tk.END)
                    self.y_offset.insert(0, str(y))

                    self.width_offset.delete(0, tk.END)
                    self.width_offset.insert(0, str(width))

                    self.height_offset.delete(0, tk.END)
                    self.height_offset.insert(0, str(height))

                    # Update the adjustments display
                    self.update_adjustments_display_for_window(window_key)

                    # Apply the position (should be same as current)
                    win32gui.SetWindowPos(
                        hwnd,
                        win32con.HWND_TOP,
                        x,
                        y,
                        width,
                        height,
                        win32con.SWP_SHOWWINDOW,
                    )
                return

            # Standard zone handling (non-custom zones)
            # Get zone position with any saved adjustments
            zone = self.zones.get_adjusted_zone(zone_key, window_key)
            if not zone:
                print(f"Zone {zone_key} not found")
                return

            # Get coordinates from zone
            x = zone.get("x", 0)
            y = zone.get("y", 0)
            width = zone.get("width", 800)
            height = zone.get("height", 600)

            # Get window handle
            hwnd = self.selected_window.get("hwnd")

            if hwnd:
                # Position the window
                win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,
                    x,
                    y,
                    width,
                    height,
                    win32con.SWP_SHOWWINDOW,
                )

                # Get any adjustments
                adjustment = self.zones.get_adjustment(window_key, zone_key)

                # Update adjustment fields
                self.x_offset.delete(0, tk.END)
                self.x_offset.insert(0, str(adjustment.get("x_offset", 0)))

                self.y_offset.delete(0, tk.END)
                self.y_offset.insert(0, str(adjustment.get("y_offset", 0)))

                self.width_offset.delete(0, tk.END)
                self.width_offset.insert(0, str(adjustment.get("width_offset", 0)))

                self.height_offset.delete(0, tk.END)
                self.height_offset.insert(0, str(adjustment.get("height_offset", 0)))

                # Update the adjustments display for this window
                self.update_adjustments_display_for_window(window_key)

                # Give visual feedback about which zone is selected
                self.update_zone_feedback(zone_key)
        except Exception as e:
            print(f"Error applying zone: {e}")
            import traceback

            traceback.print_exc()

    def update_zone_feedback(self, zone_key):
        """Update the GUI to highlight which zone is currently active"""
        # This could be expanded to visually indicate which zone is active (e.g. button coloring)
        status_text = f"Active Zone: {self.zones.get_zone_details(zone_key).get('name', zone_key)}"
        print(status_text)

    def adjust_offset(self, offset_field, delta):
        """Adjust an offset value by delta and apply the change"""
        if not self.selected_window or not self.selected_zone:
            return

        try:
            # Get the field widget based on the offset name
            if offset_field == "x_offset":
                field = self.x_offset
            elif offset_field == "y_offset":
                field = self.y_offset
            elif offset_field == "width_offset":
                field = self.width_offset
            elif offset_field == "height_offset":
                field = self.height_offset
            else:
                return

            # Print which button was pressed for debugging
            print(f"Button pressed: {offset_field} with delta {delta}")

            # Get the current value
            current = int(field.get())

            # Calculate the new value
            new_value = current + delta

            # Update the field
            field.delete(0, tk.END)
            field.insert(0, str(new_value))

            # Apply the adjustments immediately
            self.apply_adjustments()
        except Exception as e:
            print(f"Error adjusting offset: {e}")
            import traceback

            traceback.print_exc()

    def apply_adjustments(self):
        """Apply the current adjustments to the selected window"""
        if not self.selected_window or not self.selected_zone:
            return

        try:
            # Get adjustment values
            x_offset = int(self.x_offset.get())
            y_offset = int(self.y_offset.get())
            width_offset = int(self.width_offset.get())
            height_offset = int(self.height_offset.get())

            # Print values for debugging
            print(
                f"Applying adjustments: X={x_offset}, Y={y_offset}, W={width_offset}, H={height_offset}"
            )

            # Get window info
            process_name = self.selected_window.get("process_name", "").replace(
                ".exe", ""
            )
            window_class = self.selected_window.get("class", "")
            window_key = f"{process_name}|{window_class}"

            # Special handling for custom zone
            if self.selected_zone == "custom":
                # For custom zone, values are direct positions, not offsets
                x = x_offset  # Direct X position
                y = y_offset  # Direct Y position
                width = width_offset  # Direct width
                height = height_offset  # Direct height

                # Save the custom position (no need to calculate from a base)
                self.zones.save_custom_position(window_key, x, y, width, height)
            else:
                # Get base zone position (without adjustments)
                zone = self.zones.get_zone_details(self.selected_zone)
                if not zone:
                    print("Zone not found")
                    return

                # Calculate adjusted position
                x = zone.get("x", 0) + x_offset
                y = zone.get("y", 0) + y_offset
                width = zone.get("width", 800) + width_offset
                height = zone.get("height", 600) + height_offset

            # Print final position for debugging
            print(f"Final position: X={x}, Y={y}, W={width}, H={height}")

            # Get window handle
            hwnd = self.selected_window.get("hwnd")

            if hwnd:
                # Position the window - IMPORTANT: Use SWP_SHOWWINDOW to ensure changes are applied
                result = win32gui.SetWindowPos(
                    hwnd,
                    win32con.HWND_TOP,
                    x,
                    y,
                    width,
                    height,
                    win32con.SWP_SHOWWINDOW,
                )
                print(f"SetWindowPos result: {result}")

                # Force window to update and redraw
                win32gui.UpdateWindow(hwnd)
                win32gui.RedrawWindow(
                    hwnd,
                    None,
                    None,
                    win32con.RDW_INVALIDATE
                    | win32con.RDW_ERASE
                    | win32con.RDW_FRAME
                    | win32con.RDW_ALLCHILDREN,
                )
            else:
                print("Window handle not found")
        except Exception as e:
            print(f"Error applying adjustments: {e}")
            import traceback

            traceback.print_exc()

    def save_adjustments(self):
        """Save the current adjustments for this window and zone"""
        if not self.selected_window or not self.selected_zone:
            return

        try:
            # Get adjustment values
            x_offset = int(self.x_offset.get())
            y_offset = int(self.y_offset.get())
            width_offset = int(self.width_offset.get())
            height_offset = int(self.height_offset.get())

            # Get window key
            process_name = self.selected_window.get("process_name", "").replace(
                ".exe", ""
            )
            window_class = self.selected_window.get("class", "")
            window_key = f"{process_name}|{window_class}"

            # Special handling for custom zone
            if self.selected_zone == "custom":
                # For custom zone, we save the values directly, not as offsets
                self.zones.save_custom_position(
                    window_key,
                    x_offset,  # Direct X position, not offset
                    y_offset,  # Direct Y position, not offset
                    width_offset,  # Direct width, not offset
                    height_offset,  # Direct height, not offset
                )
                print(
                    f"Saved custom position for {window_key}: X={x_offset}, Y={y_offset}, W={width_offset}, H={height_offset}"
                )

                # Update adjustments display
                self.update_adjustments_display_for_window(window_key)
                return

            # Standard adjustment for non-custom zones
            self.zones.save_adjustment(
                window_key,
                self.selected_zone,
                x_offset,
                y_offset,
                width_offset,
                height_offset,
            )

            # Update adjustments display
            self.update_adjustments_display_for_window(window_key)

            print(
                f"Saved adjustment for {window_key} in {self.selected_zone} zone: "
                f"X={x_offset}, Y={y_offset}, W={width_offset}, H={height_offset}"
            )
        except Exception as e:
            print(f"Error saving adjustments: {e}")
            import traceback

            traceback.print_exc()

    def reset_adjustments(self):
        """Reset all adjustment values to zero"""
        self.x_offset.delete(0, tk.END)
        self.x_offset.insert(0, "0")

        self.y_offset.delete(0, tk.END)
        self.y_offset.insert(0, "0")

        self.width_offset.delete(0, tk.END)
        self.width_offset.insert(0, "0")

        self.height_offset.delete(0, tk.END)
        self.height_offset.insert(0, "0")

    def update_adjustments_display_for_window(self, window_key):
        """Update the display for a specific window's adjustments"""
        # Clear the text area
        self.adjustments_text.delete(1.0, tk.END)

        # Get adjustments for this window
        adjustments = self.zones.adjustments

        if not adjustments or window_key not in adjustments:
            self.adjustments_text.insert(
                tk.END, f"No saved adjustments for {window_key}"
            )
            return

        # Show adjustments for this window across all zones
        self.adjustments_text.insert(tk.END, f"Window: {window_key}\n\n")

        zones_adjustments = adjustments[window_key]
        for zone_key, adjustment in zones_adjustments.items():
            zone_name = self.zones.get_zone_details(zone_key).get("name", zone_key)

            # Highlight the currently selected zone
            if zone_key == self.selected_zone:
                self.adjustments_text.insert(tk.END, f"▶ Zone: {zone_name} (ACTIVE)\n")
            else:
                self.adjustments_text.insert(tk.END, f"  Zone: {zone_name}\n")

            x_offset = adjustment.get("x_offset", 0)
            y_offset = adjustment.get("y_offset", 0)
            width_offset = adjustment.get("width_offset", 0)
            height_offset = adjustment.get("height_offset", 0)

            self.adjustments_text.insert(
                tk.END,
                f"    Offsets: X={x_offset}, Y={y_offset}, W={width_offset}, H={height_offset}\n\n",
            )

    def update_adjustments_display(self):
        """Update the text display of all saved adjustments"""
        # Clear the text area
        self.adjustments_text.delete(1.0, tk.END)

        # Add all adjustments
        adjustments = self.zones.adjustments

        if not adjustments:
            self.adjustments_text.insert(tk.END, "No saved adjustments")
            return

        for window_key, zones in adjustments.items():
            self.adjustments_text.insert(tk.END, f"Window: {window_key}\n")

            for zone_key, adjustment in zones.items():
                zone_name = self.zones.get_zone_details(zone_key).get("name", zone_key)

                # Highlight the currently selected zone if this is the current window
                if (
                    self.selected_window
                    and f"{self.selected_window.get('process_name', '').replace('.exe', '')}|{self.selected_window.get('class', '')}"
                    == window_key
                    and zone_key == self.selected_zone
                ):
                    self.adjustments_text.insert(
                        tk.END, f"  ▶ Zone: {zone_name} (ACTIVE)\n"
                    )
                else:
                    self.adjustments_text.insert(tk.END, f"  Zone: {zone_name}\n")

                x_offset = adjustment.get("x_offset", 0)
                y_offset = adjustment.get("y_offset", 0)
                width_offset = adjustment.get("width_offset", 0)
                height_offset = adjustment.get("height_offset", 0)

                self.adjustments_text.insert(
                    tk.END,
                    f"    Offsets: X={x_offset}, Y={y_offset}, W={width_offset}, H={height_offset}\n",
                )

            self.adjustments_text.insert(tk.END, "\n")


def main():
    root = tk.Tk()
    app = FancyWindowResizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
