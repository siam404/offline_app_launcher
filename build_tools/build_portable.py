import os
import subprocess
import sys
import shutil
import winshell
from win32com.client import Dispatch

# Define project paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
PORTABLE_DIR = os.path.join(ROOT_DIR, "portable")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
DIST_DIR = os.path.join(ROOT_DIR, "dist")

def build_portable_exe():
    """
    Builds a portable executable of the launcher application using PyInstaller.
    Makes sure the executable runs without showing a console window and includes the app icon.
    """
    print("Building portable executable...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Ensure all dependencies are installed
    requirements_path = os.path.join(SRC_DIR, "requirements.txt")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=True)
    
    # Create a directory for the build if it doesn't exist
    if not os.path.exists(BUILD_DIR):
        os.makedirs(BUILD_DIR)
    
    # Build with PyInstaller
    icon_path = os.path.join(ASSETS_DIR, "app_icon.png")
    launcher_path = os.path.join(SRC_DIR, "launcher.py")
    
    # Use --noconsole to hide the terminal
    # Use --onefile to create a single executable
    # Use --icon to set the application icon
    # Use --add-data to include data files
    # Use --windowed to ensure it runs in window mode
    pyinstaller_command = [
        "pyinstaller",
        "--noconsole",      # No console window
        "--onefile",        # Single file executable
        "--windowed",       # Ensures it runs in windowed mode, no console
        f"--icon={icon_path}",  # Application icon
        "--name=OfflineLauncher", # Name of the output exe
        "--add-data", f"{icon_path};.", # Include icon file
        # Add additional configuration options
        "--hiddenimport=PIL._tkinter_finder", # Ensure PIL Tkinter support works
        launcher_path  # Main script
    ]
    
    # Change to the project root directory before running PyInstaller
    os.chdir(ROOT_DIR)
    subprocess.run(pyinstaller_command, check=True)
    
    print("\nPortable executable built successfully!")
    print(f"You can find it in the 'dist' folder as 'OfflineLauncher.exe'")
    
    # Create portable directory if it doesn't exist
    if not os.path.exists(PORTABLE_DIR):
        os.makedirs(PORTABLE_DIR)
    
    # Create a zip file for distribution
    portable_zip_path = os.path.join(PORTABLE_DIR, "OfflineLauncher_portable.zip")
    try:
        import zipfile
        with zipfile.ZipFile(portable_zip_path, 'w') as zipf:
            zipf.write(os.path.join(DIST_DIR, 'OfflineLauncher.exe'), 'OfflineLauncher.exe')
            zipf.write(os.path.join(DOCS_DIR, 'README.md'), 'README.md')
            zipf.write(os.path.join(ASSETS_DIR, 'app_icon.png'), 'app_icon.png')
            portable_instructions = os.path.join(DOCS_DIR, 'PORTABLE_INSTRUCTIONS.md')
            if os.path.exists(portable_instructions):
                zipf.write(portable_instructions, 'PORTABLE_INSTRUCTIONS.md')
        print(f"Created portable zip file: {portable_zip_path}")
    except Exception as e:
        print(f"Error creating zip file: {e}")
    
    # Create startup shortcut
    create_startup_option()
    
    print("\nInstallation Instructions:")
    print("1. Extract OfflineLauncher_portable.zip to any location")
    print("2. Double-click OfflineLauncher.exe to run")
    print("3. The application will run in the system tray")
    print("4. Press the configured hotkey (default: shift+f) to show the launcher")
    print("5. The search box should immediately be focused and ready for typing")
    print("6. To run at startup: Choose option 1 or 2 when prompted")

def create_startup_option():
    """
    Offers to create a startup shortcut for the portable application.
    """
    try:
        choice = input("\nDo you want to add the application to Windows startup?\n"
                      "1) Yes - for current user only\n"
                      "2) Yes - for all users (requires admin)\n"
                      "3) No\n"
                      "Choice (1-3): ")
        
        if choice not in ["1", "2"]:
            print("No startup shortcut created.")
            return
            
        # Get path to the executable
        exe_path = os.path.join(DIST_DIR, "OfflineLauncher.exe")
        if not os.path.exists(exe_path):
            print(f"Error: Could not find executable at {exe_path}")
            return
            
        # Determine startup folder
        if choice == "1":
            # Current user startup
            startup_folder = winshell.startup()
        else:
            # All users startup (requires admin)
            startup_folder = winshell.common_startup()
            
        # Create shortcut
        shortcut_path = os.path.join(startup_folder, "OfflineLauncher.lnk")
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.Description = "Start OfflineLauncher in system tray"
        # Set to run minimized (SW_SHOWMINNOACTIVE = 7)
        shortcut.ShowCmd = 7
        shortcut.save()
        
        print(f"Startup shortcut created in: {startup_folder}")
        print("The application will now start automatically when you log in.")
        
        # Try to ensure shortcut doesn't run as admin
        print("\nIMPORTANT: Make sure the shortcut is NOT set to 'Run as administrator':")
        print(f"1. Right-click on the shortcut at: {shortcut_path}")
        print("2. Select 'Properties'")
        print("3. Go to the 'Compatibility' tab")
        print("4. Make sure 'Run this program as an administrator' is NOT checked")
        print("5. Click 'OK' to save changes")
    except Exception as e:
        print(f"Error creating startup shortcut: {e}")
        print("You can manually add the application to startup:")
        print(f"1. Copy {exe_path}")
        print(f"2. Press Win+R, type 'shell:startup' and press Enter")
        print("3. Right-click in the folder and choose 'Paste shortcut'")
        print("4. Right-click the shortcut, choose Properties, and set it to run minimized")

if __name__ == "__main__":
    build_portable_exe() 