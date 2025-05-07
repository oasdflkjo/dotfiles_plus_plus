import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import win32api
import win32con
import win32gui
import ctypes
from ctypes import wintypes


class ZoneDesigner:
    def __init__(self, root):
        self.root = root
        self.root.title("Zone Designer")

        # Get screen dimensions
        self.screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        # Load existing zones
        self.zones_file = "zones.json"
        self.zones = self.load_zones()

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Screen info section
        info_frame = ttk.LabelFrame(main_frame, text="Screen Information", padding="5")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(info_frame, text=f"Screen Width: {self.screen_width}px").grid(
            row=0, column=0, padx=5
        )
        ttk.Label(info_frame, text=f"Screen Height: {self.screen_height}px").grid(
            row=0, column=1, padx=5
        )

        # Zone list section
        list_frame = ttk.LabelFrame(main_frame, text="Zones", padding="5")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        # Zone list
        self.zone_list = tk.Listbox(list_frame, width=20, height=10)
        self.zone_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.zone_list.bind("<<ListboxSelect>>", self.on_zone_select)

        # Scrollbar for zone list
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.zone_list.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.zone_list["yscrollcommand"] = scrollbar.set

        # Zone list buttons
        list_button_frame = ttk.Frame(list_frame)
        list_button_frame.grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Button(list_button_frame, text="New Zone", command=self.new_zone).grid(
            row=0, column=0, padx=2
        )
        ttk.Button(
            list_button_frame, text="Delete Zone", command=self.delete_zone
        ).grid(row=0, column=1, padx=2)

        # Zone editor section
        editor_frame = ttk.LabelFrame(main_frame, text="Zone Editor", padding="5")
        editor_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        # Zone name
        ttk.Label(editor_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.name_var).grid(
            row=0, column=1, sticky=(tk.W, tk.E)
        )

        # Zone description
        ttk.Label(editor_frame, text="Description:").grid(row=1, column=0, sticky=tk.W)
        self.desc_var = tk.StringVar()
        ttk.Entry(editor_frame, textvariable=self.desc_var).grid(
            row=1, column=1, sticky=(tk.W, tk.E)
        )

        # Hidden position variables (needed for internal calculations)
        self.x_var = tk.StringVar(value="0")
        self.y_var = tk.StringVar(value="0")

        # Dimensions section
        dim_frame = ttk.LabelFrame(editor_frame, text="Dimensions", padding="5")
        dim_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Width
        ttk.Label(dim_frame, text="Width:").grid(row=0, column=0, sticky=tk.W)
        self.width_var = tk.StringVar()
        ttk.Entry(dim_frame, textvariable=self.width_var, width=8).grid(
            row=0, column=1, sticky=tk.W
        )
        ttk.Button(
            dim_frame, text="-1", command=lambda: self.adjust_value("width", -1)
        ).grid(row=0, column=2, padx=2)
        ttk.Button(
            dim_frame, text="+1", command=lambda: self.adjust_value("width", 1)
        ).grid(row=0, column=3, padx=2)

        # Height
        ttk.Label(dim_frame, text="Height:").grid(row=1, column=0, sticky=tk.W)
        self.height_var = tk.StringVar()
        ttk.Entry(dim_frame, textvariable=self.height_var, width=8).grid(
            row=1, column=1, sticky=tk.W
        )
        ttk.Button(
            dim_frame, text="-1", command=lambda: self.adjust_value("height", -1)
        ).grid(row=1, column=2, padx=2)
        ttk.Button(
            dim_frame, text="+1", command=lambda: self.adjust_value("height", 1)
        ).grid(row=1, column=3, padx=2)

        # Y Position
        ttk.Label(dim_frame, text="Y Position:").grid(row=2, column=0, sticky=tk.W)
        ttk.Button(
            dim_frame, text="-1", command=lambda: self.adjust_value("y", -1)
        ).grid(row=2, column=2, padx=2)
        ttk.Button(
            dim_frame, text="+1", command=lambda: self.adjust_value("y", 1)
        ).grid(row=2, column=3, padx=2)

        # Center button
        ttk.Button(dim_frame, text="Center Zone", command=self.center_zone).grid(
            row=3, column=0, columnspan=4, pady=5
        )

        # Position info
        self.pos_info_var = tk.StringVar()
        ttk.Label(dim_frame, textvariable=self.pos_info_var).grid(
            row=4, column=0, columnspan=4, pady=2
        )

        # Preset buttons
        preset_frame = ttk.Frame(editor_frame)
        preset_frame.grid(row=3, column=0, columnspan=2, pady=5)

        ttk.Button(
            preset_frame,
            text="80% Screen",
            command=lambda: self.apply_preset("80_percent"),
        ).grid(row=0, column=0, padx=2)
        ttk.Button(
            preset_frame,
            text="90% Screen",
            command=lambda: self.apply_preset("90_percent"),
        ).grid(row=0, column=1, padx=2)
        ttk.Button(
            preset_frame,
            text="Full Screen",
            command=lambda: self.apply_preset("full_screen"),
        ).grid(row=0, column=2, padx=2)

        # Preview button
        ttk.Button(editor_frame, text="Preview Zone", command=self.preview_zone).grid(
            row=4, column=0, columnspan=2, pady=5
        )

        # Save button
        ttk.Button(editor_frame, text="Save Zone", command=self.save_zone).grid(
            row=5, column=0, columnspan=2, pady=5
        )

        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        editor_frame.columnconfigure(1, weight=1)
        dim_frame.columnconfigure(1, weight=1)

        # Update zone list
        self.update_zone_list()

        # Overlay window handle
        self.overlay_hwnd = None

    def create_overlay(self, x, y, width, height):
        """Create a semi-transparent overlay showing the zone"""
        # Register window class
        class_name = "ZoneOverlayClass"
        wc = win32gui.WNDCLASS()
        wc.lpszClassName = class_name
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.hbrBackground = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0))
        wc.lpfnWndProc = win32gui.DefWindowProc
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW

        try:
            win32gui.RegisterClass(wc)
        except:
            pass

        # Create window
        style = win32con.WS_POPUP
        ex_style = (
            win32con.WS_EX_LAYERED
            | win32con.WS_EX_TRANSPARENT
            | win32con.WS_EX_TOPMOST
            | win32con.WS_EX_TOOLWINDOW
        )

        try:
            hwnd = win32gui.CreateWindowEx(
                ex_style,
                class_name,
                "Zone Overlay",
                style,
                x,
                y,
                width,
                height,
                0,
                0,
                wc.hInstance,
                None,
            )

            # Paint the border
            hdc = win32gui.GetDC(hwnd)
            pen = win32gui.CreatePen(win32con.PS_SOLID, 2, win32api.RGB(120, 170, 240))
            old_pen = win32gui.SelectObject(hdc, pen)
            win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
            null_brush = win32gui.GetStockObject(win32con.NULL_BRUSH)
            old_brush = win32gui.SelectObject(hdc, null_brush)

            # Draw border
            win32gui.Rectangle(hdc, 0, 0, width, height)

            # Cleanup
            win32gui.SelectObject(hdc, old_pen)
            win32gui.SelectObject(hdc, old_brush)
            win32gui.DeleteObject(pen)
            win32gui.ReleaseDC(hwnd, hdc)

            # Set transparency
            color_key = win32api.RGB(0, 0, 0)
            win32gui.SetLayeredWindowAttributes(
                hwnd, color_key, 50, win32con.LWA_COLORKEY | win32con.LWA_ALPHA
            )

            # Show window
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(hwnd)

            return hwnd
        except Exception as e:
            print(f"Error creating overlay: {e}")
            return None

    def destroy_overlay(self):
        """Destroy the overlay window"""
        if self.overlay_hwnd:
            try:
                win32gui.DestroyWindow(self.overlay_hwnd)
                self.overlay_hwnd = None
            except:
                pass

    def preview_zone(self):
        """Show a preview of the current zone"""
        try:
            x = int(self.x_var.get())
            y = int(self.y_var.get())
            width = int(self.width_var.get())
            height = int(self.height_var.get())

            # Destroy existing overlay
            self.destroy_overlay()

            # Create new overlay
            self.overlay_hwnd = self.create_overlay(x, y, width, height)

        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values")

    def load_zones(self):
        """Load zones from JSON file"""
        if os.path.exists(self.zones_file):
            try:
                with open(self.zones_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror(
                    "Error", f"{self.zones_file} contains invalid JSON"
                )
                return {}
            except Exception as e:
                messagebox.showerror("Error", f"Error loading zones: {e}")
                return {}
        return {}

    def save_zones(self):
        """Save zones to JSON file"""
        try:
            with open(self.zones_file, "w") as f:
                json.dump(self.zones, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Error saving zones: {e}")

    def update_zone_list(self):
        """Update the zone list display"""
        self.zone_list.delete(0, tk.END)
        for zone_name in sorted(self.zones.keys()):
            self.zone_list.insert(tk.END, zone_name)

    def on_zone_select(self, event):
        """Handle zone selection"""
        selection = self.zone_list.curselection()
        if selection:
            zone_name = self.zone_list.get(selection[0])
            zone = self.zones[zone_name]

            # Load all values from the zone
            self.name_var.set(zone_name)
            self.desc_var.set(zone.get("description", ""))
            self.width_var.set(str(zone.get("width", 0)))
            self.height_var.set(str(zone.get("height", 0)))

            # Store position values internally
            self.x_var.set(str(zone.get("x", 0)))
            self.y_var.set(str(zone.get("y", 0)))

            # Update position info based on centering
            self.update_position_info()

    def new_zone(self):
        """Create a new zone"""
        # Clear the editor
        self.name_var.set("")
        self.desc_var.set("")
        self.x_var.set("0")
        self.y_var.set("0")
        self.width_var.set("0")
        self.height_var.set("0")
        self.destroy_overlay()

    def delete_zone(self):
        """Delete the selected zone"""
        selection = self.zone_list.curselection()
        if selection:
            zone_name = self.zone_list.get(selection[0])
            if messagebox.askyesno("Confirm", f"Delete zone '{zone_name}'?"):
                del self.zones[zone_name]
                self.save_zones()
                self.update_zone_list()
                self.new_zone()

    def adjust_value(self, field: str, delta: int):
        """Adjust a numeric value"""
        try:
            if field == "width":
                current = int(self.width_var.get())
                self.width_var.set(str(current + delta))
            elif field == "height":
                current = int(self.height_var.get())
                self.height_var.set(str(current + delta))
            elif field == "y":
                current = int(self.y_var.get())
                new_y = current + delta
                # Ensure y doesn't go negative or beyond screen height
                if 0 <= new_y <= self.screen_height:
                    self.y_var.set(str(new_y))

            # Update preview if overlay exists
            if self.overlay_hwnd:
                self.preview_zone()

            # Update position info
            self.update_position_info()

        except ValueError:
            pass

    def center_zone(self):
        """Center the zone based on current dimensions"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())

            # Calculate center position
            x = (self.screen_width - width) // 2
            y = (self.screen_height - height) // 2

            # Check if centering is pixel-perfect
            x_perfect = (self.screen_width - width) % 2 == 0
            y_perfect = (self.screen_height - height) % 2 == 0

            # Update position info
            if x_perfect and y_perfect:
                self.pos_info_var.set("✓ Pixel-perfect centering")
            else:
                self.pos_info_var.set("! Centering offset by 1px")

            # Update position variables
            self.x_var.set(str(x))
            self.y_var.set(str(y))

            # Update preview if active
            if self.overlay_hwnd:
                self.preview_zone()

        except ValueError:
            messagebox.showerror("Error", "Invalid dimensions")

    def apply_preset(self, preset: str):
        """Apply a preset zone configuration"""
        if preset == "80_percent":
            width = int(self.screen_width * 0.8)
            height = int(self.screen_height * 0.8)
        elif preset == "90_percent":
            width = int(self.screen_width * 0.9)
            height = int(self.screen_height * 0.9)
        elif preset == "full_screen":
            width = self.screen_width
            height = self.screen_height

        self.width_var.set(str(width))
        self.height_var.set(str(height))

        # Auto-center after applying preset
        self.center_zone()

        # Update preview
        self.preview_zone()

    def save_zone(self):
        """Save the current zone"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Zone name is required")
            return

        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())

            # Get current position (either from centering or existing values)
            x = int(self.x_var.get())
            y = int(self.y_var.get())

            # Validate dimensions
            if width <= 0 or height <= 0:
                messagebox.showerror("Error", "Width and height must be positive")
                return

            if x < 0 or y < 0:
                messagebox.showerror("Error", "X and Y must be non-negative")
                return

            if x + width > self.screen_width or y + height > self.screen_height:
                messagebox.showerror("Error", "Zone extends beyond screen boundaries")
                return

            # Save zone with the same structure as before
            self.zones[name] = {
                "name": name,
                "description": self.desc_var.get().strip(),
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }

            self.save_zones()
            self.update_zone_list()
            messagebox.showinfo("Success", f"Zone '{name}' saved successfully")

        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values")

    def update_position_info(self):
        """Update the position info display based on current values"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            x = int(self.x_var.get())
            y = int(self.y_var.get())

            # Check if position matches center calculation
            center_x = (self.screen_width - width) // 2
            center_y = (self.screen_height - height) // 2

            if x == center_x and y == center_y:
                # Check if centering is pixel-perfect
                x_perfect = (self.screen_width - width) % 2 == 0
                y_perfect = (self.screen_height - height) % 2 == 0

                if x_perfect and y_perfect:
                    self.pos_info_var.set("✓ Pixel-perfect centering")
                else:
                    self.pos_info_var.set("! Centering offset by 1px")
            else:
                self.pos_info_var.set(f"Position: ({x}, {y})")

        except ValueError:
            self.pos_info_var.set("Invalid values")


def main():
    root = tk.Tk()
    app = ZoneDesigner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
