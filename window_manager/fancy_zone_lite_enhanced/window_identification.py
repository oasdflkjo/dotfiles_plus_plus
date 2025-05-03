import win32gui
import win32api
import win32con
import win32process
import os


def identify_window(hwnd):
    """Core function to identify window type reliably"""
    if not hwnd:
        return None

    title = win32gui.GetWindowText(hwnd)
    class_name = win32gui.GetClassName(hwnd)

    # Get process name when possible, for extra reliability
    process_name = ""
    try:
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        hProcess = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid
        )
        if hProcess:
            try:
                process_path = win32process.GetModuleFileNameEx(hProcess, 0)
                process_name = os.path.basename(process_path).lower()
            finally:
                win32api.CloseHandle(hProcess)
    except:
        process_name = ""

    # If we have process name, use it for more reliable identification
    if process_name:
        if "chrome.exe" in process_name or "msedge.exe" in process_name:
            return "chrome_browser"
        if "code.exe" in process_name:
            return "vscode_app"
        if "cursor.exe" in process_name:
            return "cursor_app"
        if "spotify.exe" in process_name:
            return "spotify_app"
        if "discord.exe" in process_name:
            return "discord_app"
        if "wezterm-gui.exe" in process_name:
            return "wezterm_app"
        if "windowsterminal.exe" in process_name:
            return "windows_terminal"
        if "notepad.exe" in process_name:
            return "notepad"

    # Direct class name matching for specific applications
    if class_name == "org.wezfurlong.wezterm":
        return "wezterm_terminal"

    if class_name == "CASCADIA_HOSTING_WINDOW_CLASS":
        # Windows Terminal (includes PowerShell)
        if "PowerShell" in title:
            return "powershell_terminal"
        return "windows_terminal"

    if class_name == "Notepad":
        return "notepad"

    # Fall back to class+title patterns if process name isn't available
    if class_name == "Chrome_WidgetWin_1":
        # Check if it's a browser first - browser always has " - Browser" in title for Chrome
        if (
            " - Google Chrome" in title
            or " - Chrome" in title
            or " - Microsoft Edge" in title
        ):
            return "chrome_browser"

        # Common Electron apps - only if process name check didn't work
        if "Cursor" in title and "chrome.exe" not in process_name:
            return "cursor_app"
        if "Visual Studio Code" in title and "chrome.exe" not in process_name:
            return "vscode_app"
        if "Discord" in title and "chrome.exe" not in process_name:
            return "discord_app"
        if "Spotify" in title and "chrome.exe" not in process_name:
            return "spotify_app"
        if "Teams" in title and "chrome.exe" not in process_name:
            return "teams_app"
        if "WhatsApp" in title and "chrome.exe" not in process_name:
            return "whatsapp_app"

        # If title contains a website name and process is chrome, it's a browser
        if process_name and (
            "chrome.exe" in process_name or "msedge.exe" in process_name
        ):
            return "chrome_browser"

        # Default for other Electron apps
        first_word = title.split()[0] if title else "unknown"
        return f"electron_{first_word.lower()}"

    # UWP/Modern Windows apps
    elif class_name in ["ApplicationFrameWindow", "Windows.UI.Core.CoreWindow"]:
        first_word = title.split()[0] if title else "unknown"
        return f"uwp_{first_word.lower()}"

    # Terminal apps
    elif (
        "term" in class_name.lower()
        or "shell" in class_name.lower()
        or class_name == "ConsoleWindowClass"
        or "wezterm" in class_name.lower()
    ):
        return f"terminal_{class_name.lower()}"

    # Default to class name
    return f"{class_name.lower()}"
