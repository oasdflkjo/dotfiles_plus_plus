import win32gui
import win32api
import win32con
import win32process
import os

# Standardized window definitions
# Each entry has:
#   - window_title: Expected window title ('' for any, or a specific string to match)
#   - class_name: Expected class name ('' for any, or a specific class to match)
#   - process_name: Expected process name ('' for any, or a specific process to match)
#   - name: The identifier we want to use for this window type
WINDOW_DEFINITIONS = [
    {
        "window_title": "",
        "class_name": "org.wezfurlong.wezterm",
        "process_name": "wezterm-gui.exe",
        "name": "wezterm_app",
    },
    {
        "window_title": "MobaXterm",
        "class_name": "TApplication",
        "process_name": "mobaxterm.exe",
        "name": "mobaxterm_app",
    },
    {
        "window_title": "",
        "class_name": "CASCADIA_HOSTING_WINDOW_CLASS",
        "process_name": "windowsterminal.exe",
        "name": "windows_terminal",
    },
    {
        "window_title": "PowerShell",
        "class_name": "CASCADIA_HOSTING_WINDOW_CLASS",
        "process_name": "",
        "name": "powershell_terminal",
    },
    {
        "window_title": "",
        "class_name": "Notepad",
        "process_name": "notepad.exe",
        "name": "notepad",
    },
    {
        "window_title": "Steam",
        "class_name": "SDL_app",
        "process_name": "steamwebhelper.exe",
        "name": "steam_app",
    },
    {
        "window_title": "Google Chrome",
        "class_name": "Chrome_WidgetWin_1",
        "process_name": "chrome.exe",
        "name": "chrome_browser",
    },
    {
        "window_title": "Cursor",
        "class_name": "Chrome_WidgetWin_1",
        "process_name": "cursor.exe",
        "name": "cursor_app",
    },
    {
        "window_title": "Visual Studio Code",
        "class_name": "Chrome_WidgetWin_1",
        "process_name": "code.exe",
        "name": "vscode_app",
    },
    {
        "window_title": "Discord",
        "class_name": "Chrome_WidgetWin_1",
        "process_name": "discord.exe",
        "name": "discord_app",
    },
    {
        "window_title": "Spotify",
        "class_name": "Chrome_WidgetWin_1",
        "process_name": "spotify.exe",
        "name": "spotify_app",
    },
]


def identify_window(hwnd):
    """Identify a window using the standardized definitions"""
    if not hwnd:
        return None

    # Get window properties
    window_title = win32gui.GetWindowText(hwnd)
    class_name = win32gui.GetClassName(hwnd)
    process_name = get_process_name(hwnd)

    # Try to match against our definitions first
    for definition in WINDOW_DEFINITIONS:
        # Skip empty string values - only check non-empty criteria

        # Check process name (only if specified)
        if definition["process_name"] != "":
            if definition["process_name"] not in process_name:
                continue

        # Check class name (only if specified)
        if definition["class_name"] != "":
            if definition["class_name"] != class_name:
                continue

        # Check window title (only if specified) - partial match
        if definition["window_title"] != "":
            if definition["window_title"] not in window_title:
                continue

        # All specified conditions match, use this definition
        return definition["name"]

    # If no match found in our definitions, return unknown_app
    return "unknown_app"


def get_process_name(hwnd):
    """Get process name for a window handle"""
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
    except:
        pass
    return ""
