# Window Tagger

A minimalist window management system that lets you tag windows and control their positioning.

currently this mess starts with auto_resize.py

## Core Concept

The system works by tagging windows based on their properties (process name, class name, title). Each tag can have:
- A default zone (where the window should be positioned)
- Custom offsets (fine-tuning the position)

## Key Features

- **Tag Windows**: Automatically identify windows based on their properties
- **Zone System**: Define different screen zones for window positioning
- **Null Zones**: Tag windows without forcing them into a zone (they stay where you put them)
- **Fine Control**: Adjust window positions with pixel-perfect offsets
- **Quick Access**: Win+C to position a window, Ctrl+Alt+T to tag a new window

## How It Works

0. Toggle taskbar (Win+F12)

1. Tag a window (Ctrl+Alt+T)
   - System identifies the window's properties
   - You can choose which properties to match
   - Substring matching for title
   - Optionally set a default zone
   - Fine-tune the position with offsets

2. Use the window (Win+C)
   - If the window has a default zone: positions it there
   - If no default zone: leaves it where it is
   - Applies any saved offsets

3. Auto resize process
   - runs on background
   - monitors all windows
   - if window has tag and default zone, resize it to the default zone during window creation
   - if window has tag and no default zone

## Files

- `tag_definitions.json`: Window matching rules
- `tag_offsets.json`: Position adjustments
- `zones.json`: Screen zones
- `tag_zones.json`: Default zones for tags

## Hotkeys

- `Ctrl+Alt+T`: Open tagger
- `Win+C`: Position active window
- `Win+F12`: Toggle taskbar
