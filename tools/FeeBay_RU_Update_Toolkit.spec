# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).resolve().parent

datas = [
    (str(root / "translations"), "data/translations"),
    (str(root / "overrides"), "data/overrides"),
    (str(root / "reference"), "data/reference"),
]

hiddenimports = [
    "asar",
    "asar.asar",
    "deep_translator",
    "deep_translator.google",
    "bundle_paths",
    "apply_patch",
    "verify_patch",
    "patch_asar",
    "patch_core",
    "extract_strings_en",
    "build_strings_ru",
    "update_strings_ru",
    "merge_overrides",
    "update_toolkit_core",
    "paths_toolkit",
    "bundle_markers",
    "patch_adapters",
    "dictionary_migrate",
]

a = Analysis(
    ["update_toolkit_gui.py"],
    pathex=[str(root / "tools")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="FeeBay_RU_Update_Toolkit",
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
