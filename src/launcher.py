import tkinter as tk
from tkinter import ttk # Optional, for themed widgets
import winreg
import subprocess
import os
import sys
import glob
from pathlib import Path
# Additional imports for better application discovery
import winshell
from win32com.client import Dispatch
# Use keyboard library for hotkeys (simpler and more reliable)
import keyboard
import json
import threading
import time
import atexit
# Add pystray for system tray icon
import pystray
from PIL import Image, ImageDraw
import io

# --- Windows API specific imports for hotkeys ---
import win32api
import win32con
import win32gui

# --- Constants ---
APP_NAME = "OfflineLauncher"
# Remove CONFIG_FILE constant and use hardcoded hotkey
HARDCODED_HOTKEY = "shift+f"
# --- Hotkey constants ---
HOTKEY_ID_BASE = 1000
# Map of modifier names to win32con values
MODIFIER_MAP = {
    "shift": win32con.MOD_SHIFT,
    "ctrl": win32con.MOD_CONTROL,
    "control": win32con.MOD_CONTROL,
    "alt": win32con.MOD_ALT,
    "win": win32con.MOD_WIN
}

# --- Application Data ---
installed_apps = [] # List to hold {'name': 'Display Name', 'path': 'executable_path'}
# For hotkey management
hotkey_registered = False
exit_event = threading.Event()
config = {}  # Keep this for backward compatibility but don't use it
launcher_hidden = False
root = None  # Global reference to root window

# --- Functions ---

def load_config():
    """Set configuration with hardcoded hotkey."""
    global config
    # Use hardcoded hotkey instead of loading from file
    config = {
        "hotkeys": [HARDCODED_HOTKEY]
    }
    print(f"Using hardcoded hotkey: {HARDCODED_HOTKEY}")

