# OfflineLauncher

A fast, offline application launcher for Windows that lets you quickly find and start applications.

## 🚀 Features

- **Global Hotkey (Shift+F)** – Instantly search and launch apps.
- **Fast & Lightweight** – Optimized for minimal resource usage.
- **Portable & Installer Versions** – Choose the best fit for your needs.
- **Modern Dark Interface** – Clean and distraction-free design.
- **Comprehensive Scanning** – Finds all installed applications quickly.
- **Appears in Center of Screen** – Easy to access without interfering with workflow.

## 📥 Download

### **Latest Release**
[![GitHub Release](https://img.shields.io/github/v/release/siam404/offline_app_launcher)](https://github.com/siam404/offline_app_launcher/releases/latest)

- **Installer Version**: [Download OfflineLauncher_Setup.exe](https://github.com/siam404/offline_app_launcher/releases/download/v1.0.0/OfflineLauncher_Setup.exe)
- **Portable Version**: [Download OfflineLauncher_portable.zip](https://github.com/siam404/offline_app_launcher/releases/download/v1.0.0/OfflineLauncher_portable.zip)

## 🛠 Installation

### **Installer Version**
1. Download `OfflineLauncher_Setup.exe` from the link above.
2. Run the installer and follow the on-screen instructions.
3. Once installed, launch the app using the **Shift + F** shortcut.

### **Portable Version**
1. Download `OfflineLauncher_portable.zip`.
2. Extract the ZIP file to your preferred location.
3. Run `OfflineLauncher.exe` – no installation required!

## 📌 Usage

- **Launch quickly**: Press **Shift + F** to open the search bar.
- **Type and search**: Instantly find apps and open them.
- **Minimal design**: Simple and distraction-free interface.
- **Navigation**:
  - Press **Enter** to launch the selected application.
  - Press **Escape** to hide the launcher.
  - Use **Up/Down arrows** to navigate through results.

## 📂 Project Structure

### `src/`
Contains the main source code for the application:
- `launcher.py` - Main application source code
- `requirements.txt` - Python dependencies
- `launch.bat` - Quick launch batch script

### `assets/`
Contains visual assets for the application:
- `app_icon.png` - Application icon in PNG format
- `app_icon.ico` - Application icon in ICO format for Windows

### `docs/`
Contains documentation:
- `README.md` - Main application documentation
- `INSTALLER_README.md` - Installation instructions

### `build_tools/`
Contains scripts and specs for building the application:
- `build_portable.py` - Script to build the portable version
- `build_installer.py` - Script to build the Windows installer
- `fix_startup_issue.py` - Script to fix Windows startup issues
- `OfflineLauncher.spec` - PyInstaller spec file

### `installer/`
Contains installer-related files:
- `OfflineLauncher_installer.nsi` - NSIS installer script
- `OfflineLauncher_Setup.exe` - Windows installer
- `nsis/` - NSIS setup files

### `portable/`
Contains portable versions of the application:
- `OfflineLauncher_portable.zip` - Portable version (ZIP)
- `OfflineLauncher_Installer/` - Installer distribution folder

### `build/` and `dist/`
Auto-generated build directories used by PyInstaller

## ⚙ Development

To build from source:
1. Install requirements: `pip install -r src/requirements.txt`
2. Build portable: `python build_tools/build_portable.py`
3. Build installer: `python build_tools/build_installer.py`

## ❗ Troubleshooting

**If not all applications are showing up:**
- Run the launcher as administrator once to ensure it can access all registry locations.
- Wait for the initial scan to complete (may take a moment on first run).
- Check the console for any error messages during scanning.

**If hotkeys don't work:**
- Make sure another application isn't already using the same hotkeys.
- Try running the launcher as administrator.
- Check the console for any error messages related to hotkey registration.
- Note that the keyboard library requires administrative privileges on some systems.

## 📜 License

This project is licensed under the MIT License – see the `LICENSE` file for details.

---

> Feel free to contribute and improve OfflineLauncher! Fork, star ⭐, and submit PRs!

