# AC Type - Animal Crossing Text Input Tool

A tool for automatically typing text in Animal Crossing games using a virtual gamepad. Works with Dolphin Emulator and supports both German and English keyboard layouts.

## Features

- 🎮 Virtual gamepad support (ViGEmBus)
- ⌨️ Automatic text typing via gamepad controls
- 🌍 Support for German and English keyboard layouts
- 🎯 Global hotkey support (works even when window is not focused)
- 🎨 Modern GUI with dark theme
- ⚙️ Customizable keybind settings

## Requirements

- Python 3.8 or higher
- Windows 10/11
- ViGEmBus driver (for virtual gamepad support)
- Dolphin Emulator (or compatible game)

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install ViGEmBus Driver

Download and install ViGEmBus from: https://github.com/ViGEm/ViGEmBus/releases

This driver is required for the virtual gamepad to work.

### 3. Run the Application

**Option A: Run from source**
```bash
python ac_type.py
```

**Option B: Build executable**
```bash
python -m PyInstaller ac_type_onefile.spec --clean
```

The executable will be in the `dist` folder.

## Usage

1. **Start the application** - The virtual gamepad will be automatically connected
2. **Configure Dolphin** - In Dolphin, go to Controller Settings and map the virtual gamepad (XInput/0/Gamepad)
3. **Enter text** - Type or paste the text you want to input in the text field
4. **Start typing** - Press your configured hotkey (default: F1) or click "Start Typing"
5. **Stop typing** - Press the hotkey again or click "Stop Typing"

### Settings

- **Start/Stop Key**: Customize the global hotkey for starting/stopping typing
- **Keyboard Language**: Choose between German or English keyboard layout

## Building from Source

### Prerequisites

- Python 3.8+
- PyInstaller
- All dependencies from `requirements.txt`

### Build Steps

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Build executable:
   ```bash
   python -m PyInstaller ac_type_onefile.spec --clean
   ```

3. The executable will be in `dist/ac_type.exe`

## Configuration

The application saves configuration in `ac_type_config.json`:
- `keybind`: The hotkey for start/stop (default: "f1")
- `language`: Keyboard layout language ("german" or "english")

## Troubleshooting

### Gamepad not detected in Dolphin

- Make sure ViGEmBus driver is installed
- Restart Dolphin after installing ViGEmBus
- Check that the gamepad appears in Dolphin's controller settings as "XInput/0/Gamepad"

### Hotkey not working

- The application may need administrator privileges for global hotkeys
- Try running as administrator if hotkeys don't work

### Icon not showing

- Clear Windows icon cache: Delete `%LOCALAPPDATA%\IconCache.db`
- Refresh the folder (F5) or restart Explorer

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

- Uses [vgamepad](https://github.com/scottlawsonbc/vgamepad) for virtual gamepad support
- Uses [keyboard](https://github.com/boppreh/keyboard) for global hotkey support

