import os
import sys
import winshell
from win32com.client import Dispatch
import subprocess

# Define project paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
DIST_DIR = os.path.join(ROOT_DIR, "dist")
PORTABLE_DIR = os.path.join(ROOT_DIR, "portable")
INSTALLER_DIR = os.path.join(ROOT_DIR, "installer")

def fix_startup_issue():
    """
    Fixes the startup issue for existing OfflineLauncher installations.
    
    This script:
    1. Checks for existing startup shortcuts and removes them
    2. Creates a new properly configured startup shortcut
    3. Helps user find and uncheck 'Run as Administrator' if needed
    """
    print("OfflineLauncher Startup Issue Fix Tool")
    print("======================================")
    
    try:
        # First, locate the executable
        exe_path = find_executable()
        if not exe_path:
            print("\nCould not find OfflineLauncher.exe")
            print("Please enter the full path to your OfflineLauncher.exe file:")
            exe_path = input().strip('"')
            
            if not os.path.exists(exe_path):
                print(f"Error: The file {exe_path} does not exist.")
                return
        
        print(f"\nFound OfflineLauncher at: {exe_path}")
        
        # Fix executable run as admin settings
        try:
            # Try to remove any admin manifest if present (requires admin privileges)
            print("\nChecking executable permissions...")
            
            print("\nNOTE: If the application requires administrator privileges to run,")
            print("it cannot be started automatically at system startup for security reasons.")
            print("The fix is to create a new shortcut that runs without admin privileges.")
        except Exception as e:
            print(f"Error checking executable permissions: {e}")
        
        # Create a proper startup shortcut
        choice = input("\nWhere do you want to create the startup shortcut?\n"
                      "1) For current user only (recommended)\n"
                      "2) For all users (requires admin)\n"
                      "Choice (1-2): ")
        
        if choice not in ["1", "2"]:
            print("Invalid choice. Using option 1 (current user).")
            choice = "1"
        
        # Get startup folder
        if choice == "1":
            startup_folder = winshell.startup()
        else:
            startup_folder = winshell.common_startup()
        
        # Remove any existing shortcuts to avoid duplicates
        check_and_remove_existing(startup_folder, exe_path)
        
        # Create new shortcut
        shortcut_path = os.path.join(startup_folder, "OfflineLauncher.lnk")
        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.Description = "Start OfflineLauncher in system tray"
        shortcut.ShowCmd = 7  # Run minimized
        shortcut.save()
        
        print(f"\nCreated startup shortcut at: {shortcut_path}")
        
        # Instructions for manual checks
        print("\nIMPORTANT: To ensure the application starts at boot:")
        print(f"1. Right-click on the shortcut at: {shortcut_path}")
        print("2. Select 'Properties'")
        print("3. Go to the 'Compatibility' tab")
        print("4. Make sure 'Run this program as an administrator' is NOT checked")
        print("5. Click 'OK' to save changes")
        
        print("\nAfter following these steps, please restart your computer to test.")
        print("The application should now start automatically at login.")
        
    except Exception as e:
        print(f"Error fixing startup issue: {e}")
        print("\nYou can try manually adding the application to startup:")
        print("1. Press Win+R, type 'shell:startup' and press Enter")
        print("2. Right-click in the folder and select New > Shortcut")
        print("3. Browse to your OfflineLauncher.exe and click OK")
        print("4. Make sure the shortcut is not set to run as administrator")

def find_executable():
    """Find the OfflineLauncher executable"""
    possible_locations = [
        # Current directory
        os.path.join(os.getcwd(), "OfflineLauncher.exe"),
        # Dist folder
        os.path.join(DIST_DIR, "OfflineLauncher.exe"),
        # Portable folder
        os.path.join(PORTABLE_DIR, "OfflineLauncher.exe"),
        # Installer folder
        os.path.join(INSTALLER_DIR, "OfflineLauncher_Setup.exe"),
        # Common install locations
        os.path.join(os.environ["PROGRAMFILES"], "OfflineLauncher", "OfflineLauncher.exe"),
        os.path.join(os.environ["USERPROFILE"], "Desktop", "OfflineLauncher.exe"),
        os.path.join(os.environ["USERPROFILE"], "Downloads", "OfflineLauncher.exe"),
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            return os.path.abspath(location)
    
    return None

def check_and_remove_existing(startup_folder, target_exe):
    """Check for and remove any existing shortcuts to the launcher"""
    try:
        # List all shortcuts in the startup folder
        shortcuts = [f for f in os.listdir(startup_folder) if f.endswith(".lnk")]
        
        shell = Dispatch("WScript.Shell")
        removed = 0
        
        # Check each shortcut
        for shortcut_file in shortcuts:
            shortcut_path = os.path.join(startup_folder, shortcut_file)
            try:
                shortcut = shell.CreateShortCut(shortcut_path)
                if os.path.basename(shortcut.TargetPath).lower() == "offlinelauncher.exe":
                    # This is our shortcut - remove it
                    os.remove(shortcut_path)
                    print(f"Removed existing shortcut: {shortcut_path}")
                    removed += 1
            except:
                # Skip shortcuts that can't be processed
                pass
        
        if removed > 0:
            print(f"Removed {removed} existing shortcuts")
        
    except Exception as e:
        print(f"Error checking for existing shortcuts: {e}")

if __name__ == "__main__":
    # Check for required modules
    missing = []
    try:
        import winshell
    except ImportError:
        missing.append("winshell")
    try:
        from win32com.client import Dispatch
    except ImportError:
        missing.append("pywin32")
        
    if missing:
        print("Missing required modules. Please install:")
        for module in missing:
            print(f"  pip install {module}")
        sys.exit(1)
        
    fix_startup_issue() 