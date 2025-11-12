import time
import keyboard
import traceback
import sys
import os
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import json

# Fix for PyInstaller: Patch vgamepad DLL path before import
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle - patch the path before vgamepad loads the DLL
    base_path = sys._MEIPASS
    dll_path_64 = os.path.join(base_path, 'vgamepad', 'win', 'vigem', 'client', 'x64', 'ViGEmClient.dll')
    dll_path_86 = os.path.join(base_path, 'vgamepad', 'win', 'vigem', 'client', 'x86', 'ViGEmClient.dll')
    
    # Add DLL directory to PATH for dependencies
    if os.path.exists(dll_path_64):
        dll_dir = os.path.dirname(dll_path_64)
        os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')
        # Monkey-patch Path.__file__ resolution for vigem_client
        import importlib.util
        import types
        # Create a mock module to intercept the DLL path
        original_path_init = Path.__init__
        def patched_path_init(self, *args, **kwargs):
            if len(args) > 0 and isinstance(args[0], str) and 'vigem' in args[0] and 'client' in args[0]:
                # This is the DLL path construction - replace it
                if os.path.exists(dll_path_64):
                    return original_path_init(self, dll_path_64, **kwargs)
                elif os.path.exists(dll_path_86):
                    return original_path_init(self, dll_path_86, **kwargs)
            return original_path_init(self, *args, **kwargs)
        
        # Actually, better approach: patch after import but before DLL load
        # We'll do this differently - patch the module after it's imported

import vgamepad as vg

# Patch the DLL path after import if running as frozen
if getattr(sys, 'frozen', False):
    try:
        import vgamepad.win.vigem_client as vigem_mod
        # The DLL is already loaded, but we can try to reload with correct path
        dll_path_64 = os.path.join(sys._MEIPASS, 'vgamepad', 'win', 'vigem', 'client', 'x64', 'ViGEmClient.dll')
        dll_path_86 = os.path.join(sys._MEIPASS, 'vgamepad', 'win', 'vigem', 'client', 'x86', 'ViGEmClient.dll')
        if os.path.exists(dll_path_64):
            vigem_mod.pathClient = Path(dll_path_64)
        elif os.path.exists(dll_path_86):
            vigem_mod.pathClient = Path(dll_path_86)
    except:
        pass

# Text will be set from GUI input field
text = ""

# Define keyboard layouts - German version
layout_upper_de = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["q","w","e","r","t","z","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l"],
    ["y","x","c","v","b","n","m","ä","ü","ö"]
]

layout_lower_de = [
    ["ä","ö","ü","ß","?","!","ß",None,None,None],
    ["q","w","e","r","t","z","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l","´"],
    ["y","x","c","v","b","n","m",",",".",None]
]

layout_symbols_de = [
    ["#","?","\"","-","~",None,None,";",":",","],
    ["%","&","@","_",None,"/",":","x",None,"="],
    ["(",")","<",">",None,None,None,"+",None,None],
    ["ß",None,None,None,None,None,None,",",".",None]
]

# Define keyboard layouts - English version
layout_upper_en = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l"],
    ["z","x","c","v","b","n","m",",","."]
]

layout_lower_en = [
    ["!","?","\"","-","~","—","'",";",":",None],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l"],
    ["z","x","c","v","b","n","m",",","."]
]

layout_symbols_en = [
    ["#","?","\"","-","~","_",".",";",":","æ",None,None],
    ["%","&","@",None,"_","/","!","x","÷","=",None,None],
    ["(",")","<",">","»","«","≡","Ξ","+",None,None,None],
    ["β","þ","ð","§","||","μ","¬",None,",",".",None,None]
]

# Default to German layouts (backward compatibility)
layout_upper = layout_upper_de
layout_lower = layout_lower_de
layout_symbols = layout_symbols_de

# Language setting (default: "german")
current_language = "german"

