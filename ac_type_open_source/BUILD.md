# Building AC Type

This document explains how to build AC Type from source.

## Prerequisites

1. **Python 3.8 or higher**
   - Download from https://www.python.org/downloads/
   - Make sure to add Python to PATH during installation

2. **ViGEmBus Driver**
   - Required for virtual gamepad functionality
   - Download from: https://github.com/ViGEm/ViGEmBus/releases
   - Install the driver before building

## Step-by-Step Build Instructions

### 1. Install Python Dependencies

Open a terminal in the `ac_type_open_source` directory and run:

```bash
pip install -r requirements.txt
```

This will install:
- `keyboard` - For global hotkey support
- `vgamepad` - For virtual gamepad functionality
- `pyinstaller` - For building the executable

### 2. Verify favicon.ico exists

Make sure `favicon.ico` is in the same directory as `ac_type_onefile.spec`. This will be used as the application icon.

### 3. Build the Executable

Run PyInstaller with the spec file:

```bash
python -m PyInstaller ac_type_onefile.spec --clean
```

The `--clean` flag removes previous build files for a fresh build.

### 4. Find Your Executable

After building, the executable will be located at:
```
dist/ac_type.exe
```

### 5. Test the Build

1. Run `dist/ac_type.exe`
2. Verify the application starts correctly
3. Test that the gamepad connects
4. Test typing functionality

## Troubleshooting Build Issues

### "Module not found" errors

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using the correct Python version

### Icon not included

- Verify `favicon.ico` exists in the project directory
- Check that the spec file references the icon correctly

### Large executable size

- This is normal - PyInstaller bundles Python and all dependencies
- The executable is typically 20-50 MB

### Build fails with vgamepad errors

- Make sure ViGEmBus driver is installed
- Try reinstalling vgamepad: `pip uninstall vgamepad && pip install vgamepad`

## Advanced Build Options

### Custom Icon

Replace `favicon.ico` with your own icon file (must be .ico format).

### Debug Build

To create a debug build with console output, change in `ac_type_onefile.spec`:
```python
console=True,  # Enable console
```

### Optimize Build Size

You can try UPX compression (already enabled) or exclude unused modules in the spec file.

## Distribution

To distribute your build:
1. Copy `ac_type.exe` to your distribution folder
2. Include a README with usage instructions
3. Note that users will need ViGEmBus driver installed

