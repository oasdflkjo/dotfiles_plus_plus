import win32gui
import win32api
import win32con
import win32process
import os
import time
import tkinter as tk
from tkinter import ttk
from ctypes import wintypes


def get_process_name(hwnd):
    """Get process name for a window"""
    try:
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        hProcess = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
        )
        if hProcess:
            try:
                process_path = win32process.GetModuleFileNameEx(hProcess, 0)
                return os.path.basename(process_path).lower()
            finally:
                win32api.CloseHandle(hProcess)
    except Exception as e:
        return f"Error: {e}"
    return ""


def get_window_info(hwnd):
    """Get detailed information about a window"""
    if not hwnd:
        return None

    try:
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        process_name = get_process_name(hwnd)
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        parent = win32gui.GetParent(hwnd)

        return {
            "hwnd": hwnd,
            "title": title,
            "class": class_name,
            "process": process_name,
            "style": f"0x{style:08x}",
            "ex_style": f"0x{ex_style:08x}",
            "parent": parent,
        }
    except Exception as e:
        return None


def enum_windows_callback(hwnd, windows):
    """Callback for EnumWindows, collects visible windows"""
    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
        windows.append(hwnd)
    return True


def get_all_windows():
    """Get list of all visible windows"""
    windows = []
    win32gui.EnumWindows(enum_windows_callback, windows)
    return windows


def find_window_by_title_substring(substring):
    """Find windows that contain substring in title"""
    matching_windows = []

    def callback(hwnd, pattern):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if pattern.lower() in title.lower():
                matching_windows.append(hwnd)
        return True

    win32gui.EnumWindows(callback, substring)
    return matching_windows


def find_window_by_class_substring(substring):
    """Find windows that contain substring in class name"""
    matching_windows = []

    def callback(hwnd, pattern):
        if win32gui.IsWindowVisible(hwnd):
            class_name = win32gui.GetClassName(hwnd)
            if pattern.lower() in class_name.lower():
                matching_windows.append(hwnd)
        return True

    win32gui.EnumWindows(callback, substring)
    return matching_windows


def get_window_under_cursor():
    """Get window handle under cursor"""
    point = wintypes.POINT()
    win32gui.GetCursorPos(point)
    hwnd = win32gui.WindowFromPoint((point.x, point.y))

    if hwnd:
        # Get top-level window
        return win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
    return None


class WindowInspectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Inspector")
        self.root.geometry("600x500")
        self.root.attributes("-topmost", True)  # Always on top

        # Set up the main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Window selection frame
        self.selection_frame = ttk.LabelFrame(
            self.main_frame, text="Window Selection", padding="5"
        )
        self.selection_frame.pack(fill=tk.X, expand=False, pady=5)

        # Dropdown for windows
        self.window_var = tk.StringVar()
        self.window_dropdown = ttk.Combobox(
            self.selection_frame, textvariable=self.window_var, width=60
        )
        self.window_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.window_dropdown.bind("<<ComboboxSelected>>", self.on_window_selected)

        # Update button
        self.update_button = ttk.Button(
            self.selection_frame, text="Update List", command=self.update_window_list
        )
        self.update_button.pack(side=tk.LEFT, padx=5)

        # Window information display
        self.info_frame = ttk.LabelFrame(
            self.main_frame, text="Window Information", padding="5"
        )
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Create labeled fields for window info
        self.info_fields = {
            "hwnd": self.create_info_field("Window Handle (HWND):"),
            "title": self.create_info_field("Window Title:"),
            "class": self.create_info_field("Class Name:"),
            "process": self.create_info_field("Process Name:"),
            "style": self.create_info_field("Window Style:"),
            "ex_style": self.create_info_field("Extended Style:"),
            "parent": self.create_info_field("Parent Window:"),
        }

        # Configuration code block
        self.code_frame = ttk.LabelFrame(
            self.main_frame, text="Code for window_identification.py", padding="5"
        )
        self.code_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.code_text = tk.Text(self.code_frame, height=8, wrap=tk.WORD)
        self.code_text.pack(fill=tk.BOTH, expand=True)

        # Copy to clipboard button
        self.copy_button = ttk.Button(
            self.code_frame, text="Copy to Clipboard", command=self.copy_to_clipboard
        )
        self.copy_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Initialize
        self.windows_list = []
        self.windows_map = {}
        self.current_hwnd = None
        self.update_window_list()

    def create_info_field(self, label_text):
        """Create a labeled field for displaying window info"""
        frame = ttk.Frame(self.info_frame)
        frame.pack(fill=tk.X, expand=False, pady=2)

        label = ttk.Label(frame, text=label_text, width=20)
        label.pack(side=tk.LEFT)

        value = ttk.Entry(frame)
        value.pack(side=tk.LEFT, fill=tk.X, expand=True)

        return value

    def update_window_list(self):
        """Update the list of windows in the dropdown"""
        self.windows_list = get_all_windows()
        self.windows_map = {}

        dropdown_items = []
        for hwnd in self.windows_list:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            display_text = f"{title} - {class_name} ({hwnd})"
            dropdown_items.append(display_text)
            self.windows_map[display_text] = hwnd

        self.window_dropdown["values"] = dropdown_items
        if dropdown_items:
            self.window_dropdown.current(0)
            self.on_window_selected(None)

    def on_window_selected(self, event):
        """Handle window selection from dropdown"""
        selected = self.window_dropdown.get()
        if selected in self.windows_map:
            hwnd = self.windows_map[selected]
            self.update_window_info(hwnd)

    def update_window_info(self, hwnd):
        """Update the displayed window information"""
        self.current_hwnd = hwnd
        info = get_window_info(hwnd)
        if info:
            for key, entry in self.info_fields.items():
                entry.delete(0, tk.END)
                entry.insert(0, str(info.get(key, "")))

            # Generate code snippet
            self.generate_code_snippet(info)

    def generate_code_snippet(self, info):
        """Generate a code snippet for window_identification.py"""
        class_name = info.get("class", "")
        title = info.get("title", "")
        process = info.get("process", "")

        # Generate window identification logic
        code = f"""# Add to window_identification.py
# Window class: {class_name}
# Window title: {title}
# Process: {process}

"""

        # Check for general patterns
        if process:
            code += f"""# By process name:
if process_name and "{process}" in process_name:
    return "{class_name.lower()}"

"""

        if class_name and class_name.lower() == "cabinetwclass":
            code += f"""# Specific match for File Explorer (CabinetWClass):
if class_name == "CabinetWClass":
    return "cabinetwclass"

"""

        if "SDL_app" in title or "SDL" in class_name:
            code += f"""# SDL application:
if "SDL" in class_name or "SDL_app" in title:
    return "sdl_app"

"""

        if "Sticky" in title and "ApplicationFrameWindow" in class_name:
            code += f"""# Sticky Notes UWP app:
if class_name == "ApplicationFrameWindow" and "Sticky" in title:
    return "uwp_sticky"

"""

        self.code_text.delete(1.0, tk.END)
        self.code_text.insert(tk.END, code)

    def copy_to_clipboard(self):
        """Copy the generated code to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.code_text.get(1.0, tk.END))
        self.root.update()  # Required for clipboard to work


def main():
    root = tk.Tk()
    app = WindowInspectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