def set_language(lang):
    """Switch between German and English keyboard layouts"""
    global layout_upper, layout_lower, layout_symbols, current_language, current_layout
    current_language = lang
    if lang == "english":
        layout_upper = layout_upper_en
        layout_lower = layout_lower_en
        layout_symbols = layout_symbols_en
    else:  # german
        layout_upper = layout_upper_de
        layout_lower = layout_lower_de
        layout_symbols = layout_symbols_de
    # Update current layout if needed
    if current_layout == layout_upper_de or current_layout == layout_upper_en:
        current_layout = layout_upper
    elif current_layout == layout_lower_de or current_layout == layout_lower_en:
        current_layout = layout_lower
    elif current_layout == layout_symbols_de or current_layout == layout_symbols_en:
        current_layout = layout_symbols

# Timing for faster input
MOVE_HOLD = 0.05
MOVE_SETTLE = 0.03
BUTTON_HOLD = 0.02
BUTTON_SETTLE = 0.04
TRIGGER_HOLD = 0.04
TRIGGER_SETTLE = 0.04
LAYOUT_SETTLE = 0.12
POLL_INTERVAL = 0.01

cursor_row = 0
cursor_col = 0

current_layout = layout_lower
is_upper = False
is_lower = True
is_symbol = False

# Gamepad initialization - will be connected in GUI
gamepad = None
gamepad_connected = False

def init_gamepad():
    """Initialize and register the virtual gamepad with the system"""
    global gamepad, gamepad_connected
    try:
        if gamepad is None:
            gamepad = vg.VX360Gamepad()
        
        if not gamepad_connected:
            # vgamepad automatically connects when created
            # Send an initial update to register it with the system
            # This makes it visible to Dolphin and other applications
            gamepad.reset()
            gamepad.update()
            gamepad_connected = True
            print("Gamepad registered - Dolphin can now see it as XInput/0/Gamepad!")
        return True
    except Exception as e:
        error_msg = f"ERROR registering gamepad:\n{str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
        print(error_msg)
        gamepad_connected = False
        return False

def disconnect_gamepad():
    """Disconnect the virtual gamepad"""
    global gamepad_connected
    try:
        if gamepad is not None and gamepad_connected:
            # Reset gamepad state
            gamepad.reset()
            gamepad.update()
            # Note: vgamepad doesn't have explicit disconnect, it disconnects on cleanup
            gamepad_connected = False
            print("Gamepad disconnected.")
    except Exception as e:
        print(f"Error disconnecting gamepad: {e}")

# Initialize gamepad (but don't connect yet - will connect in GUI)
try:
    gamepad = vg.VX360Gamepad()
    print("Gamepad initialized (not yet connected).")
except Exception as e:
    error_msg = f"ERROR initializing gamepad:\n{str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
    print(error_msg)
    with open("ac_type_error.log", "w", encoding="utf-8") as f:
        f.write(error_msg)
    print("\nError has been saved to 'ac_type_error.log'.")
    print("\nPress any key to exit...")
    try:
        input()
    except:
        time.sleep(5)
    sys.exit(1)

# Control functions
def move_up():
    gamepad.left_joystick(0, 32767)
    gamepad.update()
    time.sleep(MOVE_HOLD)
    gamepad.left_joystick(0, 0)
    gamepad.update()
    time.sleep(MOVE_SETTLE)

def move_down():
    gamepad.left_joystick(0, -32768)
    gamepad.update()
    time.sleep(MOVE_HOLD)
    gamepad.left_joystick(0, 0)
    gamepad.update()
    time.sleep(MOVE_SETTLE)

def move_left():
    gamepad.left_joystick(-32768, 0)
    gamepad.update()
    time.sleep(MOVE_HOLD)
    gamepad.left_joystick(0, 0)
    gamepad.update()
    time.sleep(MOVE_SETTLE)

def move_right():
    gamepad.left_joystick(32767, 0)
    gamepad.update()
    time.sleep(MOVE_HOLD)
    gamepad.left_joystick(0, 0)
    gamepad.update()
    time.sleep(MOVE_SETTLE)

def press_A():
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    gamepad.update()
    time.sleep(BUTTON_HOLD)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
    gamepad.update()
    time.sleep(BUTTON_SETTLE)

