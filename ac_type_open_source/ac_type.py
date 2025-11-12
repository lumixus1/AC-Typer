import time
import keyboard
import traceback
import sys
import os
from pathlib import Path
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk
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

# Language setting (default: "english")
current_language = "english"

PRIMARY_BG = "#161A23"
SECONDARY_BG = "#1F2430"
SECTION_BG = "#202737"
ACCENT_COLOR = "#4E9AF1"
ACCENT_COLOR_DARK = "#3579C9"
TEXT_PRIMARY = "#F5F7FA"
TEXT_SECONDARY = "#A4ADBF"
TEXT_MUTED = "#6F788C"
SUCCESS_COLOR = "#4CAF70"
WARNING_COLOR = "#F7C948"
ERROR_COLOR = "#FF6B6B"
STOP_COLOR = "#F26868"
STOP_COLOR_DARK = "#C75050"

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
BASE_MOVE_HOLD = 0.05
BASE_MOVE_SETTLE = 0.03
BASE_BUTTON_HOLD = 0.02
BASE_BUTTON_SETTLE = 0.04
BASE_TRIGGER_HOLD = 0.04
BASE_TRIGGER_SETTLE = 0.04
BASE_LAYOUT_SETTLE = 0.12
BASE_POLL_INTERVAL = 0.01

speed_scale = 1.0

def apply_speed_scale():
    """Apply the current speed scale to all timing values."""
    global MOVE_HOLD, MOVE_SETTLE, BUTTON_HOLD, BUTTON_SETTLE
    global TRIGGER_HOLD, TRIGGER_SETTLE, LAYOUT_SETTLE, POLL_INTERVAL

    delay_scale = 1.0 / max(speed_scale, 0.01)

    MOVE_HOLD = BASE_MOVE_HOLD * delay_scale
    MOVE_SETTLE = BASE_MOVE_SETTLE * delay_scale
    BUTTON_HOLD = BASE_BUTTON_HOLD * delay_scale
    BUTTON_SETTLE = BASE_BUTTON_SETTLE * delay_scale
    TRIGGER_HOLD = BASE_TRIGGER_HOLD * delay_scale
    TRIGGER_SETTLE = BASE_TRIGGER_SETTLE * delay_scale
    LAYOUT_SETTLE = BASE_LAYOUT_SETTLE * delay_scale
    POLL_INTERVAL = BASE_POLL_INTERVAL * delay_scale

def set_speed(scale):
    """Update the global speed scale and reapply timing values."""
    global speed_scale
    speed_scale = max(0.1, float(scale))
    apply_speed_scale()

apply_speed_scale()

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
APP_NAME = "ac_type"
DEFAULT_CONFIG_FILENAME = "ac_type_config.json"
CONFIG_ROOT = Path(os.getenv("APPDATA") or Path.home()) / "ACType"
try:
    CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not ensure config directory {CONFIG_ROOT}: {e}")
CONFIG_FILE = CONFIG_ROOT / DEFAULT_CONFIG_FILENAME
LEGACY_CONFIG_FILE = Path(DEFAULT_CONFIG_FILENAME)

def load_config():
    """Load configuration from file"""
    default_config = {
        "keybind": "f1",  # Default keybind
        "language": "english",  # Default language
        "typing_speed": 1.0
    }

    config_path = None
    if CONFIG_FILE.exists():
        config_path = CONFIG_FILE
    elif LEGACY_CONFIG_FILE.exists():
        config_path = LEGACY_CONFIG_FILE

    if config_path:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                # Validate and set defaults
                if "keybind" not in config or not config["keybind"]:
                    config["keybind"] = default_config["keybind"]
                if "language" not in config:
                    config["language"] = default_config["language"]
                if "typing_speed" not in config:
                    config["typing_speed"] = default_config["typing_speed"]

                # Migrate legacy config if necessary
                if config_path == LEGACY_CONFIG_FILE and CONFIG_FILE != LEGACY_CONFIG_FILE:
                    try:
                        CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
                        with open(CONFIG_FILE, "w", encoding="utf-8") as f_out:
                            json.dump(config, f_out, indent=2)
                    except Exception as migrate_error:
                        print(f"Warning: Could not migrate legacy config: {migrate_error}")

                return config
        except Exception as e:
            print(f"Error loading configuration: {e}")

    return default_config.copy()

