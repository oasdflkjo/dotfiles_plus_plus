import tkinter as tk
from tkinter import ttk
from tagger_interface import TaggerInterface


class TaggerGUI:
    def __init__(self, root: tk.Tk, tagger: TaggerInterface):
        self.root = root
        self.tagger = tagger

        self.root.title("Window Tagger")
        self.root.geometry("400x650")  # Made taller for the adjustment buttons

        # Get active window info
        self.window_info = self.tagger.get_active_window_info()

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Window info section
        ttk.Label(
            main_frame, text="Active Window Info", font=("Arial", 12, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)

        info_frame = ttk.LabelFrame(main_frame, text="Window Details", padding="5")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Process name
        ttk.Label(info_frame, text="Process:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=self.window_info["process_name"]).grid(
            row=0, column=1, sticky=tk.W
        )

        # Window title
        ttk.Label(info_frame, text="Title:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=self.window_info["window_title"]).grid(
            row=1, column=1, sticky=tk.W
        )

        # Class name
        ttk.Label(info_frame, text="Class:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(info_frame, text=self.window_info["class_name"]).grid(
            row=2, column=1, sticky=tk.W
        )

        # Tag definition section
        tag_frame = ttk.LabelFrame(main_frame, text="Tag Definition", padding="5")
        tag_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        # Tag name
        ttk.Label(tag_frame, text="Tag Name:").grid(row=0, column=0, sticky=tk.W)
        self.tag_name_var = tk.StringVar()
        self.tag_name_entry = ttk.Entry(tag_frame, textvariable=self.tag_name_var)
        self.tag_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        # Default zone dropdown
        ttk.Label(tag_frame, text="Default Zone:").grid(row=1, column=0, sticky=tk.W)
        self.zone_var = tk.StringVar(value="centered")
        self.zone_dropdown = ttk.Combobox(
            tag_frame, textvariable=self.zone_var, state="readonly"
        )
        self.zone_dropdown["values"] = ["None"] + list(self.tagger.zones.keys())
        self.zone_dropdown.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)

        # Checkboxes for matching criteria
        self.use_process_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            tag_frame, text="Match Process Name", variable=self.use_process_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W)

        self.use_class_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            tag_frame, text="Match Class Name", variable=self.use_class_var
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W)

        # Title matching section
        title_frame = ttk.Frame(tag_frame)
        title_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.use_title_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            title_frame, text="Match Title", variable=self.use_title_var
        ).grid(row=0, column=0, sticky=tk.W)

        self.title_substring_var = tk.StringVar()
        self.title_entry = ttk.Entry(title_frame, textvariable=self.title_substring_var)
        self.title_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        # Offset section
        offset_frame = ttk.LabelFrame(main_frame, text="Window Offsets", padding="5")
        offset_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        # X offset
        x_frame = ttk.Frame(offset_frame)
        x_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(x_frame, text="X Offset:").grid(row=0, column=0, sticky=tk.W)
        self.x_offset_var = tk.StringVar(value="0")
        ttk.Entry(x_frame, textvariable=self.x_offset_var, width=10).grid(
            row=0, column=1, sticky=tk.W
        )
        ttk.Button(
            x_frame, text="-1", command=lambda: self.adjust_offset("x", -1)
        ).grid(row=0, column=2, padx=2)
        ttk.Button(x_frame, text="+1", command=lambda: self.adjust_offset("x", 1)).grid(
            row=0, column=3, padx=2
        )

        # Y offset
        y_frame = ttk.Frame(offset_frame)
        y_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(y_frame, text="Y Offset:").grid(row=0, column=0, sticky=tk.W)
        self.y_offset_var = tk.StringVar(value="0")
        ttk.Entry(y_frame, textvariable=self.y_offset_var, width=10).grid(
            row=0, column=1, sticky=tk.W
        )
        ttk.Button(
            y_frame, text="-1", command=lambda: self.adjust_offset("y", -1)
        ).grid(row=0, column=2, padx=2)
        ttk.Button(y_frame, text="+1", command=lambda: self.adjust_offset("y", 1)).grid(
            row=0, column=3, padx=2
        )

        # Width offset
        width_frame = ttk.Frame(offset_frame)
        width_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(width_frame, text="Width Offset:").grid(row=0, column=0, sticky=tk.W)
        self.width_offset_var = tk.StringVar(value="0")
        ttk.Entry(width_frame, textvariable=self.width_offset_var, width=10).grid(
            row=0, column=1, sticky=tk.W
        )
        ttk.Button(
            width_frame, text="-1", command=lambda: self.adjust_offset("width", -1)
        ).grid(row=0, column=2, padx=2)
        ttk.Button(
            width_frame, text="+1", command=lambda: self.adjust_offset("width", 1)
        ).grid(row=0, column=3, padx=2)

        # Height offset
        height_frame = ttk.Frame(offset_frame)
        height_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        ttk.Label(height_frame, text="Height Offset:").grid(
            row=0, column=0, sticky=tk.W
        )
        self.height_offset_var = tk.StringVar(value="0")
        ttk.Entry(height_frame, textvariable=self.height_offset_var, width=10).grid(
            row=0, column=1, sticky=tk.W
        )
        ttk.Button(
            height_frame, text="-1", command=lambda: self.adjust_offset("height", -1)
        ).grid(row=0, column=2, padx=2)
        ttk.Button(
            height_frame, text="+1", command=lambda: self.adjust_offset("height", 1)
        ).grid(row=0, column=3, padx=2)

        # Reset button
        ttk.Button(offset_frame, text="Reset Offsets", command=self.reset_offsets).grid(
            row=4, column=0, columnspan=2, pady=5
        )

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Save Tag", command=self.save_tag).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(button_frame, text="Close", command=self.root.destroy).grid(
            row=0, column=1, padx=5
        )

        # Load existing tag info if available
        self.load_existing_tag_info()

        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        tag_frame.columnconfigure(1, weight=1)
        offset_frame.columnconfigure(1, weight=1)
        title_frame.columnconfigure(1, weight=1)

    def adjust_offset(self, offset_type: str, delta: int):
        """Adjust a specific offset and update the window"""
        try:
            # Get current value
            if offset_type == "x":
                current = int(self.x_offset_var.get())
                self.x_offset_var.set(str(current + delta))
            elif offset_type == "y":
                current = int(self.y_offset_var.get())
                self.y_offset_var.set(str(current + delta))
            elif offset_type == "width":
                current = int(self.width_offset_var.get())
                self.width_offset_var.set(str(current + delta))
            elif offset_type == "height":
                current = int(self.height_offset_var.get())
                self.height_offset_var.set(str(current + delta))

            # Center window with new offsets
            self.center_window()

            # Save the new offsets
            tag_name = self.tag_name_var.get().strip()
            if tag_name:
                try:
                    x_offset = int(self.x_offset_var.get())
                    y_offset = int(self.y_offset_var.get())
                    width_offset = int(self.width_offset_var.get())
                    height_offset = int(self.height_offset_var.get())

                    self.tagger.save_offset(
                        tag_name, x_offset, y_offset, width_offset, height_offset
                    )
                    print(f"Saved offsets for tag '{tag_name}'")
                except ValueError:
                    print("Invalid offset values")

        except ValueError:
            print("Invalid offset value")

    def reset_offsets(self):
        """Reset all offsets to zero"""
        self.x_offset_var.set("0")
        self.y_offset_var.set("0")
        self.width_offset_var.set("0")
        self.height_offset_var.set("0")
        self.center_window()

        # Save the reset offsets
        tag_name = self.tag_name_var.get().strip()
        if tag_name:
            self.tagger.save_offset(tag_name, 0, 0, 0, 0)
            print(f"Reset and saved offsets for tag '{tag_name}'")

    def center_window(self):
        """Center the window with current offsets"""
        try:
            # Get current offsets
            x_offset = int(self.x_offset_var.get())
            y_offset = int(self.y_offset_var.get())
            width_offset = int(self.width_offset_var.get())
            height_offset = int(self.height_offset_var.get())

            # Get centered zone
            centered = self.tagger.get_centered_zone()

            # Position window with offsets
            self.tagger.position_window_with_offsets(
                self.window_info["hwnd"],
                centered.get("x", 0),
                centered.get("y", 0),
                centered.get("width", 0),
                centered.get("height", 0),
                x_offset,
                y_offset,
                width_offset,
                height_offset,
            )

        except ValueError:
            print("Invalid offset values")

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

            # Set the default zone
            zone = self.tagger.get_tag_zone(tag_name)
            self.zone_var.set("None" if zone is None else zone)

            # Find the matching tag definition to set checkboxes
            for tag in self.tagger.definitions:
                if tag.get("name") == tag_name:
                    # Set process name checkbox
                    self.use_process_var.set(tag.get("process_name") is not None)

                    # Set class name checkbox
                    self.use_class_var.set(tag.get("class_name") is not None)

                    # Set title matching checkbox and substring
                    if tag.get("title_substring"):
                        self.use_title_var.set(True)
                        self.title_substring_var.set(tag.get("title_substring"))
                    else:
                        self.use_title_var.set(False)
                        self.title_substring_var.set("")
                    break

    def save_tag(self):
        """Save the tag definition and offsets"""
        tag_name = self.tag_name_var.get().strip()
        if not tag_name:
            print("Please enter a tag name")
            return

        # Create tag definition
        tag_definition = {
            "name": tag_name,
            "process_name": (
                self.window_info["process_name"] if self.use_process_var.get() else None
            ),
            "class_name": (
                self.window_info["class_name"] if self.use_class_var.get() else None
            ),
        }

        # Add title substring if enabled and provided
        if self.use_title_var.get():
            title_substring = self.title_substring_var.get().strip()
            if title_substring:
                tag_definition["title_substring"] = title_substring

        # Save tag definition
        self.tagger.save_tag_definition(tag_definition)

        # Save default zone if not "None"
        selected_zone = self.zone_var.get()
        if selected_zone != "None":
            self.tagger.save_tag_zone(tag_name, selected_zone)
        else:
            # Remove zone entry if it exists
            if tag_name in self.tagger.tag_zones:
                del self.tagger.tag_zones[tag_name]
                self.tagger.save_tag_zones()

        # Save offsets
        try:
            x_offset = int(self.x_offset_var.get())
            y_offset = int(self.y_offset_var.get())
            width_offset = int(self.width_offset_var.get())
            height_offset = int(self.height_offset_var.get())

            self.tagger.save_offset(
                tag_name, x_offset, y_offset, width_offset, height_offset
            )

            print(f"Tag '{tag_name}' saved successfully")
            self.root.destroy()

        except ValueError:
            print("Please enter valid numbers for offsets")