def press_space():
    gamepad.right_trigger(value=255)
    gamepad.update()
    time.sleep(TRIGGER_HOLD)
    gamepad.right_trigger(value=0)
    gamepad.update()
    time.sleep(TRIGGER_SETTLE)

def press_Y():
    gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
    gamepad.update()
    time.sleep(BUTTON_HOLD)
    gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
    gamepad.update()
    time.sleep(LAYOUT_SETTLE)

def press_LT():
    gamepad.left_trigger(value=255)
    gamepad.update()
    time.sleep(BUTTON_HOLD)
    gamepad.left_trigger(value=0)
    gamepad.update()
    time.sleep(LAYOUT_SETTLE)

def wait_for_release(key):
    while keyboard.is_pressed(key):
        time.sleep(0.05)

# Cursor control
def reset_cursor():
    global cursor_row, cursor_col
    for _ in range(5):
        move_up()
        move_left()
    cursor_row = 0
    cursor_col = 0

def move_to(row, col):
    global cursor_row, cursor_col
    while cursor_row < row:
        move_down()
        cursor_row += 1
    while cursor_row > row:
        move_up()
        cursor_row -= 1
    while cursor_col < col:
        move_right()
        cursor_col += 1
    while cursor_col > col:
        move_left()
        cursor_col -= 1

# Keyboard switching
def switch_to_symbols():
    global is_symbol, is_upper, is_lower, current_layout
    if is_symbol:
        return
    if is_lower:
        press_LT()
        is_lower = False
        is_upper = True
        current_layout = layout_upper
    elif not is_upper:
        switch_to_upper()
    press_Y()
    current_layout = layout_symbols
    is_symbol = True
    is_upper = False
    is_lower = False

def switch_to_upper():
    global is_symbol, is_upper, is_lower, current_layout
    if is_upper:
        return
    if is_symbol:
        press_Y()
        is_symbol = False
        is_lower = False
        current_layout = layout_upper  # Emoji layout is skipped
        press_Y()
        current_layout = layout_lower
        is_lower = True
    if is_lower:
        press_LT()
    current_layout = layout_upper
    is_upper = True
    is_symbol = False
    is_lower = False

def switch_to_lower():
    global is_symbol, is_upper, is_lower, current_layout
    if is_symbol:
        press_Y()
        is_symbol = False
        current_layout = layout_upper  # Emoji layout is skipped
        press_Y()
        current_layout = layout_lower
        is_lower = True
        is_upper = False
        return
    if is_upper:
        press_LT()
    current_layout = layout_lower
    is_lower = True
    is_symbol = False
    is_upper = False

# Type characters
def type_char(ch, next_ch=None):
    global current_layout, is_symbol, is_upper, is_lower
    if ch == " ":
        press_space()
        return

    # Check where the character exists
    in_symbol = any(ch in row for row in layout_symbols)
    is_digit = ch.isdigit()
    is_letter = ch.isalpha()

    # Choose target layout
    if in_symbol:
        switch_to_symbols()
        layout = layout_symbols
        lookup_ch = ch
    elif is_letter and ch.islower():
        switch_to_lower()
        layout = layout_lower
        lookup_ch = ch  # lower layout stores lowercase letters/special characters
    elif is_letter and ch.isupper():
        switch_to_upper()
        layout = layout_upper
        lookup_ch = ch.lower()  # Positions in our arrays are lowercase
    elif is_digit:
        switch_to_upper()
        layout = layout_upper
        lookup_ch = ch
    else:
        # Fallback: first symbols, then lowercase
        switch_to_symbols()
        layout = layout_symbols
        lookup_ch = ch
        if not any(lookup_ch in row for row in layout_symbols):
            switch_to_lower()
            layout = layout_lower
            lookup_ch = ch

    for r in range(len(layout)):
        if lookup_ch in layout[r]:
            c = layout[r].index(lookup_ch)
            move_to(r, c)
            press_A()
            break
    else:
        print(f"Character '{ch}' not found, skipped.")

    # After symbol -> check next character
    if in_symbol and next_ch:
        if next_ch.isupper() and next_ch.isalpha():
            switch_to_upper()
        elif next_ch.islower():
            switch_to_lower()

