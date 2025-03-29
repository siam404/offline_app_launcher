import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
import tempfile
from PIL import Image

# Define project paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
INSTALLER_DIR = os.path.join(ROOT_DIR, "installer")
PORTABLE_DIR = os.path.join(ROOT_DIR, "portable")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
DIST_DIR = os.path.join(ROOT_DIR, "dist")

def download_file(url, target_file):
    """Download a file from a URL to a target location"""
    print(f"Downloading {url} to {target_file}...")
    urllib.request.urlretrieve(url, target_file)
    print("Download complete!")

def convert_png_to_ico(png_path, ico_path):
    """Convert PNG to ICO format"""
    print(f"Converting {png_path} to {ico_path}...")
    try:
        # Open the PNG image
        img = Image.open(png_path)
        
        # Save as ICO
        img.save(ico_path, format='ICO')
        print("Conversion complete!")
        return True
    except Exception as e:
        print(f"Error converting PNG to ICO: {e}")
        return False

def build_installer():
    """Build the OfflineLauncher installer package"""
    print("Building OfflineLauncher installer...")
    
    # Ensure we have a dist directory with the executable
    executable_path = os.path.join(DIST_DIR, "OfflineLauncher.exe")
    if not os.path.exists(executable_path):
        print("OfflineLauncher.exe not found in dist directory!")
        print("Building executable first...")
        try:
            build_portable_script = os.path.join(os.path.dirname(__file__), "build_portable.py")
            subprocess.run([sys.executable, build_portable_script], check=True)
        except subprocess.CalledProcessError:
            print("Failed to build the executable. Aborting installer creation.")
            return False
    
    # Make sure app_icon.png exists and convert to ICO
    png_icon_path = os.path.join(ASSETS_DIR, "app_icon.png")
    if not os.path.exists(png_icon_path):
        print(f"ERROR: {png_icon_path} not found!")
        return False
    
    # Convert PNG to ICO
    ico_icon_path = os.path.join(ASSETS_DIR, "app_icon.ico")
    if not os.path.exists(ico_icon_path) and not convert_png_to_ico(png_icon_path, ico_icon_path):
        print("ERROR: Failed to convert icon to ICO format!")
        return False
    
    # Create installer directory if it doesn't exist
    if not os.path.exists(INSTALLER_DIR):
        os.makedirs(INSTALLER_DIR)
    
    # Update the NSIS script to use the ICO file and work with new paths
    nsis_script_path = os.path.join(INSTALLER_DIR, "OfflineLauncher_installer.nsi")
    
    # Create new NSIS script with updated paths
    with open(nsis_script_path, 'w') as f:
        f.write(f'''; OfflineLauncher Installer Script
; Created with NSIS

!include "MUI2.nsh"
!include "LogicLib.nsh"

; Application information
!define PRODUCT_NAME "OfflineLauncher"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "OfflineLauncher"
!define PRODUCT_WEB_SITE ""
!define PRODUCT_DIR_REGKEY "Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\OfflineLauncher.exe"
!define PRODUCT_UNINST_KEY "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{PRODUCT_NAME}}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "{ico_icon_path}"
!define MUI_UNICON "{ico_icon_path}"

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "{os.path.join(DOCS_DIR, 'README.md')}"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; Product information
Name "${{PRODUCT_NAME}} ${{PRODUCT_VERSION}}"
OutFile "{os.path.join(INSTALLER_DIR, 'OfflineLauncher_Setup.exe')}"
InstallDir "$PROGRAMFILES\\OfflineLauncher"
InstallDirRegKey HKLM "${{PRODUCT_DIR_REGKEY}}" ""
ShowInstDetails show
ShowUnInstDetails show

; Install main application
Section "OfflineLauncher" SEC01
  SectionIn RO
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  ; Include main executable and required files
  File "{executable_path}"
  File "{ico_icon_path}"
  File "{os.path.join(DOCS_DIR, 'README.md')}"
  
  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\\OfflineLauncher"
  CreateShortcut "$SMPROGRAMS\\OfflineLauncher\\OfflineLauncher.lnk" "$INSTDIR\\OfflineLauncher.exe" "" "$INSTDIR\\app_icon.ico"
  CreateShortcut "$DESKTOP\\OfflineLauncher.lnk" "$INSTDIR\\OfflineLauncher.exe" "" "$INSTDIR\\app_icon.ico"
  CreateShortcut "$SMPROGRAMS\\OfflineLauncher\\Uninstall OfflineLauncher.lnk" "$INSTDIR\\uninstall.exe" "" "$INSTDIR\\uninstall.exe" 0
  
  ; Write registry entries for uninstallation
  WriteRegStr HKLM "${{PRODUCT_DIR_REGKEY}}" "" "$INSTDIR\\OfflineLauncher.exe"
  WriteRegStr ${{PRODUCT_UNINST_ROOT_KEY}} "${{PRODUCT_UNINST_KEY}}" "DisplayName" "$(^Name)"
  WriteRegStr ${{PRODUCT_UNINST_ROOT_KEY}} "${{PRODUCT_UNINST_KEY}}" "UninstallString" "$INSTDIR\\uninstall.exe"
  WriteRegStr ${{PRODUCT_UNINST_ROOT_KEY}} "${{PRODUCT_UNINST_KEY}}" "DisplayIcon" "$INSTDIR\\app_icon.ico"
  WriteRegStr ${{PRODUCT_UNINST_ROOT_KEY}} "${{PRODUCT_UNINST_KEY}}" "DisplayVersion" "${{PRODUCT_VERSION}}"
  WriteRegStr ${{PRODUCT_UNINST_ROOT_KEY}} "${{PRODUCT_UNINST_KEY}}" "Publisher" "${{PRODUCT_PUBLISHER}}"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

; Add startup option
Section "Run at Startup" SEC02
  CreateShortcut "$SMSTARTUP\\OfflineLauncher.lnk" "$INSTDIR\\OfflineLauncher.exe" "" "$INSTDIR\\app_icon.ico"
SectionEnd

; Uninstaller section
Section Uninstall
  ; Remove shortcuts, installation directory and registry keys
  Delete "$SMPROGRAMS\\OfflineLauncher\\OfflineLauncher.lnk"
  Delete "$DESKTOP\\OfflineLauncher.lnk"
  Delete "$SMSTARTUP\\OfflineLauncher.lnk"
  
  RMDir "$SMPROGRAMS\\OfflineLauncher"
  
  Delete "$INSTDIR\\OfflineLauncher.exe"
  Delete "$INSTDIR\\app_icon.ico"
  Delete "$INSTDIR\\README.md"
  Delete "$INSTDIR\\uninstall.exe"
  
  RMDir "$INSTDIR"
  
  DeleteRegKey ${{PRODUCT_UNINST_ROOT_KEY}} "${{PRODUCT_UNINST_KEY}}"
  DeleteRegKey HKLM "${{PRODUCT_DIR_REGKEY}}"
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${{SEC01}} "Install the OfflineLauncher application"
  !insertmacro MUI_DESCRIPTION_TEXT ${{SEC02}} "Configure OfflineLauncher to start automatically with Windows"
!insertmacro MUI_FUNCTION_DESCRIPTION_END
''')
    
    # Download NSIS if it's not already installed
    nsis_portable_url = "https://sourceforge.net/projects/nsis/files/NSIS%203/3.09/nsis-3.09.zip/download"
    nsis_dir = os.path.join(INSTALLER_DIR, "nsis")
    
    if not os.path.exists(nsis_dir):
        print("NSIS not found. Downloading portable version...")
        os.makedirs(nsis_dir, exist_ok=True)
        
        # Create a temporary directory for the download
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Download NSIS
            nsis_zip = os.path.join(tmp_dir, "nsis.zip")
            download_file(nsis_portable_url, nsis_zip)
            
            # Extract NSIS
            print("Extracting NSIS...")
            with zipfile.ZipFile(nsis_zip, 'r') as zip_ref:
                zip_ref.extractall(tmp_dir)
            
            # Find the NSIS directory in the extracted files
            for root, dirs, files in os.walk(tmp_dir):
                for dir_name in dirs:
                    if dir_name.lower().startswith("nsis"):
                        extracted_nsis_dir = os.path.join(root, dir_name)
                        # Move the NSIS directory to our target location
                        shutil.copytree(extracted_nsis_dir, nsis_dir, dirs_exist_ok=True)
                        break
    
    # Get the path to makensis.exe
    makensis_exe = os.path.join(nsis_dir, "makensis.exe")
    if not os.path.exists(makensis_exe):
        makensis_exe = os.path.join(nsis_dir, "bin", "makensis.exe")
        
    if not os.path.exists(makensis_exe):
        print("ERROR: Could not find makensis.exe in the NSIS directory!")
        return False
    
    # Compile the installer script
    print("Compiling installer script...")
    os.chdir(ROOT_DIR)  # Change to root directory for compilation
    result = subprocess.run([makensis_exe, nsis_script_path], check=False)
    
    if result.returncode != 0:
        print("ERROR: Failed to compile the installer script!")
        return False
    
    # Check if the installer was created
    installer_exe = os.path.join(INSTALLER_DIR, "OfflineLauncher_Setup.exe")
    if os.path.exists(installer_exe):
        print(f"\nInstaller created successfully: {installer_exe}")
        size_mb = os.path.getsize(installer_exe) / (1024 * 1024)
        print(f"Installer size: {size_mb:.2f} MB")
        
        # Create a distribution folder
        dist_folder = os.path.join(PORTABLE_DIR, "OfflineLauncher_Installer")
        os.makedirs(dist_folder, exist_ok=True)
        
        # Copy installer and README to distribution folder
        shutil.copy(installer_exe, os.path.join(dist_folder, "OfflineLauncher_Setup.exe"))
        
        installer_readme = os.path.join(DOCS_DIR, "INSTALLER_README.md")
        if os.path.exists(installer_readme):
            shutil.copy(installer_readme, os.path.join(dist_folder, "README.md"))
        
        print(f"\nDistribution files created in folder: {dist_folder}")
        return True
    else:
        print("ERROR: Installer was not created!")
        return False

if __name__ == "__main__":
    build_installer() 