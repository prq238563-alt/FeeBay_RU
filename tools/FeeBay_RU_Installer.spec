# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).resolve().parent.parent
patched_asar = root / "release" / "app.asar"
patched_unpacked = root / "release" / "app.asar.unpacked"

datas = []
if patched_asar.is_file():
    datas.append((str(patched_asar), "data"))
if patched_unpacked.is_dir():
    datas.append((str(patched_unpacked), "data/app.asar.unpacked"))

a = Analysis(
    ["patch_installer_gui.py"],
    pathex=[str(root / "tools")],
    binaries=[],
    datas=datas,
    hiddenimports=["asar"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="FeeBay_RU_Installer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