def reset_state():
    switch_to_lower()
    reset_cursor()

# Configuration management
CONFIG_FILE = "ac_type_config.json"

def load_config():
    """Load configuration from file"""
    default_config = {
        "keybind": "f1",  # Default keybind
        "language": "german"  # Default language
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Validate and set defaults
                if "keybind" not in config or not config["keybind"]:
                    config["keybind"] = default_config["keybind"]
                if "language" not in config:
                    config["language"] = default_config["language"]
                return config
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    return default_config

def save_config(keybind=None, language=None):
    """Save configuration to file"""
    try:
        # Load existing config to preserve other settings
        existing_config = load_config()
        config = existing_config.copy()
        
        if keybind is not None:
            config["keybind"] = keybind.lower() if keybind else "f1"
        if language is not None:
            config["language"] = language
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

# GUI Application
class TypeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AC Type - Text Input")
        self.root.geometry("600x550")
        self.root.configure(bg="#000000")
        self.root.resizable(True, True)
        
        # Set window icon if available
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                icon_path = os.path.join(sys._MEIPASS, 'favicon.ico')
            else:
                # Running as script
                icon_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        # Variables
        self.running = False
        self.current_index = 0
        self.typing_thread = None
        self.stop_thread = False
        
        # Load configuration
        self.config = load_config()
        self.keybind = self.config.get("keybind", "f1")
        self.language = self.config.get("language", "german")
        self.waiting_for_keybind = False
        
        # Set language on startup
        set_language(self.language)
        
        # Create GUI
        self.create_widgets()
        
        # Register global hotkeys
        self.register_hotkeys()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Connect gamepad on startup
        self.root.after(100, self.connect_gamepad_on_startup)
    
    def connect_gamepad_on_startup(self):
        """Connect gamepad when GUI starts"""
        if init_gamepad():
            self.update_gamepad_status(True)
        else:
            self.update_gamepad_status(False)
            self.status_label.config(text="Error: Gamepad could not be connected!", fg="#FF0000")
    
    def update_gamepad_status(self, connected):
        """Update gamepad connection status display"""
        if hasattr(self, 'gamepad_status_label'):
            if connected:
                self.gamepad_status_label.config(text="Gamepad: Connected (Dolphin: XInput/0/Gamepad)", fg="#00FF00")
            else:
                self.gamepad_status_label.config(text="Gamepad: Not connected", fg="#FF0000")
    
    def on_closing(self):
        """Handle window close event"""
        self.stop_thread = True
        self.running = False
        self.unregister_hotkeys()
        disconnect_gamepad()
        self.root.destroy()
        
    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self.root,
            text="AC Type",
            font=("Arial", 24, "bold"),
            bg="#000000",
            fg="#00FF00"
        )
        title_label.pack(pady=10)
        
        # Text input label
        input_label = tk.Label(
            self.root,
            text="Text to type:",
            font=("Arial", 12),
            bg="#000000",
            fg="#FFFFFF"
        )
        input_label.pack(pady=(10, 5))
        
        # Text input field
        self.text_input = scrolledtext.ScrolledText(
            self.root,
            height=8,
            width=60,
            font=("Consolas", 11),
            bg="#1a1a1a",
            fg="#00FF00",
            insertbackground="#00FF00",
            selectbackground="#333333",
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=2,
            highlightthickness=1,
            highlightbackground="#00FF00",
            highlightcolor="#00FF00"
        )
        self.text_input.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        self.text_input.insert("1.0", "isc74NV1Y#zoI4I5X@qSEdcEKbOV")
        
        # Gamepad status label
        self.gamepad_status_label = tk.Label(
            self.root,
            text="Gamepad: Connecting...",
            font=("Arial", 10),
            bg="#000000",
            fg="#888888"
        )
        self.gamepad_status_label.pack(pady=(5, 2))
        
        # Status label
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            font=("Arial", 12),
            bg="#000000",
            fg="#FFFF00"
        )
        self.status_label.pack(pady=5)
        
        # Progress label
        self.progress_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 10),
            bg="#000000",
            fg="#888888"
        )
        self.progress_label.pack(pady=2)
        
        # Button frame
        button_frame = tk.Frame(self.root, bg="#000000")
        button_frame.pack(pady=10)
        
        # Start/Stop button
        self.start_button = tk.Button(
            button_frame,
            text=f"Start Typing ({self.keybind.upper()})",
            font=("Arial", 12, "bold"),
            bg="#00AA00",
            fg="#FFFFFF",
            activebackground="#00FF00",
            activeforeground="#000000",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.toggle_typing
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # Reset button
        reset_button = tk.Button(
            button_frame,
            text="Reset",
            font=("Arial", 12),
            bg="#333333",
            fg="#FFFFFF",
            activebackground="#555555",
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.reset_typing
        )
        reset_button.pack(side=tk.LEFT, padx=10)
        
        # Settings section
        settings_frame = tk.Frame(self.root, bg="#000000")
        settings_frame.pack(pady=10, padx=20, fill=tk.X)
        
        settings_label = tk.Label(
            settings_frame,
            text="Settings:",
            font=("Arial", 10, "bold"),
            bg="#000000",
            fg="#FFFFFF"
        )
        settings_label.pack(anchor=tk.W)
        
        keybind_frame = tk.Frame(settings_frame, bg="#000000")
        keybind_frame.pack(fill=tk.X, pady=5)
        
        keybind_label = tk.Label(
            keybind_frame,
            text="Start/Stop Key:",
            font=("Arial", 9),
            bg="#000000",
            fg="#CCCCCC"
        )
        keybind_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.keybind_entry = tk.Entry(
            keybind_frame,
            font=("Arial", 10),
            bg="#1a1a1a",
            fg="#00FF00",
            width=15,
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#333333",
            highlightcolor="#00FF00"
        )
        self.keybind_entry.pack(side=tk.LEFT, padx=5)
        self.keybind_entry.insert(0, self.keybind.upper())
        self.keybind_entry.config(state=tk.DISABLED)  # Read-only, set by button
        
        set_keybind_button = tk.Button(
            keybind_frame,
            text="Press Key",
            font=("Arial", 9),
            bg="#444444",
            fg="#FFFFFF",
            activebackground="#666666",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.set_keybind
        )
        set_keybind_button.pack(side=tk.LEFT, padx=5)
        
        self.keybind_status_label = tk.Label(
            keybind_frame,
            text="",
            font=("Arial", 8),
            bg="#000000",
            fg="#888888"
        )
        self.keybind_status_label.pack(side=tk.LEFT, padx=10)
        
        # Language selection frame
        language_frame = tk.Frame(settings_frame, bg="#000000")
        language_frame.pack(fill=tk.X, pady=5)
        
        language_label = tk.Label(
            language_frame,
            text="Keyboard Language:",
            font=("Arial", 9),
            bg="#000000",
            fg="#CCCCCC"
        )
        language_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.language_var = tk.StringVar(value=self.language)
        language_radio_frame = tk.Frame(language_frame, bg="#000000")
        language_radio_frame.pack(side=tk.LEFT, padx=5)
        
        german_radio = tk.Radiobutton(
            language_radio_frame,
            text="German",
            variable=self.language_var,
            value="german",
            font=("Arial", 9),
            bg="#000000",
            fg="#CCCCCC",
            selectcolor="#1a1a1a",
            activebackground="#000000",
            activeforeground="#00FF00",
            command=self.on_language_change
        )
        german_radio.pack(side=tk.LEFT, padx=5)
        
        english_radio = tk.Radiobutton(
            language_radio_frame,
            text="English",
            variable=self.language_var,
            value="english",
            font=("Arial", 9),
            bg="#000000",
            fg="#CCCCCC",
            selectcolor="#1a1a1a",
            activebackground="#000000",
            activeforeground="#00FF00",
            command=self.on_language_change
        )
        english_radio.pack(side=tk.LEFT, padx=5)
        
        # Instructions
        instructions = tk.Label(
            self.root,
            text=f"Press {self.keybind.upper()} to Start/Stop | Press + to Start/Stop",
            font=("Arial", 9),
            bg="#000000",
            fg="#666666"
        )
        instructions.pack(pady=5)
        
        # Dolphin info
        dolphin_info = tk.Label(
            self.root,
            text="Compatible with Dolphin Emulator - Gamepad will be connected automatically",
            font=("Arial", 8),
            bg="#000000",
            fg="#444444"
        )
        dolphin_info.pack(pady=2)
        
    def register_hotkeys(self):
        """Register global hotkeys that work even when window is not focused"""
        self.hotkey_handles = []
        try:
            # Register custom keybind
            if self.keybind:
                handle = keyboard.add_hotkey(self.keybind, self.hotkey_callback, suppress=False)
                self.hotkey_handles.append(handle)
            # Also register + key as backup
            handle_plus = keyboard.add_hotkey('+', self.hotkey_callback, suppress=False)
            self.hotkey_handles.append(handle_plus)
        except Exception as e:
            print(f"Warning: Could not register hotkeys: {e}")
    
    def unregister_hotkeys(self):
        """Unregister all global hotkeys"""
        try:
            for handle in getattr(self, 'hotkey_handles', []):
                keyboard.remove_hotkey(handle)
            self.hotkey_handles = []
        except Exception as e:
            print(f"Warning: Error unregistering hotkeys: {e}")
    
    def reregister_hotkeys(self):
        """Re-register hotkeys (used when keybind changes)"""
        self.unregister_hotkeys()
        self.register_hotkeys()
    
    def hotkey_callback(self):
        """Callback function for global hotkeys"""
        if not self.waiting_for_keybind:  # Don't trigger if setting keybind
            self.root.after(0, self.toggle_typing)
    
    def on_language_change(self):
        """Handle language selection change"""
        new_language = self.language_var.get()
        if new_language != self.language:
            self.language = new_language
            set_language(new_language)
            save_config(language=new_language)
            # Reset state to apply new layout
            if not self.running:
                reset_state()
    
    def set_keybind(self):
        """Set a new keybind by waiting for key press"""
        if self.waiting_for_keybind:
            return
        
        self.waiting_for_keybind = True
        self.keybind_status_label.config(text="Press a key...", fg="#FFFF00")
        self.keybind_entry.config(state=tk.NORMAL)
        self.keybind_entry.delete(0, tk.END)
        self.keybind_entry.insert(0, "Waiting for key...")
        self.keybind_entry.config(state=tk.DISABLED)
        
        # Start thread to capture key
        threading.Thread(target=self.capture_keybind, daemon=True).start()
    
    def capture_keybind(self):
        """Capture the next key press for keybind"""
        try:
            # Wait for any key press
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                key_name = event.name
                
                # Filter out modifier keys
                if key_name in ['shift', 'ctrl', 'alt', 'windows', 'cmd']:
                    self.root.after(0, lambda: self.keybind_status_label.config(
                        text="Modifier keys not allowed", fg="#FF0000"
                    ))
                    self.root.after(2000, lambda: self.keybind_status_label.config(text="", fg="#888888"))
                    self.waiting_for_keybind = False
                    return
                
                # Save the keybind
                self.keybind = key_name.lower()
                save_config(keybind=self.keybind, language=self.language)
                
                # Re-register hotkeys with new keybind
                self.root.after(0, self.reregister_hotkeys)
                
                # Update UI
                self.root.after(0, lambda: self.keybind_entry.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.keybind_entry.delete(0, tk.END))
                self.root.after(0, lambda: self.keybind_entry.insert(0, self.keybind.upper()))
                self.root.after(0, lambda: self.keybind_entry.config(state=tk.DISABLED))
                self.root.after(0, lambda: self.keybind_status_label.config(
                    text=f"Saved: {self.keybind.upper()}", fg="#00FF00"
                ))
                
                # Update instructions and button
                for widget in self.root.winfo_children():
                    if isinstance(widget, tk.Label) and "Press" in widget.cget("text"):
                        widget.config(text=f"Press {self.keybind.upper()} to Start/Stop | Press + to Start/Stop")
                
                # Update button text if not currently typing
                if not self.running:
                    self.root.after(0, lambda: self.start_button.config(text=f"Start Typing ({self.keybind.upper()})"))
                
                # Clear status after 2 seconds
                self.root.after(2000, lambda: self.keybind_status_label.config(text="", fg="#888888"))
                
        except Exception as e:
            self.root.after(0, lambda: self.keybind_status_label.config(
                text=f"Error: {str(e)}", fg="#FF0000"
            ))
        finally:
            self.waiting_for_keybind = False
    
    def get_text(self):
        """Get text from input field"""
        return self.text_input.get("1.0", tk.END).strip()
    
    def toggle_typing(self):
        """Start or stop typing"""
        if self.running:
            self.stop_typing()
        else:
            self.start_typing()
    
    def start_typing(self):
        """Start typing thread"""
        text_to_type = self.get_text()
        if not text_to_type:
            self.status_label.config(text="Error: No text entered!", fg="#FF0000")
            return
        
        self.running = True
        self.current_index = 0
        self.stop_thread = False
        self.start_button.config(text=f"Stop Typing ({self.keybind.upper()})", bg="#AA0000", activebackground="#FF0000")
        self.status_label.config(text="TYPING...", fg="#00FF00")
        self.text_input.config(state=tk.DISABLED)
        
        # Start typing in separate thread
        self.typing_thread = threading.Thread(target=self.typing_loop, args=(text_to_type,), daemon=True)
        self.typing_thread.start()
    
    def stop_typing(self):
        """Stop typing"""
        self.running = False
        self.stop_thread = True
        self.start_button.config(text=f"Start Typing ({self.keybind.upper()})", bg="#00AA00", activebackground="#00FF00")
        self.status_label.config(text="STOPPED", fg="#FFFF00")
        self.text_input.config(state=tk.NORMAL)
        reset_state()
    
    def reset_typing(self):
        """Reset typing state"""
        if self.running:
            self.stop_typing()
        self.current_index = 0
        reset_state()
        self.status_label.config(text="Reset", fg="#FFFF00")
        self.progress_label.config(text="")
        self.root.after(1000, lambda: self.status_label.config(text="Ready", fg="#FFFF00"))
    
    def typing_loop(self, text_to_type):
        """Main typing loop running in separate thread"""
        global text
        text = text_to_type
        reset_state()
        
        try:
            while self.running and not self.stop_thread:
                if self.current_index >= len(text):
                    self.root.after(0, self.typing_complete)
                    break
                
                # Update progress
                progress = f"{self.current_index + 1}/{len(text)}"
                self.root.after(0, lambda p=progress: self.progress_label.config(text=p) if hasattr(self, 'progress_label') else None)
                
                # Type character
                next_ch = text[self.current_index + 1] if self.current_index + 1 < len(text) else None
                type_char(text[self.current_index], next_ch)
                self.current_index += 1
                
                time.sleep(POLL_INTERVAL)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=msg, fg="#FF0000"))
            self.root.after(0, self.stop_typing)
    
    def typing_complete(self):
        """Called when typing is complete"""
        self.running = False
        self.start_button.config(text=f"Start Typing ({self.keybind.upper()})", bg="#00AA00", activebackground="#00FF00")
        self.status_label.config(text="DONE!", fg="#00FF00")
        self.text_input.config(state=tk.NORMAL)
        reset_state()
        self.progress_label.config(text="")

# Main
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = TypeApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        sys.exit(0)
    except Exception as e:
        error_msg = f"ERROR occurred:\n{str(e)}\n\nFull traceback:\n{traceback.format_exc()}"
        print(error_msg)
        
        # Write error to log file
        try:
            with open("ac_type_error.log", "w", encoding="utf-8") as f:
                f.write(error_msg)
            print("\nError has been saved to 'ac_type_error.log'.")
        except:
            pass
        
        print("\nPress any key to exit...")
        try:
            input()
        except:
            time.sleep(5)
        sys.exit(1)