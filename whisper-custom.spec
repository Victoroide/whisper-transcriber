# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

current_dir = os.getcwd()

hidden_imports = [
    'whisper',
    'ffmpeg',
    'librosa',
    'numpy',
    'torch',
    'src.whisper_transcriber.app',
    'src.whisper_transcriber.audio',
    'src.whisper_transcriber.transcription',
    'tkinter',
    'tkinter.ttk',
]

datas = [('icon.ico', '.')]

models_dir = os.path.join(os.path.expanduser('~'), '.cache', 'whisper')
if os.path.exists(models_dir):
    datas.append((models_dir, './models'))

for path in sys.path:
    ffmpeg_bin = os.path.join(path, 'imageio_ffmpeg', 'binaries')
    if os.path.exists(ffmpeg_bin):
        datas.append((ffmpeg_bin, 'imageio_ffmpeg/binaries'))

a = Analysis(
    ['windows_app.py'],  # Use the new Windows entry point
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
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
    [],
    exclude_binaries=True,
    name='whisper-transcriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Make sure this is False
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='whisper-transcriber',
)