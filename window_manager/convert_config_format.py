import json
import os
from pathlib import Path
import window_scanner


def convert_config():
    """
    Convert old config format to new format with process and class information.
    This helps with the transition from process-name only configs to the more precise
    process+class configs.
    """
    config_path = Path("defined_window_positions.json")

    if not config_path.exists():
        print(f"No config file found at {config_path}")
        return

    # Load existing config
    with open(config_path, "r", encoding="utf-8") as f:
        old_config = json.load(f)

    if not old_config:
        print("Config is empty, nothing to convert.")
        return

    # Create backup of old config
    backup_path = config_path.with_suffix(".json.bak")
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(old_config, f, indent=2, ensure_ascii=False)
    print(f"Created backup of old config at {backup_path}")

    # Get current windows to match process names with classes
    print("Scanning current windows to obtain class information...")
    windows = window_scanner.scan_windows()

    # Process to window class mapping
    process_to_class = {}
    for window in windows:
        process_name = window.get("process_name", "").replace(".exe", "")
        window_class = window.get("class", "")
        if process_name and window_class:
            process_to_class[process_name] = window_class

    # Create new config
    new_config = {}

    for key, value in old_config.items():
        if isinstance(value, dict) and all(
            k in value for k in ["x", "y", "width", "height"]
        ):
            # This is a position config entry
            if "|" in key:
                # Already in new format
                new_config[key] = value
                continue

            # Old format - try to find the window class
            process_name = key
            if process_name in process_to_class:
                window_class = process_to_class[process_name]
                config_key = f"{process_name}|{window_class}"

                # Create new format entry
                new_config[config_key] = {
                    "process": process_name,
                    "class": window_class,
                    "x": value.get("x", 0),
                    "y": value.get("y", 0),
                    "width": value.get("width", 800),
                    "height": value.get("height", 600),
                }
                print(f"Converted: {process_name} → {config_key}")
            else:
                # Can't find window class, keep old format as-is but mark for manual update
                print(
                    f"Warning: Could not find window class for {process_name}, keeping old format"
                )
                new_config[process_name] = value
        else:
            # Not a standard position entry, keep as-is
            new_config[key] = value

    # Save the new config
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2, ensure_ascii=False)

    print(f"Saved new config format to {config_path}")
    print(f"Converted {len(new_config)} entries")


if __name__ == "__main__":
    convert_config()
