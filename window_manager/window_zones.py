import win32api
import json
import os
from pathlib import Path


class WindowZones:
    """
    Defines standard window zones and handles screen calculations.
    Provides zone definitions for placement and manages per-application adjustments.
    """

    def __init__(self, config_file="window_zones.json"):
        self.config_path = Path(config_file)

        # Default zones
        self.default_zones = {
            "fullscreen": {
                "name": "Full Screen",
                "x": -4,
                "y": -4,
                "width": 3559,
                "height": 1445,
                "description": "Covers the entire screen (adjusted for taskbar hiding)",
            },
            "centered": {
                "name": "Centered",
                "x": 786,
                "y": 25,
                "width": 1850,
                "height": 1395,
                "description": "Centered window with margins",
            },
            "custom": {
                "name": "Custom",
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 0,
                "description": "Custom position with no base values - direct coordinates",
                "is_custom": True,  # Special flag for custom zone type
            },
            # Additional zones can be added here
        }

        # Application-specific adjustments
        self.adjustments = {}

        # Window-specific custom positions (for the custom zone type)
        self.custom_positions = {}

        # Window-specific selected layouts
        self.window_layouts = {}

        # Default layout for new windows
        self.default_layout = "centered"

        # Load or create configuration
        self.load_or_create_config()

    def load_or_create_config(self):
        """Load existing config or create a new one based on defaults"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # Update zones and adjustments from config
                if "zones" in config:
                    self.default_zones.update(config["zones"])

                if "adjustments" in config:
                    self.adjustments = config["adjustments"]

                # Load per-window layouts if present
                if "window_layouts" in config:
                    self.window_layouts = config["window_layouts"]

                # Load custom positions if present
                if "custom_positions" in config:
                    self.custom_positions = config["custom_positions"]

                # Load default layout if present
                if "default_layout" in config:
                    self.default_layout = config["default_layout"]

                print(f"Loaded zone configuration from {self.config_path}")
            except Exception as e:
                print(f"Error loading zone configuration: {e}")
                self.save_config()  # Create a new config
        else:
            # Create a new configuration file
            self.save_config()

    def save_config(self):
        """Save the current configuration to file"""
        config = {
            "zones": self.default_zones,
            "adjustments": self.adjustments,
            "window_layouts": self.window_layouts,
            "custom_positions": self.custom_positions,
            "default_layout": self.default_layout,
        }

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"Saved zone configuration to {self.config_path}")
        except Exception as e:
            print(f"Error saving zone configuration: {e}")

    def set_window_layout(self, window_key, layout_key):
        """Set the selected layout for a specific window and save to config"""
        if layout_key in self.default_zones:
            self.window_layouts[window_key] = layout_key
            self.save_config()
            return True
        return False

    def get_window_layout(self, window_key):
        """Get the selected layout for a specific window, or default if not set"""
        return self.window_layouts.get(window_key, self.default_layout)

    def set_default_layout(self, layout_key):
        """Set the default layout for windows without a specific selection"""
        if layout_key in self.default_zones:
            self.default_layout = layout_key
            self.save_config()
            return True
        return False

    def get_default_layout(self):
        """Get the default layout for windows without a specific selection"""
        return self.default_layout

    def get_zone_details(self, zone_key):
        """Get the position and size details for a zone"""
        if zone_key in self.default_zones:
            return self.default_zones[zone_key].copy()
        return None

    def get_all_zones(self):
        """Get all available zones with their details"""
        return self.default_zones.copy()

    def get_adjusted_zone(self, zone_key, window_key):
        """
        Get zone position with any application-specific adjustments applied.

        Args:
            zone_key: The identifier for the zone
            window_key: Process and class identifier (e.g. "Cursor|Chrome_WidgetWin_1")

        Returns:
            Dictionary with x, y, width, height adjusted for the specific window
        """
        # Special handling for custom zone
        if zone_key == "custom":
            # If this window has a custom position, use it directly
            if window_key in self.custom_positions:
                custom_pos = self.custom_positions[window_key].copy()

                # Add name and description for consistency
                if "name" not in custom_pos:
                    custom_pos["name"] = "Custom"
                if "description" not in custom_pos:
                    custom_pos["description"] = "Custom position for " + window_key

                return custom_pos

            # Otherwise, return a default custom zone
            return self.default_zones["custom"].copy()

        # Standard zone handling for non-custom zones
        zone = self.get_zone_details(zone_key)
        if not zone:
            return None

        # Check for adjustments
        if window_key in self.adjustments and zone_key in self.adjustments[window_key]:
            adjustment = self.adjustments[window_key][zone_key]

            # Apply offsets
            zone["x"] += adjustment.get("x_offset", 0)
            zone["y"] += adjustment.get("y_offset", 0)
            zone["width"] += adjustment.get("width_offset", 0)
            zone["height"] += adjustment.get("height_offset", 0)

        return zone

    def save_adjustment(
        self,
        window_key,
        zone_key,
        x_offset=0,
        y_offset=0,
        width_offset=0,
        height_offset=0,
    ):
        """
        Save an adjustment for a specific window and zone.

        Args:
            window_key: Process and class identifier (e.g. "Cursor|Chrome_WidgetWin_1")
            zone_key: The identifier for the zone
            x_offset, y_offset, width_offset, height_offset: Adjustment values
        """
        # Special handling for custom zone
        if zone_key == "custom":
            # For custom zone, we save direct position values instead of offsets
            zone = self.get_zone_details(zone_key)

            # Direct position = base (0,0) + offsets
            self.save_custom_position(
                window_key,
                x_offset,  # x is direct value
                y_offset,  # y is direct value
                width_offset,  # width is direct value
                height_offset,  # height is direct value
            )
            return

        # Standard adjustment for non-custom zones
        # Initialize if needed
        if window_key not in self.adjustments:
            self.adjustments[window_key] = {}

        # Save adjustment
        self.adjustments[window_key][zone_key] = {
            "x_offset": x_offset,
            "y_offset": y_offset,
            "width_offset": width_offset,
            "height_offset": height_offset,
        }

        # Save config to file
        self.save_config()

    def save_custom_position(self, window_key, x, y, width, height):
        """
        Save a custom position for a specific window.

        Args:
            window_key: Process and class identifier (e.g. "Calculator|CalcFrame")
            x, y, width, height: Direct position values (not offsets)
        """
        self.custom_positions[window_key] = {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "is_custom": True,
        }

        # Save config to file
        self.save_config()

        # If the window doesn't have a layout set, set it to custom
        if window_key not in self.window_layouts:
            self.set_window_layout(window_key, "custom")

    def get_adjustment(self, window_key, zone_key):
        """
        Get any saved adjustments for a window and zone.

        Returns:
            Dictionary with offset values or empty dict with zeros if no adjustment exists
        """
        # Special handling for custom zone
        if zone_key == "custom" and window_key in self.custom_positions:
            # For custom zones, return the direct positions as "offsets"
            pos = self.custom_positions[window_key]
            return {
                "x_offset": pos.get("x", 0),
                "y_offset": pos.get("y", 0),
                "width_offset": pos.get("width", 0),
                "height_offset": pos.get("height", 0),
            }

        # Standard adjustment handling
        if window_key in self.adjustments and zone_key in self.adjustments[window_key]:
            return self.adjustments[window_key][zone_key].copy()

        return {"x_offset": 0, "y_offset": 0, "width_offset": 0, "height_offset": 0}
