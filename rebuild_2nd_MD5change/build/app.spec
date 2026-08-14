# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path.cwd()
datas = []

resources_dir = ROOT / "src" / "md5_rebuilder" / "resources"
if resources_dir.exists():
    for path in resources_dir.iterdir():
        if path.is_file():
            datas.append((str(path), "resources"))

ffmpeg_dir = ROOT / "ffmpeg_bin"
if ffmpeg_dir.exists():
    for file in ffmpeg_dir.iterdir():
        if file.is_file():
            datas.append((str(file), "ffmpeg_bin"))

a = Analysis(
    [str(ROOT / "src" / "run.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "loguru",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "pandas", "scipy", "IPython", "notebook"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="视频MD5重构工具",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "src" / "md5_rebuilder" / "resources" / "app.ico") if (ROOT / "src" / "md5_rebuilder" / "resources" / "app.ico").exists() else None,
)