def save_config(keybind=None, language=None, typing_speed=None):
    """Save configuration to file"""
    try:
        config = load_config()

        if keybind is not None:
            config["keybind"] = keybind.lower() if keybind else "f1"
        if language is not None:
            config["language"] = language
        if typing_speed is not None:
            config["typing_speed"] = typing_speed

        CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
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
        self.root.geometry("960x720")
        self.root.minsize(600, 480)
        self.root.configure(bg=PRIMARY_BG)
        self.root.resizable(True, True)

        # Apply ttk theme
        try:
            style = ttk.Style()
            if "azure" in style.theme_names():
                style.theme_use("azure")
            else:
                style.theme_use("clam")
            style.configure("Accent.TButton", background=ACCENT_COLOR, foreground=TEXT_PRIMARY)
            style.configure("Flat.TButton", background=SECTION_BG, foreground=TEXT_PRIMARY)
            style.configure("Status.TLabel", background=PRIMARY_BG, foreground=TEXT_PRIMARY, font=("Inter", 12, "bold"))
            style.configure("Muted.TLabel", background=PRIMARY_BG, foreground=TEXT_MUTED, font=("Inter", 9))
        except Exception as e:
            print(f"Warning: Could not set ttk theme: {e}")
        self.style = style if "style" in locals() else None

        # Scrollable content container
        self.container = tk.Frame(self.root, bg=PRIMARY_BG)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.container,
            bg=PRIMARY_BG,
            highlightthickness=0,
            borderwidth=0
        )
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=PRIMARY_BG)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
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
        self.typing_speed = float(self.config.get("typing_speed", 1.0))
        self.waiting_for_keybind = False
        
        # Set language on startup
        set_language(self.language)
        set_speed(self.typing_speed)
        
        # Create GUI
        self.create_widgets(self.scrollable_frame)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
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
            self.status_label.config(text="Error: Gamepad could not be connected!", fg=ERROR_COLOR)
    
    def update_gamepad_status(self, connected):
        """Update gamepad connection status display"""
        if hasattr(self, 'gamepad_status_label'):
            if connected:
                self.gamepad_status_label.config(
                    text="Gamepad: Connected (Dolphin: XInput/0/Gamepad)",
                    fg=SUCCESS_COLOR
                )
            else:
                self.gamepad_status_label.config(
                    text="Gamepad: Not connected",
                    fg=ERROR_COLOR
                )
    
    def on_closing(self):
        """Handle window close event"""
        self.stop_thread = True
        self.running = False
        self.unregister_hotkeys()
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Shift-MouseWheel>")
            self.canvas.unbind("<Configure>")
        except Exception:
            pass
        disconnect_gamepad()
        self.root.destroy()
        
    def _on_mousewheel(self, event):
        if self.root.winfo_exists():
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def _on_shift_mousewheel(self, event):
        if self.root.winfo_exists():
            self.canvas.xview_scroll(-1 * int(event.delta / 120), "units")

    def _on_canvas_configure(self, event):
        if self.root.winfo_exists():
            new_width = event.width
            try:
                scrollbar_width = self.scrollbar.winfo_width()
                if scrollbar_width:
                    new_width -= scrollbar_width
            except Exception:
                pass
            self.canvas.itemconfig(
                self.canvas_window,
                width=max(new_width, 200),
                height=max(event.height, 200)
            )

    def create_widgets(self, parent):
        # Title
        title_label = tk.Label(
            parent,
            text="AC Type",
            font=("Inter", 24, "bold"),
            bg=PRIMARY_BG,
            fg=TEXT_PRIMARY
        )
        title_label.pack(pady=10)
        
        # Text input label
        input_label = tk.Label(
            parent,
            text="Text to type:",
            font=("Inter", 11, "bold"),
            bg=PRIMARY_BG,
            fg=TEXT_SECONDARY
        )
        input_label.pack(pady=(10, 5))
        
        # Text input field
        self.text_input = scrolledtext.ScrolledText(
            parent,
            height=8,
            width=60,
            font=("Cascadia Code", 11),
            bg=SECTION_BG,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_COLOR,
            selectbackground="#2B3244",
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=2,
            highlightthickness=1,
            highlightbackground=ACCENT_COLOR,
            highlightcolor=ACCENT_COLOR
        )
        self.text_input.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        self.text_input.insert("1.0", "isc74NV1Y#zoI4I5X@qSEdcEKbOV")
        
        # Gamepad status label
        self.gamepad_status_label = tk.Label(
            parent,
            text="Gamepad: Connecting...",
            font=("Inter", 10),
            bg=PRIMARY_BG,
            fg=TEXT_MUTED
        )
        self.gamepad_status_label.pack(pady=(5, 2))
        
        # Status label
        self.status_label = tk.Label(
            parent,
            text="Ready",
            font=("Inter", 12, "bold"),
            bg=PRIMARY_BG,
            fg=WARNING_COLOR
        )
        self.status_label.pack(pady=5)
        
        # Progress label
        self.progress_label = tk.Label(
            parent,
            text="",
            font=("Inter", 10),
            bg=PRIMARY_BG,
            fg=TEXT_MUTED
        )
        self.progress_label.pack(pady=2)
        
        # Button frame
        button_frame = tk.Frame(parent, bg=PRIMARY_BG)
        button_frame.pack(pady=10)
        
        # Start/Stop button
        self.start_button = tk.Button(
            button_frame,
            text=f"Start Typing ({self.keybind.upper()})",
            font=("Inter", 12, "bold"),
            bg=ACCENT_COLOR,
            fg=TEXT_PRIMARY,
            activebackground=ACCENT_COLOR_DARK,
            activeforeground=TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.toggle_typing
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # Reset button a
        reset_button = tk.Button(
            button_frame,
            text="Reset",
            font=("Inter", 12),
            bg=SECTION_BG,
            fg=TEXT_PRIMARY,
            activebackground="#2E3647",
            activeforeground=TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.reset_typing
        )
        reset_button.pack(side=tk.LEFT, padx=10)
        
        # Settings section
        settings_frame = tk.Frame(parent, bg=SECONDARY_BG, bd=0, highlightthickness=0)
        settings_frame.pack(pady=12, padx=20, fill=tk.X)
        
        settings_label = tk.Label(
            settings_frame,
            text="Settings:",
            font=("Inter", 10, "bold"),
            bg=SECONDARY_BG,
            fg=TEXT_PRIMARY
        )
        settings_label.pack(anchor=tk.W)
        
        keybind_frame = tk.Frame(settings_frame, bg=SECONDARY_BG)
        keybind_frame.pack(fill=tk.X, pady=5)
        
        keybind_label = tk.Label(
            keybind_frame,
            text="Start/Stop Key:",
            font=("Inter", 9),
            bg=SECONDARY_BG,
            fg=TEXT_SECONDARY
        )
        keybind_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.keybind_entry = tk.Entry(
            keybind_frame,
            font=("Inter", 10),
            bg=SECTION_BG,
            fg=TEXT_PRIMARY,
            width=15,
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#2E3647",
            highlightcolor=ACCENT_COLOR
        )
        self.keybind_entry.pack(side=tk.LEFT, padx=5)
        self.keybind_entry.insert(0, self.keybind.upper())
        self.keybind_entry.config(state=tk.DISABLED)  # Read-only, set by button
        
        set_keybind_button = tk.Button(
            keybind_frame,
            text="Press Key",
            font=("Inter", 9, "bold"),
            bg=ACCENT_COLOR,
            fg=TEXT_PRIMARY,
            activebackground=ACCENT_COLOR_DARK,
            activeforeground=TEXT_PRIMARY,
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
            font=("Inter", 8),
            bg=SECONDARY_BG,
            fg=TEXT_MUTED
        )
        self.keybind_status_label.pack(side=tk.LEFT, padx=10)
        
        # Language selection frame
        language_frame = tk.Frame(settings_frame, bg=SECONDARY_BG)
        language_frame.pack(fill=tk.X, pady=5)
        
        language_label = tk.Label(
            language_frame,
            text="Keyboard Language:",
            font=("Inter", 9),
            bg=SECONDARY_BG,
            fg=TEXT_SECONDARY
        )
        language_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.language_var = tk.StringVar(value=self.language)
        language_radio_frame = tk.Frame(language_frame, bg=SECONDARY_BG)
        language_radio_frame.pack(side=tk.LEFT, padx=5)
        
        radio_kwargs = {
            "font": ("Inter", 9),
            "bg": SECONDARY_BG,
            "fg": TEXT_PRIMARY,
            "selectcolor": "#2B3244",
            "activebackground": SECONDARY_BG,
            "activeforeground": TEXT_PRIMARY
        }

        german_radio = tk.Radiobutton(
            language_radio_frame,
            text="German",
            variable=self.language_var,
            value="german",
            **radio_kwargs,
            command=self.on_language_change
        )
        german_radio.pack(side=tk.LEFT, padx=5)
        
        english_radio = tk.Radiobutton(
            language_radio_frame,
            text="English",
            variable=self.language_var,
            value="english",
            **radio_kwargs,
            command=self.on_language_change
        )
        english_radio.pack(side=tk.LEFT, padx=5)

        # Typing speed section
        speed_frame = tk.Frame(settings_frame, bg=SECONDARY_BG)
        speed_frame.pack(fill=tk.X, pady=(12, 6))

        speed_header = tk.Label(
            speed_frame,
            text="Typing Speed: (Can break when set over 1.00)",
            font=("Inter", 10, "bold"),
            bg=SECONDARY_BG,
            fg=TEXT_PRIMARY
        )
        speed_header.pack(anchor=tk.W, padx=5)

        self.speed_var = tk.DoubleVar(value=self.typing_speed)
        self.speed_slider = tk.Scale(
            speed_frame,
            from_=0.2,
            to=2.0,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=self.on_speed_change,
            length=260,
            resolution=0.05,
            showvalue=False,
            bg=SECONDARY_BG,
            highlightthickness=0,
            troughcolor="#2B3244",
            activebackground=ACCENT_COLOR,
            fg=TEXT_PRIMARY
        )
        self.speed_slider.pack(fill=tk.X, padx=5, pady=6)

        self.speed_value_label = tk.Label(
            speed_frame,
            text="",
            font=("Inter", 9, "bold"),
            bg=SECONDARY_BG,
            fg=ACCENT_COLOR
        )
        self.speed_value_label.pack(anchor=tk.W, padx=5)
        self.update_speed_display(self.typing_speed)
        
        # Instructions
        self.instructions_label = tk.Label(
            parent,
            text="",
            font=("Inter", 9),
            bg=PRIMARY_BG,
            fg=TEXT_MUTED
        )
        self.instructions_label.pack(pady=5)
        self.update_instruction_text()
        
        # Dolphin info
        dolphin_info = tk.Label(
            parent,
            text="Compatible with Dolphin Emulator - Gamepad will be connected automatically",
            font=("Inter", 8),
            bg=PRIMARY_BG,
            fg=TEXT_MUTED
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
    
    def on_speed_change(self, value):
        """Handle typing speed slider change"""
        try:
            speed = float(value)
        except (TypeError, ValueError):
            return
        set_speed(speed)
        self.typing_speed = speed
        self.update_speed_display(speed)
        save_config(typing_speed=speed)

    def update_speed_display(self, speed):
        if hasattr(self, "speed_value_label"):
            self.speed_value_label.config(text=f"{speed:.2f}x")

    def update_instruction_text(self):
        if hasattr(self, "instructions_label"):
            self.instructions_label.config(
                text=f"Start/Stop: {self.keybind.upper()} or '+'"
            )

    def set_keybind(self):
        """Set a new keybind by waiting for key press"""
        if self.waiting_for_keybind:
            return
        
        self.waiting_for_keybind = True
        self.keybind_status_label.config(text="Press a key...", fg=WARNING_COLOR)
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
                        text="Modifier keys not allowed", fg=ERROR_COLOR
                    ))
                    self.root.after(2000, lambda: self.keybind_status_label.config(text="", fg=TEXT_MUTED))
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
                    text=f"Saved: {self.keybind.upper()}", fg=SUCCESS_COLOR
                ))
                
                # Update instructions and button
                self.root.after(0, self.update_instruction_text)
                
                # Update button text if not currently typing
                if not self.running:
                    self.root.after(0, lambda: self.start_button.config(text=f"Start Typing ({self.keybind.upper()})"))
                
                # Clear status after 2 seconds
                self.root.after(2000, lambda: self.keybind_status_label.config(text="", fg=TEXT_MUTED))
                
        except Exception as e:
            self.root.after(0, lambda: self.keybind_status_label.config(
                text=f"Error: {str(e)}", fg=ERROR_COLOR
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
            self.status_label.config(text="Error: No text entered!", fg=ERROR_COLOR)
            return
        
        self.running = True
        self.current_index = 0
        self.stop_thread = False
        self.start_button.config(
            text=f"Stop Typing ({self.keybind.upper()})",
            bg=STOP_COLOR,
            activebackground=STOP_COLOR_DARK
        )
        self.status_label.config(text="TYPING...", fg=SUCCESS_COLOR)
        self.text_input.config(state=tk.DISABLED)
        
        # Start typing in separate thread
        self.typing_thread = threading.Thread(target=self.typing_loop, args=(text_to_type,), daemon=True)
        self.typing_thread.start()
    
    def stop_typing(self):
        """Stop typing"""
        self.running = False
        self.stop_thread = True
        self.start_button.config(
            text=f"Start Typing ({self.keybind.upper()})",
            bg=ACCENT_COLOR,
            activebackground=ACCENT_COLOR_DARK
        )
        self.status_label.config(text="STOPPED", fg=WARNING_COLOR)
        self.text_input.config(state=tk.NORMAL)
        reset_state()
    
    def reset_typing(self):
        """Reset typing state"""
        if self.running:
            self.stop_typing()
        self.current_index = 0
        reset_state()
        self.status_label.config(text="Reset", fg=WARNING_COLOR)
        self.progress_label.config(text="")
        self.root.after(1000, lambda: self.status_label.config(text="Ready", fg=WARNING_COLOR))
    
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
            self.root.after(0, lambda msg=error_msg: self.status_label.config(text=msg, fg=ERROR_COLOR))
            self.root.after(0, self.stop_typing)
    
    def typing_complete(self):
        """Called when typing is complete"""
        self.running = False
        self.start_button.config(
            text=f"Start Typing ({self.keybind.upper()})",
            bg=ACCENT_COLOR,
            activebackground=ACCENT_COLOR_DARK
        )
        self.status_label.config(text="DONE!", fg=SUCCESS_COLOR)
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