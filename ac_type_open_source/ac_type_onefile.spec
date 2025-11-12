# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Collect vgamepad binaries and data files
binaries = []
binaries += collect_dynamic_libs('vgamepad')

datas = []
datas += collect_data_files('vgamepad')
# Include favicon.ico in the bundle
if os.path.exists('favicon.ico'):
    datas.append(('favicon.ico', '.'))

a = Analysis(
    ['ac_type.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['keyboard', 'vgamepad', 'keyboard._winkeyboard', 'keyboard._nixkeyboard'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Onefile mode - single executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ac_type',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console - GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico',  # Add icon here
)

