# Window Tagger

A simple background application that allows you to tag windows and fine-tune their position and size with precise offsets.

## Features

- Run in the background and listen for hotkeys
- Tag active windows based on process name, class name, or window title
- Apply precise offsets to window position (X, Y) and size (width, height)
- Real-time saving of offsets whenever adjustments are made
- Store window offsets that can be applied to any base zone
- Auto-fills tag name with the application's process name
- Global Win+C hotkey to center windows based on their tags

## Hotkeys

- **Ctrl+Alt+T**: Open the tagging interface for the active window
- **Win+C**: Center the active window using its saved tag definition

## Usage

1. Run the application:
   ```
   python app.py
   ```
   or use the PowerShell script:
   ```
   .\start.ps1
   ```

2. When you want to tag or adjust a window:
   - Make the window active (click on it to bring it to the foreground)
   - Press `Ctrl+Alt+T` to open the tagging GUI
   - Use the adjustment buttons to fine-tune:
     - X Position: Move window left/right
     - Y Position: Move window up/down
     - Width: Adjust window width
     - Height: Adjust window height
   - Each adjustment reapplies all offsets immediately to see the effect
   - Offsets are saved automatically with each adjustment
   - The tag name is pre-filled with the application's name
   - Click "Reset Offsets" to return to the base size and position
   - Finalize the tag by selecting matching criteria
   - Click "Save Tag" to save the tag definition

3. To quickly center a window using its saved tag:
   - Make the window active
   - Press `Win+C`
   - The window will be positioned according to its tag and offsets
   - If the window has no matching tag, it will flash but not be repositioned
   
4. To exit the application, press `Ctrl+C` in the terminal where it's running

## Configuration Files

- `tag_definitions.json` - Contains window identification information
- `tag_offsets.json` - Contains window offsets for each tagged window (updated in real-time)
- `zones.json` - Contains the base definition of the centered window zone

## How Offsets Work

The application stores four separate offsets for each window:

1. **X Offset**: Adjusts the horizontal position (positive = right, negative = left)
2. **Y Offset**: Adjusts the vertical position (positive = down, negative = up)
3. **Width Offset**: Adjusts the window width (positive = wider, negative = narrower)
4. **Height Offset**: Adjusts the window height (positive = taller, negative = shorter)

These offsets are applied to the base values defined in zones.json. For example:

```
Base values from zones.json:
X: 630, Y: 20, Width: 1493, Height: 1120

Offsets for "chrome" window:
X: -5, Y: 10, Width: 2, Height: -15

Final window position/size:
X: 625, Y: 30, Width: 1495, Height: 1105
```

After each adjustment, the window is immediately repositioned with all current offsets applied, allowing you to see the cumulative effect of your changes.

## Tag Definitions

Tags are stored in `tag_definitions.json` in the same directory as the application. 