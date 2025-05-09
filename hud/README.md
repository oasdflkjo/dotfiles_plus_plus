# HUD Framework

A Python implementation of a rainmeter-like HUD framework for Windows desktops.

## Features

- Lightweight desktop widgets
- Hot-reloading for widget code and configurations
- Position persistence
- Low system resource usage

## Included Widgets

- Clock widget
- Gmail notification widget

## Installation

1. Ensure you have Python 3.8+ installed.
2. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

Start the HUD framework by running:

```
python main.py
```

## Creating New Widgets

New widgets can be created by extending the BaseWidget class. See the clock and gmail widgets for examples. 