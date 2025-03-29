# OfflineLauncher

A fast, offline application launcher for Windows that lets you quickly find and start applications.

## Project Structure

The project is organized into the following folders:

### src/
Contains the main source code for the application:
- `launcher.py` - Main application source code
- `requirements.txt` - Python dependencies
- `launch.bat` - Quick launch batch script

### assets/
Contains visual assets for the application:
- `app_icon.png` - Application icon in PNG format
- `app_icon.ico` - Application icon in ICO format for Windows

### docs/
Contains documentation:
- `README.md` - Main application documentation
- `INSTALLER_README.md` - Installation instructions

### build_tools/
Contains scripts and specs for building the application:
- `build_portable.py` - Script to build the portable version
- `build_installer.py` - Script to build the Windows installer
- `fix_startup_issue.py` - Script to fix Windows startup issues
- `OfflineLauncher.spec` - PyInstaller spec file

### installer/
Contains installer-related files:
- `OfflineLauncher_installer.nsi` - NSIS installer script
- `OfflineLauncher_Setup.exe` - Windows installer
- `nsis/` - NSIS setup files

### portable/
Contains portable versions of the application:
- `OfflineLauncher_portable.zip` - Portable version (ZIP)
- `OfflineLauncher_Installer/` - Installer distribution folder

### build/ and dist/
Auto-generated build directories used by PyInstaller

## Key Features

- Fast, responsive search for all installed applications
- No internet connection required
- Modern dark interface
- Global hotkey (Shift+F) to show/hide the launcher from anywhere
- Available as both installer and portable versions

## Getting Started

1. For installation: Use the installer in `installer/OfflineLauncher_Setup.exe`
2. For portable use: Extract `portable/OfflineLauncher_portable.zip`

## Development

To build from source:
1. Install requirements: `pip install -r src/requirements.txt`
2. Build portable: `python build_tools/build_portable.py`
3. Build installer: `python build_tools/build_installer.py`

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