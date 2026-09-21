# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)


hiddenimports = [
    *collect_submodules("whisper"),
    *collect_submodules("tiktoken_ext"),
]

# These are exclusion guards, not application dependencies. The active GUI is
# wxPython; keep retired Qt bindings and optional test/backend modules out of
# the onefile archive even when third-party hooks see them in the build env.
# Keep numpy._pytesttester, jinja2.tests, and imported torch.testing helpers:
# runtime package initialization imports them despite their test-related names.
# SymPy also imports its Matplotlib adapter at startup; only the external
# matplotlib package is excluded, not SymPy's adapter definitions.
excluded_modules = [
    "matplotlib",
    "PySide6",
    "PySide6_Addons",
    "PySide6_Essentials",
    "shiboken6",
    "PySide2",
    "PyQt5",
    "PyQt6",
    "torch.fx.passes.tests",
    "torch.utils.tensorboard",
    "torch._dynamo.testing",
    "pylab",
    "mpl_toolkits",
    "networkx.drawing.nx_pylab",
    "pytest",
    "_pytest",
    "numba.testing",
    "numba.cuda.testing",
    "numba.runtests",
    "numba.tests",
    "numpy.testing",
    "sympy.testing",
    "sympy.combinatorics.testutil",
    "mpmath.tests",
    "pygments.lexers.testing",
    "numba.np.ufunc.tbbpool",
]

spec_path = Path(globals().get("__file__", "MMD_AutoLipTool.spec")).resolve()
project_root = spec_path.parent
ffmpeg_bin_dir = project_root / "FFmpeg" / "bin"
version_file_path = project_root / "MMD_AutoLipTool.version.txt"

datas = []
datas += collect_data_files("whisper")
datas += collect_data_files("pyopenjtalk")
datas += [("src/core/whisper_models.json", "src/core")]
datas += [("assets/usage_guide.json", "assets")]
datas += [("assets/icons/MMD_AutoLipTool.ico", "assets/icons")]
datas += [
    (str(path), "assets/icons/toolbar")
    for path in sorted((project_root / "assets" / "icons" / "toolbar").iterdir())
    if path.is_file()
]
datas += [("assets/MMD_AutoLipTool_splash.png", "assets")]
datas += [("LICENSE", ".")]
datas += [("NOTICE", ".")]
datas += [("THIRD_PARTY_LICENSES.md", ".")]
datas += [("pyproject.toml", ".")]

binaries = []
binaries += collect_dynamic_libs("pyopenjtalk")
if ffmpeg_bin_dir.is_dir():
    binaries += [
        (str(path), "FFmpeg")
        for path in sorted(ffmpeg_bin_dir.iterdir())
        if path.is_file() and path.name not in {".gitkeep", "ffplay.exe"}
    ]

a = Analysis(
    ["src/main.py"],
    pathex=[".", "src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["build_hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MMD_AutoLipTool",
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
    icon="assets/icons/MMD_AutoLipTool.ico",
    version=str(version_file_path),
)
