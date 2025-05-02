import win32gui
import win32process
import psutil
import json
import os


def get_window_info():
    """Get information about all visible windows."""
    windows = []

    def enum_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True

        title = win32gui.GetWindowText(hwnd)
        if not title:
            return True

        try:
            # Get window class
            window_class = win32gui.GetClassName(hwnd)

            # Get window position and size
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Skip windows with zero dimensions
            if width <= 0 or height <= 0:
                return True

            # Get process information
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process_name = psutil.Process(pid).name()
            except:
                process_name = "Unknown"

            # Add to windows list
            windows.append(
                {
                    "title": title,
                    "class": window_class,
                    "process_name": process_name,
                    "x": left,
                    "y": top,
                    "width": width,
                    "height": height,
                }
            )
        except Exception as e:
            print(f"Error processing window {title}: {e}")

        return True

    win32gui.EnumWindows(enum_callback, None)
    return windows


def create_config(windows):
    """Create a configuration template from window information."""
    config = {"default": {"x": 100, "y": 100, "width": 800, "height": 600}}

    # Track processed applications
    processed = set()

    # Process all windows
    for window in windows:
        # Get app name (without .exe)
        process_name = window.get("process_name", "")
        app_name = process_name.replace(".exe", "")

        # Skip already processed apps and system/unknown apps
        if (
            not app_name
            or app_name.lower() == "unknown"
            or app_name.lower() in processed
        ):
            continue

        # Add to configuration
        processed.add(app_name.lower())
        config[app_name] = {
            "x": window.get("x", 100),
            "y": window.get("y", 100),
            "width": window.get("width", 800),
            "height": window.get("height", 600),
        }

    # Handle special cases for Chrome, etc.
    for window in windows:
        window_class = window.get("class", "").lower()
        if window_class == "chrome_widgetwin_1" and "chrome" not in processed:
            processed.add("chrome")
            config["Chrome"] = {
                "x": window.get("x", 100),
                "y": window.get("y", 100),
                "width": window.get("width", 800),
                "height": window.get("height", 600),
            }

    return config


def main():
    """Main function to generate configuration."""
    print("Scanning windows...")
    windows = get_window_info()
    print(f"Found {len(windows)} windows")

    # Create configuration
    config = create_config(windows)
    print(f"Created configuration with {len(config)} entries")

    # Save to JSON file
    output_file = "window_config.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"Configuration saved to {os.path.abspath(output_file)}")

    # Print first few entries as verification
    print("\nConfiguration example:")
    i = 0
    for app, settings in config.items():
        print(f"  {app}: {settings}")
        i += 1
        if i >= 3:
            break

    if len(config) > 3:
        print(f"  ... and {len(config) - 3} more")


if __name__ == "__main__":
    main()