def get_screen_center(window):
    """Calculates center coordinates for the window."""
    # Force an update to get accurate window dimensions
    window.update_idletasks()
    
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Get window dimensions - first attempt
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    
    # If dimensions are too small (not yet rendered properly), use requested size
    if window_width <= 1 or window_height <= 1:
        window_width = window.winfo_reqwidth()
        window_height = window.winfo_reqheight()
    
    # Calculate center position
    x = max(0, (screen_width // 2) - (window_width // 2))
    y = max(0, (screen_height // 2) - (window_height // 2))
    
    return x, y

def extract_executable_path(display_icon_str):
    """Tries to extract a valid executable path from DisplayIcon registry value."""
    if not display_icon_str:
        return None
    path_part = display_icon_str.split(',')[0]
    path = path_part.strip('"').strip()
    if path and os.path.exists(path) and path.lower().endswith((".exe", ".com", ".bat", ".cmd")):
        return path
    return None

def scan_installed_apps():
    """Scans multiple sources for installed applications."""
    global installed_apps
    apps = {}  # Dictionary to avoid duplicates
    
    # Track progress
    print("Scanning for installed applications...")
    
    # --- 1. Scan Windows Registry ---
    print("Scanning Windows Registry...")
    _scan_registry(apps)
    
    # --- 2. Scan Start Menu ---
    print("Scanning Start Menu...")
    _scan_start_menu(apps)
    
    # --- 3. Scan Common Program Directories ---
    print("Scanning common program directories...")
    _scan_program_dirs(apps)
    
    # --- 4. Scan Desktop Shortcuts ---
    print("Scanning desktop shortcuts...")
    _scan_desktop(apps)
    
    # --- Convert to list and sort by name ---
    installed_apps = sorted(list(apps.values()), key=lambda x: x['name'].lower())
    print(f"Scan complete. Found {len(installed_apps)} applications.")

def _scan_registry(apps_dict):
    """Scan Windows Registry for installed applications."""
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for hkey, key_path in registry_paths:
        try:
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_READ | winreg.KEY_ENUMERATE_SUB_KEYS) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            # For App Paths registry key, structure is different
                            if "App Paths" in key_path:
                                try:
                                    path = winreg.QueryValueEx(subkey, "")[0]
                                    if path and os.path.exists(path) and path.lower().endswith(".exe"):
                                        # Use filename as app name if subkey_name ends with .exe
                                        if subkey_name.lower().endswith(".exe"):
                                            name = os.path.splitext(os.path.basename(subkey_name))[0]
                                        else:
                                            name = os.path.splitext(os.path.basename(path))[0]
                                        
                                        app_key = path.lower()
                                        if app_key not in apps_dict:
                                            apps_dict[app_key] = {'name': name, 'path': path}
                                except (FileNotFoundError, OSError):
                                    pass
                            else:
                                # For Uninstall registry keys
                                display_name = None
                                display_icon = None
                                install_location = None

                                def query_value(subkey_handle, value_name):
                                    try: return winreg.QueryValueEx(subkey_handle, value_name)[0]
                                    except (FileNotFoundError, OSError): return None

                                display_name = query_value(subkey, "DisplayName")
                                if not display_name or not isinstance(display_name, str):
                                    i += 1
                                    continue

                                # Skip certain types of entries
                                system_component = query_value(subkey, "SystemComponent")
                                if system_component == 1: 
                                    i += 1
                                    continue
                                    
                                # Skip Windows Updates and certain system components
                                name_lower = display_name.lower()
                                filter_terms = ["update", "hotfix", "patch", "redistributable", 
                                               "security update", "webview2 runtime",
                                               "microsoft visual c++", "microsoft .net"]
                                if any(term in name_lower for term in filter_terms): 
                                    i += 1
                                    continue

                                # Look for executable path
                                path = None
                                
                                # Try DisplayIcon first
                                display_icon = query_value(subkey, "DisplayIcon")
                                if display_icon and isinstance(display_icon, str):
                                    path = extract_executable_path(display_icon)
                                
                                # Try InstallLocation if no path yet
                                if not path:
                                    uninstall_string = query_value(subkey, "UninstallString")
                                    if uninstall_string and isinstance(uninstall_string, str):
                                        # Extract the directory and look for main EXE
                                        uninstall_dir = os.path.dirname(uninstall_string.strip('"'))
                                        if os.path.exists(uninstall_dir):
                                            potential_exes = glob.glob(os.path.join(uninstall_dir, "*.exe"))
                                            for exe in potential_exes:
                                                if not os.path.basename(exe).lower().startswith("unins"):
                                                    path = exe
                                                    break
                                
                                # Try InstallLocation
                                if not path:
                                    install_location = query_value(subkey, "InstallLocation")
                                    if install_location and isinstance(install_location, str) and os.path.isdir(install_location):
                                        app_name_part = ''.join(c for c in display_name.split('(')[0].strip() 
                                                               if c.isalnum() or c == ' ').strip()
                                        potential_exes = [
                                            app_name_part + ".exe",
                                            display_name.split('(')[0].strip() + ".exe",
                                            subkey_name + ".exe"
                                        ]
                                        
                                        # Also check for any .exe files
                                        exe_files = glob.glob(os.path.join(install_location, "*.exe"))
                                        for exe_file in exe_files:
                                            file_name = os.path.basename(exe_file)
                                            # Skip uninstaller and setup files
                                            if not any(x in file_name.lower() for x in ["unins", "setup", "install"]):
                                                potential_exes.append(file_name)
                                        
                                        for exe_name in potential_exes:
                                            potential_path = os.path.join(install_location, exe_name)
                                            if os.path.exists(potential_path) and os.path.isfile(potential_path):
                                                path = potential_path
                                                break

                                if path:
                                    app_key = path.lower()
                                    if app_key not in apps_dict:
                                        apps_dict[app_key] = {'name': display_name.strip(), 'path': path}
                    except OSError:
                        break  # No more subkeys
                    except Exception as e:
                        print(f"Warning: Error processing registry key: {e}")
                    finally:
                        i += 1
        except (FileNotFoundError, OSError):
            pass
        except Exception as e:
            print(f"Error scanning registry path ({key_path}): {e}")

def _scan_start_menu(apps_dict):
    """Scan Windows Start Menu for applications."""
    try:
        # Common Start Menu paths
        start_menu_paths = [
            os.path.join(os.environ["PROGRAMDATA"], "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs")
        ]
        
        for start_menu_path in start_menu_paths:
            if os.path.exists(start_menu_path):
                # Process both shortcuts and subfolders
                _process_shortcut_dir(start_menu_path, apps_dict)
    except Exception as e:
        print(f"Error scanning Start Menu: {e}")

def _process_shortcut_dir(directory, apps_dict, depth=0, max_depth=3):
    """Process a directory containing shortcuts."""
    if depth > max_depth:
        return  # Prevent excessive recursion
        
    try:
        # Process all .lnk files in this directory
        for shortcut_path in glob.glob(os.path.join(directory, "*.lnk")):
            try:
                # Parse the shortcut
                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                target_path = shortcut.Targetpath
                
                # Skip non-executable targets
                if not target_path or not target_path.lower().endswith((".exe", ".bat", ".cmd")):
                    continue
                    
                # Skip Windows system files
                if "\\Windows\\" in target_path and any(x in target_path.lower() for x in 
                                                      ["system32", "syswow64", "setup", "installer"]):
                    continue
                
                # Get app name from shortcut name
                app_name = os.path.splitext(os.path.basename(shortcut_path))[0]
                
                # Add to apps dictionary
                app_key = target_path.lower()
                if os.path.exists(target_path) and app_key not in apps_dict:
                    apps_dict[app_key] = {'name': app_name, 'path': target_path}
            except Exception as e:
                print(f"Error processing shortcut {shortcut_path}: {e}")
        
        # Process subdirectories
        for subdir in [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]:
            subdir_path = os.path.join(directory, subdir)
            _process_shortcut_dir(subdir_path, apps_dict, depth + 1, max_depth)
    
    except Exception as e:
        print(f"Error processing directory {directory}: {e}")

def _scan_program_dirs(apps_dict):
    """Scan common program directories for executables."""
    program_dirs = [
        os.environ.get("PROGRAMFILES", "C:\\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")
    ]
    
    # Only scan top-level directories to avoid taking too long
    for program_dir in program_dirs:
        if os.path.exists(program_dir):
            try:
                # Get all top-level directories
                for vendor_dir in [d for d in os.listdir(program_dir) 
                                  if os.path.isdir(os.path.join(program_dir, d))]:
                    vendor_path = os.path.join(program_dir, vendor_dir)
                    
                    # Look for .exe files in this directory and immediate subdirectories
                    for exe_path in glob.glob(os.path.join(vendor_path, "*.exe")):
                        _add_exe_to_apps(exe_path, apps_dict)
                    
                    # Check one level deeper
                    for subdir in [d for d in os.listdir(vendor_path) 
                                  if os.path.isdir(os.path.join(vendor_path, d))]:
                        subdir_path = os.path.join(vendor_path, subdir)
                        for exe_path in glob.glob(os.path.join(subdir_path, "*.exe")):
                            _add_exe_to_apps(exe_path, apps_dict)
            except Exception as e:
                print(f"Error scanning program directory {program_dir}: {e}")

def _scan_desktop(apps_dict):
    """Scan desktop for application shortcuts."""
    try:
        # Get desktop path using winshell
        desktop = winshell.desktop()
        _process_shortcut_dir(desktop, apps_dict)
        
        # Also check common desktop
        common_desktop = winshell.desktop(common=True)
        _process_shortcut_dir(common_desktop, apps_dict)
    except Exception as e:
        print(f"Error scanning desktop: {e}")

def _add_exe_to_apps(exe_path, apps_dict):
    """Helper to add an executable to the apps dictionary with filtering."""
    try:
        # Skip system utilities and small executables (likely not full applications)
        file_size = os.path.getsize(exe_path)
        
        # Skip small executables (less than 100KB) as they're likely helpers/utilities
        if file_size < 100 * 1024:
            return
            
        # Skip executables in certain folders
        if any(x in exe_path.lower() for x in ["\\windows\\", "\\system32\\", "\\syswow64\\", 
                                             "\\temp\\", "\\tmp\\", "uninstall", "setup"]):
            return
            
        # Get app name from executable name
        app_name = os.path.splitext(os.path.basename(exe_path))[0]
        
        # Improve app name by replacing underscores and dashes with spaces
        app_name = app_name.replace("_", " ").replace("-", " ")
        
        # Title case the app name for nicer display
        app_name = " ".join(word.capitalize() for word in app_name.split())
        
        # Add to apps dictionary
        app_key = exe_path.lower()
        if app_key not in apps_dict:
            apps_dict[app_key] = {'name': app_name, 'path': exe_path}
    except Exception as e:
        print(f"Error adding exe to apps list {exe_path}: {e}")

# --- Hotkey Related Functions ---
def register_hotkeys():
    """Register global hotkeys to show the launcher."""
    global hotkey_registered
    
    try:
        # Use hardcoded hotkey instead of config
        hotkeys = [HARDCODED_HOTKEY]
        
        # Clear any existing hotkeys
        clear_hotkeys()
        
        # Register each hotkey
        for hotkey_str in hotkeys:
            try:
                # Use suppress=True to prevent the system beep/alert sound
                keyboard.add_hotkey(hotkey_str, toggle_launcher_visibility, suppress=True)
                print(f"Registered hotkey: {hotkey_str}")
                hotkey_registered = True
            except Exception as e:
                print(f"Failed to register hotkey: {hotkey_str} - {e}")
                
    except Exception as e:
        print(f"Error registering hotkeys: {e}")
        hotkey_registered = False

def clear_hotkeys():
    """Clear all registered hotkeys."""
    try:
        keyboard.unhook_all()
    except Exception as e:
        print(f"Error clearing hotkeys: {e}")

def toggle_launcher_visibility():
    """Toggle the visibility of the launcher window."""
    global launcher_hidden, root
    
    if root is None:
        print("Error: Root window not initialized")
        return
        
    # Check if we need to create a new launcher window or show an existing one
    if launcher_hidden:
        # Find if there's an existing launcher window
        launcher_ui = None
        for widget in root.winfo_children():
            if isinstance(widget, LauncherWindow):
                launcher_ui = widget
                break
                
        if launcher_ui:
            # Show existing window - call show_and_focus which handles focus correctly
            launcher_ui.show_and_focus()
        else:
            # Create new launcher window - the constructor calls show_and_focus
            launcher_ui = LauncherWindow(root)
            
        launcher_hidden = False
        
        # Add extra focus checks to ensure the entry widget gets focus
        # These are scheduled with increasing delays to overcome any focus stealing
        root.after(150, lambda: force_entry_focus(launcher_ui))
        root.after(300, lambda: force_entry_focus(launcher_ui))
    else:
        # Hide all launcher windows
        for widget in root.winfo_children():
            if isinstance(widget, LauncherWindow):
                widget.grab_release()  # Release grab before withdrawing
                widget.withdraw()
        launcher_hidden = True
        
    print(f"Launcher visibility toggled. Hidden: {launcher_hidden}")

def force_entry_focus(launcher_window):
    """Force focus to the entry widget of the launcher window."""
    if launcher_window and hasattr(launcher_window, 'entry'):
        try:
            launcher_window.focus_force()
            launcher_window.entry.focus_force()
            launcher_window.entry.icursor(tk.END)
        except Exception as e:
            print(f"Error forcing focus: {e}")

class LauncherWindow(tk.Toplevel):
    """The main launcher UI window."""
    def __init__(self, master):
        super().__init__(master)
        self.title(APP_NAME)
        self.overrideredirect(True)  # No window decorations
        self.attributes("-topmost", True)  # Keep window on top
        
        # Prevent appearing in taskbar
        if sys.platform == 'win32':
            self.wm_attributes('-toolwindow', 1)  # Don't show in taskbar
        
        # Set window style
        bg_color = "#2e2e2e"
        fg_color = "white"
        accent_color = "#0078d4"
        
        # --- Main container frame ---
        self.frame = tk.Frame(self, bg=bg_color, padx=12, pady=12, borderwidth=1, relief="solid")
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Top section with title ---
        self.title_frame = tk.Frame(self.frame, bg=bg_color)
        self.title_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.title_label = tk.Label(self.title_frame, text=APP_NAME, 
                                   font=('Segoe UI', 16, 'bold'), 
                                   bg=bg_color, fg=fg_color)
        self.title_label.pack(side=tk.LEFT)
        
        # --- Search box ---
        self.search_frame = tk.Frame(self.frame, bg=bg_color)
        self.search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._update_suggestions)
        
        self.search_icon = tk.Label(self.search_frame, text="🔍", font=('Segoe UI', 14),
                                   bg=bg_color, fg=fg_color)
        self.search_icon.pack(side=tk.LEFT, padx=(0, 5))
        
        self.entry = tk.Entry(self.search_frame, textvariable=self.search_var,
                             font=('Segoe UI', 14), bd=0, highlightthickness=1,
                             highlightbackground="#555555", highlightcolor=accent_color,
                             bg="#3c3c3c", fg=fg_color, insertbackground=fg_color)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # --- Results list ---
        self.listbox_frame = tk.Frame(self.frame, bg=bg_color)
        self.listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.listbox = tk.Listbox(self.listbox_frame, font=('Segoe UI', 12), 
                                 bg="#3c3c3c", fg=fg_color, 
                                 selectbackground=accent_color, selectforeground=fg_color,
                                 highlightthickness=0, bd=0, 
                                 activestyle='none', height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL, 
                                     command=self.listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
        
        # --- Status bar ---
        self.status_frame = tk.Frame(self.frame, bg=bg_color)
        self.status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = tk.Label(self.status_frame, 
                                    text=f"Found {len(installed_apps)} applications", 
                                    font=('Segoe UI', 9), 
                                    bg=bg_color, fg="#aaaaaa")
        self.status_label.pack(side=tk.LEFT)
        
        # Show hotkey info in the status bar - use hardcoded hotkey
        self.hint_label = tk.Label(self.status_frame, 
                                  text=f"Enter - Launch | Esc - Hide | {HARDCODED_HOTKEY} - Toggle", 
                                  font=('Segoe UI', 9), 
                                  bg=bg_color, fg="#aaaaaa")
        self.hint_label.pack(side=tk.RIGHT)
        
        # --- Bindings ---
        self.entry.bind("<Return>", self._launch_selected)
        self.entry.bind("<KP_Enter>", self._launch_selected) # Numpad Enter
        self.entry.bind("<Escape>", self._hide_app) # Changed to hide instead of quit
        self.entry.bind("<Down>", self._move_selection_down)
        self.entry.bind("<Up>", self._move_selection_up)
        self.bind("<FocusOut>", self._check_focus_lost)
        
        self.listbox.bind("<Double-Button-1>", self._launch_selected)
        self.listbox.bind("<ButtonRelease-1>", self._launch_selected) # Single click launch
        self.listbox.bind("<Return>", self._launch_selected)
        self.listbox.bind("<KP_Enter>", self._launch_selected)
        self.listbox.bind("<Escape>", self._hide_app) # Changed to hide instead of quit
        
        self.current_results = []
        
        # Show the window centered and focused on creation
        # Call AFTER all widgets are created and packed
        self.show_and_focus()

    def _update_suggestions(self, *args):
        """Filter apps based on search query and update listbox."""
        query = self.search_var.get().lower().strip()
        self.listbox.delete(0, tk.END)
        self.current_results = []
        self.listbox.config(fg="white")  # Reset color

        if not query:
            # If no query, show most used or recent apps
            self.status_label.config(text=f"Found {len(installed_apps)} applications")
            # Show a limited number of apps as examples
            sample_size = min(10, len(installed_apps))
            self.current_results = installed_apps[:sample_size]
            for app in self.current_results:
                display_name = app['name'][:70] + '...' if len(app['name']) > 70 else app['name']
                self.listbox.insert(tk.END, display_name)
        else:
            # Apply multi-term search
            exact_matches = []
            starts_with = []
            contains = []
            
            # Split search into terms for better matching
            query_terms = query.lower().split()
            
            for app in installed_apps:
                name_lower = app['name'].lower()
                
                # Skip if any term is completely missing
                if not all(term in name_lower for term in query_terms):
                    continue
                
                # Check exact match
                if name_lower == query:
                    exact_matches.append(app)
                # Check starts with first term
                elif name_lower.startswith(query_terms[0]):
                    starts_with.append(app)
                # Contains all terms
                else:
                    contains.append(app)
            
            # Combine results in order of relevance
            self.current_results = exact_matches + starts_with + contains
            
            # Update status label with count
            self.status_label.config(text=f"Found {len(self.current_results)} matches")
            
            # Add results to listbox
            if self.current_results:
                for app in self.current_results:
                    display_name = app['name'][:70] + '...' if len(app['name']) > 70 else app['name']
                    self.listbox.insert(tk.END, display_name)
            else:
                self.listbox.insert(tk.END, "No matching applications found")
                self.listbox.config(fg="gray")

        # Select first item if there are results
        if self.current_results:
            self.listbox.select_set(0)
            self.listbox.activate(0)
            
    def _launch_selected(self, event=None):
        """Launch the currently selected application and hide."""
        # For single-click in listbox, need to ensure the click was on an item
        if event and event.type == '4':  # ButtonRelease event
            index = self.listbox.nearest(event.y)
            if index != self.listbox.curselection():
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)
                self.listbox.activate(index)
                return "break"  # Don't launch on selection change
                
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            if self.listbox.size() > 0 and event and event.keysym in ('Return', 'KP_Enter') and self.current_results:
                selected_indices = (0,)
            else: 
                return

        selected_index = selected_indices[0]
        if 0 <= selected_index < len(self.current_results):
            app_to_launch = self.current_results[selected_index]
            try:
                print(f"Launching: {app_to_launch['name']} ({app_to_launch['path']})")
                
                # Update status to show launching
                self.status_label.config(text=f"Launching {app_to_launch['name']}...", fg="light green")
                self.update()
                
                # Get the directory of the application
                app_dir = os.path.dirname(app_to_launch['path'])
                
                # Launch the application
                subprocess.Popen([app_to_launch['path']], cwd=app_dir,
                                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                                close_fds=True)
                
                # Hide launcher after brief pause to confirm launch
                self.after(100, self._hide_app)
            except Exception as e:
                print(f"Error launching {app_to_launch['name']}: {e}")
                self._show_error_message(f"Error launching:\n{app_to_launch['name']}\n{type(e).__name__}: {e}")
        else:
            print(f"Invalid selected index {selected_index}")

    def _show_error_message(self, message):
        """Displays a temporary error message."""
        print(f"DEBUG: Showing error message: {message}")
        self.listbox.delete(0, tk.END)
        self.current_results = []
        lines = message.split('\n')
        for i, line in enumerate(lines):
             if len(line) > 70: line = line[:67] + '...'
             self.listbox.insert(tk.END, line)
        self.listbox.config(fg="red")
        self.listbox.see(0)

    def _clear_error_message(self):
         print("DEBUG: Clearing error message.")
         self.listbox.config(fg="white")
         self._update_suggestions()

    def _move_selection_down(self, event=None):
        """Move listbox selection down."""
        current_selection = self.listbox.curselection()
        max_index = self.listbox.size() - 1
        if max_index < 0: return "break"
        current_index = -1
        if current_selection: current_index = current_selection[0]
        next_index = 0
        if current_index < max_index: next_index = current_index + 1
        if current_selection: self.listbox.select_clear(current_index)
        self.listbox.select_set(next_index)
        self.listbox.activate(next_index)
        self.listbox.see(next_index)
        return "break"

    def _move_selection_up(self, event=None):
        """Move listbox selection up."""
        current_selection = self.listbox.curselection()
        max_index = self.listbox.size() - 1
        if max_index < 0: return "break"
        current_index = 0
        if current_selection: current_index = current_selection[0]
        prev_index = max_index
        if current_index > 0: prev_index = current_index - 1
        if current_selection: self.listbox.select_clear(current_index)
        self.listbox.select_set(prev_index)
        self.listbox.activate(prev_index)
        self.listbox.see(prev_index)
        return "break"

    def show_and_focus(self):
        """Make the window visible, centered, and focused."""
        # Configure window size before showing it
        self.minsize(600, 400)  # Set minimum window size
        
        # Set a fixed size for the window
        self.geometry("600x400")
        
        # Force update to calculate sizes
        self.update_idletasks()
        
        # Calculate center position
        x, y = get_screen_center(self)
        
        # Set window position
        self.geometry(f"+{x}+{y}")
        
        # Show the window
        self.deiconify()
        
        # Set window style and make it stand out
        self.attributes("-alpha", 0.95)  # Slight transparency
        
        # Make sure this window is the active window
        self.lift()
        self.attributes("-topmost", True)
        
        # Ensure this window gets and keeps focus
        self.focus_set()
        self.focus_force()
        
        # Grab all input so it can't lose focus until released
        self.grab_set()
        
        # Directly set focus to the entry widget multiple times
        # First force focus
        self.entry.focus_set()
        self.entry.focus_force()
        
        # Set cursor position at the end of any text
        self.entry.icursor(tk.END)
        
        # Schedule additional focus calls to defeat any focus stealing
        self.after(10, lambda: self.entry.focus_force())
        self.after(50, lambda: self.entry.focus_force())
        self.after(100, lambda: self.entry.focus_force())
        
        # Reset search text
        self.search_var.set("")
        self._update_suggestions()

    def _hide_app(self, event=None):
        """Hides the application instead of quitting."""
        global launcher_hidden
        print("DEBUG: Hiding application.")
        self.grab_release()  # Release input grab
        self.withdraw()
        launcher_hidden = True
        return "break"

    def _check_focus_lost(self, event=None):
        """Check if focus moved outside the launcher window and hide if so."""
        # This checks if the widget currently holding focus *within this app*
        # is NOT the main window, the entry, or the listbox. If focus moves
        # truly outside the app, focus_get() might return None or the root.
        focused_widget = self.focus_get()
        if focused_widget not in (self, self.entry, self.listbox, self.frame):
             # Adding a small delay because focus shifts can be rapid/intermediate
             # Only hide if focus is *still* outside after a moment
             self.after(50, self._confirm_focus_lost)

    def _confirm_focus_lost(self):
        """Confirms focus is still lost and then hides."""
        focused_widget = self.focus_get()
        if focused_widget not in (self, self.entry, self.listbox, self.frame):
            print("DEBUG: Focus confirmed lost, hiding.")
            self._hide_app()
        else:
            print("DEBUG: Focus returned to launcher, not hiding.")

def create_tray_icon():
    """Create and return a system tray icon."""
    # Load icon from file if it exists, otherwise create a default one
    icon_path = "app_icon.png"
    if os.path.exists(icon_path):
        icon_image = Image.open(icon_path)
    else:
        # Create a default icon
        icon_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(icon_image)
        d.ellipse((0, 0, 64, 64), fill=(0, 120, 212))
        d.text((20, 20), "OL", fill=(255, 255, 255))

    # Define menu items
    def show_launcher():
        global launcher_hidden, root
        if root and launcher_hidden:
            # Must be run in the main thread
            root.after(0, toggle_launcher_visibility)

    def exit_app():
        global root, tray_icon
        if tray_icon:
            tray_icon.stop()
        if root:
            root.quit()

    # Create system tray icon
    menu = (
        pystray.MenuItem('Show Launcher', show_launcher),
        pystray.MenuItem('Exit', exit_app)
    )
    
    icon = pystray.Icon(APP_NAME, icon_image, APP_NAME, menu)
    return icon

def run_tray_icon():
    """Run the system tray icon in a separate thread."""
    global tray_icon
    tray_icon.run()

# --- Main Execution ---
if __name__ == "__main__":
    # Check for required packages
    missing_packages = []
    try:
        import winshell
    except ImportError:
        missing_packages.append("winshell")
    
    try:
        from win32com.client import Dispatch
    except ImportError:
        missing_packages.append("pywin32")
        
    try:
        import keyboard
    except ImportError:
        missing_packages.append("keyboard")
    
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        missing_packages.append("pystray")
        missing_packages.append("Pillow")
    
    if missing_packages:
        print("ERROR: Missing required packages. Please install the following:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nRun: pip install -r requirements.txt")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Load configuration
    load_config()
    
    # 1. Scan for applications
    print("Scanning for installed applications...")
    
    # Create root window during scan to avoid flickering
    root = tk.Tk()
    root.withdraw()  # Hide the main root window
    
    # Make root window truly invisible
    root.attributes("-alpha", 0)  # Make fully transparent
    
    # Set focus mode to be more aggressive (helps with focus issues)
    root.tk.call('tk_focusFollowsMouse')
    
    # Configure style for better appearance
    root.option_add('*TkDefaultFont', 'Segoe UI 10')
    if sys.platform == 'win32':
        try:
            root.iconbitmap(default='NONE')  # Remove the default Tk icon
            # Prevent the root window from showing in taskbar or alt+tab
            root.wm_attributes("-toolwindow", 1)
        except:
            pass
    
    # Show a scanning progress window
    scan_window = tk.Toplevel(root)
    scan_window.title("Scanning")
    scan_window.geometry("300x100")
    scan_window.overrideredirect(True)
    scan_window.configure(bg="#2e2e2e")
    
    # Place in center of screen
    scan_window.update_idletasks()
    width = scan_window.winfo_width()
    height = scan_window.winfo_height()
    x = (scan_window.winfo_screenwidth() // 2) - (width // 2)
    y = (scan_window.winfo_screenheight() // 2) - (height // 2)
    scan_window.geometry(f"+{x}+{y}")
    
    # Add progress message
    scan_label = tk.Label(scan_window, text="Scanning for applications...", 
                        font=('Segoe UI', 12), bg="#2e2e2e", fg="white")
    scan_label.pack(pady=20)
    
    scan_window.update()
    
    # Perform scan
    scan_installed_apps()
    
    # Close scan window
    scan_window.destroy()
    
    # Register global hotkeys
    register_hotkeys()
    
    # Ensure hotkeys are cleared on exit
    atexit.register(clear_hotkeys)
    
    # 3. Create the launcher UI window instance
    launcher_ui = LauncherWindow(root)
    launcher_hidden = True  # Start with launcher hidden
    launcher_ui.withdraw()  # Hide initially
    
    # 4. Create system tray icon
    tray_icon = create_tray_icon()
    tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
    tray_thread.start()
    
    # 5. Start the Tkinter event loop
    print(f"Launcher running in system tray with {len(installed_apps)} applications.")
    print("Type to search, Enter to launch, Esc to hide.")
    
    # Display currently active hotkeys - use hardcoded hotkey
    print(f"Global hotkey: {HARDCODED_HOTKEY}")
    
    try:
        root.mainloop()
    finally:
        # Clear hotkeys
        clear_hotkeys()
        # Stop tray icon if still running
        if tray_icon:
            tray_icon.stop()
    
    print("Launcher exited.")