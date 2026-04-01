# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)


hiddenimports = []
hiddenimports += collect_submodules("matplotlib.backends")
hiddenimports += collect_submodules("whisper")
hiddenimports += collect_submodules("tiktoken_ext")

project_root = Path(__file__).resolve().parent
ffmpeg_bin_dir = project_root / "FFmpeg" / "bin"

datas = []
datas += collect_data_files("whisper")
datas += collect_data_files("pyopenjtalk")
datas += collect_data_files("tiktoken")
datas += collect_data_files("tiktoken_ext")
datas += [("assets/icons/MMD_AutoLipTool.ico", "assets/icons")]
datas += [("assets/MMD_AutoLipTool_splash.png", "assets")]
datas += [("LICENSE", ".")]
datas += [("NOTICE", ".")]
datas += [("THIRD_PARTY_LICENSES.md", ".")]

binaries = []
binaries += collect_dynamic_libs("pyopenjtalk")
if ffmpeg_bin_dir.is_dir():
    binaries += [
        (str(path), "FFmpeg")
        for path in sorted(ffmpeg_bin_dir.iterdir())
        if path.is_file() and path.name != ".gitkeep"
    ]

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MMD_AutoLipTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icons/MMD_AutoLipTool.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MMD_AutoLipTool",
)
