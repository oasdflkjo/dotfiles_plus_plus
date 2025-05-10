import json
import os
import win32gui
import win32process
import psutil
import keyboard
import tkinter as tk
from tkinter import ttk
import win32con
import win32api
import time


class WindowSwitcher:
    def __init__(self):
        print("Initializing WindowSwitcher...")
        self.definitions_file = "tag_definitions.json"
        self.definitions = self.load_definitions()
        print(f"Loaded {len(self.definitions)} definitions")

        # Register hotkeys
        print("Registering hotkeys...")
        try:
            # Test hotkey first
            keyboard.add_hotkey("ctrl+alt+t", lambda: print("Test hotkey works!"))
            print("Test hotkey (Ctrl+Alt+T) registered")

            # Main hotkey
            keyboard.add_hotkey("ctrl+alt+j", self.show_switcher)
            print("Main hotkey (Ctrl+Alt+J) registered")

            # List all registered hotkeys
            print("Currently registered hotkeys:")
            for hotkey in keyboard._hotkeys:
                print(f"  {hotkey}")

        except Exception as e:
            print(f"Error registering hotkeys: {e}")

    def load_definitions(self):
        """Load window definitions from JSON file"""
        print(f"Loading definitions from {self.definitions_file}")
        if os.path.exists(self.definitions_file):
            try:
                with open(self.definitions_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading definitions: {e}")
                return []
        print("Definitions file not found")
        return []

    def find_window_by_tag(self, tag_name):
        """Find a window that matches the given tag"""
        print(f"Finding window for tag: {tag_name}")
        for tag in self.definitions:
            if tag["name"] == tag_name:
                # Get all windows
                def callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        windows.append(hwnd)
                    return True

                windows = []
                win32gui.EnumWindows(callback, windows)
                print(f"Found {len(windows)} visible windows")

                # Check each window
                for hwnd in windows:
                    try:
                        # Get window info
                        title = win32gui.GetWindowText(hwnd)
                        class_name = win32gui.GetClassName(hwnd)
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        process_name = process.name()

                        # Check if window matches tag criteria
                        match = True

                        if (
                            "process_name" in tag
                            and tag["process_name"].lower() != process_name.lower()
                        ):
                            match = False

                        if "class_name" in tag and tag["class_name"] != class_name:
                            match = False

                        if (
                            "title_substring" in tag
                            and tag["title_substring"].lower() not in title.lower()
                        ):
                            match = False

                        if match:
                            print(f"Found matching window: {title} ({process_name})")
                            return hwnd

                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        print(f"Error processing window: {e}")
                        continue

        print("No matching window found")
        return None

    def show_switcher(self):
        """Show the window switcher dialog"""
        print("Showing window switcher...")
        try:
            # Create root window
            root = tk.Tk()
            print("Created root window")
            root.title("Window Switcher")

            # Make it float above other windows
            root.attributes("-topmost", True)
            print("Set window to topmost")

            # Create search box
            search_var = tk.StringVar()
            search_var.trace(
                "w",
                lambda name, index, mode: self.filter_list(search_var.get(), listbox),
            )

            search_entry = ttk.Entry(root, textvariable=search_var)
            search_entry.pack(fill=tk.X, padx=5, pady=5)
            print("Created search box")

            # Create listbox
            listbox = tk.Listbox(root, height=10)
            listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            print("Created listbox")

            # Add tags to listbox
            for tag in self.definitions:
                listbox.insert(tk.END, tag["name"])
            print(f"Added {len(self.definitions)} tags to listbox")

            # Select first item by default
            if listbox.size() > 0:
                listbox.selection_set(0)
                listbox.see(0)
                print("Selected first item")

            # Bind keyboard events
            def on_key(event):
                print(f"[ROOT] Key pressed: {event.keysym}")
                if event.keysym == "Return":
                    self.switch_to_selected(listbox, root)
                elif event.keysym == "Up":
                    if listbox.curselection():
                        current = listbox.curselection()[0]
                        if current > 0:
                            listbox.selection_clear(current)
                            listbox.selection_set(current - 1)
                            listbox.see(current - 1)
                elif event.keysym == "Down":
                    if listbox.curselection():
                        current = listbox.curselection()[0]
                        if current < listbox.size() - 1:
                            listbox.selection_clear(current)
                            listbox.selection_set(current + 1)
                            listbox.see(current + 1)
                elif event.keysym == "Escape":
                    root.destroy()

            def on_entry_key(event):
                print(f"[ENTRY] Key pressed: {event.keysym}")

            # Bind events to root window so they work anywhere
            root.bind("<Key>", on_key)
            print("Bound keyboard events")
            search_entry.bind("<Key>", on_entry_key)
            print("Bound entry key events")

            # Center the window
            root.update_idletasks()
            width = root.winfo_width()
            height = root.winfo_height()
            x = (root.winfo_screenwidth() // 2) - (width // 2)
            y = (root.winfo_screenheight() // 2) - (height // 2)
            root.geometry(f"{width}x{height}+{x}+{y}")
            print(f"Centered window at {x},{y} with size {width}x{height}")

            # Get the window handle
            hwnd = win32gui.GetParent(root.winfo_id())

            # Force window to front and activate
            def activate_window():
                try:
                    hwnd = win32gui.GetParent(root.winfo_id())
                    # Immediate attempt
                    root.lift()
                    root.focus_force()
                    search_entry.focus_set()
                    search_entry.select_range(0, tk.END)
                    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                    try:
                        win32gui.SetForegroundWindow(hwnd)
                    except Exception as e:
                        print(f"SetForegroundWindow error (immediate): {e}")
                    win32api.keybd_event(
                        win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0
                    )
                    if win32gui.GetForegroundWindow() == hwnd:
                        print(
                            "Tkinter window is now foreground and focused (immediate)"
                        )
                        return
                    # Fallback loop
                    start = time.time()
                    while time.time() - start < 0.5:
                        root.lift()
                        root.focus_force()
                        search_entry.focus_set()
                        search_entry.select_range(0, tk.END)
                        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                        try:
                            win32gui.SetForegroundWindow(hwnd)
                        except Exception as e:
                            print(f"SetForegroundWindow error (loop): {e}")
                        win32api.keybd_event(
                            win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0
                        )
                        if win32gui.GetForegroundWindow() == hwnd:
                            print("Tkinter window is now foreground and focused (loop)")
                            break
                        time.sleep(0.05)
                    else:
                        print("Failed to focus Tkinter window after several attempts")
                except Exception as e:
                    print(f"Error activating window: {e}")

            # Call activate_window after a short delay
            root.after(100, activate_window)

            # Start the main loop
            print("Starting main loop")
            root.mainloop()
            print("Main loop ended")
            root.destroy()
            print("Root window destroyed")
        except Exception as e:
            print(f"Error in show_switcher: {e}")

    def filter_list(self, search_text, listbox):
        """Filter the listbox based on search text"""
        print(f"Filtering list with text: {search_text}")
        listbox.delete(0, tk.END)
        search_text = search_text.lower()

        for tag in self.definitions:
            if search_text in tag["name"].lower():
                listbox.insert(tk.END, tag["name"])

        # Select first item after filtering
        if listbox.size() > 0:
            listbox.selection_set(0)
            listbox.see(0)
        print(f"Filtered list now has {listbox.size()} items")

    def switch_to_selected(self, listbox, root):
        """Switch to the selected window"""
        print("Switching to selected window...")
        selection = listbox.curselection()
        if selection:
            tag_name = listbox.get(selection[0])
            print(f"Selected tag: {tag_name}")
            hwnd = self.find_window_by_tag(tag_name)

            if hwnd:
                print(f"Found window handle: {hwnd}")
                # Bring window to front
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                print("Brought window to front")
            else:
                print("No window found for tag")

            root.destroy()
            print("Closed switcher window")
        else:
            print("No selection made")


def main():
    print("Starting Window Switcher...")
    switcher = WindowSwitcher()
    print("Window Switcher running in background.")
    print("Press Ctrl+C to exit.")
    print("Try pressing Ctrl+Alt+T to test hotkey functionality")
    print("Try pressing Ctrl+Alt+J to open the window switcher")

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == "__main__":
    main()
