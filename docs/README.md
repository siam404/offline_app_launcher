# Offline Launcher

A fast, offline application launcher for Windows that lets you quickly find and start applications.

## Features

- Fast, responsive search for all installed applications
- No internet connection required
- Modern dark interface
- Appears in center of screen
- Comprehensive scanning of installed applications
- Global hotkeys to show/hide the launcher from anywhere

## Installation

1. Make sure you have Python 3.6 or newer installed
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Run the launcher:
   ```
   python launcher.py
   ```

## Usage

- Press **Shift+F** to toggle the launcher from anywhere (show/hide)
- Press Enter to launch the selected application
- Press Escape to hide the launcher
- Use Up/Down arrows to navigate through results
- Type to search for applications

## Troubleshooting

If not all applications are showing up:
- Run the launcher as administrator once to ensure it can access all registry locations
- Wait for the initial scan to complete (may take a moment on first run)
- Check the console for any error messages during scanning

If hotkeys don't work:
- Make sure another application isn't already using the same hotkeys
- Try running the launcher as administrator
- Check the console for any error messages related to hotkey registration
- Note that the keyboard library requires administrative privileges on some systems 