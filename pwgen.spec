# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build recipe for PWGen · DGKN@Labs (Windows .exe)."""

import os

ROOT = os.path.dirname(os.path.abspath(SPEC))
ASSETS = os.path.join(ROOT, "assets")

a = Analysis(
    [os.path.join(ROOT, "pwgen_gui.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ASSETS, "pwgen.png"), "assets"),
        (os.path.join(ASSETS, "pwgen.ico"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PIL", "pytest", "numpy", "unittest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PWGen-DGKN-Labs",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ASSETS, "pwgen.ico"),
    version=os.path.join(ROOT, "packaging", "version_info.txt"),
)
